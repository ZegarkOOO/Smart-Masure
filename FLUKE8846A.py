import pyvisa
import asyncio
import time
import datetime
import Small_window as sm
import re

class Fluke_8846A:

    '''Konstruktor ustawiajacy wszystkie najważniejsze pozycje'''
    def __init__(self, port, baud_rate=9600, mode=1, timeout=5000):
        self.instr = pyvisa.ResourceManager().open_resource(port)
        self.port = port
        self.mode = mode #tryb działania multimetru (only info)
        self.instr.baud_rate = baud_rate
        self.instr.timeout = timeout
        self.configure()

    '''Wstepna konfiguracja "dla bezpieczeństwa" w razie czego jakby na multimetrze były włączone inne funckje'''
    def configure(self):
        self.reset()
        time.sleep(1)
        self.instr.write("L1\n") # setting meter's mode to language 8846
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
    def start_measure(self, duration, gather_freq):
        
        self.instr.write("TRIG:SOUR BUS\n")
        self.instr.write("TRIG:COUN 1\n")
        self.instr.write(f"TRIG:DEL {gather_freq}\n")
        self.instr.write(f"SAMP:COUN {int(duration/gather_freq)}\n")
        self.instr.write("INIT\n")
        print("Pomiary...")
        time.sleep(1)
        self.instr.write("*TRG\n")
        time.sleep(duration+1);
        
        #zwraca ciąg danych oddzielonych ',' bez spacji: +9.97740000E-04,+9.82470000E-04,+9.31330000E-04
        reader = self.instr.query("FETCh?")

        czas = datetime.datetime.now().strftime("%X.%f")[:-4]
        string = str(czas + " " + reader)

        print(string)
        #file.write(string)
        #await asyncio.sleep(gather_freq)
        return 1

    '''The main method for starting measurements with number of measurments'''
    async def start_measure2(self, number_of_measurements: int, file, freq=1):
        measurment_list = []
        gather_freq = freq
        self.instr.write("TRIG:SOUR BUS\n")
        self.instr.write("TRIG:COUN 1\n")
        self.instr.write(f"TRIG:DEL {gather_freq}\n")
        self.instr.write(f"SAMP:COUN {number_of_measurements}\n")
        self.instr.write("INIT\n")
        time.sleep(1)
        self.instr.write("*TRG\n")
        #time.sleep(gather_freq * number_of_measurements)
        await asyncio.sleep(gather_freq * number_of_measurements)

        reader = self.instr.query("FETCh?")
        measurment_list = reader.split(',')

        #  processing data and calculating the average of the measurements
        sum = 0.00
        for number in measurment_list:
            sci_number = self.extract_number(number)
            float_number = self.convert_scientific_to_float(sci_number)
            sum += float_number
        time_captured = datetime.datetime.now().strftime("%X.%f")[:-4]
        string = str(time_captured + " " + str(float(sum/number_of_measurements)) + '\n')

        # the average is saved to a file with the date
        print(string)
        file.write(string)
        
        return 1

    '''The method resets the measuring device'''
    def reset(self):
        # disables additional functions such as math, filter... and enables DCV
        self.instr.write("*RST\n")
        time.sleep(1)
        return 1

    '''A method that returns what device you are'''
    def it_is(self):
        answer = ""
        try:
            answer = self.instr.query("*IDN?")
        except Exception as err:
            news = sm.Small_window()
            news.show_error(f"ERROR {self.port} Fluke8846A Unexpected {err=}, {type(err)=}")
        return answer

    '''Metoda ustawiajaca multimetr w tryb voltomierza'''
    def set_DCvolts(self):
        self.instr.write("FUNC \"VOLT:DC\"\n")
        time.sleep(1)
        self.instr.write("VOLT:RANG:AUTO ON\n")
        time.sleep(1)
        return 1
    
    '''Metoda ustawiajaca multimetr w tryb amperomierza'''
    def set_DCcurrent(self):
        self.instr.write("FUNC \"CURR:DC\"\n")
        time.sleep(1)
        return 1
    
    '''Clearing the buffer in the device, e.g. after an error occurs'''
    def clear_buffer(self):
        self.instr.write("*CLS\n")
        return 1
