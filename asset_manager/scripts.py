"""Contains utility scripts for the repo"""

import os


def lint():
    """Lint the asset_manager folder"""
    os.system("poetry run pylint asset_manager/")


def test():
    """Run the python tests"""
    os.system("poetry run pytest --verbose")
