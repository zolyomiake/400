from PIL import Image
import gzip
import pickle
from rle_coder import rle_encode, rle_decode, code_matches
from kmeans import kmeans_explorer, kmeans_np
from image_tools import write_list_to_image_file, smear_on_low_freq, downscale_img, smear_outside_of_portrait_mask,\
    create_center_list
from compression_helpers import remove_linear_bumps, find_optimal_vertical_compression, SizeConstrainedCompressor,\
    compress_line_by_line, decompress_neighbors_vertical, remove_linear_singles
from numpy import array, reshape
import logging
from os import stat, path
import glob

logging.getLogger().setLevel(logging.INFO)


def compress_image(filename, small_dimesion=50, k_centers=5):
    im = Image.open(filename, 'r')
    im = downscale_img(im, small_dimesion)

    width, height = im.size
    pixel_values = list(im.getdata())

    if k_centers < 5:
        memberships, centers = kmeans_explorer(pixel_values, k_centers, width, 4000)
    else:
        memberships, centers = kmeans_np(pixel_values, k_centers, 5000)
    flat = memberships
    # flat = smear_on_low_freq(im, flat, median_size=3, contour_contrast_threshold=200, dilation=3)
    # flat = smear_outside_of_portrait_mask(im, flat, median_size=7, circle_mask_fill=0.9)
    flat = remove_linear_bumps(flat)
    # flat = remove_linear_singles(flat)

    vertical_compression, flat_compressed = find_optimal_vertical_compression(flat, width, k_centers)
    # metadata = [width, height, k_centers, vertical_compression])
    flat_rle = rle_encode(flat_compressed)
    return flat_rle, flat, width, height, centers


def benchmark_on_folder(source_folder, target_folder):
    sizes = list()
    for file_name in glob.glob(path.join(source_folder, "*.jpg")):  # ['images/portrait5.jpg']
        logging.info('\n**** %s ****', file_name)
        rle2, flat, width, height, centers = compress_image(file_name, k_centers=5, small_dimesion=50)

        logging.info("Flatcomp len: %d", len(rle2))
        binary_name = path.join('results', file_name[7:-4] + '.binary')
        with gzip.open(binary_name, 'wb') as f:
            pickle.dump(rle2, f, protocol=2)

        file_stat = stat(binary_name)
        logging.info("File size: %d", file_stat.st_size)
        sizes.append(file_stat.st_size)

        # Write the transformed image as a bmp so it van be displayed
        write_list_to_image_file(flat, width, height, centers, path.join(target_folder, file_name[7:-4] + '.bmp'))
        # Write the same image as JPG for comparison
        write_list_to_image_file(flat, width, height, centers, path.join(target_folder, file_name[7:-4] + '_c.jpg'))

        # Write the downscaled image, original colors, as JPG for comparison
        im = Image.open(file_name, 'r')
        im = im.resize((width, height), Image.ANTIALIAS)
        im.save(path.join('results', file_name[7:-4] + '.jpg'), quality=10)

    logging.info("Average file size: %f", sum(sizes) / len(sizes))


def main():
    benchmark_on_folder('images', 'results')


if __name__ == "__main__":
    main()
