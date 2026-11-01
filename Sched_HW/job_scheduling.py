from ortools.sat.python import cp_model

class SchedObj(object):
    def __init__(self, name):
        self.name = name

    def __str__(self): return "[%s: %s]" %(type(self).__name__, self.name)
    def __repr__(self): return self.__str__()
    
class Machine(SchedObj):
    def __init__(self, name, energy_cost):
        super(Machine, self).__init__(name)
        self.energy_cost = energy_cost

class Tool(SchedObj):
    def __init__(self, name, num):
        super(Tool, self).__init__(name)
        self.num = num

    def __str__(self): return "[Tool: %s: %d]" %(self.name, self.num)

class Part(SchedObj):
    def __init__(self, name, quantity, cost):
        super(Part, self).__init__(name)
        self.quantity = quantity
        self.cost = cost

    def __str__(self): return "[Part: %s: %d, %d]" %(self.name, self.quantity,
                                                     self.cost)

# parts are consumable/renewable resources; tools are sharable resources
# The parts and tools need to be available throughout the task duration
class Task(SchedObj):
    def __init__(self, name, tools, parts):
        super(Task, self).__init__(name)
        self.tools = tools
        self.parts = parts

    # A list of TaskMachine structures, indicating how a task can be
    #  accomplished by a machine
    def addTaskMachineList(self, task_machines):
        self.task_machines = task_machines

# It's a special type of Task that creates new parts
class PartsTask(Task):
    def __init__(self, name, part, quantity, tools=[], parts=[]):
        super(PartsTask, self).__init__(name, tools, parts)
        self.produced_part = part
        self.quantity = quantity

# The parameters for a machine completing a given task
class TaskMachine(SchedObj):
    def __init__(self, task, machine, duration, value):
        super(TaskMachine, self).__init__("%s-%s" %(task.name, machine.name))
        self.task = task
        self.machine = machine
        self.duration = duration
        self.value = value

class Job(SchedObj):
    def __init__(self, name, tasks):
        super(Job, self).__init__(name)
        self.tasks = tasks

class JobScheduling():
    def __init__(self, name, deadline, jobs, tasks, machines, parts, tools,
                 use_costs, use_parts):
        self.name = name
        self.deadline = deadline
        self.jobs = jobs
        self.tasks = tasks
        self.machines = machines
        self.parts = parts
        self.tools = tools
        self.use_costs = use_costs
        self.use_parts = use_parts
        self.model = None

        # Add any additional instance variables
        # BEGIN STUDENT CODE
        # END STUDENT CODE

    def _namelist(self, thelist):
        return "[%s]" %", ".join([element.name for element in thelist])

    def __repr__(self):
        return ("<JobScheduling %s: %d %s %s %s %s %s%s%s>"
                %(self.name, self.deadline, self._namelist(self.jobs),
                  self._namelist(self.tasks), self._namelist(self.machines),
                  self._namelist(self.parts), self._namelist(self.tools),
                  ", COSTS" if self.use_costs else "",
                  ", PARTS" if self.use_parts else ""))


    # Uuse this function to create a key for any of the dictionaries
    #   you may need, passing instances of Job, Task, and Machine
    def _key(self, job, task, machine):
        return (job.name, task.name, machine.name)

    # You may use this function to create the prefix for a variable.
    # For instance, self._prefix(job, task, machine)+"-start" might produce
    #  a variable name such as "J1-T1-M1-start"
    def _prefix(self, job, task, machine):
        return '%s-%s-%s' %self._key(job, task, machine)

    # Create variables for each job/task/machine
    # 
    # You likely will need integer variables for the start and end of
    #   each combination of tasks and machines that can be used to complete
    #   a job, a Boolean variable for whether that task/machine combination
    #   was actually scheduled, and an interval variable that combines the
    #   start, end, and duration of the task
    def create_job_task_variables(self):
        self.starts = {}
        self.ends = {}
        self.scheduleds = {}
        self.intervals = {}

        model = self.model
        for job in self.jobs:
            for task in job.tasks:
                for tm in task.task_machines:
                    key = self._key(job, task, tm.machine)
                    prefix = self._prefix(job, task, tm.machine)
                    self.starts[key] = model.NewIntVar(1, self.deadline,
                                                       prefix+"-start")
                    self.ends[key] = model.NewIntVar(1, self.deadline,
                                                     prefix+"-end")
                    self.scheduleds[key] = model.NewBoolVar(prefix+"-sched")
                    self.intervals[key] = \
                         model.NewOptionalIntervalVar(self.starts[key],
                                                      tm.duration,
                                                      self.ends[key],
                                                      self.scheduleds[key],
                                                      prefix+"-int")

    # Add constraints such that, for each job, each task must 
    #   be achieved by only one machine
    def create_task_constraints(self):
        model = self.model
        for job in self.jobs:
            for task in job.tasks:
                # BEGIN STUDENT CODE
                # END STUDENT CODE
                pass

    # Add constraints such that each machine can handle only
    #   one task at a time
    def create_machine_constraints(self):
        model = self.model
        for machine in self.machines:
            # BEGIN STUDENT CODE
            # END STUDENT CODE
            pass

    # For each job, add constraints such that the tasks of that job
    #   are done in sequence
    # Don't forgt that tasks can be achieved by different machines,
    #   and you need to account for that in the constraints
    def create_task_ordering_constraints(self):
        model = self.model
        for job in self.jobs:
            # BEGIN STUDENT CODE
            # END STUDENT CODE
            pass

    # For each job, add constraints such that if a job is started it
    #   must be finished.  That is, either all tasks in a job are 
    #   scheduled, or none are
    # Don't forgt that tasks can be achieved by different machines,
    #   and you need to account for that in the constraints
    def create_task_completion_constraints(self):
        model = self.model
        for job in self.jobs:
            # BEGIN STUDENT CODE
            # END STUDENT CODE
            pass

    # If a scheduled task needs a tool, it is removed from the pool at
    #   the start of the task and returned at the end.
    # Ensure that the number of tools in concurrent use is never
    #   greater than the pool size.
    def create_tools_constraints(self):
        model = self.model
        # BEGIN STUDENT CODE
        # END STUDENT CODE
        pass

    def isPartsTask(self, task): return isinstance(task, PartsTask)

    # If a scheduled task needs a part, it is removed from the pool of parts
    #   at the *start* of the task.
    # If a scheduled PartsTask creates a part, the quantity of that part
    #   produced is added to the pool at the *end* of the task
    def create_parts_constraints(self):
        model = self.model
        # BEGIN STUDENT CODE
        # END STUDENT CODE
        pass

    # Set the self.value variable to be the total value of objects produced
    #  by all the scheduled tasks
    def add_values(self):
        model = self.model
        self.value = model.NewIntVar(0, 1000000, "value")
        values = []
        for job in self.jobs:
            for task in job.tasks:
                for tm in task.task_machines:
                    sched = self.scheduleds[self._key(job, task, tm.machine)]
                    values.append(tm.value * sched)
        model.Add(self.value == sum(values))        

    # Set the self.cost variable to be the total cost of producing the objects,
    #   including both the energy costs of running the machines and the 
    #   costs of the parts used
    def add_costs(self):
        model = self.model
        self.cost = model.NewIntVar(0, 1000000, "cost")
        # BEGIN STUDENT CODE
        # END STUDENT CODE

    def add_optimization(self):
        model = self.model
        self.objective = model.NewIntVar(0, 1000000, "objective")
        self.add_values()
        if (self.use_costs):
            self.add_costs()
            model.Add(self.objective == (self.value - self.cost))
        else:
            model.Add(self.objective == self.value)
        model.Maximize(self.objective)

    # use_constraints is a list of integers 1-N about which constraints to
    #  include.  Constraints 6 and 7 are added only if
    #  self.use_parts is also True
    def create_model(self):
        self.model = cp_model.CpModel()
        self.create_job_task_variables()
        self.create_task_constraints()
        self.create_machine_constraints()
        self.create_task_ordering_constraints()
        self.create_task_completion_constraints()
        if (self.use_parts):
            self.create_tools_constraints()
            self.create_parts_constraints()
        self.add_optimization()

    # If the status is not INFEASIBLE, return a dictionary of scheduled jobs,
    #   where the job name is the dictionary key and the value is a list of
    #   tuples of the machine names that accomplish each task the start/end
    #   times of the task.
    # For instance, solution['j1'] = [('m1', 0, 1), ('m3', 3, 2)]
    #   indicates that job j1 has two tasks, the first starts at time 0 and
    #   runs for one hour; the second starts at time 3 and runs for 2 hours
    def solve(self):
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        if (status == cp_model.INFEASIBLE):
            return None, solver
        else:
            solution = {}
            for job in self.jobs:
                sched_machines = []
                for task in job.tasks:
                    for tm in task.task_machines:
                        key = self._key(job, task, tm.machine)
                        if solver.Value(self.scheduleds[key]):
                            start = int(solver.Value(self.starts[key]))
                            sched_machines.append((tm.machine.name, start,
                                                   tm.duration))
                if (len(sched_machines) > 0):
                    solution[job.name] = sched_machines
            return solution, solver
