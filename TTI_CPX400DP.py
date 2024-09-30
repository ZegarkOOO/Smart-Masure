import pyvisa
import time

class TTI_CPX400DP:

    '''Initializes the power supply by opening a connection to it'''
    def __init__(self, port):
        try:
            self.instr = pyvisa.ResourceManager().open_resource(port)
        except pyvisa.Error as e:
            print("Device initialization error: ", e)

    '''Queries the power supply for its identification string'''
    def it_is(self):
        answer = ""
        #self.instr.clear()
        try:
            answer = self.instr.query("*IDN?")
        except pyvisa.Error as e:
            print("Error reading device name: ", e)
        return answer

    '''Sets the current level'''
    def set_current(self, current):
        self.instr.write("CURR " + str(current) + "\n")
        time.sleep(1)

    '''Sets the voltage level'''
    def set_voltage(self, voltage):
        self.instr.write("VOLT " + str(voltage) + "\n")
        time.sleep(1)

    '''Reads the current and voltage levels of the power supply'''
    def read(self):
        answer, voltR, currR = "", "", ""
        try:
            voltR += self.instr.query("VOLT?")
            time.sleep(1)
            currR += self.instr.query("CURR?")
            time.sleep(1)

            answer = "Voltage: " + voltR + "Current: " + currR
        except pyvisa.Error as e:
            print("Value reading error: ", e)
        return answer

    '''Resets the power supply to its default settings'''
    def reset(self):
        self.instr.write("*RST")
        time.sleep(1)

    '''Turns on the output of the power supply'''
    def output_on(self):
        self.instr.write("OP1 1")
        time.sleep(1)

    '''Turns off the output of the power supply'''
    def output_off(self):
        self.instr.write("OP1 0")
        time.sleep(1)

    '''Sets the output current'''
    '''The output current is not changing, but when the output is turned off the value changes to the value we set'''
    '''For example we set 2A, but output values show -0.006A then OUTPUT turns off and it sets to 2A'''
    '''The voltage function is the same, but working as intended'''
    def set_output_current(self, current):
        self.instr.write("I1 " + str(current))
        #time.sleep(1)

    '''Sets the output voltage'''
    def set_output_voltage(self, voltage):
        self.instr.write("V1 " + str(voltage))
        #time.sleep(1)

    '''Reads the output voltage'''
    def read_output_voltage(self):
        try:
            voltage_response = self.instr.query("V1O?").strip() #value is ending with V in the end for example 0.06V
            voltage = float(voltage_response.rstrip('V')) #rewriting value without V : 0.06
        except pyvisa.Error as e:
            print("Voltage reading error: ", e)
        return voltage

    '''Reads the output current'''
    '''Reads the same value because the output current does not change xd'''
    def read_output_current(self):
        try:
            current_response = self.instr.query("I1O?").strip() #value is ending with A in the end for example 0.06A
            current = float(current_response.rstrip('A')) #rewriting value without A : 0.06
        except pyvisa.Error as e:
            print("Current reading error: ", e)
        return current
