import pyvisa
import asyncio
import time
import datetime

async def start_symulation(czas_trwania, czas_pomiedzy_pomiarami, device, file):
    start_time = time.time()

    while time.time() - start_time < czas_trwania:
        reader = device.read()
        czas = datetime.datetime.now().strftime("%X.%f")[:-4]

        string = str(czas + " " + reader)
        
        file.write(string)
        await asyncio.sleep(czas_pomiedzy_pomiarami)

    device.write('off')
    print("Koniec pomiaru")

async def main():
    rm = pyvisa.ResourceManager()
    print(rm.list_resources())

    czas_pomiaru = 1000
    czas_cyklu_pomiarow = 0.5
    device1 = rm.open_resource('ASRL3::INSTR')
    device2 = rm.open_resource('ASRL7::INSTR')
    device3 = rm.open_resource('ASRL8::INSTR')
    device4 = rm.open_resource('ASRL9::INSTR')

    device1.baud_rate = 115200
    device2.baud_rate = 115200
    device3.baud_rate = 115200
    device4.baud_rate = 115200

    data_now = datetime.datetime.now()
    lista = ["INP_VOLTAGE", "INP_CURR", "OUT_VOLTAGE", "OUT_CURR"]
    lista_files = []
    for name in lista:
        file_name = "test_" + data_now.strftime("%d_%m_%Y_%H_%M_%S") + "_" + name + ".txt"
        lista_files.append(file_name)

    file1 = open(lista_files[0], "w", encoding="utf-8", newline="")
    file2 = open(lista_files[1], "w", encoding="utf-8", newline="")
    file3 = open(lista_files[2], "w", encoding="utf-8", newline="")
    file4 = open(lista_files[3], "w", encoding="utf-8", newline="")

    print(device1.write('on'))
    tasks = [start_symulation(czas_pomiaru, czas_cyklu_pomiarow, device1, file1), 
             start_symulation(czas_pomiaru, czas_cyklu_pomiarow, device2, file2), 
             start_symulation(czas_pomiaru, czas_cyklu_pomiarow, device3, file3), 
             start_symulation(czas_pomiaru, czas_cyklu_pomiarow, device4, file4)]
    await asyncio.gather(*tasks)

    file1.close()
    file2.close()
    file3.close()
    file4.close()
    rm.close()

asyncio.run(main())

