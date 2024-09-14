import logging

from fibsem_maestro.microscope_control.abstract_control import MicroscopeControl, StagePosition, BeamControl
from fibsem_maestro.tools.support import Point

try:
    from autoscript_sdb_microscope_client import SdbMicroscopeClient
    from autoscript_sdb_microscope_client.structures import (Point as PointAS, GrabFrameSettings, AdornedImage)
    from autoscript_sdb_microscope_client.enumerations import ImagingDevice, ImageFileFormat

    virtual_mode = False
    logging.info("AS library imported.")
except ImportError:
    from fibsem_maestro.microscope_control.virtual_control import VirtualMicroscope
    from fibsem_maestro.microscope_control.virtual_control import StagePosition as StagePositionAS, ImagingDevice

    from fibsem_maestro.tools.support import Point as PointAS

    virtual_mode = True
    logging.warning("AS library could not be imported. Virtual mode used.")


class AutoscriptMicroscopeControl(MicroscopeControl):

    def __init__(self, ip_address="localhost"):
        """ Connect to AS server
        ip_address: ip address of the microscope."""

        if virtual_mode:
            self._microscope = VirtualMicroscope()
        else:
            self._microscope = SdbMicroscopeClient()
            self._microscope.connect(ip_address)

        self._electron_beam = Beam(self._microscope, 'eb')
        self._ion_beam = Beam(self._microscope, 'ib')

    @property
    def position(self):
        """Get stage position"""
        self._microscope.specimen.stage.unlink()
        p = StagePosition.from_stage_position_as(self._microscope.specimen.stage.current_position)
        logging.debug(f"Getting stage position: {p.to_dict()}...")
        return p  # Convert AS stage pos to standard stage pos

    @position.setter
    def position(self, goal: StagePosition):
        """Set stage position"""
        self._microscope.specimen.stage.absolute_move(goal.to_stage_position_as())
        logging.debug(f"Moving stage to {goal.to_dict()}...")

    @property
    def relative_position(self):
        raise AttributeError("Relative position is write-only")

    @relative_position.setter
    def relative_position(self, goal: StagePosition):
        logging.debug(f"Moving stage to {goal.to_dict()} (relative) ...")
        self._microscope.specimen.stage.relative_move(goal.to_stage_position_as())

    @property
    def electron_beam(self) -> BeamControl:
        """
        Returns the electron beam of the microscope.

        :return: The electron_beam instance of Beam
        """
        return self._electron_beam

    @property
    def ion_beam(self) -> BeamControl:
        """
        Returns the ion beam of the microscope.

        :return: The ion_beam instance of Beam
        """
        return self._ion_beam


class Beam(BeamControl):
    """ Implementation of Microscope Beam. The class is universal for electrons and ions"""

    def __init__(self, microscope, modality):
        """
        Constructor for the Beam class.

        :param microscope: A concrete instance of a microscope control object.
        :param modality: Must be eb (electron beam) or ib (ion beam).
        """
        self._scanning_area = None  # reduced area. If none, reduced area is not applied
        self._microscope = microscope
        self._modality = modality

        if modality == 'eb':
            self._beam = self._microscope.beams.electron_beam
        elif modality == 'ib':
            self._beam = self._microscope.beams.ion_beam
        else:
            raise ValueError(f"Modality {modality} not supported")

        # default values
        self._line_integration = 1
        self._extended_resolution = None  # extended resolution is set only if the required resolution is not standard
        self._standard_resolutions = ([1024, 884], [1536, 1024], [2048, 1768], [3072, 2048], [4096, 3536], [512, 442],
                                      [6144, 4096], [768, 512])  # available resolutions supported in standard mode

    @property
    def working_distance(self):
        """
        Returns the beam working distance of the microscope.

        :return: The beam working distance.
        """
        wd = self._beam.working_distance.value
        logging.debug(f"Getting working distance ({self._modality}): {wd}")
        return wd

    @working_distance.setter
    def working_distance(self, wd):
        """
        :param wd: The working distance value to be set.

        This method is used to set the working distance of the beam in the microscope.        
        """
        logging.debug(f"Setting working distance ({self._modality}): {wd}")
        if self._modality == 'eb':
            self._beam.working_distance.set_value_no_degauss(wd)
        if self._modality == 'ib':
            self._beam.working_distance.value = wd

    @property
    def stigmator_x(self):
        """
        Retrieves the x-coordinate value of the beam stigmator on the microscope.

        :return: The x-coordinate value of the beam stigmator.
        """
        value = self._beam.stigmator.value.x
        logging.debug(f"Getting stigmator x ({self._modality}): {value}")
        return value

    @stigmator_x.setter
    def stigmator_x(self, value):
        """
        Setter method for the stigmator_x property.
        """
        logging.debug(f"Setting stigmator x ({self._modality}): {value}")
        self._beam.stigmator.value = PointAS(value, self.stigmator_y)

    @property
    def stigmator_y(self):
        """
        Retrieves the y-coordinate value of the beam stigmator on the microscope.

        :return: The y-coordinate value of the beam stigmator.
        """
        value = self._beam.stigmator.value.y
        logging.debug(f"Getting stigmator y ({self._modality}): {value}")
        return value

    @stigmator_y.setter
    def stigmator_y(self, value):
        """
        Setter method for stigmator_y.

        :return: The current value of the stigmator_y.
        """
        logging.debug(f"Setting stigmator y ({self._modality}): {value}")
        self._beam.stigmator.value = PointAS(self.stigmator_x, value)

    @property
    def stigmator(self) -> Point:
        value_as = self._beam.stigmator.value
        value = Point.from_point_as(value_as)
        logging.debug(f"Getting stigmator ({self._modality}): {value.to_dict()}")
        return value

    @stigmator.setter
    def stigmator(self, p: Point):
        if not isinstance(p, Point):
            raise TypeError('Expected a Point instance')
        logging.debug(f"Setting stigmator ({self._modality}): {p.to_dict()}")
        self._beam.stigmator.value = PointAS(p.x, p.y)

    @property
    def lens_alignment_x(self):
        """Get the x-coordinate of the lens alignment value of the beam.

        :return: The x-coordinate of the lens alignment value of the beam.
        """
        value = self._beam.lens_alignment.value.x
        logging.debug(f"Getting lens alignment x ({self._modality}): {value}")
        return value

    @lens_alignment_x.setter
    def lens_alignment_x(self, value):
        """
        Sets the x-coordinate of the lens alignment for the  beam.

        :param value: The x-coordinate value for the lens alignment.
        :return: None

        """
        logging.debug(f"Setting lens alignment x ({self._modality}): {value}")
        self._beam.lens_alignment.value = PointAS(value, self.lens_alignment_y)

    @property
    def lens_alignment_y(self):
        """
        Returns the y-axis value of the lens alignment for the beam in the microscope.

        :return: The y-axis value of the lens alignment for the beam.
        """
        value = self._beam.lens_alignment.value.y
        logging.debug(f"Getting lens alignment y ({self._modality}): {value}")
        return value

    @lens_alignment_y.setter
    def lens_alignment_y(self, value):
        """
        Setter method for lens alignment y.

        :param value: The new value for lens alignment y.
        :return: None
        """
        logging.debug(f"Setting lens alignment y ({self._modality}): {value}")
        self._beam.lens_alignment.value = PointAS(self.lens_alignment_y, value)

    @property
    def lens_alignment(self):
        value_as = self._beam.lens_alignment.value
        value = Point.from_point_as(value_as)
        logging.debug(f"Getting lens alignment ({self._modality}): {value.to_dict()}")
        return value

    @lens_alignment.setter
    def lens_alignment(self, point: Point):
        if not isinstance(point, Point):
            raise TypeError('Expected a Point instance')
        logging.debug(f"Setting lens alignment ({self._modality}): {point.to_dict()}")
        self._beam.lens_alignment.value = PointAS(point.x, point.y)

    @property
    def beam_shift_x(self):
        """Get the x value of the beam shift."""
        value = self._beam.beam_shift.value.x
        logging.debug(f"Getting beam shift x ({self._modality}): {value}")
        return value

    @beam_shift_x.setter
    def beam_shift_x(self, value):
        """Set the x value of the beam shift."""
        logging.debug(f"Setting beam shift x ({self._modality}): {value}")
        self._beam.beam_shift.value = PointAS(value, self.beam_shift_y)

    @property
    def beam_shift_y(self):
        """Get the y value of the beam shift."""
        value = self._beam.beam_shift.value.y
        logging.debug(f"Getting beam shift y ({self._modality}): {value}")
        return value

    @beam_shift_y.setter
    def beam_shift_y(self, value):
        """Set the y value of the beam shift."""
        logging.debug(f"Setting beam shift y ({self._modality}): {value}")
        self._beam.beam_shift.value = PointAS(self.beam_shift_x, value)

    @property
    def beam_shift(self):
        value_as = self._beam.beam_shift.value
        value = Point.from_point_as(value_as)
        logging.debug(f"Getting beam shift ({self._modality}): {value.to_dict()}")
        return value

    @beam_shift.setter
    def beam_shift(self, point: Point):
        if not isinstance(point, Point):
            raise TypeError('Expected a Point instance')
        logging.debug(f"Setting beam shift ({self._modality}): {point.to_dict()}")
        self._beam.beam_shift.value = PointAS(point.x, point.y)

    @property
    def detector_contrast(self):
        """Get the contrast of the detector."""
        self.select_modality()  # activate right quad
        value = self._microscope.detector.contrast.value
        logging.debug(f"Getting detector contrast ({self._modality}): {value}")
        return value

    @detector_contrast.setter
    def detector_contrast(self, value):
        """Set the contrast of the detector."""
        self.select_modality()  # activate right quad
        logging.debug(f"Setting detector contrast ({self._modality}) to: {value}")
        self._microscope.detector.contrast.value = value

    @property
    def detector_brightness(self):
        """Get the brightness of the detector."""
        self.select_modality()  # activate right quad
        value = self._microscope.detector.brightness.value
        logging.debug(f"Getting detector brightness ({self._modality}): {value}")
        return value

    @detector_brightness.setter
    def detector_brightness(self, value):
        """Set the brightness of the detector."""
        self.select_modality()  # activate right quad
        logging.debug(f"Setting detector brightness ({self._modality}) to: {value}")
        self._microscope.detector.brightness.value = value

    def blank(self):
        """
        Blank the beam.
        """
        self.select_modality()  # activate right quad
        logging.debug(f"Blanking beam ({self._modality}).")
        self._beam.blank()

    def unblank(self):
        """
        Unblank the beam.
        """
        self.select_modality()
        logging.debug(f"Unblanking beam ({self._modality}).")
        self._beam.unblank()

    def start_acquisition(self):
        logging.debug(f"Starting acquisition ({self._modality})...")
        self.select_modality()  # activate right quad
        self._microscope.imaging.start_acquisition()

    def stop_acquisition(self):
        logging.debug(f"Stopping acquisition ({self._modality})...")
        self.select_modality()  # activate right quad
        self._microscope.imaging.stop_acquisition()

    def select_modality(self):
        """
        This method is used to switch the microscope's modality between the Electron Beam (eb) mode and the Ion Beam
        (ib) mode. The selection of the modality will have an impact on starting and stopping the acquisition,
        grab and get image, and on the selected detector.

        The Electron Beam mode is always in Quad 1, while the Ion Beam mode is always in Quad 2.

        """
        if self._modality.lower() == 'eb':
            self._microscope.imaging.set_active_view(1)
            self._microscope.imaging.set_active_device(ImagingDevice.ELECTRON_BEAM)
        elif self._modality.lower() == 'ib':
            self._microscope.imaging.set_active_view(2)
            self._microscope.imaging.set_active_device(ImagingDevice.ION_BEAM)
        else:
            raise ValueError("Invalid modality. Please choose either 'eb' for Electron Beam or 'ib' for Ion Beam.")

    def grab_frame(self, file_name=None):
        """
        Scans and retrieves an image.

        If file_name is provided, the image will be saved to file_name.

        Returns:
            Frame data
        """
        self.select_modality()  # activate right quad
        logging.debug(f"Grabbing frame ({self._modality}).")

        img_settings = GrabFrameSettings(line_integration=self._line_integration,
                                         bit_depth=self.bit_depth)
        if self._extended_resolution is not None:
            img_settings.resolution = f'{self._extended_resolution[0]}x{self._extended_resolution[1]}'
        if self._scanning_area is not None:
            img_settings.reduced_area = self._scanning_area.to_as()

        logging.info(f"Acquiring image..")
        try:
            grabbed_image = self._microscope.imaging.grab_frame(img_settings)
            logging.info(f"Image grabbed.")
            if file_name is not None:
                grabbed_image.save(file_name)
            return grabbed_image
        except Exception as e:
            logging.info('Grabbing frame to disk. ' + repr(e))
            if file_name is not None:
                self._microscope.imaging.grab_frame_to_disk(file_name, ImageFileFormat.TIFF, img_settings)
                logging.info(f"Image grabbed to disk.")
                return AdornedImage.load(file_name)
            else:
                raise Exception('Unable to grab the image. File name must be provided')

    def get_image(self):
        """
        Retrieves the current image being displayed.

        Returns:
            Current image data
        """
        self.select_modality()  # activate right quad
        logging.debug(f"Getting image ({self._modality}).")
        return self._microscope.imaging.get_image().data

    @property
    def line_integration(self):
        logging.debug(f"Getting line integration ({self._modality}): {self._line_integration}.")
        return self._line_integration

    @line_integration.setter
    def line_integration(self, li: int):
        """
        Set line integration for grab_frame
        Args:
            li (int): Line integration
        """
        logging.debug(f"Setting line integration to ({self._modality}): {li}.")
        self._line_integration = li

    @property
    def dwell_time(self):
        """
        Gets the dwell time of the beam.

        Returns:
            float: The beam dwell time
        """
        value = self._beam.scanning.dwell_time.value
        logging.debug(f"Getting dwell time ({self._modality}): {value}.")
        return value

    @dwell_time.setter
    def dwell_time(self, dwell_time):
        """
        Sets the dwell time of the beam.

        Args:
            dwell_time (float): The new dwell time
        """
        self._beam.scanning.dwell_time.value = dwell_time
        logging.debug(f"Setting dwell time to ({self._modality}): {dwell_time}.")

    @property
    def bit_depth(self):
        """
        Gets the bit depth of the image from the microscope. Can be either 8 or 16.

        Returns:
            int: The bit depth of the image
        """
        value = self._beam.scanning.bit_depth
        logging.debug(f"Getting bit depth ({self._modality}): {value}.")
        return value

    @bit_depth.setter
    def bit_depth(self, depth):
        """
        Sets the bit depth of the image.

        Args:
            depth (int): The new bit depth (8 or 16)
        """
        assert depth == 8 or depth == 16
        self._beam.scanning.bit_depth = depth
        logging.debug(f"Setting bit depth to ({self._modality}): {depth}.")

    @property
    def resolution(self):
        """
        Gets the resolution of the image from the microscope.

        Returns:
            tuple: The resolution of the image
        """
        r = str(self._beam.scanning.resolution.value)
        if self._extended_resolution is not None:
            logging.debug(f"Getting standard resolution ({self._modality}): {r}.")
            return r.split('x')
        else:
            logging.debug(f"Getting extended resolution ({self._modality}): {self._extended_resolution}.")
            return self._extended_resolution

    @resolution.setter
    def resolution(self, resolution):
        """
        Sets the resolution of the image.

        Args:
            resolution (tuple): The new resolution
        """
        value = f'{resolution[0]}x{resolution[1]}'
        for r in self._standard_resolutions:
            if resolution[0] == r[0] and resolution[1] == r[1]:
                logging.debug(f"Setting standard resolution to ({self._modality}): {value}.")
                self._beam.scanning.resolution.value = value
                return
        logging.debug(f"Setting extended resolution to ({self._modality}): {value}.")
        self._extended_resolution = resolution

    @property
    def horizontal_field_width(self):
        """
        Gets the horizontal field value of the image from the microscope.

        Returns:
            float: The horizontal pixel values
        """
        value = self._beam.horizontal_field_width.value
        logging.debug(f"Getting hfw ({self._modality}): {value}.")
        return value

    @horizontal_field_width.setter
    def horizontal_field_width(self, value):
        """
        Sets the horizontal pixel values.

        Args:
            value (float): The new horizontal field value
        """
        logging.debug(f"Setting hfw to ({self._modality}): {value}.")
        self._beam.horizontal_field_width.value = value

    @property
    def pixel_size(self):
        """
        Gets the pixel size of the image from the microscope.

        Returns:
            tuple: The size of the pixel
        """
        ps = self._beam.horizontal_field_width / self.resolution[0]  # x resolution
        logging.debug(f"Getting pixel size ({self._modality}): {ps}.")
        return ps

    @property
    def scanning_area(self):
        logging.debug(f"Getting scanning area ({self._modality}): {self._scanning_area}.")
        return self._scanning_area

    @scanning_area.setter
    def scanning_area(self, value):
        if value is None:
            logging.debug(f"Disabling scanning area({self._modality}).")
        else:
            logging.debug(f"Setting scanning area to ({self._modality}): {value}.")
        self._scanning_area = value
