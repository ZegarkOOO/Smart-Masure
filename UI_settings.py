import pyvisa
import os
import shutil
import asyncio
import ConfigData
import BKprecision8601
import Small_window as sm
import FLUKE8808A
import FLUKE8846A
import TTI_CPX400DP
import CTS_T6550
import data
from PyQt5.QtWidgets import QFileDialog

#TODO dodać informacje o skanowaniu w trakcie dzialania funkcji

class UiSettings:
    def __init__(self, ui):
        self.ui = ui
        self.rm = pyvisa.ResourceManager()
        self.list_ports = list(self.rm.list_resources())
        self.steps_number = 1  # number of all steps
        self.step_no = 0  # number of selected step
        self.freq = 1.0  # data gathering frequency
        self.time_per_step = 120  # time per step in seconds
        self.steps_list = []  # list of steps
        self.DeviceList = []  # list of devices
        self.save_path = None  # path to save files
        self.measurements_per_average = 10  # number of measurements per average

        self.list_baud_rates = ["110", "300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "38400",
                                "57600"]  # list of baud rates for combos
        self.list_available_devices = ["FLUKE8808A", "FLUKE8846A", "BKprecision8601",
                                       "TTI_CPX400DP"]  # list of devices for which the interface is created

        self.ui.step_num2_lbl.setEnabled(0)
        self.ui.step_num2_combo.setEnabled(0)
        self.ui.set_temp_radio.setEnabled(0)
        self.ui.set_gradient_radio.setEnabled(0)
        self.ui.set_temp_lbl.setEnabled(0)
        self.ui.set_temp_spb.setEnabled(0)
        self.ui.set_humidity_lbl.setEnabled(0)
        self.ui.set_humidity_spb.setEnabled(0)
        self.ui.use_allowable_humidity_err_chkbox.setEnabled(0)
        self.ui.use_allowable_temp_err_chkbox.setEnabled(0)
        self.ui.gr_temp_step_lbl.setEnabled(0)
        self.ui.gr_temp_step_spb.setEnabled(0)
        self.ui.gr_temp_lbl.setEnabled(0)
        self.ui.gr_temp_spb.setEnabled(0)
        self.ui.gr_humidity_step_lbl.setEnabled(0)
        self.ui.gr_humidity_step_spb.setEnabled(0)
        self.ui.gr_humidity_lbl.setEnabled(0)
        self.ui.gr_humidity_spb.setEnabled(0)
        self.ui.gr_temp_step_info_lbl.setEnabled(0)
        self.ui.gr_humidity_step_info_lbl.setEnabled(0)
        self.ui.allowable_temp_err_lbl.setEnabled(0)
        self.ui.allowable_temp_err_spb.setEnabled(0)
        self.ui.allowable_humidity_err_lbl.setEnabled(0)
        self.ui.allowable_humidity_err_spb.setEnabled(0)
        first_step = ConfigData.ConfigData()
        self.steps_list.append(first_step)
        self.steps_output()

    # Scanning for new devices
    def refresh_devices(self):

        #self.rm = pyvisa.ResourceManager()
        tmp_list = list(self.rm.list_resources())

        # remove not display ports
        for address in self.list_ports:
            if address not in tmp_list:
                self.list_ports.remove(address)
                self.ui.device_port_1.removeItem(self.ui.device_port_1.findText(address))
                self.ui.device_port_2.removeItem(self.ui.device_port_2.findText(address))
                self.ui.device_port_3.removeItem(self.ui.device_port_3.findText(address))
                self.ui.device_port_4.removeItem(self.ui.device_port_4.findText(address))
                self.ui.device_port_5.removeItem(self.ui.device_port_5.findText(address))
                self.ui.device_port_6.removeItem(self.ui.device_port_6.findText(address))
                self.ui.device_port_7.removeItem(self.ui.device_port_7.findText(address))

        # add new open ports                
        for address in tmp_list:
            if address not in self.list_ports:
                self.list_ports.append(address)
                self.ui.device_port_1.addItem(address)
                self.ui.device_port_2.addItem(address)
                self.ui.device_port_3.addItem(address)
                self.ui.device_port_4.addItem(address)
                self.ui.device_port_5.addItem(address)
                self.ui.device_port_6.addItem(address)
                self.ui.device_port_7.addItem(address)

                # Starting test

    # (port_com, nazwa, baudrate, przeznaczenie)
    """
       1 - inlet amm
       2 - inlet volt
       3 - outlet amm
       4 - outlet volt
       5 - DC load
       6 - power supply
       7 - temp chamber
       """
    def run_start_test(self):
        asyncio.run(self.start_test())

    def find_path_clicked(self):
        options = QFileDialog.Options()
        self.save_path = QFileDialog.getExistingDirectory(None, "Select Directory", "",
                                                          QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog)

        if self.save_path:
            print(self.save_path)
            self.ui.save_path_ledit.setText(self.save_path)

    async def start_test(self):
        self.ui.state_lbl.setText("Setting devices...")

        if len(self.DeviceList) < 6:
            sm.Small_window().show_warning("Connect and test devices first!")
            self.ui.state_lbl.setText(" ")
            return

        # Tworzenie forlderu badania
        folder_name = self.ui.test_name_ledit.text()

        if folder_name == "":
            sm.Small_window().show_warning("No test name!")
            self.ui.state_lbl.setText("No test name!")
            self.ui.estimated_time_lbl.setText("")
            return

        sm.Small_window().show_info("Attention! Setup and data collection has started. Don't change anything!")

        #dezaktywowanie przycisków w trakcie działania
        self.ui.save_cfg_btn1.setEnabled(0)
        self.ui.test_connection.setEnabled(0)
        self.ui.refresh_dev_btn.setEnabled(0)
        self.ui.start_test_btn.setEnabled(0)

        estim_sec = 30
        for j in range(len(self.steps_list)):
            estim_sec += (self.steps_list[j].dcl_changes_no * 10)
        estim_mins = round(estim_sec / 60, 0)
        estim_hours = round(estim_mins / 60, 0)

        self.ui.estimated_time_lbl.setText(
            "Estimated test time: " + str(estim_hours) + ":" + str(estim_mins) + ":" + str(estim_sec))

        devices = {}

        for i in range(len(self.DeviceList)):
            print("Baud rate: " + str(self.DeviceList[i][2]))
            if "8601" in self.DeviceList[i][1]:
                DCLoad = BKprecision8601.BKprecision8601(self.DeviceList[i][0])
                devices["DCload"] = DCLoad

            elif "8808A" in self.DeviceList[i][1]:
                if self.DeviceList[i][3] == 1:
                    inlet_amm = FLUKE8808A.Fluke_8808A(self.DeviceList[i][0], int(self.DeviceList[i][2]))
                    inlet_amm.configure()
                    devices["inlet_amm"] = inlet_amm

                elif self.DeviceList[i][3] == 2:
                    inlet_volt = FLUKE8808A.Fluke_8808A(self.DeviceList[i][0], int(self.DeviceList[i][2]))
                    inlet_volt.configure()
                    devices["inlet_volt"] = inlet_volt

                elif self.DeviceList[i][3] == 3:
                    out_amm = FLUKE8808A.Fluke_8808A(self.DeviceList[i][0], int(self.DeviceList[i][2]))
                    out_amm.configure()
                    devices["out_amm"] = out_amm

                elif self.DeviceList[i][3] == 4:
                    out_volt = FLUKE8808A.Fluke_8808A(self.DeviceList[i][0], int(self.DeviceList[i][2]))
                    out_volt.configure()
                    devices["out_volt"] = out_volt

            elif "8846A" in self.DeviceList[i][1]:
                if self.DeviceList[i][3] == 1:
                    inlet_amm = FLUKE8846A.Fluke_8846A(self.DeviceList[i][0], int(self.DeviceList[i][2]))
                    inlet_amm.configure()
                    devices["inlet_amm"] = inlet_amm

                elif self.DeviceList[i][3] == 2:
                    inlet_volt = FLUKE8846A.Fluke_8846A(self.DeviceList[i][0], int(self.DeviceList[i][2]))
                    inlet_volt.configure()
                    devices["inlet_volt"] = inlet_volt

                elif self.DeviceList[i][3] == 3:
                    out_amm = FLUKE8846A.Fluke_8846A(self.DeviceList[i][0], int(self.DeviceList[i][2]))
                    out_amm.configure()
                    devices["out_amm"] = out_amm

                elif self.DeviceList[i][3] == 4:
                    out_volt = FLUKE8846A.Fluke_8846A(self.DeviceList[i][0], int(self.DeviceList[i][2]))
                    out_volt.configure()
                    devices["out_volt"] = out_volt

            elif "CPX400DP" in self.DeviceList[i][1]:
                power_supply = TTI_CPX400DP.TTI_CPX400DP(self.DeviceList[i][0])
                devices["power_supply"] = power_supply


            elif "T6550" in self.DeviceList[i][1]:
                pass  # << do zrobienia dla przyszłych pokoleń

        # Setting inlet ammeter
        devices["inlet_amm"].set_DCcurrent()

        # Setting inlet voltmeter
        devices["inlet_volt"].set_DCvolts()

        # Setting outlet ammeter
        devices["out_amm"].set_DCcurrent()

        # Setting outlet voltmeter
        devices["out_volt"].set_DCvolts()

        path = ""
        if len(self.save_path) > 0:
            path = self.save_path + '/'

        if not os.path.exists(folder_name):
            os.mkdir(path + folder_name)

        self.ui.state_lbl.setText("Testing...")

    

        for i in range(self.steps_number):

            # Tworzenie plików do badań
            inlet_amm_path =  path + folder_name +"\inlet_amm" + str(i) + ".txt"
            inlet_volt_path = path + folder_name +"\inlet_volt" + str(i) + ".txt"
            out_amm_path = path + folder_name +"\out_amm" + str(i) + ".txt"
            out_volt_path = path + folder_name +"\out_volt" + str(i) + ".txt"

            inlet_amm_file = open(inlet_amm_path, 'w')
            #inlet_amm_file.write("Inlet ammeter: \n")

            inlet_volt_file = open(inlet_volt_path, 'w')
            #inlet_volt_file.write("Inlet voltmeter: \n")

            out_amm_file = open(out_amm_path, 'w')
            #out_amm_file.write("Outlet ammeter: \n")

            out_volt_file = open(out_volt_path, 'w')
            #out_volt_file.write("Outlet voltmeter: \n")
            print("Stworzono pliki")

            # Setting DCLoad
            if "CC" in self.steps_list[i].dcl_mode:
                devices["DCload"].set_mode("CURR")
                print('Krok: '+ str(self.steps_list[i].dcl_start))
                devices["DCload"].set_current(self.steps_list[i].dcl_start)
            elif "CV" in self.steps_list[i].dcl_mode:
                devices["DCload"].set_mode("VOLT")
                devices["DCload"].set_voltage(self.steps_list[i].dcl_start)

            devices["DCload"].power_on()

            tmpsum = self.steps_list[i].dcl_start

            # Setting PSU
            devices["power_supply"].output_on()
            devices["power_supply"].set_output_voltage(self.steps_list[i].psu_volt)
            devices["power_supply"].set_output_current(self.steps_list[i].psu_amm)


            for j in range(self.steps_list[i].dcl_changes_no + 1):


                """devices["inlet_amm"].start_measure2(self.steps_list[i].dcl_changes_no, inlet_amm_file)
                devices["inlet_volt"].start_measure2(self.steps_list[i].dcl_changes_no, inlet_volt_file)
                devices["out_amm"].start_measure2(self.steps_list[i].dcl_changes_no, out_amm_file)
                devices["out_volt"].start_measure2(self.steps_list[i].dcl_changes_no, out_volt_file)"""

                tasks = [
                    devices["inlet_amm"].start_measure2(self.measurements_per_average, inlet_amm_file, self.freq),
                    devices["inlet_volt"].start_measure2(self.measurements_per_average, inlet_volt_file, self.freq),
                    devices["out_amm"].start_measure2(self.measurements_per_average, out_amm_file, self.freq),
                    devices["out_volt"].start_measure2(self.measurements_per_average, out_volt_file, self.freq)]

                await asyncio.gather(*tasks)
                inlet_amm_file.flush()
                inlet_volt_file.flush()
                out_amm_file.flush()
                out_volt_file.flush()

                tmpsum += round((self.ui.DCload_end_spb.value() - self.ui.DCload_start_spb.value())/self.ui.DCload_steps_spb.value(), 2)

                if "CC" in self.steps_list[i].dcl_mode:
                    print('Krok: ' + str(tmpsum))
                    devices["DCload"].set_current(tmpsum)
                elif "CV" in self.steps_list[i].dcl_mode:
                    print('Krok: ' + str(tmpsum))
                    devices["DCload"].set_voltage(tmpsum)

            devices["DCload"].power_off()
            devices["power_supply"].output_off()

            inlet_amm_file.close()
            inlet_volt_file.close()
            out_amm_file.close()
            out_volt_file.close()

        if self.ui.generate_raport_chkbox.isChecked():
            path1 = path + folder_name
            data.data_analized(self.steps_number, path1)

        self.ui.save_cfg_btn1.setEnabled(1)
        self.ui.test_connection.setEnabled(1)
        self.ui.refresh_dev_btn.setEnabled(1)
        self.ui.start_test_btn.setEnabled(1)

        sm.Small_window().show_info("Data collection completed.")

        
        if self.ui.delete_txt_chkbox.isChecked():
            path1 = path + folder_name+'/'
            for i in range (self.steps_number):
                os.remove(path1 +'/' + f'inlet_amm{i}.txt')
                os.remove(path1 +'/' + f'inlet_volt{i}.txt')
                os.remove(path1 +'/' + f'out_amm{i}.txt')
                os.remove(path1 +'/' + f'out_volt{i}.txt')

    # Switching to next tab
    def next_page(self):
        current_index = self.ui.tabWidget.currentIndex()
        tab_count = self.ui.tabWidget.count()
        next_index = (current_index + 1) % tab_count
        self.ui.tabWidget.setCurrentIndex(next_index)

    # changing number of steps
    def steps_set(self):
        self.steps_number = self.ui.steps_spb.value()
        self.ui.step_num1_combo.clear()
        self.ui.step_num2_combo.clear()
        for i in range(1, self.steps_number + 1):
            self.ui.step_num1_combo.addItem(str(i))
            self.ui.step_num2_combo.addItem(str(i))

            # jeżeli lista nr i nie istnieje, stwórz ją pustą.
            # jeżeli istnieje, zostaw.

            if len(self.steps_list) < i:
                step = self.create_step(i)
                self.steps_list.append(step)

        # jeżeli są, usuń wszystkie listy o nr większym niż steps_number
        while len(self.steps_list) > self.steps_number:
            self.steps_list.pop()

        if self.step_no > self.steps_number:
            self.step_no = self.steps_number

        self.steps_output()

    # creating step object
    def create_step(self, nr):
        chamber_on = self.ui.use_temp_chamber_chkbox.isChecked()
        chamber_mod = self.ui.set_temp_radio.isChecked()
        temp_err = self.ui.use_allowable_temp_err_chkbox.isChecked()
        humid_err = self.ui.use_allowable_humidity_err_chkbox.isChecked()
        step = ConfigData.ConfigData(nr, chamber_on, chamber_mod, temp_err, humid_err)
        return step

    # ------------TEMP CHAMBER--------------
    # When using chamber, enable functions
    def use_chamber(self):
        if self.ui.use_temp_chamber_chkbox.isChecked():
            self.ui.step_num2_lbl.setEnabled(1)
            self.ui.step_num2_combo.setEnabled(1)
            self.ui.set_temp_radio.setEnabled(1)
            self.ui.set_gradient_radio.setEnabled(1)
            self.ui.set_temp_lbl.setEnabled(1)
            self.ui.set_temp_spb.setEnabled(1)
            self.ui.set_humidity_lbl.setEnabled(1)
            self.ui.set_humidity_spb.setEnabled(1)
            self.ui.use_allowable_humidity_err_chkbox.setEnabled(1)
            self.ui.use_allowable_temp_err_chkbox.setEnabled(1)
        else:
            self.ui.step_num2_lbl.setEnabled(0)
            self.ui.step_num2_combo.setEnabled(0)
            self.ui.set_temp_radio.setEnabled(0)
            self.ui.set_gradient_radio.setEnabled(0)
            self.ui.set_temp_lbl.setEnabled(0)
            self.ui.set_temp_spb.setEnabled(0)
            self.ui.set_humidity_lbl.setEnabled(0)
            self.ui.set_humidity_spb.setEnabled(0)
            self.ui.use_allowable_humidity_err_chkbox.setEnabled(0)
            self.ui.use_allowable_temp_err_chkbox.setEnabled(0)
        # self.steps_output()

    # Enabling limiting temp error
    def chamber_temp_limit(self):
        if self.ui.use_allowable_temp_err_chkbox.isChecked():
            self.ui.allowable_temp_err_lbl.setEnabled(1)
            self.ui.allowable_temp_err_spb.setEnabled(1)
        else:
            self.ui.allowable_temp_err_lbl.setEnabled(0)
            self.ui.allowable_temp_err_spb.setEnabled(0)

        self.steps_output()

    # Enabling limiting humidity error
    def chamber_humidity_limit(self):
        if self.ui.use_allowable_humidity_err_chkbox.isChecked():
            self.ui.allowable_humidity_err_lbl.setEnabled(1)
            self.ui.allowable_humidity_err_spb.setEnabled(1)
        else:
            self.ui.allowable_humidity_err_lbl.setEnabled(0)
            self.ui.allowable_humidity_err_spb.setEnabled(0)

        self.steps_output()

    # Selecting temperature chamber mode, gradient or fixed temp
    def select_chamber_mode(self):
        if self.ui.set_temp_radio.isChecked():
            self.ui.set_temp_lbl.setEnabled(1)
            self.ui.set_temp_spb.setEnabled(1)
            self.ui.set_humidity_lbl.setEnabled(1)
            self.ui.set_humidity_spb.setEnabled(1)
            self.ui.gr_temp_step_lbl.setEnabled(0)
            self.ui.gr_temp_step_spb.setEnabled(0)
            self.ui.gr_temp_lbl.setEnabled(0)
            self.ui.gr_temp_spb.setEnabled(0)
            self.ui.gr_humidity_step_lbl.setEnabled(0)
            self.ui.gr_humidity_step_spb.setEnabled(0)
            self.ui.gr_humidity_lbl.setEnabled(0)
            self.ui.gr_humidity_spb.setEnabled(0)
            self.ui.gr_temp_step_info_lbl.setEnabled(0)
            self.ui.gr_humidity_step_info_lbl.setEnabled(0)
        else:
            self.ui.gr_temp_step_lbl.setEnabled(1)
            self.ui.gr_temp_step_spb.setEnabled(1)
            self.ui.gr_temp_lbl.setEnabled(1)
            self.ui.gr_temp_spb.setEnabled(1)
            self.ui.gr_humidity_step_lbl.setEnabled(1)
            self.ui.gr_humidity_step_spb.setEnabled(1)
            self.ui.gr_humidity_lbl.setEnabled(1)
            self.ui.gr_humidity_spb.setEnabled(1)
            self.ui.gr_temp_step_info_lbl.setEnabled(1)
            self.ui.gr_humidity_step_info_lbl.setEnabled(1)
            self.ui.set_temp_lbl.setEnabled(0)
            self.ui.set_temp_spb.setEnabled(0)
            self.ui.set_humidity_lbl.setEnabled(0)
            self.ui.set_humidity_spb.setEnabled(0)

        self.steps_output()

    # Calculating estimated difference in temp or humidity in step
    # (only when using gradient)
    def chamber_temp_calc(self):
        temp1 = self.ui.gr_temp_step_spb.value()
        temp2 = self.ui.gr_humidity_step_spb.value()
        TPS_min = self.time_per_step / 60

        self.ui.gr_temp_step_info_lbl.setText("Exp. temp. change in step: " + str(round(temp1 * TPS_min, 2)) + " °C")
        self.ui.gr_humidity_step_info_lbl.setText(
            "Exp. humid. change in step: " + str(round(temp2 * TPS_min, 2)) + " %rH")
        self.steps_output()

    # ------------STEPS FUNCTIONS--------------
    def step_btn1_clicked(self):
        if self.ui.step_num1_combo.currentIndex() == self.ui.step_num2_combo.currentIndex():
            self.step_change(self.ui.step_num1_combo.currentIndex())
        else:
            self.ui.step_num2_combo.setCurrentIndex(self.ui.step_num1_combo.currentIndex())

    def step_btn2_clicked(self):
        if self.ui.step_num2_combo.currentIndex() == self.ui.step_num1_combo.currentIndex():
            self.step_change(self.ui.step_num2_combo.currentIndex())
        else:
            self.ui.step_num1_combo.setCurrentIndex(self.ui.step_num2_combo.currentIndex())

    # Step change
    def step_change(self, number):
        self.step_no = number
        #print("numer kroku: " + str(self.step_no))
        #print("ilosc kroków: " + str(self.steps_number))

        # Load and display data of selected step
        step = self.steps_list[int(self.step_no)]

        self.ui.amp_inlet_combo.setCurrentText(step.amm_inl_unit)
        self.ui.volt_inlet_combo.setCurrentText(step.volt_inl_unit)

        self.ui.amp_outlet_combo.setCurrentText(step.amm_out_unit)
        self.ui.volt_outlet_combo.setCurrentText(step.volt_out_unit)

        self.ui.PSU_volt_pwr_spb.setValue(step.psu_volt)
        self.ui.PSU_amp_pwr_spb.setValue(step.psu_amm)
        self.ui.PSU_volt_unit_combo.setCurrentText(step.psu_amm_unit)
        self.ui.PSU_amp_unit_combo.setCurrentText(step.psu_volt_unit)

        self.ui.DCload_mode_combo.setCurrentText(step.dcl_mode)
        self.ui.DCload_end_spb.setValue(step.dcl_end)
        self.ui.DCload_steps_spb.setValue(step.dcl_changes_no)
        self.ui.DCload_start_spb.setValue(step.dcl_start)
        self.DCload_mode_change()

        self.ui.use_temp_chamber_chkbox.setChecked(step.use_chamber)
        if step.chamber_mode:
            self.ui.set_temp_radio.setChecked(True)
            self.ui.set_temp_spb.setValue(step.chb_temp)
            self.ui.set_humidity_spb.setValue(step.chb_humidity)
        else:
            self.ui.set_gradient_radio.setChecked(True)
            self.ui.gr_temp_step_spb.setValue(step.chb_temp_step)
            self.ui.gr_temp_spb.setValue(step.chb_start_temp)
            self.ui.gr_humidity_step_spb.setValue(step.chb_humidity_step)
            self.ui.gr_humidity_spb.setValue(step.chb_start_humidity)

        self.ui.use_allowable_temp_err_chkbox.setChecked(step.chb_allow_temp_err)
        self.ui.use_allowable_humidity_err_chkbox.setChecked(step.chb_allow_humidity_err)

        if self.ui.use_allowable_temp_err_chkbox.isChecked():
            self.ui.allowable_temp_err_spb.setValue(step.chb_temp_err)

        if self.ui.use_allowable_humidity_err_chkbox.isChecked():
            self.ui.allowable_humidity_err_spb.setValue(step.chb_humidity_err)

        self.use_chamber()

    # Step change from button
    def steps_increment(self):
        if self.ui.step_num1_combo.currentIndex() == self.steps_number - 1:
            self.ui.step_num1_combo.setCurrentIndex(0)
            self.step_change(self.ui.step_num1_combo.currentIndex())
        else:
            self.ui.step_num1_combo.setCurrentIndex(self.ui.step_num1_combo.currentIndex() + 1)
            self.step_change(self.ui.step_num1_combo.currentIndex())

    def avg_res_no_spb_change(self):
        self.measurements_per_average = self.ui.avg_res_no_spb.value()
        print(self.measurements_per_average)


    def freq_change(self):
        self.freq = self.ui.freq_spb.value()
        print(self.freq)

    # outputting data to the screen
    def steps_output(self):
        self.ui.steps_textEdit.clear()
        self.ui.steps_textEdit2.clear()
        for i in range(self.steps_number):
            step = self.steps_list[i]

            if step.dcl_mode == "Constant voltage (CV)":
                unit_list = 'V'
            else:
                unit_list = 'A'

            self.ui.steps_textEdit.append(
                "Step " + str(i + 1) + ": PSU " + str(step.psu_volt) + step.psu_volt_unit + ", " + str(
                    step.psu_amm) + step.psu_amm_unit + "; DCL: start:" + str(
                    step.dcl_start) + unit_list + " end: " + str(
                    step.dcl_end) + unit_list + ", jumps: " + str(step.dcl_changes_no))

            if not step.chb_allow_temp_err:
                temp_err_text = "Temp err: off"
            else:
                temp_err_text = str("Temp err: " + str(step.chb_temp_err) + "°C")

            if not step.chb_allow_humidity_err:
                humidity_err_text = "Humid err: off"
            else:
                humidity_err_text = str("Humid err: " + str(step.chb_humidity_err) + "%rH")

            if step.chamber_mode:
                self.ui.steps_textEdit2.append(
                    "Step " + str(i + 1) + ": PSU " + str(step.psu_volt) + step.psu_volt_unit +
                    ", " + str(step.psu_amm) + step.psu_amm_unit + "; DCL " + ", start:" + str(
                        step.dcl_start) + unit_list + " stop: " + str(step.dcl_end) + unit_list + " changes: " + str(
                        "dcl_time") + "s, CHB: " + str(step.chb_temp) + "°C, " + str(step.chb_humidity) + "%, " +
                    temp_err_text + ", " + humidity_err_text)
            else:
                self.ui.steps_textEdit2.append(
                    "Step " + str(i + 1) + ": PSU " + str(step.psu_volt) + step.psu_volt_unit + ", " + str(
                        step.psu_amm) + step.psu_amm_unit + "; DCL " + ", start:" + str(
                        step.dcl_start) + unit_list + " stop: " + str(step.dcl_end) + unit_list + " changes: " + str(
                        step.dcl_changes_no) + "s, CHB: " + str(step.chb_start_temp) + "°C, " + str(step.chb_temp_step) +
                    "°C/min, " + temp_err_text + ", " + humidity_err_text)

    def DCload_mode_change(self):
        if self.ui.DCload_mode_combo.currentText() == "Constant current (CC)":
            self.ui.DCload_end_spb.setSuffix(" A")
            self.ui.DCload_start_lbl.setText("Start current:")
            self.ui.DCload_step_lbl.setText("End current:")
            self.ui.DCload_start_spb.setSuffix(" A")
            if self.ui.DCload_steps_spb.value() == 0:
                exp_value_change = 0
            else:
                exp_value_change = round((self.ui.DCload_end_spb.value() - self.ui.DCload_start_spb.value())/self.ui.DCload_steps_spb.value(), 2)
            self.ui.DCload_step_info_lbl.setText("Value change per DCLoad step: " + str(exp_value_change) + " A")

        elif self.ui.DCload_mode_combo.currentText() == "Constant voltage (CV)":
            self.ui.DCload_end_spb.setSuffix(" V")
            self.ui.DCload_start_lbl.setText("Start voltage:")
            self.ui.DCload_step_lbl.setText("End voltage:")
            self.ui.DCload_start_spb.setSuffix(" V")
            if self.ui.DCload_steps_spb.value() == 0:
                exp_value_change = 0
            else:
                exp_value_change = round(
                    (self.time_per_step / self.ui.DCload_steps_spb.value()) * self.ui.DCload_end_spb.value(), 2)
            self.ui.DCload_step_info_lbl.setText(
                "Exp. current change in step: " + str(round(exp_value_change, 2)) + " V")

    # Save data from UI to ConfigData object
    def save_config(self):
        self.steps_list[self.step_no].amm_inl_unit = self.ui.amp_inlet_combo.currentText()
        self.steps_list[self.step_no].volt_inl_unit = self.ui.volt_inlet_combo.currentText()
        self.steps_list[self.step_no].amm_out_unit = self.ui.amp_outlet_combo.currentText()
        self.steps_list[self.step_no].volt_out_unit = self.ui.volt_outlet_combo.currentText()
        self.steps_list[self.step_no].psu_volt = round(float(self.ui.PSU_volt_pwr_spb.value()), 2)
        self.steps_list[self.step_no].psu_volt_unit = self.ui.PSU_volt_unit_combo.currentText()
        self.steps_list[self.step_no].psu_amm = round(float(self.ui.PSU_amp_pwr_spb.value()), 2)
        self.steps_list[self.step_no].psu_amm_unit = self.ui.PSU_amp_unit_combo.currentText()

        self.steps_list[self.step_no].dcl_mode = self.ui.DCload_mode_combo.currentText()
        self.steps_list[self.step_no].dcl_end = round(float(self.ui.DCload_end_spb.value()), 3)
        self.steps_list[self.step_no].dcl_changes_no = int(self.ui.DCload_steps_spb.value())
        self.steps_list[self.step_no].dcl_start = round(float(self.ui.DCload_start_spb.value()), 3)

        self.steps_list[self.step_no].use_chamber = self.ui.use_temp_chamber_chkbox.isChecked()
        self.steps_list[self.step_no].chamber_mode = self.ui.set_temp_radio.isChecked()

        self.steps_list[self.step_no].chb_temp = round(float(self.ui.set_temp_spb.value()), 2)
        self.steps_list[self.step_no].chb_humidity = round(float(self.ui.set_humidity_spb.value()), 2)

        self.steps_list[self.step_no].chb_temp_step = round(float(self.ui.gr_temp_step_spb.value()), 2)
        self.steps_list[self.step_no].chb_start_temp = round(float(self.ui.gr_temp_spb.value()), 2)
        self.steps_list[self.step_no].chb_humidity_step = round(float(self.ui.gr_humidity_step_spb.value()), 2)
        self.steps_list[self.step_no].chb_start_humidity = round(float(self.ui.gr_humidity_spb.value()), 2)

        self.steps_list[self.step_no].chb_allow_temp_err = self.ui.use_allowable_temp_err_chkbox.isChecked()
        self.steps_list[self.step_no].chb_allow_humidity_err = self.ui.use_allowable_humidity_err_chkbox.isChecked()
        self.steps_list[self.step_no].chb_temp_err = round(float(self.ui.allowable_temp_err_spb.value()), 2)
        self.steps_list[self.step_no].chb_humidity_err = round(float(self.ui.allowable_humidity_err_spb.value()), 2)

        self.steps_output()

    """
    1 - inlet amm
    2 - inlet volt
    3 - outlet amm
    4 - outlet volt
    5 - DC load
    6 - power supply
    7 - temp chamber
    """

    def set_device_select_combos(self):

        # combo boxes "Port"
        self.ui.device_port_1.addItems(self.list_ports)
        self.ui.device_port_2.addItems(self.list_ports)
        self.ui.device_port_3.addItems(self.list_ports)
        self.ui.device_port_4.addItems(self.list_ports)
        self.ui.device_port_5.addItems(self.list_ports)
        self.ui.device_port_6.addItems(self.list_ports)
        # self.ui.device_port_7.addItems(self.list_ports)

        # combo boxes "Baud rate"
        self.ui.baud_rate_1.addItems(self.list_baud_rates)
        self.ui.baud_rate_2.addItems(self.list_baud_rates)
        self.ui.baud_rate_3.addItems(self.list_baud_rates)
        self.ui.baud_rate_4.addItems(self.list_baud_rates)
        self.ui.baud_rate_5.addItem("-----")
        self.ui.baud_rate_5.setCurrentIndex(1)
        self.ui.baud_rate_6.addItem("-----")
        self.ui.baud_rate_6.setCurrentIndex(1)
        # self.ui.baud_rate_7.addItems(self.list_baud_rates)

        # combo boxes "Model"
        self.ui.device_model1.addItems(self.list_available_devices[:2])
        self.ui.device_model2.addItems(self.list_available_devices[:2])
        self.ui.device_model3.addItems(self.list_available_devices[:2])
        self.ui.device_model4.addItems(self.list_available_devices[:2])
        self.ui.device_model5.addItem(self.list_available_devices[2])
        self.ui.device_model6.addItem(self.list_available_devices[3])
        # self.ui.device_model7.addItem()

    @staticmethod
    def check_unique_texts(*texts):
        # Tworzymy zbiór z podanych tekstów
        unique_texts = set(texts)

        # Sprawdzamy, czy rozmiar zbioru jest równy liczbie podanych tekstów
        # jeśli teksty są unikalne zwraca true
        return len(unique_texts) == len(texts)

    def test_connection(self):
        check = 0
        list_models = []
        list_models.append((self.ui.device_port_1.currentText(), self.ui.device_model1.currentText(),
                            self.ui.baud_rate_1.currentText(), 1))
        list_models.append((self.ui.device_port_2.currentText(), self.ui.device_model2.currentText(),
                            self.ui.baud_rate_2.currentText(), 2))
        list_models.append((self.ui.device_port_3.currentText(), self.ui.device_model3.currentText(),
                            self.ui.baud_rate_3.currentText(), 3))
        list_models.append((self.ui.device_port_4.currentText(), self.ui.device_model4.currentText(),
                            self.ui.baud_rate_4.currentText(), 4))
        list_models.append((self.ui.device_port_5.currentText(), self.ui.device_model5.currentText(), 0, 5))
        list_models.append((self.ui.device_port_6.currentText(), self.ui.device_model6.currentText(), 0, 6))
        # list_models.append((self.ui.device_port_7.currentText(), self.ui.device_model7.currentText(), self.ui.baud_rate_7.currentText()))

        # protection against starting with too few devices
        for port in list_models:
            if port[0] == '':
                news = sm.Small_window()
                news.show_warning("Devices are missing! Connect more.")
                return 0

        # protection against connecting to one port several times
        if not self.check_unique_texts(list_models[0][0], list_models[1][0], list_models[2][0], list_models[3][0],
                                       list_models[4][0], list_models[5][0]):
            news = sm.Small_window()
            news.show_warning("You cannot connect to one port twice! Fix ports.")
            return 0

        # test connection and waiting for it_is() to be returned from each device
        for i in range(len(list_models)):
            if list_models[i][1] == "FLUKE8808A":
                try:
                    meter = FLUKE8808A.Fluke_8808A(list_models[i][0], int(list_models[i][2]))
                    answer = meter.it_is()
                    print(answer)
                except Exception as e:
                    news = sm.Small_window()
                    news.show_error(f"Error with {i + 1} device: " + str(e))
                else:
                    check += 1
            elif list_models[i][1] == "FLUKE8846A":
                try:
                    meter = FLUKE8846A.Fluke_8846A(list_models[i][0], int(list_models[i][2]))
                    answer = meter.it_is()
                    print(answer)
                except Exception as e:
                    news = sm.Small_window()
                    news.show_error(f"Error with {i + 1} device: " + str(e))
                else:
                    check += 1
            elif list_models[i][1] == "TTI_CPX400DP":
                try:
                    dcload = TTI_CPX400DP.TTI_CPX400DP(list_models[i][0])
                    answer = dcload.it_is()
                    print(answer)
                except Exception as e:
                    news = sm.Small_window()
                    news.show_error(f"Error with {i + 1} device: " + str(e))
                else:
                    check += 1
            elif list_models[i][1] == "BKprecision8601":
                try:
                    power = BKprecision8601.BKprecision8601(list_models[i][0])
                    answer = power.it_is()
                    print(answer)
                except Exception as e:
                    news = sm.Small_window()
                    news.show_error(f"Error with {i + 1} device: " + str(e))
                else:
                    check += 1

        # if connection passed with 6 devices function return good list devices
        if check >= 6:
            self.DeviceList = list_models
            news = sm.Small_window()
            news.show_info("Devices saved and successfully tested!")
            return 1  # test passed
        else:
            news = sm.Small_window()
            news.show_error("Something went wrong! Test again.")
            return 0  # test failed
        
