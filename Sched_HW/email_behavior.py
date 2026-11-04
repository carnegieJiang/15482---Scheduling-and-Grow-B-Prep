from behavior import *
from transitions import Machine
from greenhouse_behaviors import Greenhouse_Behavior
import send_email
import os
import time
from urllib.error import HTTPError, URLError

'''
The behavior should send an email that includes the team name and TerraBot
number, the date and time, the current sensor and actuator readings, and
the most recent image taken
'''
class Email(Greenhouse_Behavior):
    def __init__(self, agent):
        super(Email, self).__init__(agent, "EmailBehavior")
        # Initialize the FSM and add transitions
        # BEGIN STUDENT CODE

        self.initial = 'Halt'
        self.states = ['Halt', 'Init', 'Sent']

        self.fsm = Machine(
            self,
            states=self.states,
            initial=self.initial,
            ignore_invalid_triggers=True
        )

        self.fsm.add_transition(
            'enable',
            'Halt',
            'Init'
        )

        self.fsm.add_transition(
            'disable',
            '*',
            'Halt'
        )

        self.fsm.add_transition(
            'markSent',
            'Init',
            'Sent'
        )

        self.team_name = "Agamemnon"
        self.sender = "terrabot.6@outlook.com"
        self.recipients = "songyij@andrew.cmu.edu, kevinlu3@andrew.cmu.edu, shinyonp@andrew.cmu.edu, rsimmons@andrew.cmu.edu, ryanding@andrew.cmu.edu, shubhj@andrew.cmu.edu"

        # False while testing. Do NOT email professor/TAs yet.
        self.include_instructors = False

        # END STUDENT CODE

    # Add the condition and action functions
    #  Remember: if statements only in the condition functions;
    #            modify state information only in the action functions
    # BEGIN STUDENT CODE

    def readyToSend(self):
        return True

    def findLatestImage(self):
        picture_dir = os.path.expanduser("/home/robotanist/TerraBot/agents/deploy/pictures_A")

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

    def sendEmail(self):
        actuator_state = self.actuators.actuator_state

        subject = "TerraBot6 Daily Report - " + self.team_name

        text = (
            "Team: %s\n"
            "TerraBot: 6\n"
            "Simulation Time: %s\n\n"
            "Latest Sensor Data:\n"
            "Light: %.2f\n"
            "Temperature: %.2f\n"
            "Humidity: %.2f\n"
            "Weight: %.2f\n"
            "Soil Moisture: %.2f\n"
            "Water Level: %.2f\n\n"
            "Current Actuator Data:\n"
            "LED: %s\n"
            "Fan: %s\n"
            "Water Pump: %s\n"
            % (
                self.team_name,
                str(self.time),
                self.light,
                self.temp,
                self.humid,
                self.weight,
                self.smoist,
                self.level,
                str(actuator_state.get("led", 0)),
                str(actuator_state.get("fan", False)),
                str(actuator_state.get("wpump", False))
            )
        )

        images = []
        image_name = self.findLatestImage()

        if image_name is not None:
            try:
                with open(image_name, 'rb') as f:
                    images.append(f.read())
            except OSError as e:
                print("Could not read image:", e)

        recipients = self.recipients

        # Add professor/TA addresses here before final deployment.
        # Keep include_instructors False while testing.
        if self.include_instructors:
            pass

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                success = send_email.send(
                    self.sender,
                    "",
                    recipients,
                    subject,
                    text,
                    images,
                    False
                )
            except HTTPError as error:
                if error.code != 429 and not 500 <= error.code < 600:
                    print("Email failed with non-retryable HTTP error:", error)
                    return False
                success = False
            except URLError as error:
                print("Temporary email connection failure:", error)
                success = False

            if success:
                print("Email sent successfully")
                return True

            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)

        print("Email failed to send after retries")
        return False

    # END STUDENT CODE

    def perceive(self):
        self.time = self.sensordata['unix_time']
        # Add any sensor data variables you need for the behavior
        # BEGIN STUDENT CODE

        self.light = self.sensordata['light']
        self.temp = self.sensordata['temp']
        self.humid = self.sensordata['humid']
        self.weight = self.sensordata['weight']
        self.smoist = self.sensordata['smoist']
        self.level = self.sensordata['level']

        # END STUDENT CODE

    def act(self):
        if self.state == 'Init' and self.readyToSend() and self.sendEmail():
            self.trigger("markSent")
