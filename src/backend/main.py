import os 
from .project import DbtProject

# target_dbt_project = DbtProject(os.environ['PROJECT'])

target_dbt_project = tdp = DbtProject('tests/testing')

print(tdp.graph_repr())
pass
