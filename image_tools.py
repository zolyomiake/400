from numpy import zeros, ogrid, full, array, invert
from PIL import Image, ImageFilter
from scipy.misc import imresize
from contour_grid import cleaned_contour
from scipy.ndimage.morphology import grey_dilation
import glob
from kmeans import kmeans_np
from os.path import join

def circle_mask(radius):
    y, x = ogrid[-radius: radius + 1, -radius: radius + 1]
    mask = x ** 2 + y ** 2 <= radius ** 2
    return mask


def portrait_mask(width_orig, height_orig, fill_factor=1):
    width = int(width_orig * fill_factor)
    height = int(height_orig * fill_factor)
    radius = max(width, height)
    cm = circle_mask(radius)
    greyData = zeros(cm.shape, dtype='uint8')
    greyData[cm] = 255
    resized = imresize(greyData, (width, height))
    resized_bool = resized > 0

    if fill_factor < 1:
        img_toreturn = full((width_orig, height_orig), False, dtype=bool)
        offset_x = int((width_orig - width) / 2)
        offset_y = int((height_orig - height) / 2)
        img_toreturn[offset_x:offset_x+width, offset_y:offset_y+height ] = resized_bool
        return img_toreturn
    else:
        return resized_bool


def write_list_to_image_file(list_items, width, height, centers, filename):
    pixels = list()
    for member in list_items:
        pixels.append(centers[member])
    output_image = Image.new("RGB", (width, height))
    output_image.putdata(pixels)
    output_image.save(filename, quality=20)


def display_ndarray_as_grey_image(data):
    img = Image.fromarray(data, 'L')
    img.show()


def display_binary_ndarray_as_grey_image(data):
    greyData = zeros(data.shape, dtype='uint8')
    greyData[data] = 255
    img = Image.fromarray(greyData, 'L')
    # img[img > 0] = 255
    img.show()


def smear_on_low_freq(image, mapped_image_values, median_size=5, contour_contrast_threshold=200, dilation=3):
    contour_array = cleaned_contour(image, contrast_threshold=contour_contrast_threshold)
    contour_array = grey_dilation(contour_array, size=(dilation, dilation))

    value_array = array(mapped_image_values).reshape((image.height, image.width)).astype('uint8')
    img = Image.fromarray(value_array, 'L')

    median_image = img.filter(ImageFilter.MedianFilter(median_size))

    median_data = array(median_image.getdata()).reshape((image.height, image.width)).astype('uint8')
    high_freq_mask = [contour_array > 100]
    median_data[high_freq_mask] = value_array[high_freq_mask]

    return median_data.flatten().tolist()


def smear_outside_of_portrait_mask(image, mapped_image_values, median_size=7, circle_mask_fill=1):
    circlemask = portrait_mask(image.height, image.width, circle_mask_fill)

    value_array = array(mapped_image_values).reshape((image.height, image.width)).astype('uint8')
    img = Image.fromarray(value_array, 'L')

    median_image = img.filter(ImageFilter.MedianFilter(median_size))

    median_data = array(median_image.getdata()).reshape((image.height, image.width)).astype('uint8')
    median_data[circlemask] = value_array[circlemask]

    return median_data.flatten().tolist()


def downscale_img(image, target_short_dim=50):
    short_dim = min(image.width, image.height)
    scaling = target_short_dim / short_dim
    im = image.resize((int(image.width * scaling), int(image.height * scaling)), Image.ANTIALIAS)
    return im


def create_center_list(folder_name, num_of_centers = 100):
    values = list()
    for file_name in glob.glob(join(folder_name, "*.jpg")):
        im = Image.open(file_name, 'r')
        values.extend(im.getdata())

    centers = kmeans_np(values, num_of_centers, num_of_samples=10000, centers_only=True)

    return centers

