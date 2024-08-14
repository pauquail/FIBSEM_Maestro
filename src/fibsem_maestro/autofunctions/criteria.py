import numpy as np
from scipy.ndimage import gaussian_filter


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


def bandpass_criterion(img, px_size, lowest_detail, highest_detail) -> float:
    """
    Mean value of band-passed image. 

    :param img: The input image.
    :param px_size: The pixel size of the image (m).
    :param lowest_detail: The level of minimal detail in the image (m).
    :param highest_detail: The level of maximal detail in the image (m).
    :return: Criterion.
    """
    img_low = gauss_filter(img, px_size, lowest_detail)
    img_high = gauss_filter(img, px_size, highest_detail)

    result = np.mean(abs(img_high - img_low))  # mean of absolute images
    return result


def bandpass_var_criterion(img, px_size, lowest_detail, highest_detail) -> float:
    """
    Variance of band-passed image. 

    :param img: The input image.
    :param px_size: The pixel size of the image (m).
    :param lowest_detail: The level of minimal detail in the image (m).
    :param highest_detail: The level of maximal detail in the image (m).
    :return: Criterion.
    """
    img_low = gauss_filter(img, px_size, lowest_detail)
    img_high = gauss_filter(img, px_size, highest_detail)
    
    result = np.var(img_high - img_low)
    return result


def fft_criterion(img, px_size, lowest_detail, highest_detail):
    """
    :param img: The image data. It can be either a 1-dimensional array representing an image line or a 2-dimensional array representing the entire image.
    :param px_size: The size of each pixel in the image.
    :param lowest_detail: The lowest detail (lowest frequency) to consider in the FFT.
    :param highest_detail: The highest detail (highest frequency) to consider in the FFT.
    :return: The sum of the amplitudes of the filtered frequencies.

    This method calculates the FFT (Fast Fourier Transform) of the given image data. It removes frequencies within the specified range and returns the sum of the amplitudes of the remaining frequencies.
    """
    def fft_criterion1d():
        img0 = img - np.mean(img)  # remove 0 frequency
        fft_line = np.fft.fft(img0)  # fft

        freq = np.fft.fftfreq(len(img), px_size)  # get freq axis
        fft_line = fft_line[freq > 0]  # remove negative frequencies
        freq = freq[freq > 0]  # remove negative frequencies from freq axis
    
        # filter frequencies
        band_i = np.where((freq < 1 / highest_detail) & (freq > 1 / lowest_detail))[0]
        # sum of amplitudes of all filtered frequencies
        result = np.sum(abs(fft_line[band_i]))
        return result

    def fft_criterion_2d():
        img0 = img - np.mean(img)  # remove 0 frequency
        fft_img = np.fft.fft2(img0)  # fft

        freq1 = np.fft.fftfreq(fft_img.shape[0], px_size) # get x freq axis
        freq2 = np.fft.fftfreq(fft_img.shape[1], px_size) # get y freq axis

        freq1 = np.repeat(freq1[:, np.newaxis], freq2.shape[0], axis=1)
        freq2 = np.repeat(freq2[:, np.newaxis], freq1.shape[0], axis=1).T
        freq = np.sqrt(freq1 ** 2 + freq2 ** 2)  # make freq matrix

        highf = 1 / highest_detail  # highest detail frequency
        lowf = 1 / lowest_detail  # lowest detail frequency

        # make freq filter
        freq[freq > highf] = 0 
        freq[freq < lowf] = 0
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