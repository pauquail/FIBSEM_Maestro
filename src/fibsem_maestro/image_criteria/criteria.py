import importlib
import logging
import os

import numpy as np
from matplotlib import pyplot as plt, patches

class Criterion:
    def __init__(self, criterion_settings, mask=None, logging_enabled=False, log_dir=None):
        self.name = criterion_settings['name']
        self.border = criterion_settings['border']
        self.tile_size = criterion_settings['tile_size']
        self.final_resolution = getattr(np, criterion_settings['final_resolution'])
        self.final_regions_resolution = getattr(np, criterion_settings['final_regions_resolution'])
        self.criterion_name = criterion_settings['criterion']

        criteria_module = importlib.import_module('fibsem_maestro.image_criteria.criteria_math')
        self.criterion_func = getattr(criteria_module, criterion_settings['criterion'])

        if 'detail' in criterion_settings:
            self.lowest_detail = criterion_settings['detail'][0]
            self.highest_detail = criterion_settings['detail'][1]
        self.logging_enabled = logging_enabled
        self.log_dir = log_dir
        self.mask = mask

        self.pixel_size = None  # pixel size is measured from image
        self.tile_width_px = None  # tile width calculated from image size
        self.border_x = None  # border width in pixels
        self.border_y = None  # border height in pixels
        self.img_with_border = None  # Image without border

    def _tiles_resolution(self, img):

        if min(img.shape) == 1:  # line
            logging.info('Line image does not support tiling')
            return self.criterion_func(img)

        logging.info("Tiles resolution calculation...")
        # Apply resolution border to the acquired image
        self.img_with_border = self._crop_image_with_border(img)

        self.tile_size_px = int(self.tile_size / self.pixel_size)
        self.tile_size_px -= self.tile_size_px % 4  # must be divisible by 4

        # Get resolution of each tile and calculate final resolution
        res_arr = []

        # if tile size = 0, not apply tilling
        if self.tile_size == 0:
            tiles = [self.img_with_border]
        else:
            tiles = self._generate_image_fractions(self.img_with_border)

        for tile_img in tiles:
            try:
                res = self.criterion_func(tile_img)
            except Exception as e:
                logging.warning("FRC error on current tile. " + repr(e))
                continue
            res_arr.append(res)

        logging.debug(f'Image sectioned to {len(res_arr)} sections')

        if len(res_arr) == 0:
            logging.error("FRC nor computed")
            return 0
        else:

            final_res = self.final_resolution(np.array(res_arr))
            return final_res

    @property
    def mask_used(self):
        return self.mask is not None

    def _generate_image_fractions(self, img, overlap=0, return_coordinates=False):
        """
        Generate image fractions (tiles) with optional overlap.

        Parameters:
            img (numpy.ndarray): The input image.
            overlap (float): Proportion of overlap between tiles (0 - no overlap, 1 - complete overlap).
            return_coordinates (bool): Whether to return tile coordinates.

        Yields:
            numpy.ndarray: A generated tile from the image.
            list: [x_start, y_start, tile_width, tile_height] if return_coordinates is True.
        """
        for x in np.arange(0, img.shape[0] - self.tile_size_px + 1, int(self.tile_size_px * (1 - overlap))):
            for y in np.arange(0, img.shape[1] - self.tile_size_px + 1, int(self.tile_size_px * (1 - overlap))):
                xi = int(x)
                yi = int(y)
                if return_coordinates:
                    yield [xi, yi, self.tile_size_px, self.tile_size_px]
                else:
                    yield img[xi: xi + self.tile_size_px, yi: yi + self.tile_size_px]

    def _crop_image_with_border(self, img, return_coordinates=False):
        """
        Crop an image based on a specified border size.

        Parameters:
            img (numpy.ndarray): The input image to be cropped.
            return_coordinates (bool): Whether to return the crop coordinates.

        Returns:
            numpy.ndarray: The cropped image.
            list: [x_start, y_start, cropped_width, cropped_height] if return_coordinates is True.
        """
        self.border_x = int(img.shape[0] * self.border)
        self.border_y = int(img.shape[1] * self.border)

        if return_coordinates:
            return [self.border_x, self.border_y, img.shape[0] - 2 * self.border_x, img.shape[1] - 2 * self.border_y]
        else:
            cropped_img = img[self.border_x: self.border_x + img.shape[0] - 2 * self.border_x,
                          self.border_y: self.border_y + img.shape[1] - 2 * self.border_y]
            return cropped_img

    def tile_log_image(self, img):
        # Create figure and axes
        fig, ax = plt.subplots()
        # Display the image
        ax.imshow(img, cmap='gray')
        # if tile size = 0, not apply tilling
        if self.tile_size > 0:
            tiles = self._generate_image_fractions(self.img_with_border, return_coordinates=True)
            # Create a Rectangle patch for each tile and add it to the axes
            for tile in tiles:
                rect = patches.Rectangle((tile[0]+self.border_x, tile[1]+self.border_y), tile[2], tile[3],
                                         linewidth=1, edgecolor='r',
                                         facecolor='none')
                ax.add_patch(rect)
            plt.tight_layout()
        return fig

    def __call__(self, image, line_number=None, slice_number = None):
        """
        It measures selected resolution criterion on image.
        It uses masking, tiling, border exclusion.

        line_number - if set, only one line is selected from mask image
        """

        self.pixel_size = image.metadata.binary_result.pixel_size.x
        images = [image.data] #  only one image if o masking

        if self.mask is not None:
            images = self.mask.get_masked_images(image.data, line_number)

            if images is None:
                logging.error('Not enough masked regions for resolution calculation - masking omitted!')
                images = [image]  # calculate resolution on entire image

        # resolution from different masked regions
        region_resolutions = []
        for i, image in enumerate(images):
            # region resolution
            region_resolutions.append(self._tiles_resolution(image))
            self._save_log_subimage(image, slice_number, i)

        self._save_log_images(image, slice_number)
        return self.final_regions_resolution(region_resolutions)

    def _save_log_subimage(self, image, slice_number, index):
        """ Input image with drew tiles """
        if self.logging_enabled:
            fig = self.tile_log_image(image)
            fig.savefig(f'{self.log_dir}/{slice_number:05}/criterion_subimage_{index}.png')

    def _save_log_images(self, image, slice_number):
        # save log mask
            if self.logging_enabled and self.mask is not None:
                mask_filename = os.path.join(self.log_dir, f'{slice_number:05}/resolution')
                self.mask.save_log_images(mask_filename)
