import schedule as sched

class Layer:
    def __init__(self, agent):
        self.agent = agent

    def doStep(self, t=0):
        print("doStep NYI")

class BehavioralLayer(Layer):

    def __init__(self, sensors, actuators, behaviors, agent):
        self.behaviors = behaviors
        for behavior in behaviors:
            behavior.setSensors(sensors)
            behavior.setActuators(actuators)
        self.enabled = []
        super(BehavioralLayer, self).__init__(agent)
        # Initialize any extra variables here

    def getBehavior(self, name):
        for b in self.behaviors:
            if (b.name == name): return b
        return None

    def isEnabled(self, behavior):
        return behavior in self.enabled

    def startBehavior(self,name):
        # BEGIN STUDENT CODE
        b = self.getBehavior(name)
        if b is not None:
            if not self.isEnabled(b):
                self.enabled.append(b)
                b.start()
        # END STUDENT CODE
        pass

    def pauseBehavior(self,name):
        # BEGIN STUDENT CODE
        b = self.getBehavior(name)
        if b is not None:
            if self.isEnabled(b):
                self.enabled.remove(b)
                b.pause()
        # END STUDENT CODE
        pass

    def doStep(self):
        for behavior in self.enabled:
            behavior.doStep()

    def startAll(self):
        for behavior in self.behaviors:
            self.startBehavior(behavior.name)

    #more functions? write them here!

class ExecutiveLayer(Layer):

    def __init__(self, agent):
        self.schedule = {}
        self.laststep = -1
        self.monitors = []
        super(ExecutiveLayer, self).__init__(agent)
        # Initialize any extra variables here

    def setSchedule(self, schedule):
        self.schedule = schedule

    def requestNewSchedule(self):
        self.agent.getPlanningLayer().requestNewSchedule()

    def getMonitor(self, name):
        for m in self.monitors:
            if (m.name == name): return m
        return None

    def setMonitors(self, sensors, actuator_state, monitorsList):
        self.monitors = monitorsList
        now = sensors.getTime()
        for monitor in self.monitors:
            monitor.setSensors(sensors)
            monitor.setActuatorState(actuator_state)
            monitor.setExecutive(self)
            monitor.last_time = now
            monitor.dt = 0
            monitor.activate()

    def doStep(self, t):
        bl = self.agent.getBehavioralLayer()

        # Disable behaviors first
        for b in list(bl.enabled):
            should_be_enabled = False

            for time_interval in self.schedule.get(b.name, []):
                start_secs = time_interval[0] * 60
                end_secs = time_interval[1] * 60

                if start_secs <= t < end_secs:
                    should_be_enabled = True

            if not should_be_enabled:
                bl.pauseBehavior(b.name)

        # Then enable scheduled behaviors
        for b in bl.behaviors:
            should_be_enabled = False

            for time_interval in self.schedule.get(b.name, []):
                start_secs = time_interval[0] * 60
                end_secs = time_interval[1] * 60

                if start_secs <= t < end_secs:
                    should_be_enabled = True

            if should_be_enabled and not bl.isEnabled(b):
                bl.startBehavior(b.name)

        for monitor in self.monitors:
            monitor.doMonitor()


class PlanningLayer(Layer):

    def __init__(self, schedulefile, agent):
        self.schedulefile = schedulefile
        self.usetestfile = False
        self.schedulerequested = True
        self.schedule = {}
        self.laststep = 0
        super(PlanningLayer, self).__init__(agent)

    def setTestingSchedule(self, testschedule):
        self.testschedule = testschedule

    def switch_to_test_sched(self):
        self.usetestfile = True
        self.requestNewSchedule()

    def getNewSchedule(self):
        scheduleFile = self.testschedule if self.usetestfile else self.schedulefile
        self.schedule = self.scheduleFromFile(scheduleFile)
        self.agent.getExecutiveLayer().setSchedule(self.schedule)
        self.schedulerequested = False

    def requestNewSchedule(self):
        self.schedulerequested = True

    def doStep(self, t):
        if self.schedulerequested or self.checkEnded(t):
            self.getNewSchedule()
        self.laststep = (t//60)%(24*60)

    def checkEnded(self, t):
        mins = (t//60)%(24*60)
        if mins < self.laststep: #looped back around
            return True
        return False

    def scheduleFromFile(self, scheduleFile):
        print(f"Reading schedule from {scheduleFile}")
        return sched.readSchedule(scheduleFile)
