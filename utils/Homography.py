import numpy as np
import cv2
from matplotlib import pyplot as plt


class NotEnoughMatchesForHomography(Exception):
    pass


class HomographyNotValid(Exception):
    pass


def compute_homography(frame_left, frame_right, MIN_MATCH_COUNT=10, DEBUG=False):
    """
    compute the homography given a frame from the left and right camera
    See these: 
        https://docs.opencv.org/3.4/da/df5/tutorial_py_sift_intro.html
        https://docs.opencv.org/3.4/d1/de0/tutorial_py_feature_homography.html
    :param frame_left: 
    :param frame_right: 
    :return: H = 3x3 homography matrix
    """

    # Initiate SIFT detector
    sift = cv2.SIFT_create()

    # find the keypoints and descriptors with SIFT
    kp_left, des_left = sift.detectAndCompute(frame_left, None)
    kp_right, des_right = sift.detectAndCompute(frame_right, None)

    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des_left, des_right, k=2)

    # store all the best_matches matches as per Lowe's ratio test.
    best_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            best_matches.append(m)

    if len(best_matches) < MIN_MATCH_COUNT: raise NotEnoughMatchesForHomography(
        "Not enough matches are found - {}/{}".format(len(best_matches), MIN_MATCH_COUNT))

    dst_pts = np.float32([kp_left[m.queryIdx].pt for m in best_matches]).reshape(-1, 1, 2)
    src_pts = np.float32([kp_right[m.trainIdx].pt for m in best_matches]).reshape(-1, 1, 2)

    # compute the hom
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    # todo check if the homo is valid, otherwise raise error
    if DEBUG:
        matchesMask = mask.ravel().tolist()
        h, w, c = frame_left.shape
        pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, H)
        frame_right = cv2.polylines(frame_right, [np.int32(dst)], True, 255, 3, cv2.LINE_AA)

        draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                           singlePointColor=None,
                           matchesMask=matchesMask,  # draw only inliers
                           flags=2)
        img3 = cv2.drawMatches(frame_left, kp_left, frame_right, kp_right, best_matches, None, **draw_params)
        plt.imshow(img3, 'gray'), plt.show()

    return H
