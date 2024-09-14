import logging
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import cv2
import tifffile

from fibsem_maestro.tools.support import Point


class TemplateMatchingDriftCorrection:
    def __init__(self, microscope, settings, template_matching_dir, logging_dict, logging_enabled=False, log_dir=None):
        self._microscope = microscope
        self.min_confidence = settings['min_confidence']

        self.log_dir = log_dir
        self.logging = logging_enabled
        self.template_matching_dir = template_matching_dir
        self.logging_dict = logging_dict
        self.areas = None

    def _prepare_image(self, img):
        pixel_size = img.metadata.binary_result.pixel_size.x
        img = img.data

        # convert to 8bit if necessary
        if max(img) > 255:
            logging.warning('Template matching: Incorrect bit depth. Converting to 8 bit')
            img = (img / 256).astype('uint8')

        return img, pixel_size

    def _calculate_shift(self, i, img, area, pixel_size, shift_x, shift_y, new_areas):
        """
        :param i: The index of the template image being processed.
        :type i: int
        :param img: The image to be matched against the template image.
        :type img: numpy.ndarray
        :param area: The area of the image to be matched.
        :type area: Tuple[int, int, int, int]
        :param pixel_size: The size of each pixel in the image.
        :type pixel_size: float
        :param shift_x: A list to store the calculated X-shifts.
        :type shift_x: List[float]
        :param shift_y: A list to store the calculated Y-shifts.
        :type shift_y: List[float]
        :param new_areas: A list to store the new areas after shifting.
        :type new_areas: List[List[int]]
        :return: None

        This method calculates the shift between the template image and the given area of the input image. It uses
        template matching with the TM_CCOEFF_NORMED method to find the best match. The calculated shift values are
        stored in the shift_x and shift_y lists, and the new_areas list is updated with the shifted areas. The
        template image file is refreshed with the new area and saved.

        This method does not return any value.
        """
        template_image_name = os.path.join(self.template_matching_dir, f"dc_template_{i}.tiff")

        template_image = tifffile.imread(template_image_name)

        # locate
        result = cv2.matchTemplate(img, template_image, cv2.TM_CCOEFF_NORMED)
        (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)
        logging.info(f'Template matching confidence: {maxVal}')
        center_x = maxLoc[0] - area[0]
        center_y = maxLoc[1] - area[1]

        # log
        self.logging_dict[f"template{i}_dx"] = center_x
        self.logging_dict[f"template{i}_dy"] = center_y
        self.logging_dict[f"template{i}_confidence"] = maxVal

        # save shift
        if maxVal > self.min_confidence:
            shift_x.append(center_x * pixel_size)
            shift_y.append(center_y * pixel_size)
        else:
            logging.warning("Confidence too low")

        # refresh template
        new_x = int(area[0] + center_x)
        new_y = int(area[1] + center_y)
        new_template_image = img[new_y:new_y + area[3], new_x:new_x + area[2]]

        # add new area to logging image
        rect = Rectangle((new_x, new_y), area[2], area[3], linewidth=1,
                         edgecolor='b', facecolor='none')
        self.log_img.add_patch(rect)

        # rewrite template
        tifffile.imwrite(template_image_name, new_template_image)
        # store all new areas to the list
        new_areas.append([new_x, new_y, area[2], area[3]])

        del template_image

    def _shift_process(self, pixel_size, shift_x, shift_y, new_areas):
        if len(shift_x) == 0:
            logging.error("Confidence of all templates is too low. Drift correction disabled")
            shift_x, shift_y = 0, 0

        # final shift
        shift_x = np.mean(shift_x)
        shift_y = np.mean(shift_y)

        # add result shift to new areas position (new area position must calculate with a result beam shift)
        for a in new_areas:
            a[0] += int(-shift_x // pixel_size)
            a[1] += int(-shift_y // pixel_size)
        shift_x = -shift_x  # beam shift X axis is reversed to image axis
        return shift_x, shift_y, new_areas

    def _log(self, slice_number, shift_x, shift_y):
        if self.logging:
            fig = self.log_img()
            fig.savefig(os.path.join(self.log_dir, f"{slice_number:05}/template_matching.png"))

        # log final shift
        self.logging_dict['shift_x'] = shift_x
        self.logging_dict['shift_y'] = shift_y

    def _log_plot(self, img):
        plt.figure()
        plt.imshow(img, cmap='gray')
        ax = plt.gca()
        for a in self.areas:
            # Create a Rectangle patch
            rect = Rectangle((a[0], a[1]), a[2], a[3], linewidth=1, edgecolor='r', facecolor='none')
            # Add the patch to the Axes
            ax.add_patch(rect)
        plt.tight_layout()
        plt.axis('off')
        return fig

    def __call__(self, img, slice_number):
        """
        :param img: The input image for drift correction.
        :param slice_number: The number of the image slice.
        :return: The point object representing the calculated beam shift.
        """
        if self.areas is None:
            logging.error('Template matching enabled but no areas not found. Drift correction disabled')
            return

        shift_x = []
        shift_y = []
        new_areas = []  # updated area positions
        # convert to 8b if needed
        img, pixel_size = self._prepare_image(img)
        # image with rectangles on areas positions
        self.log_img = self._log_plot(img)
        
        for i, area in enumerate(self.areas):
            # update shifts and new_areas
            self._calculate_shift(i, img, area, pixel_size, shift_x, shift_y, new_areas)

        # calculate final  shift and new areas
        shift_x, shift_y, new_areas = self._shift_process(pixel_size, shift_x, shift_y, new_areas)

        self._log(slice_number, shift_x, shift_y)

        # update areas
        self.areas = new_areas

        # perform beam shift
        bs = Point(shift_x, shift_y)
        self._microscope.beam_shift_with_verification(bs)
        return bs
