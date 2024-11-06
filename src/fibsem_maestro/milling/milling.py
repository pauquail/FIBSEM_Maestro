class Milling:
    def __init__(self, milling_settings, log_dir=None):
        self.settings_init(milling_settings)
        self._log_dir = log_dir

    def settings_init(self, milling_settings):
        self.direction = milling_settings['direction']
        self.fiducial_margin = milling_settings['fiducial_margin']
        self.milling_depth = milling_settings['milling_depth']
        self.pattern = milling_settings['pattern']
        self.slice_distance = milling_settings['slice_distance']
        self.variables_to_save = milling_settings['variables_to_save']
        self.settings_file = milling_settings['settings_file']

