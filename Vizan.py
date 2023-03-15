import cv2

import time
import ctypes
from argparse import ArgumentParser
import msvcrt

# parse arguments from command line including delay
parser = ArgumentParser()
parser.add_argument("-d", "--delay", dest="delay", default=10,
                    help="Sets the video output to be delayed by the argument value (in seconds)", metavar="DELAY")
parser.add_argument("-s", "--source", dest="source", default=0,
                    help="Set the video stream source (0-x)", metavar="SOURCE")
parser.add_argument("-f", "--flip",
                    action="store_false", dest="flip", default=False,
                    help="Flips the output horizontally")

args = parser.parse_args()
DELAY_SECONDS = float(args.delay)
SOURCE = int(args.source)
SHOULD_FLIP = bool(args.flip)

WINDOW_NAME = 'Video Analysis'
aborted = False


# initialize video capture object to read video from external webcam
video_capture = cv2.VideoCapture(SOURCE)
# if there is no external camera then take the built-in camera
if not video_capture.read()[0]:
    video_capture = cv2.VideoCapture(0)

# Full screen mode
cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# set up video delay
start_time = time.time()
frames = []


while (video_capture.isOpened() and not aborted):
 # get Screen Size
    user32 = ctypes.windll.user32
    screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
 
 # read video frame by frame
    ret, frame = video_capture.read()
    frames.append(frame)

    if time.time() - start_time > DELAY_SECONDS:
        display_frame = frames.pop(0)

        display_frame = cv2.flip(display_frame, 1)

        frame_height, frame_width, _ = display_frame.shape

        scaleWidth = float(screen_width)/float(frame_width)
        scaleHeight = float(screen_height)/float(frame_height)

        if scaleHeight>scaleWidth:
            imgScale = scaleWidth
        else:
            imgScale = scaleHeight

        newX,newY = display_frame.shape[1]*imgScale, display_frame.shape[0]*imgScale
        display_frame = cv2.resize(display_frame,(int(newX),int(newY)))
        cv2.imshow(WINDOW_NAME, display_frame)

    # quit if q is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        aborted = True
        break
    # quit if escape key is pressed
    if msvcrt.kbhit() and msvcrt.getch()[0] == 27:
        aborted = True
        break



# release video capture object
video_capture.release()
cv2.destroyAllWindows()


# Vizan Icon Source Acknowledgement: https://www.flaticon.com/free-icon/video-camera_4021977
# GoPro Icon Source Acknowledgement: https://www.flaticon.com/free-icon/gopro_2489971