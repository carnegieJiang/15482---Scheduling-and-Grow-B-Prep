'''
Defines a general behavior.
Each behavior needs to be able to take in sensor and actuators
Each behavior must implement:
     perceive - to take in sensor data and time and output percepts
     plan - to take in percepts, determine new state
     act - to take in the state and output actions for each actuator
     start - to start up after running
     pause - to shut down before stopping
Each behavior performs one perceive, plan, act loop and returns the desired actions
doStep sends commands to actuators
'''
from std_msgs.msg import String

class Behavior(object):
    enablePub = None
    disablePub = None

    def __init__(self, agent, name):
        self.name = name
        if not Behavior.enablePub and agent != None:
            Behavior.enablePub = agent.create_publisher(String, 'enable', 10)
            Behavior.disablePub = agent.create_publisher(String, 'disable', 10)

    def setSensors(self, sensors):
        self.sensors = sensors

    def setActuators(self, actuators):
        self.actuators = actuators

    def start(self):
        self.sensordata = self.sensors.doSense()
        self.perceive()
        print("Enable: %s" %self.name)
        # Let the world know this behavior has begun
        try: Behavior.enablePub.publish(String(data=self.name))
        except: pass
        self.enable()

    def pause(self):
        print("Disable: %s" %self.name)
        # Let the world know this behavior has stopped
        try: Behavior.disablePub.publish(String(data=self.name))
        except: pass
        self.disable()

    def perceive(self):
        pass

    def act(self):
        pass

    def doStep(self):
        self.sensordata = self.sensors.doSense()
        self.perceive()
        self.act()
