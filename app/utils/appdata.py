# app/utils/appdata.py
from threading import Lock

class AppData:
    default_json_grid = {}
    _last_selection_lock = Lock()
    last_selected = {"cross": "", "arm": ""}  # Set default starting value

    saved_unitary_U1 = None     
    saved_unitary_U2 = None     
    saved_unitary_U3 = None    

    @classmethod
    def update_last_selection(cls, cross, arm):
        cls.last_selected["cross"] = cross.split('-')[0]  # Handle composite labels
        cls.last_selected["arm"] = arm.split('-')[0]
        
    @classmethod 
    def get_last_selection(cls):
        with cls._last_selection_lock:
            return cls.last_selected.copy()

    test_json_grid = {"A1": {"arms": ["TL", "TR", "BL", "BR"], "theta": "0", "phi": "0"},
    "B1": {"arms": ["TL", "TR", "BL", "BR"], "theta": "0", "phi": "0"}}
    def __init__(self, n_channels):
        self.n_channels = n_channels
        
        # Fit functions and I/O configuration.
        self.fit_func = [
            "Linear fit (V = R₀ * I )", 
            "Cubic + linear fit (V = R₀ ( I + αI³)"
        ]
        self.default_fit = self.fit_func[1]
        self.IOconfig_options = ["Cross", "Bar", "50:50", "Custom"]
        self.default_IOconfig = self.IOconfig_options[0]


        # Calibration parameters (dummy data, one set per channel).
        self.caliparamlist_lin_cross = [{"amp": 1.0, "omega": 1.0, "phase": 0.5, "offset": 2.0} for _ in range(n_channels)]
        self.caliparamlist_lin_bar   = [{"amp": 1.1, "omega": 1.1, "phase": 0.6, "offset": 2.1} for _ in range(n_channels)]
        self.caliparamlist_lincub_cross = [{"amp": 1.2, "omega": 1.2, "phase": 0.7, "offset": 2.2} for _ in range(n_channels)]
        self.caliparamlist_lincub_bar   = [{"amp": 1.3, "omega": 1.3, "phase": 0.8, "offset": 2.3} for _ in range(n_channels)]

        # Resistance parameters.
        self.linear_resistance_list = [10, 20, 30, 40][:n_channels]
        self.currentheaterid = [f"Heater{i+1}" for i in range(n_channels)]
        self.resistance_parameter_list = [[1.0, 2.0] for _ in range(n_channels)]

        # Dummy function for fitting.
        self.fit_cos = lambda x: x

        # Data structures for storing per-channel runtime data.
        self.channellist = []
        self.idlist = []
        self.customtkinterresistancelist = []
        self.customtkinterrmin_list = []
        self.customtkinterrmax_list = []
        self.customtkinteralpha_list = []
        self.customtkinterlinear_resistance_list = []
        self.customtkinterresistance_parameter_list = []
        self.currentlimitlist = []       # Global current limits for each channel.
        self.appliedcurrlist = []
        self.measuredcurrentlist = []
        self.rampstartlist = []
        self.rampendlist = []
        self.stepslist = []
        self.stabtimelist = []
        self.setcurrlabellist = []
        self.setphaselist = []
        self.setphaselabellist = []

        # Global per-channel configuration.
        self.fit_func_allchannels = [self.fit_func[0] for _ in range(n_channels)]
        self.IOconfig_allchannels = [self.IOconfig_options[0] for _ in range(n_channels)]
        self.set_ioconfig = ['Null' for _ in range(n_channels)]
        self.set_fit = ['Null' for _ in range(n_channels)]
        
        # Default selections.
        self.fit = self.fit_func[0]
        self.IOconfig = self.IOconfig_options[0]

        # New attributes required for phase application.
        self.phase_offset = 0.5        # Dummy offset value (update as needed)
        self.b = 1.0                   # Dummy value for conversion factor
        self.R = 50.0                  # Dummy linear resistance value (Ohms)
        self.R0 = 50.0                 # Dummy value for nonlinear fit (Ohms)
        self.alpha = 0.01              # Dummy nonlinear parameter
        self.current_fit = self.fit_func[0]  # Choose the first fit function by default
        self.allowedinputvalues = "0123456789."  # Allowed characters for phase input

        # Additional lists for GUI grouping.
        self.fitselectpack = []
        self.IOconfigselectpack = []
        self.setIlimitpack = []
        self.setIpack = []
        self.startpack = []
        self.endpack = []
        self.stepspack = []
        self.pausepack = []
        self.acqresist_minpack = []
        self.acqresist_maxpack = []
        self.alphapack = []
        self.acqresist_linpack = []

        # Define matrices explicitly. For any attribute not defined, we default to an empty list.
        self.xdatalist_IObar = []
        self.ydatalist_IObar = []
        self.xdatalist_IOcross = []
        self.ydatalist_IOcross = []
        self.linchar_current = []
        self.linchar_voltage = []
        self.lincubchar_current = []
        self.lincubchar_voltage = []
        self.resistancelist = []
        self.rmin_list = []
        self.rmax_list = []
        self.alpha_list = []
        self.derivedcurrentlist = []
        self.phiphase2list = []

        self.standard_matrices = {
            "xdatalist_IObar": self.xdatalist_IObar,
            "ydatalist_IObar": self.ydatalist_IObar,
            "xdatalist_IOcross": self.xdatalist_IOcross,
            "ydatalist_IOcross": self.ydatalist_IOcross,
            "linchar_current": self.linchar_current,
            "linchar_voltage": self.linchar_voltage,
            "lincubchar_current": self.lincubchar_current,
            "lincubchar_voltage": self.lincubchar_voltage,
            "resistancelist": self.resistancelist,
            "resistance_parameter_list": self.resistance_parameter_list,
            "rmin_list": self.rmin_list,
            "rmax_list": self.rmax_list,
            "alpha_list": self.alpha_list,
            "linear_resistance_list": self.linear_resistance_list,
            "caliparamlist_lin_cross": self.caliparamlist_lin_cross,
            "caliparamlist_lin_bar": self.caliparamlist_lin_bar,
            "caliparamlist_lincub_cross": self.caliparamlist_lincub_cross,
            "caliparamlist_lincub_bar": self.caliparamlist_lincub_bar,
            "derivedcurrentlist": self.derivedcurrentlist,
            "phiphase2list": self.phiphase2list
        }

        self.res_lin_char_images = []
        self.res_lincub_char_images = []
        self.opmod_lin_char_cross_state_images = []
        self.opmod_lin_char_bar_state_images = []
        self.opmod_lincub_char_cross_state_images = []
        self.opmod_lincub_char_bar_state_images = []

        self.bytesio_matrices = {
            "res_lin_char_images": self.res_lin_char_images,
            "res_lincub_char_images": self.res_lincub_char_images,
            "opmod_lin_char_cross_state_images": self.opmod_lin_char_cross_state_images,
            "opmod_lin_char_bar_state_images": self.opmod_lin_char_bar_state_images,
            "opmod_lincub_char_cross_state_images": self.opmod_lincub_char_cross_state_images,
            "opmod_lincub_char_bar_state_images": self.opmod_lincub_char_bar_state_images
        }
