import cv2

def main():
    left_camera = cv2.VideoCapture('input_videos/test.mp4')
    right_camera = cv2.VideoCapture('input_videos/test_2.mp4')
    if not left_camera.isOpened() or not right_camera.isOpened():
        print("Error opening the video file")
        return


    # Get frame rate information
    print(f"Frames per second (left camera) :", left_camera.get(cv2.CAP_PROP_FPS))
    print(f"Frames per second (right camera) :", right_camera.get(cv2.CAP_PROP_FPS))

    while left_camera.isOpened() or right_camera.isOpened():
        ret_left, frame_left = left_camera.read()
        ret_right, frame_right = right_camera.read()

        if not ret_right or not ret_left: break

    # Release the video capture object
    left_camera.release()
    right_camera.release()
    return

if __name__ == '__main__':
    main()