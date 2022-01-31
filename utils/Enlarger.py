import numpy as np
import cv2
import matplotlib.pyplot as plt 


def enlarge_fov(frame_left, frame_right, homography):
    h_left, w_left, c_left = frame_left.shape
    h_right, w_right, c_right = frame_right.shape
    image_enlarged = cv2.warpPerspective(frame_right, homography, ((frame_left.shape[1] + frame_right.shape[1]), frame_right.shape[0]))  # wraped image

    # append the left portion on it
    image_enlarged[0: h_right, 0: w_left] = frame_left
    return image_enlarged

