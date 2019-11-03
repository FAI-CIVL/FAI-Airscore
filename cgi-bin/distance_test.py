from task   import Task as T
from route  import get_shortest_path


task = T.read(76)
print(f'org. opt. distance: {task.opt_dist}')
opt_dist = get_shortest_path(task)
print(f'opt. distance on ellipsoid: {opt_dist}')
