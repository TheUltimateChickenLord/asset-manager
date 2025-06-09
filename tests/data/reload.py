import sys
import importlib


def reload_all_modules():
    """Reload all imported modules and their dependencies"""
    reloaded: set[str] = set()

    for name, module in list(sys.modules.items()):
        if name in reloaded:
            continue
        if not (name.startswith("tests.") or name.startswith("asset_manager.")):
            continue
        try:
            importlib.reload(module)
            reloaded.add(name)
        except Exception as e:
            print(f"Could not reload {name}: {e}")
