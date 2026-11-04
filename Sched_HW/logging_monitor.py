from monitor import *

class LoggingMonitor(Monitor):

    def __init__(self, period=10):
        super(LoggingMonitor, self).__init__("LoggingMonitor", period)
        # Put any iniitialization code here
        # BEGIN STUDENT CODE
        self.filename = "greenhouse_log.csv"
        with open(self.filename, "w") as f:
            f.write(
                "time,light,temp,humid,smoist,weight,level,led,fan,wpump\n"
            )
        # END STUDENT CODE

    def perceive(self):
        # BEGIN STUDENT CODE
        self.time = self.sensordata["unix_time"]
        self.light = self.sensordata["light"]
        self.temp = self.sensordata["temp"]
        self.humid = self.sensordata["humid"]
        self.smoist = self.sensordata["smoist"]
        self.weight = self.sensordata["weight"]
        self.level = self.sensordata["level"]
        # END STUDENT CODE
        pass

    def monitor(self):
        # Use self.sensorData and self.actuator_state to log the sensor and
        #  actuator data, preferably as a comma-separated line of values.
        #  Make sure to timestamp the line of data
        # BEGIN STUDENT CODE
        led = self.actuator_state.get("led", 0)
        fan = self.actuator_state.get("fan", False)
        wpump = self.actuator_state.get("wpump", False)

        with open(self.filename, "a") as f:
            f.write(
                f"{self.time},"
                f"{self.light},"
                f"{self.temp},"
                f"{self.humid},"
                f"{self.smoist},"
                f"{self.weight},"
                f"{self.level},"
                f"{led},"
                f"{fan},"
                f"{wpump}\n"
            )
        # END STUDENT CODE
        pass

