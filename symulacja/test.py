import pyvisa
import time
import datetime

async def connect():
    print("ABC")


data_now = datetime.datetime.now()
print(data_now.strftime("%d_%m_%Y_%H_%M_%S"))
file_name = "test_" + data_now.strftime("%d_%m_%Y_%H_%M_%S") + ".txt"
file = open(file_name, "w")


rm = pyvisa.ResourceManager()
print(rm.list_resources())

#choosen enable port
stm = rm.open_resource('ASRL3::INSTR')

#set timeout waiting time for a interrupt
stm.timeout = 100

#baud rate transmit our me. instrument
stm.baud_rate = 115200

#commands configuring our measurments instruments
print(stm.write('off'))

#here, we should cleaning buffer
#stm.clear()->don't work

time.sleep(0.25)

#start measuring
print(stm.write('on'))
time.sleep(0.25)

while(1):
    try:

        #read data from measure instrument
        reader = stm.read()
        print(reader, end="")

        TimeMeasure = datetime.datetime.now()
        #write line to text file without '\n'
        file.write(TimeMeasure.strftime("%x %X") + " " + reader[:len(reader)-1])

        #important time between measurments
        time.sleep(0.25)

    #stop measuring with 'ctrl + C'
    except KeyboardInterrupt:
        print(stm.write('off'))
        break

file.close()
rm.close()

