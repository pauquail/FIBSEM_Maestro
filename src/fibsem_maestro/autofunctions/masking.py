import importlib
import numpy as np
from matplotlib import pyplot as plt, patches
from scipy.ndimage.measurements import label
from scipy.ndimage import binary_fill_holes
from skimage.measure import regionprops
import logging
from patchify import patchify, unpatchify

from fibsem_maestro.tools.math_tools import crop_image

class Masking:
    def __init__(self, settings):
        # settings
        self.name = settings['mame']
        self.update_mask = settings['update_mask']
        self.mask_image_li = settings['mask_image_li']
        self.min_fraction = settings['min_fraction']
        self.model_path = settings['model_path']
        self.patch_size = settings['patch_size']
        self.threshold = settings['threshold']
        self.min_area = settings['min_area']
        self.fill_holes = settings['fill_holes']
        self.iterative_training = settings['iterative_training']
        # default values
        self._image = None
        self._rectangles = None
        self._mask = None
        # load model
        try:
            module = importlib.import_module(self.model_path)
            self.model = module.load_model()
        except Exception as e:
            logging.error(f'Error in loading model {self.model_path}. The masking is disabled! {e} ')
            self.use_mask = False

    def get_masked_images(self, line_number=None):
        self._mask = self._get_mask_array()

        if line_number is not None:
            mask_image = self._mask[line_number]
        else:
            mask_image = self._mask

        if np.sum(mask_image)/len(mask_image) < self.min_fraction:
            logging.warning('Focus criterion: Not enough masked pixels')
            return None
        else:
            self._rectangles = self._largest_rectangles_in_mask()
            images = []
            for r in self._rectangles:
                images.append(crop_image(self._image, r))
            return images

    def update_img(self, beam):
        if self.update_mask:
            beam.line_integration = self.mask_image_li
            img = beam.grab_frame()
            self.set_img(img)
            logging.debug('New mask grabbed')

    def set_img(self, img):
        self._image = np.array(img)

    def _get_mask_array(self):
        # shape to patches (with padding)
        pad_height = self.patch_size[0] - (self._image.shape[0] % self.patch_size[0]) \
            if (self._image.shape[0] % self.patch_size[0]) != 0 else 0
        pad_width =  self.patch_size[1] - (self._image.shape[1] % self.patch_size[1]) \
            if (self._image.shape[1] % self.patch_size[1]) != 0 else 0
        input_image = np.pad(self._image, ((0, pad_height), (0, pad_width)), mode='constant')
        original_padded_shape = input_image.shape
        input_image = patchify(input_image, self.patch_size, step=self.patch_size[0])
        original_patches_shape = input_image.shape
        input_image = input_image.reshape(-1, *input_image.shape[2:])[..., np.newaxis]  # merge first two axis and add depth
        segmented = self.model(input_image).numpy()
        # convert to binary
        segmented = segmented[..., 1]
        segmented[segmented > 0.5] = 1
        segmented[segmented <= 0.5] = 0

        if self.iterative_training:
            self.model.fit(input_image, segmented, {
                'epochs': 1,
                'batchSize': 16
            })

        # reshape back to image size
        segmented = segmented.reshape(original_patches_shape)
        segmented = unpatchify(segmented, original_padded_shape)
        segmented = segmented[0:self._image.shape[0], 0:self._image.shape[1]]
        if self.fill_holes:
            segmented = binary_fill_holes(segmented)
        segmented = segmented.astype(np.uint8)
        self._mask = segmented
        return segmented

    def plot(self):
        # Create figure and axes
        fig, ax = plt.subplots(1)

        # Display the image
        ax.imshow(self._image * 255)

        # Create a Rectangle patch for each rectangle and add it to the plot
        for rectangle in self._rectangles:
            y1, x1, y2, x2 = rectangle
            rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
        fig.tight_layout()
        return fig

    def _get_labeled_mask(self):
        # Perform connected component analysis, the `structure` parameter defines
        # how pixels are connected
        structure = np.ones((3, 3), dtype=np.int)
        labeled_mask, num_features = label(self._mask, structure)

        # filter small blobs
        if self.min_area is not None:
            # Calculate the area of each blob
            blob_areas = np.bincount(labeled_mask.ravel())
            # Create a mask for blobs that have area greater than the defined min_area
            mask = np.isin(labeled_mask, np.where(blob_areas > self.min_area)[0])
            # Apply the mask to the image,
            # This will set pixels in blobs with area <= min_area to 0
            filtered_image = self._mask * mask
            labeled_mask, num_features = label(filtered_image, structure)

        return labeled_mask, num_features

    def _largest_rectangles_in_mask(self):

        labeled_mask, num_features = self._get_labeled_mask()

        rectangles = []

        # Iterate over each found feature
        for feature in range(1, num_features + 1):

            # Create a binary mask for the current feature
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

    def _get_center(self):
        labeled_mask, num_features = self._get_labeled_mask()
        if num_features > 1:
            logging.warning(f"Too much features ({num_features}) found in mask. Drift correction skipped.")
            return None

        properties = regionprops(labeled_mask)

        return properties[0].centroid[1], properties[0].centroid[0]

    @property
    def image_pixel_size(self):
        pixel_size = self._image.metadata.binary_result.pixel_size.x
        return pixel_size

    @property
    def image_center(self):
        return self._image.data.shape[0] // 2, self._image.data.shape[1] // 2