import sys
import cv2
import numpy as np
import utils.Homography as Homography
import utils.Enlarger as Enlarger
import argparse
from subprocess import Popen, PIPE
from utils.syncstart import file_offset
import tempfile
from tqdm import tqdm
from utils.syncstart import UnableToProcessVideo
# todo preprocessing -> portare stesso frame rate ffmpeg -i 2_R.mp4 -filter:v fps=30 2_R_30.mp4
# todo errore se shape inpt è diverso
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

    if not int(fps_right) == int(fps_left):
        print("!ABORT!: fps are different for the cameras")
        sys.exit(-1)
        # todo handle the case

    has_to_compute_homography = True
    homography = np.zeros((3, 3))

    # Video creation
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    h, w = round(right_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)), round(right_camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("Shape of the final video is:", (w * 2, h))
    video_enlarged = cv2.VideoWriter("results/result.mp4", fourcc, fps_left, (w * 2, h))

    tot_frame_first_video = int(left_camera.get(cv2.CAP_PROP_FRAME_COUNT))
    tot_frame_second_video = int(right_camera.get(cv2.CAP_PROP_FRAME_COUNT))
    total_iteration = tot_frame_first_video if tot_frame_first_video < tot_frame_second_video else tot_frame_second_video
    progress_bar = tqdm(total=total_iteration)

    while left_camera.isOpened() or right_camera.isOpened():
        ret_left, frame_left = left_camera.read()
        ret_right, frame_right = right_camera.read()
        if not ret_right or not ret_left: break

        if grayscale:
            frame_left = cv2.cvtColor(cv2.cvtColor(frame_left, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
            frame_right = cv2.cvtColor(cv2.cvtColor(frame_right, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)

        # compute the homography once
        if has_to_compute_homography:
            tqdm.write("Computing homography for the first time ...")
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
            tqdm.write("computed!")

        # combined from the left and right frame
        img_enlarged = Enlarger.enlarge_fov(frame_left, frame_right, homography)
        # todo check that the shape is equal, otherwise it will fail
        video_enlarged.write(img_enlarged)  # write want h, w, c
        progress_bar.update(1)

    # Release the video capture object
    print("Releasing resources")
    left_camera.release()
    right_camera.release()
    video_enlarged.release()
    progress_bar.close()
    return


def sync_videos(args):
    syncstart_args = {'in1': args.right_video_path,
                      'in2': args.left_video_path,
                      'take': 20,
                      'show': False,
                      'normalize': False,
                      'denoise': False,
                      'lowpass': 0}

    try:
        file, offset = file_offset(syncstart_args)  # get offset
        print(f"Done! File {file} needs {offset} to get in sync")
    except UnableToProcessVideo as e:
        print(e)
        print("Set offset 0 for both the videos")
        file, offset = args.left_video_path, 0
    except Exception as e:
        print("Unable to process. Exit the program")
        sys.exit(-1)



    # which video I have to cut
    is_left = True
    video_to_cut = args.left_video_path

    video_with_offset = tempfile.NamedTemporaryFile(delete=False).name + ".mp4"  # create temp file for the video that will be cut

    if file == args.right_video_path:
        video_to_cut = args.right_video_path
        is_left = "right"

    process = Popen(['ffmpeg', '-i', video_to_cut, '-ss', str(offset), '-async', '1', video_with_offset], stdout=PIPE,
                    stderr=PIPE) # todo handle offset format, fail if in   seconds
    stdout, stderr = process.communicate() # todo handle error

    # return the video in the right order
    if is_left:
        return video_with_offset, args.right_video_path
    else: return args.left_video_path, video_with_offset,


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
    # todo add result video path
    args = parser.parse_args()

    # calculating offset between the video
    first_video, second_video = sync_videos(args)
    enlarge_videos_fov(first_video, second_video, args.grayscale)
