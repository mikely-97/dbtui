"""
Isolated mode support for UI development.

When a '.isolated' file exists in the working directory, the frontend uses
mock backend classes from the pseudo module. This allows developing and
testing the UI without a real dbt project.
"""
from os.path import exists

isolated = exists('.isolated')
if isolated:
    from ..pseudo.pseudo import DbtModel, DbtProject
else:
    from ...backend.project import DbtModel, DbtProject
