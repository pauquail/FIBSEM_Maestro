import importlib
import numpy as np
from matplotlib import pyplot as plt, patches
from scipy.ndimage.measurements import label
from scipy.ndimage import binary_fill_holes, zoom
from skimage.measure import regionprops
import logging
from patchify import patchify, unpatchify

from fibsem_maestro.tools.math_tools import crop_image


class ImagePreparator:
    """ Prepare image for model prediction: downsampling + padding + patchify
    and unpack prediction mask to image format"""

    def __init__(self, patch_size, downsampling_factor, fill_holes):
        self.patch_size = patch_size
        self.downsampling_factor = downsampling_factor
        self.fill_holes = fill_holes
        self.original_shape = None
        self.original_padded_shape = None
        self.original_patches_shape = None

    def prepare_image_for_prediction(self, img):
        """ Input image -> prediction format"""
        self.original_shape = img.shape
        # downsampling
        input_image = zoom(img, 1 / self.downsampling_factor)

        # padding
        pad_height = self.patch_size[0] - (input_image.shape[0] % self.patch_size[0]) \
            if (input_image.shape[0] % self.patch_size[0]) != 0 else 0
        pad_width = self.patch_size[1] - (input_image.shape[1] % self.patch_size[1]) \
            if (input_image.shape[1] % self.patch_size[1]) != 0 else 0
        input_image = np.pad(input_image, ((0, pad_height), (0, pad_width)), mode='constant')
        self.original_padded_shape = input_image.shape

        # split to patches
        input_image = patchify(input_image, self.patch_size, step=self.patch_size[0])
        self.original_patches_shape = input_image.shape

        # merge patches to one axis
        input_image = input_image.reshape(-1, *input_image.shape[2:])[
            ..., np.newaxis]  # merge first two axis and add depth
        return input_image

    def get_mask_image_from_prediction(self, img):
        """ Predicted format -> Output mask in file format"""
        # reshape back to image size
        output_image = img.reshape(self.original_patches_shape)
        output_image = unpatchify(output_image, self.original_padded_shape)
        output_image = zoom(output_image, self.downsampling_factor)  # upsampling
        output_image = output_image[0:self.original_padded_shape[0],
                       0:self.original_padded_shape[1]]
        # convert to binary
        output_image[output_image > 0.5] = 1
        output_image[output_image <= 0.5] = 0
        if self.fill_holes:
            output_image = binary_fill_holes(output_image)
        output_image = output_image.astype(np.uint8)
        return output_image


class MaskPostProcessor:
    """ The functions with mask processing (get center, get the largest rectangles)"""

    def __init__(self, min_area):
        self.min_area = min_area

    def _get_labeled_mask(self, mask_image):
        # Perform connected component analysis, the `structure` parameter defines
        # how pixels are connected
        structure = np.ones((3, 3), dtype=np.int8)
        labeled_mask, num_features = label(mask_image, structure)

        # filter small blobs
        if self.min_area is not None:
            # Calculate the area of each blob
            blob_areas = np.bincount(labeled_mask.ravel())
            # Create a _mask for blobs that have area greater than the defined min_area
            mask = np.isin(labeled_mask, np.where(blob_areas > self.min_area)[0])
            # Apply the _mask to the image,
            # This will set pixels in blobs with area <= min_area to 0
            filtered_image = mask_image * mask
            labeled_mask, num_features = label(filtered_image, structure)

        return labeled_mask, num_features

    def get_center(self, mask_image):
        """ Get center of masked blob """
        labeled_mask, num_features = self._get_labeled_mask(mask_image)
        if num_features > 1:
            logging.warning(f"Too much features ({num_features}) found in _mask. Drift correction skipped.")
            return None

        properties = regionprops(labeled_mask)

        return properties[0].centroid[1], properties[0].centroid[0]

    def largest_rectangles_in_mask(self, mask_image):
        """ Get the largest possible rectangle that fits to masked blob"""
        labeled_mask, num_features = self._get_labeled_mask(mask_image)

        rectangles = []

        # Iterate over each found feature
        for feature in range(1, num_features + 1):

            # Create a binary _mask for the current feature
            feature_mask = (labeled_mask == feature).astype(int)

            # Initialize the DP table and variables to hold the max area and
            # coordinates of max rectangle
            dp = np.zeros_like(feature_mask, dtype=int)
            max_area = 0
            max_rect = (0, 0, 0, 0)  # x1, y1, x2, y2

            for i in range(feature_mask.shape[0]):
                for j in range(feature_mask.shape[1]):
                    if feature_mask[i, j] == 0:
                        dp[i, j] = 0
                    else:
                        dp[i, j] = dp[i - 1, j] + 1 if i > 0 else 1
                    m = dp[i, j]
                    for k in range(j, -1, -1):
                        if dp[i, k] == 0:
                            break
                        m = min(m, dp[i, k])
                        area = m * (j - k + 1)
                        if area > max_area:
                            max_area = area
                            max_rect = (k, i - m + 1, j, i)

            rectangles.append(max_rect)
        return rectangles


class Masking:
    def __init__(self, settings):
        # settings
        self.name = settings['mame']
        self.update_mask = settings['update_mask']
        self.mask_image_li = settings['mask_image_li']
        self.min_fraction = settings['min_fraction']
        self.model_path = settings['model_path']
        self.threshold = settings['threshold']
        self.iterative_training = settings['iterative_training']
        # default values
        self._image = None
        self._rectangles = None
        self._mask = None
        self._model = None
        self.original_padded_shape = None
        self.original_patches_shape = None
        # load model
        try:
            module = importlib.import_module(self.model_path)
            self._model = module.load_model()
        except Exception as e:
            logging.error(f'Error in loading model {self.model_path}. The masking is disabled! {e} ')
            self.use_mask = False
            self._model = None

        self.image_preparator = ImagePreparator(settings['patch_size'], settings['downsampling_factor'],
                                                settings['fill_holes'])
        self.mask_post_processor = MaskPostProcessor(settings['min_area'])

    def mask_images(self, line_number=None):
        """

        :param line_number: The line number of the image to be masked. If None, all images will be masked.
        :return: A list of masked rectangle areas.

        This method masks image (rectangle areas) based on a predicted mask. If a line number is provided,
        only the image at that line number will be masked. Otherwise, while image will be masked.

        """
        self._mask = self.predict_mask()

        if line_number is not None:
            mask_image = self._mask[line_number]
        else:
            mask_image = self._mask

        if np.sum(mask_image) / len(mask_image) < self.min_fraction:
            logging.warning('Focus criterion: Not enough masked pixels')
            return None
        else:
            self._rectangles = self.mask_post_processor.largest_rectangles_in_mask(self._mask)
            images = []
            for r in self._rectangles:
                images.append(crop_image(self._image, r))
            return images

    def predict_mask(self):
        """ Predict mask from image """
        # convert image to the form suitable for prediction
        input_image = self.image_preparator.prepare_image_for_prediction(self._image)
        # predict _mask
        predicted = self._model(input_image).numpy()[..., 1]
        # unpack mask to image format
        mask = self.image_preparator.get_mask_image_from_prediction(predicted)

        if self.iterative_training:
            mask_for_training = self.image_preparator.prepare_image_for_prediction(mask)
            self._model.fit(input_image, mask_for_training, {
                'epochs': 1,
                'batchSize': 16
            })

        return mask

    def update_img(self, beam, image_for_mask=None):
        """ Based on update_mask setting, it grabs new image, or it takes last image passes as argument."""
        if self.update_mask:
            self._grab_img(beam)
            logging.debug('Image for the new _mask grabbed')
        else:
            if image_for_mask is None:
                logging.warning("Image for masking is not available! Grabbing new image")
                self._grab_img(beam)
            else:
                self._set_img(image_for_mask)
                logging.debug('Image for the new _mask updated')

    def _set_img(self, img):
        self._image = np.array(img)

    def _grab_img(self, beam):
        beam.line_integration = self.mask_image_li
        img = beam.grab_frame()
        self._set_img(img)

    def plot_image_rectangles(self):
        # Create figure and axes
        fig, ax = plt.subplots(1)

        # Display the image
        ax.imshow(self._image)

        # Create a Rectangle patch for each rectangle and add it to the plot
        for rectangle in self._rectangles:
            y1, x1, y2, x2 = rectangle
            rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
        fig.tight_layout()
        return fig

    def plot_mask(self):
        # Create figure and axes
        fig, ax = plt.subplots(1)
        # Display the image
        ax.imshow(self._mask)
        fig.tight_layout()
        return fig

    def save_log_files(self, filename_prefix):
        # Mask image
        mask_filename = filename_prefix + '_mask.png'
        self.plot_mask().savefig(mask_filename)
        # Image with rectangles for criterion calculation
        mask_filename = filename_prefix + '_rectangles_mask.png'
        self.plot_image_rectangles().savefig(mask_filename)

    @property
    def image_pixel_size(self):
        pixel_size = self._image.metadata.binary_result.pixel_size.x
        return pixel_size

    @property
    def image_center(self):
        return self._image.data.shape[0] // 2, self._image.data.shape[1] // 2
