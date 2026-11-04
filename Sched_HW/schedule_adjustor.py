from greenhouse_scheduler import *
from monitor import *
from terrabot_utils import clock_time, time_since_midnight
from plant_health import *
from cv_utils import *
from cv_learn import *
from foliage import *
import os

class ScheduleAdjustmentMonitor(Monitor):
    

    def __init__(self, period=3600):
        super(ScheduleAdjustmentMonitor, self).__init__("ScheduleAdjustmentMonitor", period)
        self.ambient_data = []
        self.lighting_intervals = []
        self.insolation = 0 # Per hour
        self.target = 8500 # Default value

        self.stage = "unsprouted"
        self.scheduled_light = 5
        self.percent_white = 0
        self.filename = "plant_status_log.csv"
        with open(self.filename, "w") as f:
            f.write(
                "time,status,scheduled light,percent white\n"
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
        self.problem = Greenhouse_Scheduler("greenhouse_schedule.txt",self.behaviors_info, self.minutes)
    
        self.solution = self.problem.solveProblem(visualize=False)

        self.reset()

    def perceive(self):
        self.time = self.sensordata["unix_time"]
        self.mtime = self.sensordata["midnight_time"]
        self.light = self.sensordata["light"]

        

    def monitor(self):
        foliage_classifier = FoliageClassifier("foliage_classifier.dill")
        latest_image = self.findLatestImage()
        if (latest_image == None):
            print("No images found")
        else:
            out_mask = foliage_classifier.classify(readImage(latest_image))
            self.percent_white = np.count_nonzero(out_mask == 255)/out_mask.size
            if (self.stage == "unsprouted" and self.percent_white > 0.05):
                self.stage = "sprouts"
                self.scheduled_light = 7-(self.insolation/1000.0)
                self.behaviors_info["Light"] = (self.scheduled_light*60,(self.minutes,4*60),3*60)
                self.problem = Greenhouse_Scheduler("greenhouse_schedule.txt",self.behaviors_info, self.minutes)
                self.solution = self.problem.solveProblem(visualize=False)

            if (self.stage == "sprouts" and self.percent_white > 0.1):
                self.stage = "small"
                self.scheduled_light = 10-(self.insolation/1000.0)
                self.behaviors_info["Light"] = (self.scheduled_light*60,(self.minutes,4*60),3*60)
                self.problem = Greenhouse_Scheduler("greenhouse_schedule.txt",self.behaviors_info, self.minutes)
                self.solution = self.problem.solveProblem(visualize=False)
                
            if (self.stage == "small" and self.percent_white > 0.2):
                self.stage = "big"
                self.scheduled_light = 12-(self.insolation/1000.0)
                self.behaviors_info["Light"] = (self.scheduled_light*60,(self.minutes,4*60),3*60)
                self.problem = Greenhouse_Scheduler("greenhouse_schedule.txt",self.behaviors_info, self.minutes)
                self.solution = self.problem.solveProblem(visualize=False)
                
            with open(self.filename, "a") as f:
                f.write(
                    f"{self.time},"
                    f"{self.stage},"
                    f"{self.scheduled_light},"
                    f"{self.percent_white}\n"
                )

        #light monitering behavior

        #print("INSOLATION: %.1f %d" %(self.mtime/3600.0, self.insolation))
        if (self.mtime < time_since_midnight(self.last_time)):
            print("INSOLATION TODAY: %.1f" %self.insolation)
            self.reset()
        else:
            # Calculate the optimal light level to reach the target value,
            #  given the amount of time the LightBehavior will be running and
            #  the amount of ambient light expected to be received when
            #  the LightBehavior is not running.  Set the optimal limits
            #  for the LightBehavior based on this calculation

            # BEGIN STUDENT CODE
            self.insolation = self.light * self.dt / 3600.0

            end_of_day = 24 * 60 * 60
            ambient_left = self.non_lighting_ambient_insolation(self.mtime, end_of_day)

            time_left = self.lighting_time_left(self.mtime)
            if time_left > 0:
                light_needed = self.target - self.insolation - ambient_left
                optimal = light_needed * 3600.0 / time_left

                optimal = max(0.0, optimal)
                optimal = min(1000.0, optimal)

                self.current_optimal = optimal
                self.lightBehavior.setOptimalLevel(optimal)

    def findLatestImage(self):
        picture_dir = os.path.expanduser("/home/robotanist/User/pictures_B")

        if not os.path.isdir(picture_dir):
            return None

        pictures = [
            os.path.join(picture_dir, f)
            for f in os.listdir(picture_dir)
            if f.startswith("terrabot6_pic_")
        ]

        if len(pictures) == 0:
            return None

        return max(pictures, key=os.path.getmtime)


    def reset(self):
        self.insolation = 0

    def setTarget(self, target):
        self.target = target

    def read_log_file(self, filename):
        self.ambient_data = []
        with open(filename) as log_file:
            for line in log_file:
                sline = line.split(" ")
                time = float(sline[0])
                data = float(sline[1].strip(' \n'))
                self.ambient_data.append((time, data))

    def activate(self):
        self.read_log_file("grader_files/ambient.log")
        self.lightBehavior = self.getExecutive().agent.getBehavioralLayer().getBehavior("LightBehavior")
        schedule = self.getExecutive().schedule
        self.lighting_intervals = [(start*60, end*60)
                                    for start, end in schedule['LightBehavior']]
        self.current_optimal = 900 # Arbitrary value - will be reset once the monitor begins

    def integrate_ambient(self, ts, te):
        ambient_insolation = 0
        t1, v1 = self.ambient_data[0]
        for index in range(1, len(self.ambient_data)):
            t2, v2 = self.ambient_data[index]
            if (ts < t2 and te > t1):
                if (ts > t1): # Starts within an interval
                    v1 = v1 + ((v2 - v1)*(ts - t1)/(t2 - t1))
                    t1 = ts
                if (te < t2): # Ends within an interval
                    v2 = v1 + ((v2 - v1)*(te - t1)/(t2 - t1))
                    t2 = te
                mval = (v1 + v2)/2.0
                ambient_insolation += mval*(t2 - t1)/3600.0
            t1, v1 = self.ambient_data[index]
        return ambient_insolation

    # Helper function:
    # How much ambient light will there be when LightBehavior is not running
    #  between start time (ts) and end time (te)
    def non_lighting_ambient_insolation(self, ts, te):
        ambient_light = 0
        t, t_last = (ts, 0)
        for interval in self.lighting_intervals:
            if (te <= interval[0]): break
            elif (t < interval[0]):
                t = max(t, t_last)
                ambient_light += self.integrate_ambient(t, min(te, interval[0]))
                t = interval[1]
            t_last = interval[1]

        if (te > t):
            ambient_light += self.integrate_ambient(t, te)
        #print("AMBIENT INSOLATION: (%d, %d) %.1f" %(ts/3600, te/3600, ambient_light))
        return ambient_light

    # Helper function:
    # How much time is left in the schedule for LightBehavior to run
    def lighting_time_left(self, time):
        time_left = 0
        for interval in self.lighting_intervals:
            if (interval[0] <= time and time < interval[1]):
                time_left = interval[1] - time
            elif (time < interval[0]):
                time_left += interval[1] - interval[0]

        return time_left
