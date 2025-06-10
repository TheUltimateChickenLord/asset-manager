"""Module defining methods to cast objects to pydantic schemas"""

from types import NoneType
from typing import TypeVar, Union, get_args, get_origin, overload, Sequence

from fastapi import HTTPException, status
from pydantic import BaseModel

from asset_manager.db.base import Base


T = TypeVar("T", bound=BaseModel)


@overload
def cast_to_pydantic(input_objs: Base, output_type: type[T]) -> T: ...


@overload
def cast_to_pydantic(input_objs: Sequence[Base], output_type: type[T]) -> list[T]: ...


def cast_to_pydantic(
    input_objs: Union[Sequence[Base], Base], output_type: type[T]
) -> Union[list[T], T]:
    """Drops fields from db classes that shouldn't be returned to the user"""

    def cast_single(input_obj: Base, output_type: type[T]) -> T:
        # generate empty dict to create pydantic object from
        final_dict = {}
        for key in output_type.model_fields.keys():
            # if the key isnt in the pydantic schema then just skip it
            value = getattr(input_obj, key)

            # calculate if the pydantic type is another pydantic type
            # i.e. if the attribute in the class is `key: <subclass of BaseModel>`
            cast = False
            sub_output_type = output_type.model_fields[key].annotation
            if sub_output_type is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Cannot safely cast response",
                )
            # check if it is directly a pydantic class
            if issubclass(sub_output_type, BaseModel):
                cast = True
            # check if it is a list of pydantic classes
            elif get_origin(sub_output_type) is list:
                generic_of_sub_output_type = get_args(sub_output_type)[0]
                if issubclass(generic_of_sub_output_type, BaseModel):
                    sub_output_type = generic_of_sub_output_type
                    cast = True
            # check if it is optional
            elif get_origin(sub_output_type) is Union:
                args = [arg for arg in get_args(sub_output_type) if arg is not NoneType]
                if len(args) == 1:
                    generic_of_sub_output_type = args[0]
                    if (
                        issubclass(generic_of_sub_output_type, BaseModel)
                        and value is not None
                    ):
                        sub_output_type = generic_of_sub_output_type
                        cast = True
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Cannot safely cast response",
                    )

            # save the output in the dict, casting where necessary
            if cast:
                final_dict[key] = cast_to_pydantic(value, sub_output_type)
            else:
                final_dict[key] = value
        return output_type(**final_dict)

    if isinstance(input_objs, Sequence):
        return [cast_single(input_obj, output_type) for input_obj in input_objs]
    return cast_single(input_objs, output_type)
