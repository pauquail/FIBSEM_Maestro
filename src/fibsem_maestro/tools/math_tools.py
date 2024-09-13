import numpy as np


def crop_image(image, rectangle):
    y1, x1, y2, x2 = rectangle
    cropped_image = image[y1:y2, x1:x2]
    return cropped_image
