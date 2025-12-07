# TODO: i don't know what to do with it, but let it be for now

from os.path import exists

isolated = exists('.isolated')
if isolated:
    from ..pseudo.pseudo import DbtModel, DbtProject
else:
    from ...backend.project import DbtModel, DbtProject
