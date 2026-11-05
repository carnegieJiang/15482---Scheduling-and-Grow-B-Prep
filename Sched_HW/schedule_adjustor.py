from greenhouse_scheduler import *
from monitor import *
from terrabot_utils import clock_time, time_since_midnight
from plant_health import *
from cv_utils import *
from cv_learn import *
from foliage import *
import os
from limits import *
import shutil



class ScheduleAdjustmentMonitor(Monitor):
    

    def __init__(self, period=1800):
        super(ScheduleAdjustmentMonitor, self).__init__("ScheduleAdjustmentMonitor", period)
        self.period = period
        self.day_light_should_be_on_counter = 0
        self.day_rm_should_be_on_counter = 0
        self.lighting_intervals = []
        self.rm_intervals = []
        self.last_time = 24*60*60 # Start with the prior day
        self.light_level_limits = limits['light_level']
        self.raise_moist_limits = limits['moisture']
        self.scheduled_light = 10
        self.scheduled_raise_moist = 2
        self.mtime = 0 # Temporary value
        self.time = 0 # Temporary value
        

        self.filename = "schedule_status_log.csv"
        with open(self.filename, "w") as f:
            f.write(
                "time,light miss counter,scheduled light hours,rm miss counter,scheduled rm hours\n"
            )


        #schedule 30 minute chunks
        self.minutes = 30
        self.behaviors_info = {}
    
        self.behaviors_info["Light"] = (self.scheduled_light*60,(self.minutes,4*60),3*60)
        self.behaviors_info["LowerHumid"] = (8*60,(self.minutes,60),12*60)
        self.behaviors_info["LowerTemp"] = (120,(2*60,4*60),12*60)
        self.behaviors_info["RaiseTemp"] = (120,(2*60,4*60),12*60)
        self.behaviors_info["LowerMoist"] = (120,(2*60,4*60),12*60)
        self.behaviors_info["RaiseMoist"] = (120,(2*60,4*60),12*60)
        self.behaviors_info["TakeImage"] = (60,(3*60,6*60),0)
        self.problem = Greenhouse_Scheduler("test_schedule.txt",self.behaviors_info, self.minutes)
    
        self.solution = self.problem.solveProblem(visualize=False)

        if (self.mtime < time_since_midnight(self.last_time)):
            self.reset_day()

    def activate(self):
        # Might need to be here since getExecutive might not exist in __init__
        self.planningLayer = self.getExecutive().agent.getPlanningLayer()
        self.planningLayer.setTestingSchedule("test_schedule.txt")
        self.planningLayer.switch_to_test_sched()

    def perceive(self):
        self.time = self.sensordata["unix_time"]
        self.mtime = self.sensordata["midnight_time"]
        self.light = self.sensordata["light"]

        

    def monitor(self):
        schedule = self.getExecutive().schedule
        self.lighting_intervals = [(start*60, end*60)
                                    for start, end in schedule['LightBehavior']]
        lighting_behavior_on = False
        for time_interval in self.lighting_intervals:
            # print(f"ti 0 {time_interval[0]}, ti 1 {time_interval[1]}, time {self.mtime}")

            if time_interval[0] <= self.mtime < time_interval[1]:
                lighting_behavior_on = True

        if (lighting_behavior_on and not 
            (self.light_level_limits[0] <= self.light < self.light_level_limits[1])):
            self.day_light_should_be_on_counter += 1
        # Should get new schedule every day
        
        if (self.mtime < time_since_midnight(self.last_time)):
            self.reset_day()

    def reset_day(self):
        self.scheduled_light = max(min(self.scheduled_light/(1.3-2*self.day_light_should_be_on_counter*self.period/86400.0), 14), 5)
        self.behaviors_info["Light"] = (self.scheduled_light*60,(self.minutes,4*60),3*60)

        self.scheduled_raise_moist = max(min(self.scheduled_raise_moist/(1.3-2*self.day_rm_should_be_on_counter*self.period/86400.0), 6), 1)
        self.behaviors_info["RaiseMoist"] = (self.scheduled_raise_moist*60,(2*60,4*60),12*60)
        
        self.problem = Greenhouse_Scheduler("test_schedule.txt",self.behaviors_info, self.minutes)
        self.solution = self.problem.solveProblem(visualize=False)
        
        if (self.solution == cp_model.INFEASIBLE):
            print("No solution feasable 1")
            self.scheduled_light = max(2, self.scheduled_raise_moist - 4)
            self.behaviors_info["Light"] = (self.scheduled_light*60,(self.minutes,4*60),3*60)
            self.scheduled_raise_moist = max(1, self.scheduled_raise_moist - 2)
            self.behaviors_info["RaiseMoist"] = (self.scheduled_raise_moist*60,(2*60,4*60),12*60)
            self.problem = Greenhouse_Scheduler("test_schedule.txt",self.behaviors_info, self.minutes)
            self.solution = self.problem.solveProblem(visualize=False)
            if (self.solution == cp_model.INFEASIBLE):
                print("No solution feasable 2")
        
        shutil.copy("test_schedule.txt", f"./schedules/schedule_{str(int(self.sensordata['unix_time']))}.txt")

        with open(self.filename, "a") as f:
            f.write(
                f"{self.time},"
                f"{self.day_light_should_be_on_counter*self.period/86400.0},"
                f"{self.scheduled_light},"
                f"{self.day_rm_should_be_on_counter*self.period/86400.0},"
                f"{self.scheduled_raise_moist}\n"
            )
        
        self.last_time = self.mtime
        self.day_light_should_be_on_counter = 0

            

        

    