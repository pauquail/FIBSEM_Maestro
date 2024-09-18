import math
from scipy.ndimage.measurements import label
import numpy as np
from skimage.measure import regionprops


def center_padding(image, goal_size):
    """ Add padding to goal_size. The image will be in the center of final image"""
    d_height = image.shape[0] - goal_size[0]
    d_width = image.shape[1] - goal_size[1]

    # do not pad if image is bigger than goal_size
    if d_height < 0:
        d_height = 0
    if d_width < 0:
        d_width = 0

    pad_height = math.ceil(d_height / 2)
    pad_width = math.ceil(d_width / 2)
    output_image = np.pad(image, ((pad_height, pad_height), (pad_width, pad_width)), mode='constant')
    # crop if needed
    if output_image[0] != goal_size[0] or output_image[1] != goal_size[1]:
        output_image = output_image[:goal_size[0],:goal_size[1]]
    return output_image


def center_cropping(image, goal_size):
    """ The image will be cropped in the center to the size of final image"""
    d_height = goal_size[0] - image.shape[0]
    d_width = goal_size[1] - image.shape[1]

    # do not crop if image is smaller than goal_size
    if d_height < 0:
        d_height = 0
    if d_width < 0:
        d_width = 0

    pad_height = math.floor(d_height / 2)
    pad_width = math.floor(d_width / 2)
    output_image = np.copy(image)
    output_image = output_image[pad_height:pad_height+goal_size[0],pad_width:pad_width+goal_size[1]]
    return output_image


blobs_structure = np.ones((3, 3), dtype=np.int8)


def find_blobs(image):
    labeled_image, _ = label(image, blobs_structure)
    return labeled_image


def filter_blobs_min_area(labeled_image, min_area):
    # filter small blobs
    assert min_area is not None

    # Calculate the area of each blob
    blob_areas = np.bincount(labeled_image.ravel())
    # Create a mask for blobs that have area greater than the defined min_area
    mask = np.isin(labeled_image, np.where(blob_areas > min_area)[0])
    # Apply the mask to the image,
    # This will set pixels in blobs with area <= min_area to 0
    filtered_image = labeled_image * mask
    labeled_mask, _ = label(filtered_image, blobs_structure)
    return labeled_mask

def find_central_blob_label(labeled_image):
    """ Find the label closest to the image center"""
    # Get number of labels
    num_labels = labeled_image.max()

    # Define image center
    center = np.array(labeled_image.shape) / 2

    min_dist = np.inf
    central_label = None

    # Iterate over each label
    for label in range(1, num_labels + 1):
        # Find pixels with current label
        pixels = np.transpose(np.where(labeled_image == label))

        # Compute centroid of current labeled region
        centroid = pixels.mean(axis=0)

        # Compute distance from centroid to center
        dist = np.linalg.norm(center - centroid)

        # If it's closer to the center than what we've found so far
        if dist < min_dist:
            min_dist = dist
            central_label = label

    return central_label

def blob_center(labeled_image):
    """ Return center of labeled image (closest to center of FoV)"""
    central_blob = find_central_blob_label(labeled_image)
    properties = regionprops(labeled_image)
    return properties[labeled_image].centroid[1], properties[labeled_image].centroid[0]


def largest_rectangles_in_blobs(self, labeled_image):
    """ Get the largest possible rectangle that fits to blobs"""
    num_features = np.max(labeled_image.ravel())
    rectangles = []

    # Iterate over each found feature
    for feature in range(1, num_features + 1):

        # Create a binary mask for the current feature
        feature_mask = np.array(labeled_image == feature).astype(int)

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


def crop_image(image, rectangle):
    y1, x1, y2, x2 = rectangle
    cropped_image = image[y1:y2, x1:x2]
    return cropped_image


def get_stripes(img, separate_value=10, minimal_stripe_height=5):
    """ Get stripes of image separated by black lines (<separate_value)"""
    # identify the blank spaces
    x_proj = np.sum(img, axis=1)  # identify blank line by min function
    zero_pos = np.where(x_proj < separate_value)[0]  # position of all blank lines
    # go through the sections
    image_section_index = 0  # actual image section
    for i in range(len(zero_pos) - 1):  # iterate all blank lines - find the image section
        x0 = zero_pos[i]
        x1 = zero_pos[i + 1]  # 2 blank lines
        # if these 2 blank lines are far from each other (it makes the image section)
        if x1 - x0 >= minimal_stripe_height:
            bin = np.arange(x0 + 1, x1)  # list of stripe indices
            yield image_section_index, bin
            image_section_index += 1
