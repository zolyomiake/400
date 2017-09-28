
from random import randint, seed
from math import sqrt
from numpy import reshape, array, subtract, repeat, power, sum as np_sum, argmin, append
from scipy.cluster.vq import kmeans as kmeans_sp


def kmeans_explorer(pixels, k_centers, width, num_of_samples=1000):
    explore_centers = 40
    mb, centers_explore = kmeans_np(pixels, explore_centers, num_of_samples)
    memberships, centers_tmp = kmeans_np(pixels, k_centers, num_of_samples)

    height = len(pixels) / width

    labels = sorted(set(memberships))
    mapped_centers = []
    for label in labels:
        candidate_error = -1
        candidate_explore_center = None
        for center in centers_explore:
            error = 0
            for index, p in enumerate(pixels):
                if memberships[index] == label:
                    error += get_point_distance(p, center) * error_multiplier(index, width, height)
            if candidate_error < 0 or candidate_error > error:
                candidate_error = error
                candidate_explore_center = center
        mapped_centers.append(candidate_explore_center)

    return memberships, mapped_centers


def error_multiplier(index, width, height):
    x = index % width
    y = index // width

    dist_h = abs(width / 2 - x)
    if dist_h < width / 6:
        h = 3
    elif dist_h < width / 6 * 2:
        h = 2
    elif dist_h < width / 6 * 4:
        h = 1
    else:
        h = 0.5

    dist_v = abs(height / 2 - y)
    if dist_v < height / 6:
        v = 3
    elif dist_v < height / 6 * 2:
        v = 2
    elif dist_v < height / 6 * 4:
        v = 1
    else:
        v = 0.5

    return min(h, v)


def labels_to_values(centers, labels):
    pixels = list()
    for member in labels:
        pixels.append(centers[member])
    return pixels


def kmeans_np(pixels, k_centers, num_of_samples=1000, centers_only=False):

    pixels_np = array(pixels)
    # Limit size of pixel values
    subsampling_ratio = max(1, len(pixels) // num_of_samples)
    subsampled_pixels = pixels[0::subsampling_ratio]
    subs_np = array(subsampled_pixels)
    codebook, distortion = kmeans_sp(subs_np.astype(float), k_or_guess=k_centers, iter=100)
    centers = codebook.astype(int).tolist()
    if centers_only:
        return centers

    distances_to_centers = dict()
    one_channel_distances = list()
    for index, c in enumerate(centers):
        tmp = pixels_np - c
        if type(pixels[0]) is not int:
            squared = pow(tmp, 2)
            summed = np_sum(squared, axis=1).tolist()
            distances_to_centers[index] = summed
        else:
            dist = abs(tmp)
            one_channel_distances.append(dist)
            pass

    one_channel_distances = array(one_channel_distances).transpose()

    if type(pixels[0]) is not int:
        dist2 = None
        for key in distances_to_centers.keys():
            if dist2 is None:
                dist2 = distances_to_centers[key]
            else:
                dist2 = append(dist2, distances_to_centers[key])
        dist3 = dist2.reshape((len(centers), len(pixels)))
        membership = argmin(dist3, axis=0).flatten().tolist()
        centers_simple = list()
        for c in centers:
            centers_simple.append((c[0], c[1], c[2]))
    else:
        membership = argmin(one_channel_distances, axis=1).flatten().tolist()
        centers_simple = centers

    return membership, centers_simple


def get_point_distance(point1, point2):
    a2 = pow(point1[0] - point2[0], 2)
    b2 = pow(point1[1] - point2[1], 2)
    c2 = pow(point1[2] - point2[2], 2)
    return sqrt(a2 + b2 + c2)
