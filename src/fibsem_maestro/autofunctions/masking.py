from matplotlib import pyplot as plt, patches


class Masking:
    def __init__(self):
        self._image = None
        self._rectangles = None

    def update_img(self, img):
        pass

    def get_mask_array(self):
        pass

    def plot(self):
        # Create figure and axes
        fig, ax = plt.subplots(1)

        # Display the image
        ax.imshow(self._image)

        # Create a Rectangle patch for each rectangle and add it to the plot
        for rectangle in self._rectangles:
            y1, x1, y2, x2 = rectangle
            rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)
        plt.tight_layout()

