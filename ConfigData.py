class ConfigData:
    # Class for storing configuration data for the test
    ''' Chamber_on - bool do we use temp chamber
        chamber_mode - bool what mode we are using: True - temp, False - gradient
        temp_err - do we restrict temperature error
        humidity_err - do we restrict humidity error '''
    def __init__(self, step_nr=1, chamber_on=False, chamber_mod=True, temp_err=False, humid_err=False):

        self.step_no = step_nr

        self.use_chamber = chamber_on
        self.chamber_mode = chamber_mod
        self.chb_allow_temp_err = temp_err
        self.chb_allow_humidity_err = humid_err

        self.amm_inl_unit = 'A'
        self.volt_inl_unit = 'V'

        self.amm_out_unit = 'A'
        self.volt_out_unit = 'V'

        self.psu_volt = 0.0
        self.psu_volt_unit = 'V'
        self.psu_amm = 0.0
        self.psu_amm_unit = 'A'

        self.dcl_mode = "Constant current (CC)"
        self.dcl_end = 0.0
        self.dcl_changes_no = 10
        self.dcl_start = 0.0

        self.chb_temp = 20.0
        self.chb_humidity = 40.0

        self.chb_temp_step = 1.0
        self.chb_start_temp = 20.0
        self.chb_humidity_step = 1.0
        self.chb_start_humidity = 40.0

        self.chb_temp_err = 1.0
        self.chb_humidity_err = 1.0
