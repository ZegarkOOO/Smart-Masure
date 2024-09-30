import sys
import asyncio
from PyQt5 import QtWidgets
import UI_settings
from BurySmartMeasure import Ui_BurySmartMeasureClass

def main():
    app = QtWidgets.QApplication(sys.argv)
    BurySmartMeasureClass = QtWidgets.QMainWindow()
    ui = Ui_BurySmartMeasureClass()
    ui.setupUi(BurySmartMeasureClass)

    ui_set = UI_settings.UiSettings(ui)

    chamber_radio_gr = QtWidgets.QButtonGroup()
    chamber_radio_gr.addButton(ui.set_gradient_radio)
    chamber_radio_gr.addButton(ui.set_temp_radio)

    # ---------Connect buttons to functions-------------
    # refresh button
    ui.refresh_dev_btn.clicked.connect(ui_set.refresh_devices)

    # start test button
    ui.start_test_btn.clicked.connect(ui_set.run_start_test)
 
    # device selection
    ui_set.set_device_select_combos()

    # test connection button
    ui.test_connection.clicked.connect(ui_set.test_connection)

    # navigation
    ui.config_dev.clicked.connect(ui_set.next_page)
    ui.next_pg1_btn.clicked.connect(ui_set.next_page)
    ui.next_pg2_btn.clicked.connect(ui_set.next_page)

    # temp chamber settings
    ui.use_temp_chamber_chkbox.toggled.connect(ui_set.use_chamber)
    ui.use_allowable_temp_err_chkbox.stateChanged.connect(ui_set.chamber_temp_limit)
    ui.use_allowable_humidity_err_chkbox.stateChanged.connect(ui_set.chamber_humidity_limit)
    ui.set_temp_radio.toggled.connect(ui_set.select_chamber_mode)
    ui.set_gradient_radio.toggled.connect(ui_set.select_chamber_mode)
    ui.gr_temp_step_spb.valueChanged.connect(ui_set.chamber_temp_calc)
    ui.gr_humidity_step_spb.valueChanged.connect(ui_set.chamber_temp_calc)

    # steps
    ui.avg_res_no_spb.valueChanged.connect(ui_set.avg_res_no_spb_change)
    ui.steps_spb.valueChanged.connect(ui_set.steps_set)
    ui.step_num1_combo.currentIndexChanged.connect(ui_set.step_btn1_clicked)
    ui.step_num2_combo.currentIndexChanged.connect(ui_set.step_btn2_clicked)
    ui.next_step_btn.clicked.connect(ui_set.steps_increment)
    ui.next_step1_btn.clicked.connect(ui_set.steps_increment)
    ui.freq_spb.valueChanged.connect(ui_set.freq_change)

    # DC load
    ui.DCload_mode_combo.currentIndexChanged.connect(ui_set.DCload_mode_change)
    ui.DCload_steps_spb.valueChanged.connect(ui_set.DCload_mode_change)
    ui.DCload_start_spb.valueChanged.connect(ui_set.DCload_mode_change)
    ui.DCload_end_spb.valueChanged.connect(ui_set.DCload_mode_change)
    ui.save_cfg_btn1.clicked.connect(ui_set.save_config)
    ui.save_cfg_btn2.clicked.connect(ui_set.save_config)

    ui.browse_path_toolbtn.clicked.connect(ui_set.find_path_clicked)

    BurySmartMeasureClass.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()