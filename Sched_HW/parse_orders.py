import job_scheduling as js

def get(name, objects):
    for object in objects:
        if (name == object.name): return object
    return None

# For each parameter, if it is one of the allowable_params, add that to
#  a dictionary.  The parameter can be a tuple, in which case the value
#  is to be processed according to the type
# required_params is a list of parameters that must be present.
# Raise exceptions if not an allowable parameter or not all required
#  parameters are found
def parse_attrs(type, name, params, allowable_params, required_params=None):
    pvals = {}
    for param in params:
        pname = param[0]
        allowed, ptype = find_param(pname, allowable_params)
        if (allowed):
            sparam = param[1] if len(param) > 1 else 'True'
            pvals[pname] = parse_list(sparam) if ptype == list else ptype(sparam)
        else:
            raise Exception("Unknown parameter for %s %s: %s" %(type, name, pname))
    for required in required_params:
        if (isinstance(required, tuple)): required = required[0]
        if (pvals.get(required) == None):
            raise Exception("Missing parameter for %s %s: %s"
                            %(type, name, required))
    return pvals

# Return the value in the list of parameters that matches
def find_param(pname, parameters):
    for param in parameters:
        if (pname == (param[0] if isinstance(param, tuple) else param)):
            return param if isinstance(param, tuple) else (param, str)
    return (None, None)

# Parse the comma-separated list, if it exists
def parse_list(comma_list):
    return comma_list.split(',') if comma_list else None

def process_task_machines(items):
    for tm_name in items['Task-Machine']:
        tname, mname = tm_name.split(',')
        tm = items['Task-Machine'][tm_name]
        task = items['Task'][tname]
        if (task.get('task-machines') == None): task['task-machines'] = []
        task['task-machines'].append((mname, tm['duration'], tm['value']))

def collect_tasks(jobs, items):
    tasks = set()
    for job in jobs:
        tasks = tasks.union(items['Job'][job]['tasks'])
    tasks = list(tasks); tasks.sort()
    return tasks

def collect_parts(tasks, items):
    parts = set()
    for task in tasks:
        parts = parts.union(items['Task'][task].get('parts', {}))
    parts = list(parts); parts.sort()
    return parts

def collect_tools(tasks, items):
    tools = set()
    for task in tasks:
        tools = tools.union(items['Task'][task].get('tools', {}))
    tools = list(tools); tools.sort()
    return tools

def create_order(order_name, deadline, machines_list, tasks_list, jobs_list,
                 parts_list, tools_list, use_costs, use_parts):
    machines = [js.Machine(name, energy_cost)
                for name, energy_cost in machines_list]
    parts = [js.Part(name, quantity, cost)
             for name, quantity, cost in parts_list]
    tools = [js.Tool(name, num) for name, num in tools_list]
    tasks = []
    for task_list in tasks_list:
        name = task_list[0]
        tnames = task_list[-3]; pnames = task_list[-2]; tms = task_list[-1]
        if (len(task_list) > 4): # It's a PartsTask
            task = js.PartsTask(name, get(task_list[1], parts), task_list[2],
                                [get(tname, tools) for tname in tnames],
                                [get(pname, parts) for pname in pnames])
        else:
            task = js.Task(name, [get(tname, tools) for tname in tnames],
                           [get(pname, parts) for pname in pnames])
        task.addTaskMachineList([js.TaskMachine(task, get(mname, machines),
                                                duration, value)
                                 for mname, duration, value in tms])
        tasks.append(task)
    jobs = [js.Job(name, [get(task, tasks) for task in tnames])
            for name, tnames in jobs_list]
    return js.JobScheduling(order_name, deadline, jobs, tasks, machines,
                            parts, tools, use_costs, use_parts)
def process_order(order_name, order_dict, items):
    jobs = order_dict['jobs']
    tasks = collect_tasks(jobs, items)
    task_items = items['Task']
    part_items = items['Part']

    return \
      create_order(order_name, order_dict['deadline'],
                   [(mname, items['Machine'][mname]['energy'])
                    for mname in order_dict['machines']],
                   [(tname, task_items[tname].get('tools', []),
                     task_items[tname].get('parts', []),
                     task_items[tname]['task-machines'])
                    if not task_items[tname].get('made-part') else
                    (tname, task_items[tname]['made-part'],
                     task_items[tname]['quantity'],
                     task_items[tname].get('tools', []),
                     task_items[tname].get('parts', []),
                     task_items[tname]['task-machines']) for tname in tasks],
                   [(jname, items['Job'][jname]['tasks']) for jname in jobs],
                   [(pname, part_items[pname]['num'], part_items[pname]['cost'])
                    for pname in collect_parts(tasks, items)],
                   [(tname, items['Tool'][tname]['num'])
                    for tname in collect_tools(tasks, items)],
                   order_dict.get('use_costs', False),
                   order_dict.get('use_parts', False))

def process_orders(items):
    return [process_order(oname, order, items)
            for oname, order in items['Order'].items()]

item_params = {'Machine': ([('energy', int)], ['energy']),
               'Tool': ([('num', int)], ['num']),
               'Part': ([('num', int), ('cost', int)], ['num', 'cost']),
               'Task': ([('tools', list), ('parts', list),
                         'made-part', ('quantity', int)], []),
               'Task-Machine': ([('duration', int), ('value', int)],
                                ['duration', 'value']),
               'Job': ([('tasks', list)], ['tasks']),
               'Order': ([('deadline', int), ('jobs', list), ('machines', list),
                          ('use_costs', bool), ('use_parts', bool)],
                         ['deadline', 'jobs', 'machines'])}

def parse_orders(filename):
    # Dictionary whose keys are item name and values are dict of {name: params}
    items = {}
    for item in item_params: items[item] = {}
    with open(filename) as f:
        for line in f.readlines():
            l = line.split('#')[0].strip(' \n')
            if l: 
                parts = [p.strip(' ').split(':') for p in l.replace(' ','').split(';')]
                type = parts[0][0]
                name = parts[0][1]
                item_param = item_params.get(type)
                if (item_param):
                    pvals = parse_attrs(type, name, parts[1:], 
                                        item_param[0], item_param[1])
                    items[type][name] = pvals
                else:
                    raise Exception("Unknown item: %s" %type)
    process_task_machines(items)
    return process_orders(items)

if __name__ == '__main__':
    orders = parse_orders("grader_files/orders.txt")
    for order in orders: print(order)
