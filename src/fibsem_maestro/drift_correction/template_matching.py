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
        try:
            self.areas = self._microscope.template_matching_areas
        except Exception as e:
            self.area = None
            logging.error('Template matching enabled but no areas not found')

    def __call__(self, img, slice_number):

        if self.area is None:
            logging.error('Template matching enabled but no areas not found. Drift correction disabled')
            return

        pixel_size = img.metadata.binary_result.pixel_size.x
        img = img.data

        # convert to 8bit if necessary
        if max(img) > 255:
            logging.warning('Template matching: Incorrect bit depth. Converting to 8 bit')
            img = (img / 256).astype('uint8')

        shift_x = []
        shift_y = []
        new_areas = []  # updated area positions

        log_img = self.save_log()
        
        for i, area in enumerate(self.areas):
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
            log_img.add_patch(rect)

            # rewrite template
            tifffile.imwrite(template_image_name, new_template_image)
            # store all new areas to the list
            new_areas.append([new_x, new_y, area[2], area[3]])

            del template_image

        if len(shift_x) == 0:
            logging.error("Confidence of all templates is too low. Drift correction disabled")
            shift_x, shift_y = 0, 0

        shift_x = np.mean(shift_x)
        shift_y = np.mean(shift_y)

        # add result shift to new areas position (new area position must calculate with a result beam shift)
        for a in new_areas:
            a[0] += int(-shift_x // pixel_size)
            a[1] += int(-shift_y // pixel_size)

        if self.logging:
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(os.path.join(self.log_dir, f"{slice_number:05}/template_matching.png"))

        shift_x = -shift_x  # beam shift X axis is reversed to image axis

        # log final shift
        self.logging_dict['shift_x'] = shift_x
        self.logging_dict['shift_y'] = shift_y

        # perform beam shift
        bs = Point(shift_x, shift_y)
        self._microscope.beam_shift_with_verification(bs)
        return bs

    def save_log(self, img):
        plt.figure()
        plt.imshow(img, cmap='gray')
        ax = plt.gca()
        for a in self.areas:
            # Create a Rectangle patch
            rect = Rectangle((a[0], a[1]), a[2], a[3], linewidth=1, edgecolor='r', facecolor='none')
            # Add the patch to the Axes
            ax.add_patch(rect)
        return ax