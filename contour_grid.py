from PIL import ImageFilter, Image, ImageOps
from PIL.ImageOps import autocontrast
from numpy import array


def cleaned_contour(image, contrast_cutoff_percent=5, contrast_threshold=200):
    contour = image.filter(ImageFilter.CONTOUR)
    grey_image = contour.convert("L")
    grey_image = ImageOps.invert(grey_image)
    grey_image = autocontrast(grey_image, contrast_cutoff_percent)
    grey_contours = array(grey_image)
    low_indices = grey_contours < contrast_threshold
    grey_contours[low_indices] = 0

    # Remove edges
    grey_contours[:, 0] = 0
    grey_contours[:, grey_contours.shape[1] - 1] = 0
    grey_contours[0, :] = 0
    grey_contours[grey_contours.shape[0] - 1, :] = 0
    return grey_contours
