# Import Python wrapper for or-tools CP-SAT solver.
from ortools.sat.python import cp_model
import visualize_solution

class Greenhouse_Scheduler:

    # name is the name of the schedule to be written to
    # behaviors_info contains for each behavior, a tuple of
    #    0: the least cumulative amount of time in minutes that the behavior 
    #       needs to be run
    #    1: the spacing between the behaviors in minutes (min, max) s.t.
    #       <= 1 run in min time and >= 1 in max time
    #       This is only used for some behaviors: (LowerTemp, LowerHumid,
    #       LowerSMoist, Camera, RaiseTemp, RaiseSMoist) and not for any other
    #    2: the maximum amount of time the behavior should run at night
    #       between [20,24) U [0,8)
    # minutes_per_chunk is the number of minutes that we break the day into
    def __init__(self, name, behaviors_info, minutes_per_chunk,print=False):
        self.name = name
        self.behaviors_info = behaviors_info
        self.minutes_per_chunk = minutes_per_chunk #all are the same length
        self.horizon = 24*60//self.minutes_per_chunk
        self.print = print

        # Create the model.
        self.model = cp_model.CpModel()

        # Creates behavior/time dictionary mapping to binary variables.
        self.all_jobs = {}
        #This is boolean and is 1 when the variable is true
        for behavior in self.behaviors_info:
            for time in range(self.horizon):
                suffix = '%s_%i' % (behavior, time)
                #boolean variable for whether a robot does a job at a time
                self.all_jobs[behavior,time] = self.model.NewBoolVar(suffix)

    # This is the function to call to test the problem being solved.
    # It takes the requirements from the class constructor
    # DO NOT ALTER THIS FUNCTION!
    def solveProblem(self, visualize=False):
        #Each Type of constraint that you will need to make
        #This has been broken down for you
        self.createDurationConstraints(self.model)
        self.createMutualExclusiveConstraints(self.model)
        self.createNightConstraints(self.model)
        self.createSpacingConstraints(self.model)
        return self.solve(self.model, visualize)

    # CREATE and add constraints for the minimum duration each behavior
    #     should be run (see self.behaviors_info)
    def createDurationConstraints(self, model):
        for behavior in self.behaviors_info:
            duration = self.behaviors_info[behavior][0] # in minutes
            # BEGIN STUDENT CODE
            # END STUDENT CODE
            pass

    # CREATE and add constraints for behaviors that cannot be run
    #   simultaneously for each time
    # 1. All raising and lowering behaviors for the same value (temperature,
    #   humidity, moisture) must be mutually exclusive
    # 2. Any two behaviors in this list that need to use the same
    #   actuator on (e.g., LowerHumid, LowerSMoist) or in which one wants the
    #   actuator on and one wants it off (e.g., LowerHumid and RaiseTemp)
    #   must be mutually exclusive (note: they are not exclusive if they
    #   both need the actuator off)
    #    LowerTemp: fan on, lights off
    #    RaiseTemp: lights on, fan off
    #    LowerHumid: fan on, wpump off
    #    LowerSMoist: fan on, wpump off
    #    RaiseSMoist: fan off, wpump on
    #    Lights: lights on
    #    Camera: lights on
    def createMutualExclusiveConstraints(self,model):
        for time in range(self.horizon):
            # BEGIN STUDENT CODE
            # END STUDENT CODE
            pass

    # CREATE and add constraints for maximum amount of time behaviors should
    # be run at night between [20,24) U [0,8)
    def createNightConstraints(self, model):
        for behavior in self.behaviors_info:
            max_night = self.behaviors_info[behavior][2] # in minutes
            # BEGIN STUDENT CODE
            # END STUDENT CODE
            pass

    # CREATE and add constraints for running behaviors at most once per 
    #    minimum and at least once per maximum time (given in minutes)
    #    Not applicable for the "Light" behavior
    #    For the "Camera" behavior, constrain only from 8am to 8pm; for all
    #    other behaviors, midnight to midnight (0 to 24 hours)
    def createSpacingConstraints(self,model):
        for behavior in self.behaviors_info:
            if (behavior != "Light"):
                min_spacing, max_spacing = self.behaviors_info[behavior][1]
                # BEGIN STUDENT CODE
                # END STUDENT CODE
                pass

    # Solve model.
    def solve(self,model, visualize):
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status == cp_model.INFEASIBLE:
            if self.print: print("infeasible")
            return None
        else:
            if self.print: print("feasible")
            assigned_jobs_list = {}
            i =0
            blist = self.behaviors_info.keys()

            f = open(self.name,"w")

            #print and write out to self.name the schedule
            for behavior in blist:
                if self.print: print("Behavior:",behavior)
                s = "  Times: "
                for t in range(self.horizon):
                    assigned_jobs_list[i,i,t/2.] = solver.Value(self.all_jobs[behavior,t])
                    if solver.Value(self.all_jobs[behavior,t]) > 0:
                        s += str(t/2.)+" "
                        f.write(behavior+"Behavior"+" ")
                        f.write(("0" if t/2 < 10 else "")+str(int(t//2))+(":00" if t/2 == t//2 else ":30")+"-")
                        x = t + 1
                        f.write(("0" if x/2 < 10 else "")+str(int(x//2))+(":00" if x/2 == x//2 else ":30")+"\n")
                if self.print: print(s)
                f.write("\n")
                i += 1

            # Finally print the solution found.
            if status == cp_model.OPTIMAL:
               if self.print: print('Student Optimal Schedule Length: %i' % solver.ObjectiveValue())
            if visualize:
                visualize_solution.plot_binary(blist, self.horizon/2, False, 0.5, assigned_jobs_list)
            return assigned_jobs_list

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
