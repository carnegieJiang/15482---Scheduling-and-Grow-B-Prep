from hardware import *
import rclpy
import sys
from topic_def import sensor_types, actuator_types, actuator_names
from terrabot_utils import time_since_midnight, get_ros_time, spin_for

#sensor data passed as a file
class ROSSensors(Sensors):

    light_level = 0
    temperature = 0
    humidity = 0
    weight = 0
    moisture = 0
    wlevel = 0
    light_level_raw = [0, 0]
    temperature_raw = [0, 0]
    humidity_raw = [0, 0]
    weight_raw = [0, 0]
    moisture_raw = [0, 0]
    wlevel_raw = 0

    def __init__(self, agent):
        self.agent = agent
        self.subscribe_sensor('light', self.light_callback)
        self.subscribe_sensor('temp', self.temp_callback)
        self.subscribe_sensor('humid', self.humid_callback)
        self.subscribe_sensor('weight', self.weight_callback)
        self.subscribe_sensor('smoist', self.smoist_callback)
        self.subscribe_sensor('level', self.level_callback)

    def subscribe_sensor(self, sensor, callback):
        self.agent.create_subscription(sensor_types[sensor], 
                                       '%s_output' %sensor, callback, 1)

    def getTime(self):
        return get_ros_time(self.agent)

    # Implement subscriber handlers here
    def light_callback(self, data):
        # BEGIN STUDENT CODE
        self.light_level_raw = data.data
        self.light_level = (data.data[0] + data.data[1])/2
        # END STUDENT CODE
        pass

    def temp_callback(self, data):
        # BEGIN STUDENT CODE
        self.temperature_raw = data.data
        self.temperature = (data.data[0] + data.data[1])/2
        # END STUDENT CODE
        pass

    def humid_callback(self, data):
        # BEGIN STUDENT CODE
        self.humidity_raw = data.data
        self.humidity = (data.data[0] + data.data[1])/2
        # END STUDENT CODE
        pass

    def weight_callback(self, data):
        # BEGIN STUDENT CODE
        self.weight_raw = data.data
        self.weight = data.data[0] + data.data[1]
        # END STUDENT CODE
        pass

    def smoist_callback(self, data):
        # BEGIN STUDENT CODE
        self.moisture_raw = data.data
        self.moisture = (data.data[0] + data.data[1])/2
        # END STUDENT CODE
        pass

    def level_callback(self, data):
        # BEGIN STUDENT CODE
        self.wlevel_raw = data.data
        self.wlevel = data.data
        # END STUDENT CODE
        pass

    def doSense(self):
        #update the dictionary to return your values
        now = self.getTime()
        return {"unix_time":now,
                "midnight_time":time_since_midnight(now),
                "light": self.light_level,
                "temp": self.temperature, "humid": self.humidity,
                "weight": self.weight,"smoist": self.moisture,
                "level": self.wlevel, "light_raw": self.light_level_raw,
                "temp_raw": self.temperature_raw, "humid_raw": self.humidity_raw,
                "weight_raw": self.weight_raw, "smoist_raw": self.moisture_raw,
                "level_raw": self.wlevel_raw}

#actuators commanded as a file
class ROSActuators(Actuators):
    actuators = {}
    actuator_state = {"fan": False, "wpump": False, "led": 0, "camera": ""}

    def __init__(self, agent):
        self.agent = agent
        for actuator in actuator_names:
            topic = actuator if actuator == 'camera' else '%s_input' %actuator
            self.actuators[actuator] = \
                 agent.create_publisher(actuator_types[actuator], topic, 1)

    def doActions(self, actions_tuple):
        # Publish actuator commands here
        # BEGIN STUDENT CODE
        _, _, act_dict = actions_tuple
        for (key, val) in act_dict.items():
            self.actuators[key].publish(actuator_types[key](data=val))
            self.actuator_state[key] = val
        # END STUDENT CODE
        # Give the messages a chance to propagate
        #spin_for(self.agent, 0.5)
        pass


