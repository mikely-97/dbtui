import os 
from project import DbtProject

# target_dbt_project = DbtProject(os.environ['PROJECT'])

target_dbt_project = DbtProject('tests/testing')

target_dbt_project.populate_graph()
g = target_dbt_project.graph
for a, b in g.edges: print(a.name, '->', b.name)
print(g)
