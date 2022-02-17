import cv2
import numpy as np
import utils.Homography as Homography
import utils.Enlarger as Enlarger
import argparse
from os.path import join as osp
import platform
import datetime
from tqdm import tqdm
from subprocess import Popen, PIPE
from utils.syncstart import file_offset

def enlarge_videos_fov(left_path, right_path, grayscale):
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
    if not fps_right == fps_left :
        print("! NOTE !: fps are different for the cameras")

    has_to_compute_homography = True
    homography = np.zeros((3, 3))

    # Video creation
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    h, w = round(right_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)), round(right_camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("Shape of the final video is:", (w*2, h))
    video_enlarged = cv2.VideoWriter("results/result.mp4", fourcc, fps_left, (w*2, h))

    # for image in tqdm(images):
    #     video.write(cv2.imread(os.path.join(image_folder, image)))

    while left_camera.isOpened() or right_camera.isOpened():
        ret_left, frame_left = left_camera.read()
        ret_right, frame_right = right_camera.read()
        if not ret_right or not ret_left: break

        if grayscale:
            frame_left = cv2.cvtColor(cv2.cvtColor(frame_left, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
            frame_right = cv2.cvtColor(cv2.cvtColor(frame_right, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)

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
                #todo improve code
                pass
            has_to_compute_homography = False
            print("computed!")

        # combined from the left and right frame
        img_enlarged = Enlarger.enlarge_fov(frame_left, frame_right, homography)
        # swap the width with the height, final shape is : w,h,c
        #img_enlarged_for_video = np.rollaxis(img_enlarged, 1, 0)
        #img_enlarged_for_video = cv2.flip(img_enlarged, 0)
        img_enlarged_for_video = img_enlarged
        #print(img_enlarged_for_video.shape)
        video_enlarged.write(img_enlarged_for_video)


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
    parser.add_argument('--grayscale', type=int,
                        help='generate grayscale output,'
                             ' useful when combining videos obtained with different cameras',
                        default=0)
    args = parser.parse_args()

    # implementare sync video

    syncargs = {'in1': args.right_video_path,
                'in2': args.left_video_path,
                'take': 20,
                'show': False,
                'normalize': False,
                'denoise': False,
                'lowpass': 0}

    file, offset = file_offset(syncargs)
    cutvideo = ""
    newname = "input_videos/cutvid.mp4"
    # taglio video
    # ffmpeg -i 5_L.mp4  -ss 00:00:00.75 -async 1 5_L_prod.mp4
    if file == args.right_video_path:
        video_to_cut = args.right_video_path
        cutvideo = "right"
    else:
        video_to_cut = args.left_video_path
        cutvideo = "left"

    process = Popen(['ffmpeg', '-i', video_to_cut, '-ss', str(offset), '-async', '1', newname], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    if cutvideo == "right":
        enlarge_videos_fov(args.left_video_path, newname, args.grayscale)
    elif cutvideo == "left":
        enlarge_videos_fov(newname, args.right_video_path, args.grayscale)
    else:
        enlarge_videos_fov(args.left_video_path, args.right_video_path, args.grayscale)