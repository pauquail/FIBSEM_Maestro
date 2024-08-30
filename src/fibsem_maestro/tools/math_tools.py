from scipy.ndimage.measurements import label
import numpy as np

def largest_rectangles_in_mask(mask):
    # Perform connected component analysis, the `structure` parameter defines
    # how pixels are connected
    structure = np.ones((3, 3), dtype=np.int)
    labeled_mask, num_features = label(mask, structure)

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


def crop_image(image, rectangle):
    y1, x1, y2, x2 = rectangle
    cropped_image = image[y1:y2, x1:x2]
    return cropped_image
