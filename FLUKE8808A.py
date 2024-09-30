import pyvisa
import asyncio
import time
import datetime
import Small_window as sm
import re

class Fluke_8808A:

    '''The constructor sets all the most important items'''
    def  __init__(self, port, baud_rate=19200, mode=1, timeout=5000):
        self.instr = pyvisa.ResourceManager().open_resource(port)
        self.port = port
        self.mode = mode  # multimetr operation mode (only info)
        self.instr.baud_rate = baud_rate
        self.instr.timeout = timeout

    '''Initial configuration "for safety" in case other functions are turned on on the multimeter'''
    def configure(self):
        self.instr.write("TRIGGER 4\n")  # VERY IMPORTANT function triggers measurements with an external source
        time.sleep(1)
        self.instr.write("FORMAT 2\n")  # notation with units
        time.sleep(1)
        self.instr.write("DBCLR\n")  # shows normal units not Po and not dB
        time.sleep(1)
        self.instr.write("MMCLR\n")  # disabling the min max modifier
        time.sleep(1)
        self.instr.write("RELCLR\n")  # turns off absolute value
        time.sleep(1)
        self.instr.write("COMPCLR\n")  # exits the comparison function
        time.sleep(1)
        self.instr.write("RATE F\n")  # VERY IMPORTANT transfer speed F-fast M-medium S-slow
        time.sleep(1)
        self.instr.write("PRINT 1\n")  # VERY IMPORTANT also the transfer speed function, see the table in the documentation
        time.sleep(1)
        self.instr.write("AUTO\n")
        time.sleep(1)

    def extract_number(self, text):
        # Wyrażenie regularne do wyszukania liczby w notacji wykładniczej
        match = re.search(r'([+-]?\d*\.?\d+([eE][+-]?\d+)?)', text)
        if match:
            return match.group(0)
        else:
            raise ValueError("No number found in the text")

    def convert_scientific_to_float(self, sci_num):
        return float(sci_num)

    '''The main method for starting measurements with time specification'''
    async def start_measure(self, duration, gather_freq, file):
        start_time = time.time()

        # clearing the communication buffer
        self.instr.clear()

        # a while loop that runs for a specified period of time
        while time.time() - start_time < duration:

            # VERY IMPORTANT section retrieves results from the multimeter
            # the reading is performed 3 times because the device still sends prompts ("=>")
            reader = self.instr.query('*TRG\n')
            self.instr.read()
            self.instr.read()


            time_captured = datetime.datetime.now().strftime("%X.%f")[:-4]
            string = str(time_captured + " " + reader)

            print(string)
            #file.write(string)
            
            time.sleep(gather_freq)
            #await asyncio.sleep(gather_freq)
        return 1
    
    '''The main method for starting measurements with number of measurments'''
    async def start_measure2(self, number_of_measurements: int, file, freq=1):
        #start_time = time.time()
        measurement_list = []
        # clearing the communication buffer
        self.instr.clear()
        gather_freq = freq
        #duration = number_of_measurements * gather_freq;
        # a while loop that runs for a specified period of time
        for i in range(number_of_measurements):

            # VERY IMPORTANT section retrieves results from the multimeter
            # the reading is performed 3 times because the device still sends prompts ("=>")
            reader = self.instr.query('*TRG\n')
            self.instr.read()
            self.instr.read()

            measurement_list.append(reader)
            
            #time.sleep(gather_freq)
            await asyncio.sleep(gather_freq)
        
        # sum of those measurmments 
        sum = 0.00
        for number in measurement_list:
            sci_number = self.extract_number(number)
            float_number = self.convert_scientific_to_float(sci_number)
            sum += float_number
        time_captured = datetime.datetime.now().strftime("%X.%f")[:-4]
        string = str(time_captured + " " + str(float(sum/number_of_measurements)) + '\n')

        print(string)
        file.write(string)

        return 1

    '''The method resets the measuring device'''
    def reset(self):
        self.instr.write('*RST')
        time.sleep(14) # time determined "by eye"
        self.instr.clear()

    '''A method that returns what device you are'''
    def it_is(self):
        answer = ""
        self.instr.clear()
        try:
            answer = self.instr.query("*IDN?")
        except Exception as err:
            news = sm.Small_window()
            news.show_error(f"ERROR {self.port} Fluke8808A Unexpected {err=}, {type(err)=}")
        return answer

    '''A method that sets the multimeter into voltmeter mode'''
    def set_DCvolts(self):
        self.instr.write("VDC\n")
        time.sleep(5)
        return 1
    
    '''Method of setting the multimeter to ammeter mode'''
    def set_DCcurrent(self):
        self.instr.write("ADC\n")
        time.sleep(5)
        return 1
