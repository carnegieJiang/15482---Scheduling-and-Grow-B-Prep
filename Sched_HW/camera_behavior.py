from behavior import *
from greenhouse_behaviors import Greenhouse_Behavior
from transitions import Machine
import os, os.path as op

'''
The behavior should adjust the lights to a reasonable level (say 400-600),
wait a bit for the light to stabilize, and then request an image.
It should check to be sure the image has been recorded and, if so, process
the image; if not, try again for up to 3 times before giving up
'''
class TakeImage(Greenhouse_Behavior):
    def __init__(self, agent):
        super(TakeImage, self).__init__(agent, "TakeImageBehavior")
        # Your code here
	# Initialize the FSM and add transitions
        # BEGIN STUDENT CODE
        self.pics_taken = 0
        self.last_time = 24*60*60 # Start with the prior day
        self.path_name = "random_path"
        self.tries = 0

        self.initial = 'Halt'
        self.states = [self.initial]
        
        self.states.append('Init')
        self.states.append('LightAdjustment')
        self.states.append('WaitForLights')
        self.states.append('WaitForImage')
        self.states.append('CheckForImage')

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        self.fsm.add_transition('enable', '*', 'Init', after=['setLED0'])
        self.fsm.add_transition('disable', '*', 'Halt', after=['setLED0', 'setLastTime'])
        # First matching transition should execute, next two transitions should be skipped if this one happens
        self.fsm.add_transition('doStep', ['Init'], 'LightAdjustment', conditions=['nextDay'], after=['resetPicsTaken'])
        self.fsm.add_transition('doStep', ['Init'], 'LightAdjustment', conditions=['withinPicLimit'])
        self.fsm.add_transition('doStep', ['Init'], 'Halt')
        self.fsm.add_transition('doStep', ['LightAdjustment'], 'WaitForLights', conditions=['lightInOptimal'], after=['setTimer5'])
        self.fsm.add_transition('doStep', ['LightAdjustment'], 'LightAdjustment', unless=['lightInOptimal'], after=['adjustLED'])
        self.fsm.add_transition('doStep', ['WaitForLights'], 'WaitForImage', conditions=['timerUp'], after=['requestImage', 'setTimer10', 'setTries0']) # Functions should execute in order of list
        self.fsm.add_transition('doStep', ['WaitForImage'], 'CheckForImage', conditions=['timerUp'], after=['incrementTries'])
        # First matching transition should execute, next two transitions should be skipped if this one happens
        self.fsm.add_transition('doStep', ['CheckForImage'], 'Halt', conditions=['imageFound'], after=['incrementPicsTaken', 'setLED0'])
        self.fsm.add_transition('doStep', ['CheckForImage'], 'Halt', conditions=['threeTries'], after=['printWarning', 'setLED0'])
        self.fsm.add_transition('doStep', ['CheckForImage'], 'WaitForImage', after=['requestImage', 'setTimer20'])
        # END STUDENT CODE

    # Add the condition and action functions
    #  Remember: if statements only in the condition functions;
    #            modify state information only in the action functions
    # BEGIN STUDENT CODE
    def nextDay(self):
        print(f"Is next day: {self.last_time > self.mtime}")
        return self.last_time > self.mtime

    def withinPicLimit(self):
        print(f"Pics: {self.pics_taken}")
        return self.pics_taken < 3

    def lightInOptimal(self):
        return 400 <= self.light and self.light < 600
    
    def timerUp(self):
        return self.time >= self.waittime

    def imageFound(self):
        return os.path.exists(self.path_name)

    def threeTries(self):
        return self.tries == 3



    def setLED(self, level):
        self.led = max(0, min(255, level))
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                    {"led": self.led}))
    
    def setLED0(self):
        self.setLED(0)

    def setLastTime(self):
        self.last_time = self.mtime

    def resetPicsTaken(self):
        self.pics_taken = 0
        self.setLastTime()

    def setTimer(self, wait):
        self.waittime = self.time + wait

    def setTimer5(self):
        self.setTimer(5)
        # print("Done setTimer5")

    def setTimer10(self):
        self.setTimer(10)

    def setTimer20(self):
        self.setTimer(20)

    def adjustLED(self):
        if self.light < 400:
            self.setLED(self.led+20)
        elif self.light >= 600:
            self.setLED(self.led-20)
        print(f"Adjusting, current light = {self.light}")

    def requestImage(self):
        # self.path_name = "~/Pictures/terrabot6_pic_" + str(self.sensordata['unix_time'])
        # image_name = "terrabot6_pic_" + "1" # + str(self.sensordata['unix_time']) + ".jpg"
        # self.path_name = "~/TerraBot/" + image_name
        print("Requesting image")
        self.path_name = "/home/robotanist/User/pictures_B/terrabot6_pic_" + str(int(self.sensordata['unix_time'])) + ".jpg"
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"camera": self.path_name}))

    def setTries0(self):
        self.tries = 0

    def incrementTries(self):
        self.tries += 1

    def incrementPicsTaken(self):
        self.pics_taken += 1
        print("Picture taken")

    def printWarning(self):
        print("Warning: Failed to find image in 3 tries")
    
    # END STUDENT CODE

    def perceive(self):
        self.time = self.sensordata['unix_time']
        # Add any sensor data variables you need for the behavior
        # BEGIN STUDENT CODE
        self.mtime = self.sensordata["midnight_time"]
        self.light = self.sensordata["light"]
        # END STUDENT CODE

    def act(self):
        self.trigger("doStep")
