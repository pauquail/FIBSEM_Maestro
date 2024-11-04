import logging
import os

from scipy.spatial import distance

from fibsem_maestro.tools.support import StagePosition, Point, ScanningArea, find_in_dict
from fibsem_maestro.microscope_control.autoscript_control import AutoscriptMicroscopeControl
from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl


def create_microscope(control: str):
    """
    :param control: The type of microscope control. Possible values are: 'autoscript'
    :type control: str
    :return: A dynamically created Microscope class based on the given control type.

    """
    if control.lower() == 'autoscript':
        microscope_base = AutoscriptMicroscopeControl
    else:
        raise ValueError(f"Invalid microscope control type: {control}")

    class Microscope(microscope_base):
        def __init__(self, image_settings, microscope_settings, data_dir):
            """
            Initializes a new instance of the class.

            """
            super().__init__(microscope_settings['ip_address'])
            self.beam = self.electron_beam  # default setting for actual beam

            self._settings_init(microscope_settings, image_settings)

            self.data_dir = data_dir

            self._detector_contrast_backup = None
            self._detector_brightness_backup = None
            self.stage_trial_counter = self.stage_trials

        def _settings_init(self, microscope_settings, image_settings):
            self.image_settings = image_settings
            self.li = image_settings['images_line_integration']
            self.name = image_settings['name']
            self.stage_tolerance = microscope_settings['stage_tolerance']
            self.stage_trials = microscope_settings['stage_trials']
            self.beam_shift_tolerance = microscope_settings['beam_shift_tolerance']
            self.relative_beam_shift_to_stage = microscope_settings['relative_beam_shift_to_stage']

        def settings_init(self, settings):
            """ For global re-initialization of settings  (global settings always passed)"""
            image_settings = find_in_dict(self.name, settings['image'])
            self._settings_init(settings['microscope'], image_settings)

        def stage_move_with_verification(self, new_stage_position: StagePosition):
            """
            Moves the stage to the specified position and verifies the movement within a tolerance.

            :param new_stage_position: The new position of the stage.
            :return: None
            """
            self.position = new_stage_position  # set stage position
            position = self.position  # get stage position
            # after movement, verify whether the movement is within tolerance
            dist = distance.euclidean(position.to_xy(), new_stage_position.to_xy())

            if dist > self.stage_tolerance:
                logging.warning(
                    f"Stage reached position {new_stage_position} is too far ({dist}) from defined "
                    f"position {new_stage_position} ")
                self.stage_trial_counter -= 1
                self.stage_move_with_verification(new_stage_position)  # move again
                if self.stage_trial_counter == 0:
                    logging.error("Stage movement failed after multiple trials")
                    raise Exception("Stage movement failed after multiple trials")
            else:
                # reset trials counter
                self.stage_trial_counter = self.stage_trials

        def beam_shift_with_verification(self, new_beam_shift: Point):
            """
            Do beam shift.
            If the beam shift is out of range, do relative movement by stage.
            """
            try:
                self.beam.beam_shift = new_beam_shift  # set beam shift
                dist = distance.euclidean(self.beam.beam_shift.to_xy(), new_beam_shift.to_xy())
                if dist > float(self.beam_shift_tolerance):
                    raise Exception("Beam shift out of range")
            except Exception as e:  # if any problem with beam shift or out of range -> stage move
                logging.warning("Beam shift is out of range. Stage position needs to be adjusted. " + repr(e))
                # stage move = beam shift * shift conversion
                new_stage_move = new_beam_shift * Point(self.relative_beam_shift_to_stage[0],
                                                        self.relative_beam_shift_to_stage[1])
                new_stage_move *= self.beam.beam_shift_to_stage_move  # Direction conversion
                self.relative_position = StagePosition(x=new_stage_move.x, y=new_stage_move.y)
                self.beam.beam_shift = Point(0, 0)  # zero beam shift

        def blank_screen(self):
            """
            Make a black screen (blank and grab frame).
            :return: None
            """
            contrast_backup = self.beam.detector_contrast
            brightness_backup = self.beam.detector_brightness
            dwell_backup = self.beam.dwell_time
            li_backup = self.beam.line_integration
            self.beam.detector_contrast = 0
            self.beam.detector_brightness = 0
            self.beam.blank()
            self.beam.line_integration = 1
            self.beam.dwell_time = self.beam.minimal_dwell
            self.beam.grab_frame()
            self.beam.dwell_time = dwell_backup
            self.beam.detector_contrast = contrast_backup
            self.beam.detector_brightness = brightness_backup
            self.beam.line_integration = li_backup

        def total_blank(self):
            """
            Blank with zero contrast and brightness
            :return:
            """
            if not self.beam.detector_contrast == 0:
                self._detector_contrast_backup = self.beam.detector_contrast
            if not self.beam.detector_brightness == 0:
                self._detector_brightness_backup = self.beam.detector_brightness
            self.beam.detector_contrast = 0
            self.beam.detector_brightness = 0
            self.beam.blank()

        def total_unblank(self):
            if self._detector_contrast_backup is not None and not self._detector_contrast_backup == 0:
                self.beam.detector_contrast = self._detector_contrast_backup
            if self._detector_brightness_backup is not None and not self._detector_brightness_backup == 0:
                self.beam.detector_brightness = self._detector_brightness_backup
            self.beam.unblank()

        def area_scanning(self):
            """ Perform scanning in reduced area and crop out the image """
            assert self.beam.scanning_area is not None, "Scanning area is not set"
            img = self.beam.grab_frame()
            left_top, size = self.beam.scanning_area.to_img_coordinates(img.shape)
            img_cropped = img[left_top.x:left_top.x + size[0], left_top.y:left_top.y + size[1]]
            return img_cropped

        def apply_beam_settings(self, image_settings):
            if 'bit_depth' in image_settings:
                self.beam.bit_depth = image_settings['bit_depth']
            if 'field_of_view' in image_settings:
                self.beam.horizontal_field_width = image_settings['field_of_view'][0]
                self.beam.vertical_field_width = image_settings['field_of_view'][1]
            if 'resolution' in image_settings:
                self.beam.resolution = image_settings['resolution']
            # call pixel size from Beam class, set correct resolution
            if 'pixel_size' in image_settings:
                self.beam.pixel_size = float(image_settings['pixel_size'])
            if 'images_line_integration' in image_settings:
                self.beam.line_integration = image_settings['images_line_integration']
            if 'dwell' in image_settings:
                self.beam.dwell_time = image_settings['dwell']

        def acquire_image(self, slice_number=None):
            """
            Acquires an images using the microscope's electron beam.
            The resolution is set based on the FoV and pixe_size.
            It can acquire multiple images if the li (setting images_line_integration) is array.
            It saves image (data_dir used)

            :param slice_number: Optional slice number for the image. Defaults to None.
            :return: The acquired image.
            """
            image = None

            self.apply_beam_settings(self.image_settings)

            if slice_number is not None:
                img_name = f"slice_{slice_number:05}.tif"
            else:
                img_name = f"slice_test.tif"

            img_name = os.path.join(self.data_dir, img_name)
            logging.info(f"Acquiring {img_name}.")
            image = self.beam.grab_frame(img_name)
            if slice_number is not None:
                print(f"Image {slice_number} acquired.")

            return image

    return Microscope  # factory
