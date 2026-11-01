#!/usr/bin/env python
import os, sys
import argparse, dill
import ortools
from ortools.sat.python import cp_model
import visualize_solution as vs
import job_scheduling as js
from parse_orders import get, parse_orders
from greenhouse_scheduler import Greenhouse_Scheduler
import schedule as sched

grader_files = "grader_files"

if(os.path.isdir(os.path.join(grader_files, "-".join(sys.version.split(".")[:2])))):
    grader_files=grader_files+"/"+"-".join(sys.version.split(".")[:2])
    #print(grader_files)

if(os.path.isdir(os.path.join(grader_files, "-".join(ortools.__version__.split(".")[:2])))):
    grader_files=grader_files+"/"+"-".join(ortools.__version__.split(".")[:2])
    #print(grader_files)

job_scheduling_file = grader_files + "/jobscheduling.pkl"

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--part', default=-1, type=int,
                    help='Which part to test (defaults to all)')
parser.add_argument('-s', '--step', default=-1, type=int,
                    help='Which step to test (defaults to all)')
parser.add_argument('-t', '--test', default=None,
                    help='Which tests to perform - can be a single test or list, (defaults to all); use ? to see which are valid')
parser.add_argument('-g', '--graphics', action='store_true',
                    help="Visualize the schedules")
parser.add_argument('-v', '--verbose', action='store_true',
                    help="Verbose output")
args = parser.parse_args()

def create_constrained_model(order, use_constraints):
    order.model = cp_model.CpModel()
    order.create_job_task_variables()
    if (1 in use_constraints): order.create_task_constraints()
    if (2 in use_constraints): order.create_machine_constraints()
    if (3 in use_constraints): order.create_task_ordering_constraints()
    if (4 in use_constraints): order.create_task_completion_constraints()
    if (order.use_parts):
        if (5 in use_constraints): order.create_tools_constraints()
        if (6 in use_constraints): order.create_parts_constraints()
    order.add_optimization()

class JS_Solution:
    def __repr__(self):
        return ("<%s: %s %s>" %(type(self).__name__, self.name, self.solution))

    def __init__(self, name):
        self.name = name
        self.solution = None
        self.objective = 0
        self.value = 0
        self.cost = 0

    def initialize(self, test):
        self.solution = test.solution
        self.objective = test.objective
        self.value = test.value
        self.cost = test.cost
        self.use_costs = test.use_costs

    def print_solution(self, type):
        print("%s solution:" %type)
        print(" Objective: %d" %self.objective)
        if (self.use_costs):
            print(" Value: %d, Cost: %d" %(self.value, self.cost))
        for job in self.solution:
            print("  %s: %s" %(job, self.solution[job]))

# order: a JobScheduling instance (student code)
# ref_js_class: the JobScheduling class with refsol code (imported from dill)
# solution: a list of the schedule created
class JS_Test(JS_Solution):
    def __init__(self, order, ref_js_class, constraints_to_use):
        super(JS_Test, self).__init__(order.name)
        self.use_costs = order.use_costs
        self.ref_js = ref_js_class(order.name+"_refsol", order.deadline,
                                   order.jobs, order.tasks, order.machines,
                                   order.parts, order.tools,
                                   order.use_costs, order.use_parts)
        create_constrained_model(self.ref_js, constraints_to_use)
        self.order = order
        self.order.create_model()

    def solve(self, verbose=False, visualize=False):
        self.solution, solver = self.order.solve()
        is_solved = False
        self.objective = self.value = self.cost = 0
        if (verbose):
            print(" Branches: %d" %solver.NumBranches())
            print(" Wall time: %f" %solver.WallTime())
        if (self.solution == None):
            print("  Infeasible schedule!!")
        elif (len(self.solution) == 0):
            print("  Empty schedule!!")
        elif (not check_solution_syntax(self.solution, self.order)):
            print("  Your solution is not compatible with the required format;")
            print("    Use -v to see what your solution format looks like\n")
        else:
            is_solved = True

        if (is_solved):
            self.objective = solver.Value(self.order.objective)
            if (self.order.use_costs):
                self.value = solver.Value(self.order.value)
                self.cost = solver.Value(self.order.cost)
            
        return is_solved
            
# refsol is a list [schedule, objective, value, cost]
def is_schedule_correct(test, refsol, verbose=False):
    tname = order.name
    solution = test.solution

    # Check whether solution is compatible with the refsol class constraints
    is_correct = True
    ref_js = test.ref_js
    try:
        for jname in solution:
            tasks = get(jname, test.order.jobs).tasks
            for idx, (mname, start, duration) in enumerate(solution[jname]):
                tname = tasks[idx].name
                end = start + duration
                ref_js.model.Add(ref_js.scheduleds[jname, tname, mname] == True)
                ref_js.model.Add(ref_js.starts[jname, tname, mname] == start)
                ref_js.model.Add(ref_js.ends[jname, tname, mname] == end)
        status = cp_model.CpSolver().Solve(ref_js.model)
    except Exception as inst:
        print("EXCEPTION", inst.args); status = cp_model.INFEASIBLE
    if (status == cp_model.INFEASIBLE):
        print("INCORRECT: Your solution is infeasible given the refsol constraints")
        is_correct = False
    elif (test.objective != refsol.objective):
        print("INCORRECT: Your solution is NOT consistent with the refsol constraints")
        is_correct = False
    else:
        print("CORRECT: Your solution is consistent with the refsol!")

    if verbose or not is_correct:
        test.print_solution("Your")
        refsol.print_solution("Reference")

    return is_correct

def check_solution_syntax(solution, test):
    for jname in solution:
        if (not get(jname, test.jobs)): return False
        for mname, start, duration in solution[jname]:
            if (not get(mname, test.machines) or start < 0 or duration < 1):
                return False
    return True

def plot_schedule(test):
    order = test.order
    assigned_jobs = {}
    for id, machine in enumerate(order.machines): machine.id = id
    for job_id, job in enumerate(order.jobs):
        if (job.name in test.solution):
            for machine, start, duration in test.solution[job.name]:
                assigned_jobs[get(machine, order.machines).id,
                              job_id] = (True, start, duration,
                                         start+duration)
    vs.plot_intervals([job.name for job in order.jobs],
                      order.deadline, True, assigned_jobs)

def do_scheduling_test(order, refsols, refsol_class, constraints_to_use,
                       visualize=False, verbose=False):
    print("Running test %s, constraints: %s" %(test_name, constraints_to_use))
    if verbose: print(" Costs: %s, Parts: %s" %(order.use_costs, order.use_parts))
    test = JS_Test(order, refsol_class, constraints_to_use)
    status = test.solve(verbose, visualize)

    if (test.solution):
        correct = is_schedule_correct(test, refsols[order.name], verbose)
        if (visualize): plot_schedule(test)
        print('')
        return correct
    else: return False

def add_orders(filename):
    orders = {}
    for order in parse_orders(filename):
        if (orders.get(order.name)):
            raise Exception("Order %s already loaded" %order.name)
        orders[order.name] = order
    return orders

order_files = ["grader_files/orders_s1.txt", "grader_files/orders_s2.txt",
               "grader_files/orders_s3.txt", "grader_files/orders_s4.txt",
               "grader_files/orders_s5.txt", "grader_files/orders_s6.txt",
               "grader_files/orders_s7.txt", "grader_files/orders_s8.txt"]
num_steps = 7
if args.part in [-1, 1]:
    with open(job_scheduling_file, "rb") as f:
        refsol_class, refsols = dill.load(f)

    tot_correct = tot_num = 0
    for step in [args.step] if args.step > 0 else list(range(1,num_steps+1)):
        correct = 0
        orders = add_orders(order_files[step-1])
        all_tests = [order for order in orders]
        if (not args.test):
            tests = all_tests
        elif (args.test == '?'):
            print("Valid tests are %s" %all_tests); exit()
        else:
            tests = args.test.replace(",", " ").split(" ")
            for test in tests:
                if (not test in all_tests):
                    print("%s is not a valid test for this part" %test)
                    print("Valid tests are %s" %all_tests); exit()

        constraints_to_use = list(range(1,step+1))
        for test_name in tests:
            order = orders[test_name]
            correct += do_scheduling_test(order, refsols, refsol_class,
                                          constraints_to_use,
                                          args.graphics, args.verbose)
        print("Part 1, Step %d: %d correct out of %d\n"
              %(step, correct, len(tests)))
        tot_correct += correct; tot_num += len(tests)

    if (args.step < 0):
        print("Part 1: Total %d correct out of %d\n" %(tot_correct, tot_num))

minutes = 30

def solveProblem_constrained(problem, testType, visualize):
    # Add only the constraints needed for this test type
    if (testType >= 1): problem.createDurationConstraints(problem.model)
    if (testType >= 2): problem.createMutualExclusiveConstraints(problem.model)
    if (testType >= 3): problem.createNightConstraints(problem.model)
    if (testType >= 4): problem.createSpacingConstraints(problem.model)
    return problem.solve(problem.model, visualize)

def greenhouse_test(test_num, testType, behaviors_info, should_succeed=True):
    correct = 0
    print("Running test %s %s..."
          %(test_num, ("" if not args.graphics else
                       "(expect a schedule image here) " if should_succeed else
                       "(infeasible constraints - should not expect a schedule)" )))

    problem = Greenhouse_Scheduler("main_schedule.txt",behaviors_info,
                                   minutes, args.verbose)
    solution = solveProblem_constrained(problem, testType, args.graphics)
    if (solution == None):
        if should_succeed:
            print("FAILED: Your model found no solution where one exists")
        else:
            print("CORRECT: Your model found no solution for infeasible constraints")
            correct = 1
    else:
        if should_succeed:
            print("CORRECT: Your model found a solution")
            correct = 1
        else:
            print("FAILED: Your model found a solution where one should not exist")
    print("")
    return correct

def greenhouse_test_against_refsol(test_num, testType, behaviors_info):
    correct = 0
    print("Running test %s against the refsol %s..."
          %(test_num,
            ("" if not args.graphics else "(expect a schedule image here) ")))

    problem = Greenhouse_Scheduler("main_schedule.txt",behaviors_info,
                                   minutes, args.verbose)
    solution = solveProblem_constrained(problem, testType, args.graphics)

    with open(grader_files+"/Autograde.pkl", "rb") as f:
        autosolver = dill.load(f)
    autosolver.init("main_schedule.txt", behaviors_info, minutes, testType)
    solution = autosolver.solveProblem()

    if (solution == None):
        print("FAILED: Your solution was INCONSISTENT with the refsol constraints")
    else:
        print("CORRECT: Your solution was consistent with the refsol constraints")
        correct = 1
    print("")
    return correct

if (args.part in [-1, 2]):
    testType = 4 if (args.step < 0) else args.step
    score = 0
    max_score = 5

    behaviors_info = {}
    behaviors_info["Light"] = (10*60, (minutes, 4*60), 3*60)
    behaviors_info["LowerHumid"] = (8*60, (minutes, 60), 12*60)
    behaviors_info["LowerTemp"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["RaiseTemp"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["LowerSMoist"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["RaiseSMoist"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["Camera"] = (60, (3*60, 6*60), 0)
    score += greenhouse_test(1, testType, behaviors_info)

    behaviors_info_inf = {}
    behaviors_info_inf["Light"] = (16*60, (minutes, 4*60), 0)
    behaviors_info_inf["LowerHumid"] = (12*60, (minutes, 60), 12*60)
    behaviors_info_inf["LowerTemp"] = (120, (2*60, 4*60), 12*60)
    behaviors_info_inf["RaiseTemp"] = (120, (2*60, 4*60), 12*60)
    behaviors_info_inf["LowerSMoist"] = (120, (2*60, 4*60), 12*60)
    behaviors_info_inf["RaiseSMoist"] = (120, (2*60, 4*60), 12*60)
    behaviors_info_inf["Camera"] = (300, (6*60, 6*60), 0)
    # Feasible for duration constraints only, infeasible for mutex and beyond
    score += greenhouse_test(2, testType, behaviors_info_inf, testType == 1)

    score += greenhouse_test_against_refsol(3, testType, behaviors_info)

    behaviors_info = {}
    behaviors_info["Light"] = (5*60, (minutes, 4*60), 3*60)
    behaviors_info["LowerHumid"] = (8*60, (minutes, 60), 12*60)
    behaviors_info["LowerTemp"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["RaiseTemp"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["LowerSMoist"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["RaiseSMoist"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["Camera"] = (30*2, (6*60, 6*60), 0)
    score += greenhouse_test_against_refsol(4, testType, behaviors_info)

    behaviors_info = {}
    # Light should be on for at least 12 hours
    # start times should be schedules at least 30 minutes apart and no more than 4 hours
    # (note, this allows for back to back scheduling)
    # and lights should be on no more than 3 hours at night
    behaviors_info["Light"] = (4*60, (minutes, 4*60), 3*60)
    behaviors_info["LowerHumid"] = (5*60, (minutes, 60), 12*60)
    behaviors_info["LowerTemp"] = (180, (2*60, 4*60), 12*60)
    behaviors_info["RaiseTemp"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["LowerSMoist"] = (120, (2*60, 4*60), 12*60)
    behaviors_info["RaiseSMoist"] = (120, (2*60, 4*60), 12*60)
    # camera should not be on at all at night
    behaviors_info["Camera"] = (120, (3*60, 6*60), 0)
    score +=greenhouse_test_against_refsol(5, testType, behaviors_info)

    print("Total Score for Part 2: %s/%s" %(score, max_score))

