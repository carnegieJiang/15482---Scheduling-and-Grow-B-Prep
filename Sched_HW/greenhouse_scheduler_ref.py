# Import Python wrapper for or-tools CP-SAT solver.
from ortools.sat.python import cp_model
import visualize_solution
import os,sys,ortools
import dill
import schedule as sched
grader_files = "grader_files/"

#Default is in here

if(os.path.isdir(os.path.join(grader_files, "-".join(sys.version.split(".")[:2])))):
    grader_files=os.path.join(grader_files, "-".join(sys.version.split(".")[:2]))

if(os.path.isdir(os.path.join(grader_files, "-".join(ortools.__version__.split(".")[:2])))):
    grader_files=os.path.join(grader_files,"-".join(ortools.__version__.split(".")[:2]))

class Greenhouse_Scheduler:

    # name is the name of the schedule to be written to
    # behaviors_info contains for each behavior, a tuple of
    #    0: the least cumulative amount of time in minutes that the behavior needs to be run
    #    1: the spacing between the behaviors in minutes (min, max) s.t. <= 1 run in min time and >= 1 in max time
    #       This is only used for some behaviors: ["LowerTemp","LowerHumid","LowerSMoist","Camera","RaiseTemp","RaiseSMoist"]
    #       and not for any other
    #    2: the maximum amount of time the behavior should run at night between [20,24) U [0,8)
    # minutes_per_chunk is the number of minutes that we break the day into

    def __init__(self, name, behaviors_info, minutes_per_chunk, print=True):
        f = open(grader_files+"/RefSol.pkl", "rb")
        self.GB = dill.load(f)
        f.close()
        self.GB.init(name, behaviors_info, minutes_per_chunk, print)

    # This is the function to call to test the problem being solved.
    # It takes the requirements from init and
    def solveProblem(self, visualize=False):
        return self.GB.solveProblem(visualize)

if __name__ == "__main__":
    #This is an example Schedule generation problem

    #schedule 30 minute chunks
    minutes = 30
    behaviors_info = {}

    #Light should be on for at least 12 hours
    # start times should be schedules at least 30 minutes apart and no more than 4 hours
    # (note, this allows for back to back scheduling)
    # and lights should be on no more than 3 hours at night
    behaviors_info["Light"] = (10*60,(minutes,4*60),3*60)
    behaviors_info["LowerHumid"] = (8*60,(minutes,60),12*60)
    behaviors_info["LowerTemp"] = (120,(2*60,4*60),12*60)
    behaviors_info["RaiseTemp"] = (120,(2*60,4*60),12*60)
    behaviors_info["LowerSMoist"] = (120,(2*60,4*60),12*60)
    behaviors_info["RaiseSMoist"] = (120,(2*60,4*60),12*60)
    #camera should not be on at all at night
    behaviors_info["Camera"] = (60,(3*60,6*60),0)
    problem = Greenhouse_Scheduler("main_schedule.txt",behaviors_info, minutes)

    solution = problem.solveProblem(visualize=True)
