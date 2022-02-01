import cv2
import numpy as np
import utils.Homography
import utils.Homography as Homography
import utils.Enlarger  as Enlarger
import argparse
from tqdm import tqdm


def enlarge_videos_fov(left_path, right_path):
    left_camera = cv2.VideoCapture(left_path)
    right_camera = cv2.VideoCapture(right_path)
    if not left_camera.isOpened() or not right_camera.isOpened():
        print("Error opening the video file")
        return

    # Get frame rate information
    fps_left = left_camera.get(cv2.CAP_PROP_FPS)
    fps_right = right_camera.get(cv2.CAP_PROP_FPS)
    print(f"Frames per second (left camera) :", left_camera.get(cv2.CAP_PROP_FPS))
    print(f"Frames per second (right camera) :", right_camera.get(cv2.CAP_PROP_FPS))
    if not fps_right == fps_left:
        print("! NOTE !: fps are different for the cameras")
        # todo handle the case

    has_to_compute_homography = True
    homography = np.zeros((3, 3))

    # Video creation
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    h, w = round(right_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)), round(right_camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("Shape of the final video is:", (w * 2, h))
    video_enlarged = cv2.VideoWriter("results/result.mp4", fourcc, fps_left, (w * 2, h))

    while left_camera.isOpened() or right_camera.isOpened():
        ret_left, frame_left = left_camera.read()
        ret_right, frame_right = right_camera.read()
        if not ret_right or not ret_left: break

        # compute the homography once
        if has_to_compute_homography:
            print("Computing homography for the first time ...")
            try:
                homography = Homography.compute_homography(frame_left, frame_right)
            except Homography.NotEnoughMatchesForHomography as e:
                print("NotEnoughMatchesForHomography, needs to be computed in other ways", e)
                return
            except Homography.HomographyNotValid:
                print("HomographyNotValid")
                return
            finally:
                # todo improve code
                pass
            has_to_compute_homography = False
            print("computed!")

        # combined from the left and right frame
        img_enlarged = Enlarger.enlarge_fov(frame_left, frame_right, homography)
        # todo check thath the shape is equal, otherwise it will fail
        video_enlarged.write(img_enlarged)  # write want h, w, c

    # Release the video capture object
    print("Releasing resources")
    left_camera.release()
    right_camera.release()
    video_enlarged.release()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Video enlarger')
    parser.add_argument('--left-video-path', type=str,
                        help='path to the left video')
    parser.add_argument('--right-video-path', type=str,
                        help='path to the right video')
    args = parser.parse_args()

    enlarge_videos_fov(args.left_video_path, args.right_video_path)
