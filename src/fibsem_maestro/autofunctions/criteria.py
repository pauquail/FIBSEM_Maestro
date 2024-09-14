import logging
import os

import numpy as np
from matplotlib import pyplot as plt, patches
from scipy.ndimage import gaussian_filter

from fibsem_maestro.FRC.frc import frc


def gauss_filter(x, px_size, detail):
    """
    Applies a Gaussian filter to the input array.

    :param x: The input array.
    :param px_size: The pixel size of the input array (m).
    :param detail: The level of detail in the filter (m).
    :return: The filtered array.

    """
    px = detail / px_size
    sigma = 1 / (2 * np.pi * (1 / px))
    return gaussian_filter(x.astype(np.float32), sigma, mode='nearest', truncate=6)


class Criterion:
    def __init__(self, criterion_settings, mask=None, logging_enabled=False, log_dir=None):
        self.name = criterion_settings['name']
        self.border = criterion_settings['border']
        self.tile_size = criterion_settings['tile_size']
        self.final_resolution = getattr(np, criterion_settings['final_resolution'])
        self.final_regions_resolution = getattr(np, criterion_settings['final_regions_resolution'])
        self.criterion_name = criterion_settings['criterion']
        self.criterion_func = getattr(self, criterion_settings['criterion'])
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

    def bandpass_criterion(self, img) -> float:
        """
        Mean value of band-passed image.

        :param img: The input image.
        :return: Criterion.
        """
        img_low = gauss_filter(img, self.pixel_size, self.lowest_detail)
        img_high = gauss_filter(img, self.pixel_size, self.highest_detail)

        result = np.mean(abs(img_high - img_low))  # mean of absolute images
        return result

    def bandpass_var_criterion(self, img) -> float:
        """
        Variance of band-passed image.

        :param img: The input image.
        :return: Criterion.
        """
        img_low = gauss_filter(img, self.pixel_size, self.lowest_detail)
        img_high = gauss_filter(img, self.pixel_size, self.highest_detail)

        result = np.var(img_high - img_low)
        return result

    def fft_criterion(self, img):
        """
        :param img: The image data. It can be either a 1-dimensional array representing an image line
        or a 2-dimensional array representing the entire image.

        :return: The sum of the amplitudes of the filtered frequencies.

        This method calculates the FFT (Fast Fourier Transform) of the given image data. It removes frequencies within
        the specified range and returns the sum of the amplitudes of the remaining frequencies.
        """

        def fft_criterion1d():
            img0 = img - np.mean(img)  # remove 0 frequency
            fft_line = np.fft.fft(img0)  # fft

            freq = np.fft.fftfreq(len(img), self.pixel_size)  # get freq axis
            fft_line = fft_line[freq > 0]  # remove negative frequencies
            freq = freq[freq > 0]  # remove negative frequencies from freq axis

            # filter frequencies
            band_i = np.where((freq < 1 / self.highest_detail) & (freq > 1 / self.lowest_detail))[0]
            # sum of amplitudes of all filtered frequencies
            result = np.sum(abs(fft_line[band_i]))
            return result

        def fft_criterion_2d():
            img0 = img - np.mean(img)  # remove 0 frequency
            fft_img = np.fft.fft2(img0)  # fft

            freq1 = np.fft.fftfreq(fft_img.shape[0], self.pixel_size)  # get x freq axis
            freq2 = np.fft.fftfreq(fft_img.shape[1], self.pixel_size)  # get y freq axis

            freq1 = np.repeat(freq1[:, np.newaxis], freq2.shape[0], axis=1)
            freq2 = np.repeat(freq2[:, np.newaxis], freq1.shape[0], axis=1).T
            freq = np.sqrt(freq1 ** 2 + freq2 ** 2)  # make freq matrix

            high_frequency = 1 / self.highest_detail  # highest detail frequency
            low_frequency = 1 / self.lowest_detail  # lowest detail frequency

            # make freq filter
            freq[freq > high_frequency] = 0
            freq[freq < low_frequency] = 0
            freq[freq > 0] = 1

            fft_img *= freq  # filter freq
            result = np.sum(abs(fft_img))
            return result

        if np.ndim(img) == 1:
            return fft_criterion1d()
        elif np.ndim(img) == 2:
            return fft_criterion_2d()
        else:
            raise NotImplementedError('Only 1D and 2D images are currently supported for focus criterion.')

    def frc_criterion(self, img):
        try:
            res = frc(img, self.pixel_size)
        except Exception as e:
            logging.warning("FRC error on current tile. " + repr(e))
            return np.nan
        return res

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
        images = [image.data] #  only one image if o maskinf

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
        if self.logging_enabled:
            fig = self.tile_log_image(image)
            fig.savefig(f'{self.log_dir}/{slice_number:05}/criterion_subimage_{index}.png')

    def _save_log_images(self, image, slice_number):
        # save log mask
            if self.logging_enabled and self.mask is not None:
                mask_filename = os.path.join(self.log_dir, f'{slice_number:05}/resolution')
                self.mask.save_log_images(mask_filename)
