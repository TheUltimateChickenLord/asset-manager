from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo
from tests.data.models import DummyModelHardDelete, DummyModelSoftDelete


class DummySoftRepo(AbstractCRUDRepo[DummyModelSoftDelete]):
    pass


class DummyHardRepo(AbstractCRUDRepo[DummyModelHardDelete]):
    pass
