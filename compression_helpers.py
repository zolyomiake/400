from rle_coder import rle_encode
import logging
from image_tools import downscale_img, smear_outside_of_portrait_mask, smear_on_low_freq
from kmeans import kmeans_np, kmeans_explorer
import gzip
import pickle
from os import stat
from numpy import array, min, add, max, subtract
from rle_coder import rle_encode


class SizeConstrainedCompressor:
    TEMP_FILE_NAME = 'compressortemp'

    def __init__(self, min_short_dim, min_num_color, max_size=400, start_short_dim=100, start_num_color=6):
        self.min_short_dim = min_short_dim
        self.min_num_color = min_num_color
        self.max_size = max_size
        self.start_short_dim = start_short_dim
        self.start_num_color = start_num_color

    def compress(self, image):
        dim = self.start_short_dim
        k_centers = self.start_num_color

        size, data = SizeConstrainedCompressor.compress_step(image, 5, dim)
        if size < self.max_size:
            score = dim * k_centers

        return

    @staticmethod
    def compress_step(image, k_centers, short_dim, smear_low_freq=True, smear_portrait=True,
                      remove_linear_bump=True):
        im = downscale_img(image, short_dim)
        width, height = im.size
        pixel_values = list(im.getdata())

        if k_centers < 5:
            memberships, centers = kmeans_explorer(pixel_values, k_centers, width, 4000)
        else:
            memberships, centers = kmeans_np(pixel_values, k_centers, 5000)
        flat = memberships
        if smear_low_freq:
            flat = smear_on_low_freq(im, flat, median_size=3, contour_contrast_threshold=200, dilation=3)
        if smear_portrait:
            flat = smear_outside_of_portrait_mask(im, flat, median_size=7, circle_mask_fill=0.9)
        if remove_linear_bump:
            flat = remove_linear_bumps(flat)

        vertical_compression, flat_compressed = find_optimal_vertical_compression(flat, width, k_centers)

        flat_compressed = rle_encode(flat_compressed)
        with gzip.open(SizeConstrainedCompressor.TEMP_FILE_NAME, 'wb') as f:
            pickle.dump(flat_compressed, f, protocol=2)

        file_stat = stat(SizeConstrainedCompressor.TEMP_FILE_NAME)
        return file_stat.st_size, flat_compressed


def remove_linear_bumps(memberships, bump_length=1):
    for i in range(bump_length, len(memberships) - bump_length):
        if memberships[i - bump_length] == memberships[i + bump_length] and memberships[i] != memberships[
                    i - bump_length]:
            memberships[i] = memberships[i + bump_length]
    return memberships


def remove_linear_singles(memberships):
    for i in range(1, len(memberships) - 1):
        if memberships[i - 1] != memberships[i] and memberships[i] != memberships[i + 1]:
            memberships[i] = memberships[i - 1]
    return memberships


def find_optimal_vertical_compression(pixels, width, k_centers):
    flat_compressed = compress_neighbors_vertical(pixels, width, k_centers, 1)
    candidate_compression = rle_encode(flat_compressed)
    candidate_vertical = 1
    for i in range(2, 5):
        compression = rle_encode(compress_neighbors_vertical(pixels, width, k_centers, i))
        if len(compression) < len(candidate_compression):
            candidate_compression = compression
            candidate_vertical = i

    logging.info("Vertical compression %d has been selected", candidate_vertical)
    return candidate_vertical, compress_neighbors_vertical(pixels, width, k_centers, candidate_vertical)


def compress_neighbors_vertical(items, width, k_centers, compression_height=2):
    if pow(k_centers, compression_height) >= 225:
        # logging.warning("Cannot compress values with %d centers and height %d", k_centers, compression_height)
        return items
    height = int(len(items) / width)
    compressed = []
    for y in range(0, height, compression_height):
        for x in range(0, width):
            val = 0
            for h in range(0, compression_height):
                offset = (y + h) * width + x
                if offset < len(items):
                    val += items[offset] * pow(k_centers, h)
            compressed.append(val)

    return compressed


def decompress_neighbors_vertical(items, width, height, k_centers, compression_height):
    decompressed = []
    tuple_list = []
    expansion_count = 0
    for c in items:
        decomp_tmp = []
        comp_val = c
        for h in range(compression_height - 1, -1, -1):
            divisor = pow(k_centers, h)
            decomp_val = comp_val // divisor
            comp_val -= decomp_val * divisor
            decomp_tmp.append(decomp_val)
        decomp_tmp.reverse()
        tuple_list.append(tuple(decomp_tmp))

        if len(tuple_list) == width:
            expansion_count += 1
            for t in range(0, compression_height):
                if len(decompressed) < width * height:
                    row_items = [x[t] for x in tuple_list]
                    decompressed.extend(row_items)
            tuple_list.clear()

    return decompressed


def compress_line_by_line(items, width):
    height = int(len(items) / width)
    prev_line = None

    maxval = max(array(items))
    magic1 = maxval+1

    errors = dict()
    line_diffed = []
    for i in range(0, height):
        line = items[i*width:(i+1)*width]
        if prev_line is None:
            line_diffed.extend(line)
        else:
            nomatches = get_diff_locations_and_values(prev_line, line)

            diffline = subtract(array(prev_line), array(line))

            line_diffed.extend(diffline.tolist())
            # if len(nomatches) < 2:
            #     # logging.info("Replacing %d items", len(nomatches))
            #     line_diffed.append(magic1)
            #     # for nomatch in nomatches:
            #     #     line_diffed.append(nomatch[1])
            #     #     line_diffed.append(nomatch[0])
            # else:
            #     line_diffed.extend(line)

            if len(nomatches) not in errors.keys():
                errors[len(nomatches)] = 1
            else:
                errors[len(nomatches)] += 1

        prev_line = line

    line_diffed = add(array(line_diffed), -1*min(array(line_diffed)))

    return line_diffed


def add_replacements_to_line(replacements, magic, line):
    line.append(magic)
    for replacement in replacements:
        for key in replacement.keys():
            line.append(key)
            for loc in replacement[key]:
                line.append(loc)


def get_diff_locations_and_values(line1, line2):
    if len(line1) != len(line2):
        logging.error("Line lengths do not match")
        return
    nomatches = []
    for j in range(0, len(line1)):
        if line1[j] != line2[j]:
            nomatches.append((j, line2[j]))

    return nomatches
