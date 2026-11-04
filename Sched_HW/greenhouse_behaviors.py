from behavior import *
from limits import *
from transitions import Machine

#sensor data passed into greenhouse behaviors:
#  [time, lightlevel, temperature, humidity, soilmoisture, waterlevel]
#actuators are looking for a dictionary with any/all of these keywords:
#  {"led":val, "fan":True/False, "pump": True/False}

# A very basic class, so we don't have to declare enable and disable every time
class Greenhouse_Behavior(Behavior):
    def __init__(self, agent, name):
        super(Greenhouse_Behavior, self).__init__(agent, name)    
        
    def enable(self):  self.trigger('enable')
    def disable(self): self.trigger('disable')

'''
The combined ambient and LED light level between 8am and 10pm should be 
in the optimal['light_level'] range;
Between 10pm and 8am, the LEDs should be off (set to 0).
'''
class Light(Greenhouse_Behavior):

    def __init__(self, agent):
        super(Light, self).__init__(agent, "LightBehavior")
        self.optimal_level = optimal['light_level']

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states = [
            self.initial,
            'light',
            'dark'
        ]
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        self.fsm.add_transition(
            trigger='enable',
            source=self.initial,
            dest='light',
            after='led_off'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='light',
            dest='dark',
            unless='light_time',
            after='led_off'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='light',
            dest='light',
            conditions='dark',
            after='brighter'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='light',
            dest='light',
            conditions='bright',
            after='darker'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='dark',
            dest='light',
            conditions=['light_time', 'dark'],
            after='brighter'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='dark',
            dest='light',
            conditions=['light_time', 'bright'],
            after='darker'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='dark',
            dest='light',
            conditions='light_time'
        )

        self.fsm.add_transition(
            trigger='disable',
            source='*',
            dest=self.initial,
            after='led_off'
        )
        # END STUDENT CODE

    def setInitial(self):
        self.led = 0
        self.setLED(self.led)
        
    def perceive(self):
        self.mtime = self.sensordata["midnight_time"]
        self.time = self.sensordata["unix_time"]
        self.light = self.sensordata["light"]
    
    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")
        
    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def light_time(self):
        hour = (self.mtime//3600)%24
        return hour >= 8 and hour < 22

    def dark(self):
        return self.light < self.optimal_level[0]

    def bright(self):
        return self.light >= self.optimal_level[1]
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def led_off(self):
        self.setLED(0)

    def brighter(self):
        self.setLED(self.led+20)

    def darker(self):
        self.setLED(self.led-20)
    # END STUDENT CODE

    def setLED(self, level):
        # print(f"Setting LED to {level}")
        self.led = max(0, min(255, level))
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"led": self.led}))

    def setOptimalLevel(self, optimal):
        deadband = 20
        self.optimal_level = (optimal - deadband, optimal + deadband)
                                  

"""
The temperature should be greater than the lower limit
"""
class RaiseTemp(Greenhouse_Behavior):

    def __init__(self, agent):
        super(RaiseTemp, self).__init__(agent, "RaiseTempBehavior")

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states = [
            self.initial,
            'Perfect',
            'TooLow'
        ]
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        self.fsm.add_transition(
            trigger='enable',
            source=self.initial,
            dest='Perfect',
            after='led_off'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Perfect',
            dest='TooLow',
            conditions='too_cold',
            after='led_on'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='TooLow',
            dest='Perfect',
            conditions='temp_normal',
            after='led_off'
        )

        self.fsm.add_transition(
            trigger='disable',
            source='*',
            dest=self.initial,
            after='led_off'
        )
        # END STUDENT CODE

    def setInitial(self):
        self.setLED(0)
        
    def perceive(self):
        self.temp = self.sensordata["temp"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def too_cold(self):
        return self.temp <= limits['temperature'][0]
    def temp_normal(self):
        return self.temp >= optimal['temperature'][0]
    # END STUDENT CODE

    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def led_on(self):
        self.setLED(200)

    def led_off(self):
        self.setLED(0)
    # END STUDENT CODE
            
    def setLED(self, level):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"led": level}))
        
"""
The temperature should be less than the upper limit
"""
class LowerTemp(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerTemp, self).__init__(agent, "LowerTempBehavior")

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states = [
            self.initial,
            'Perfect',
            'TooHigh'
        ]
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        self.fsm.add_transition(
            trigger='enable',
            source=self.initial,
            dest='Perfect',
            after='fan_off'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Perfect',
            dest='TooHigh',
            conditions='too_hot',
            after='fan_on'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='TooHigh',
            dest='Perfect',
            conditions='temp_normal',
            after='fan_off'
        )

        self.fsm.add_transition(
            trigger='disable',
            source='*',
            dest=self.initial,
            after='fan_off'
        )
        # END STUDENT CODE

    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.temp = self.sensordata["temp"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def too_hot(self):
        return self.temp >= limits['temperature'][1]

    def temp_normal(self):
        return self.temp <= optimal['temperature'][1]
    # END STUDENT CODE
    
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def fan_on(self):
        self.setFan(True)

    def fan_off(self):
        self.setFan(False)
    # END STUDENT CODE
            
    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))
    
"""
Humidity should be less than the limit
"""
class LowerHumid(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerHumid, self).__init__(agent, "LowerHumidBehavior")

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states = [
            self.initial,
            'Perfect',
            'TooHumid'
        ]
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        self.fsm.add_transition(
            trigger='enable',
            source=self.initial,
            dest='Perfect',
            after='fan_off'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Perfect',
            dest='TooHumid',
            conditions='too_humid',
            after='fan_on'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='TooHumid',
            dest='Perfect',
            conditions='perfect',
            after='fan_off'
        )

        self.fsm.add_transition(
            trigger='disable',
            source='*',
            dest=self.initial,
            after='fan_off'
        )
        # END STUDENT CODE
        
    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.humid = self.sensordata["humid"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def too_humid(self):
        return self.humid >= limits['humidity'][1]

    def perfect(self):
        return self.humid <= optimal['humidity'][1]
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def fan_on(self):
        self.setFan(True)

    def fan_off(self):
        self.setFan(False)
    # END STUDENT CODE

    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))
            
"""
Soil moisture should be greater than the lower limit
"""
class RaiseSMoist(Greenhouse_Behavior):

    def __init__(self, agent):
        super(RaiseSMoist, self).__init__(agent, "RaiseMoistBehavior")
        self.weight = 0
        self.weight_window = []
        self.smoist_window = []
        self.total_water = 0
        self.water_level = 0
        self.start_weight = 0
        self.last_time = 24*60*60 # Start with the prior day
        self.daily_limit = 100
        self.wet = limits["moisture"][1]

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states = [
            self.initial,
            'Init',
            'Waiting',
            'Watering',
            'Measuring',
            'Done'
        ]
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        self.fsm.add_transition(
            trigger='enable',
            source='Halt',
            dest='Init',
            after='initialize'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Init',
            dest='Waiting',
            conditions='time_up'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Init',
            dest='Init',
            conditions='next_day',
            after='resetTotalWater'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Done',
            dest='Init',
            conditions='next_day',
            after='resetTotalWater'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Waiting',
            dest='Done',
            conditions='watered_enough',
            before = 'printWateredEnough',
            after = 'setLastTime'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Waiting',
            dest='Done',
            conditions='not_enough',
            before = 'emailNoWater',
            after = 'setLastTime'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Waiting',
            dest='Done',
            conditions='soil_moist',
            before = 'print_soil_enough',
            after = 'setLastTime'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Waiting',
            dest='Watering',
            unless=['watered_enough', 'not_enough', 'soil_moist'],
            after = 'startWatering'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Watering',
            dest='Measuring',
            conditions='time_up',
            after = 'measure'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Measuring',
            dest='Waiting',
            conditions='time_up',
            after = 'calcWaterAdded'
        )

        self.fsm.add_transition(
            trigger='disable',
            source='*',
            dest='Halt',
            after='stop_behavior'
        )
        # END STUDENT CODE
        
    def setInitial(self):
        pass
        
    def sliding_window(self, window, item, length=4):
        if (len(window) == length): window = window[1:]
        window.append(item)
        return window, sum(window)/float(len(window))
    
    def perceive(self):
        self.time = self.sensordata["unix_time"]
        self.mtime = self.sensordata["midnight_time"]
        self.water_level = self.sensordata["level"]
        self.weight = self.sensordata["weight"]
        self.weight_window, self.weight_est = self.sliding_window(self.weight_window, self.weight)
        self.smoist = self.sensordata["smoist"]
        self.smoist_window, self.smoist_est = self.sliding_window(self.smoist_window, self.smoist)

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def time_up(self):
        return self.time >= self.waittime

    def next_day(self):
        return self.last_time > self.mtime

    def watered_enough(self):
        return self.total_water >= self.daily_limit

    def not_enough(self):
        return self.water_level < 30

    def soil_moist(self):
        return self.smoist_est >= self.wet
    
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def initialize(self):
        self.setPump(False)
        self.setTimer(10)

    def resetTotalWater(self): # Reset total water each day
        print("Resetting total water")
        self.total_water = 0
        self.setLastTime()

    def calcWaterAdded(self):
        dwater = self.weight_est - self.start_weight # ml of water weighs a gram
        # Sometimes scales are off - cannot lose weight after watering
        dwater = max(0, dwater)

        self.total_water += dwater
        print("calcWaterAdded: %.1f (%.1f = %.1f - %.1f)"
              %(self.total_water, dwater, self.weight_est, self.start_weight))
        
    def printWateredEnough(self):
        print("Watered Enough: %.1f" %self.total_water)

    def emailNoWater(self): # Email TBD
        print("NOT ENOUGH WATER IN RESERVOIR")

    def setLastTime(self):
        self.last_time = self.mtime

    def print_soil_enough(self):
        print("Soil is moist enough (%s)" %self.smoist_est)

    def startWatering(self):
        print("Start watering", self.smoist_est)
        self.start_weight = self.weight_est
        self.setTimer(10)
        self.setPump(True)

    def measure(self):
        self.setPump(False)
        self.setTimer(300)

    def setTimer(self, wait):
        self.waittime = self.time + wait

    def stop_behavior(self):
        self.setPump(False)
        self.setLastTime()
    # END STUDENT CODE

    def setPump(self,state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"wpump": state}))

"""
Soil moisture below the upper limit
"""
class LowerSMoist(Greenhouse_Behavior):

    def __init__(self, agent):
        super(LowerSMoist, self).__init__(agent, "LowerMoistBehavior")

        self.initial = 'Halt'
        self.states = [self.initial]
        # Add all your FSM state names to self.states
        # BEGIN STUDENT CODE
        self.states = [
            self.initial,
            'TooMoist',
            'Perfect'
        ]
        # END STUDENT CODE

        self.fsm = Machine(self, states=self.states, initial=self.initial,
                           ignore_invalid_triggers=True)

        # Add FSM transitions and actions
        # BEGIN STUDENT CODE
        self.fsm.add_transition(
            trigger='enable',
            source=self.initial,
            dest='Perfect',
            after='fan_off'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='Perfect',
            dest='TooMoist',
            conditions='too_moist',
            after='fan_on'
        )

        self.fsm.add_transition(
            trigger='doStep',
            source='TooMoist',
            dest='Perfect',
            conditions='perfect',
            after='fan_off'
        )

        self.fsm.add_transition(
            trigger='disable',
            source='*',
            dest=self.initial,
            after='fan_off'
        )
        # END STUDENT CODE
        
    def setInitial(self):
        self.setFan(False)
        
    def perceive(self):
        self.smoist = self.sensordata["smoist"]

    def act(self):
        # Use 'doStep' trigger for all other transitions
        self.trigger("doStep")

    # Add all your condition functions here
    # BEGIN STUDENT CODE
    def too_moist(self):
        return self.smoist >= limits["moisture"][1]
    def perfect(self):
        return self.smoist <= optimal['moisture'][1]
    # END STUDENT CODE
        
    # Add all your before / after action functions here
    # BEGIN STUDENT CODE
    def fan_on(self):
        self.setFan(True)

    def fan_off(self):
        self.setFan(False)
    # END STUDENT CODE
            
    def setFan(self, act_state):
        self.actuators.doActions((self.name, self.sensors.getTime(),
                                  {"fan": act_state}))

