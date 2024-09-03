import logging
import os

from scipy.spatial import distance

from fibsem_maestro.tools.support import StagePosition, Point, ScanningArea
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
        def __init__(self, settings, data_dir):
            """
            Initializes a new instance of the class.

            """
            super().__init__(settings['ip_address'])
            self.settings = settings
            self.beam = self.electron_beam  # default setting for actual beam
            self.vertical_field_width = None # vertical field of view. serves for resolution calculation
            self.li = self.settings['images_line_integration']
            self.data_dir = data_dir

        @property
        def pixel_size(self):
            return super().pixel_size
        @pixel_size.setter
        def pixel_size(self, pixel):
            """ pixel size is not possible to set directly to microscope, but it is needed for resolution calculation"""
            extended_res_i_x = int(self.horizontal_field_width / pixel)
            extended_res_i_y = int(self.vertical_field_width / pixel)
            extended_res = f"{extended_res_i_x}x{extended_res_i_y}"
            logging.info(f'Extended resolution set to: {extended_res}')
            self.beam.resolution = [extended_res_i_x, extended_res_i_y]

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

            if dist > self.settings['stage_tolerance']:
                logging.warning(
                    f"Stage reached position {new_stage_position} is too far ({dist}) from defined position {new_stage_position} ")
                self.stage_trial_counter -= 1
                self.stage_move_with_verification(new_stage_position)  # move again
                if self.stage_trial_counter == 0:
                    logging.error("Stage movement failed after multiple trials")
                    raise Exception("Stage movement failed after multiple trials")
            else:
                # reset trials counter
                self.stage_trial_counter = self.settings['stage_trials']

        def beam_shift_with_verification(self, new_beam_shift: Point):
            """
            Do beam shift.
            If the beam shift is out of range, do relative movement by stage.
            """
            try:
                self.beam.beam_shift = new_beam_shift  # set beam shift
                dist = distance.euclidean(self.beam.beam_shift.to_xy(), new_beam_shift.to_xy())
                if dist > float(self.settings['beam_shift_tolerance']):
                    raise Exception("Beam shift out of range")
            except Exception as e:  # if any problem with beam shift or out of range -> stage move
                logging.warning("Beam shift is out of range. Stage position needs to be adjusted. " + repr(e))
                # stage move = beam shift * axis reversion
                new_stage_move = new_beam_shift * Point(self.settings['beam_shift_to_stage_move'][0],
                                                        self.settings['beam_shift_to_stage_move'][1])
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
            self.beam.detector_contrast = 0
            self.beam.detector_brightness = 0
            self.beam.blank()
            self.beam.grab_frame()
            self.beam.dwell_time = dwell_backup
            self.beam.contrast = contrast_backup
            self.beam.brightness = brightness_backup

        def total_blank(self):
            """
            Blank with zero contrast and brightness
            :return:
            """
            self._detector_contrast_backup = self.beam.detector_contrast
            self._detector_brightness_backup = self.beam.detector_brightness
            self.beam.detector_contrast = 0
            self.beam.detector_brightness = 0
            self.beam.blank()

        def total_unblank(self):
            self.beam.detector_contrast = self._detector_contrast_backup
            self.beam.detector_brightness = self._detector_brightness_backup
            self.beam.unblank()

        def area_scanning(self):
            """ Perform scanning in reduced area and crop out the image """
            assert self.beam.scanning_area is not None, "Scanning area is not set"
            img = self.beam.grab_frame()
            left_top, size = self.beam.scanning_area.to_img_coordinates(img.shape)
            img_cropped = img[left_top[0]:left_top[0] + size[0], left_top[1]:left_top[1] + size[1]]
            return img_cropped

        def acquire_image(self, slice_number=None):
            self.beam = self.electron_beam
            self.beam.horizontal_field_width = self.settings['field_of_view'][0]
            self.vertical_field_width = self.settings['field_of_view'][1]
            self.pixel_size = float(self.settings['pixel_size'])  # set correct resolution

            for i in range(len(self.li)):
                self.line_integration = self.li[i]

                if slice_number is not None:
                    img_name = f"slice_{slice_number:05}_({i}).tif"
                else:
                    img_name = f"slice_test_({i}).tif"

                img_name = os.path.join(self.data_dir, img_name)
                logging.info(f"Acquiring {img_name}.")
                image = self.beam.grab_frame()
                if slice_number is not None:
                    print(f"Image {slice_number} acquired.")
                image.save(img_name)
                return image

    return Microscope  # factory

