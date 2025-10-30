import os 
from project import DbtProject

# target_dbt_project = DbtProject(os.environ['PROJECT'])

target_dbt_project = DbtProject('tests/testing')


