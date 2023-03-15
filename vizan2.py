#!/usr/bin/env python

from PySide6.QtCore import QTimer,  QSize, Qt, QPoint
from PySide6.QtGui import QImage, QPixmap, QScreen
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QSpinBox, QComboBox

import cv2
import sys

import time
import ctypes
from argparse import ArgumentParser
from pygrabber.dshow_graph import FilterGraph
import msvcrt

VIDEO_SCALE = 0.65

# parse arguments from command line including delay
parser = ArgumentParser()
parser.add_argument("-d", "--delay", dest="delay", default=10,
                    help="Sets the video output to be delayed by the argument value (in seconds)", metavar="DELAY")
parser.add_argument("-s", "--source", dest="source", default=3,
                    help="Set the video stream source (0-x)", metavar="SOURCE")
parser.add_argument("-f", "--flip",
                    action="store_false", dest="flip", default=False,
                    help="Flips the output horizontally")
parser.add_argument("-p", "--fps", dest="fps", default=30,
                    help="Set the video stream frames per second", metavar="FPS")

args = parser.parse_args()
DELAY_SECONDS = 8#float(args.delay)
SOURCE = int(args.source)
SHOULD_FLIP = bool(args.flip)
VIDEO_FPS = float(args.fps)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        print("Starting Initialisation...")

        self.delay = DELAY_SECONDS
        self.selected_camera_index = SOURCE

        self.setup_window()
        self.setup_ui()
        self.setup_camera()

        print("Initialised!")

    def setup_window(self):
        self.setWindowTitle("Vizan")
        app = QApplication.instance() # Get a reference to the current application
        self.screens = app.screens()
        self.primaryScreen = app.primaryScreen()

        # Set the size of the window to 3/4 of the screen size
        targetWindowSize = self.primaryScreen.size()*0.75
        self.resize(targetWindowSize)
        # Set the video scale
        testSize = QSize(1920,1080)
        targetVideoSize = testSize*VIDEO_SCALE
        self.video_size = targetVideoSize
        # Get Window initial position (Center)
        self.initWinXoff = (self.primaryScreen.size().width()-targetWindowSize.width())/2
        self.initWinYoff = (self.primaryScreen.size().height()-targetWindowSize.height())/2
        #Set window to its initial position
        self.move(QPoint(self.primaryScreen.availableGeometry().left()+self.initWinXoff, self.primaryScreen.availableGeometry().top()+self.initWinYoff))
        print("Window Initiliased")
        

    def setup_ui(self):
        """Initialize widgets.
        """
        self.isFullScreened = False

        # Set up top level layout
        self.vLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.bottomLayout = QHBoxLayout()

        self.vLayout.addLayout(self.topLayout)
        self.vLayout.addLayout(self.bottomLayout)

        # Set up video (top layout)
        # Set up image label to contain the standard video output
        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.topLayout.addWidget(self.imageLabel)

        # Set up the image label to contain the fullscreen image
        self.fullscreen_image = QLabel()
        self.move(QPoint(0,0))
        self.resize(QSize(1920,1080))
        self.fullscreen_image.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.fullscreen_image.keyPressEvent = self.keyPressEvent
        self.fullscreen_image.showFullScreen()
        self.fullscreen_image.hide()

        # Set up the bottom layout
        # Set up the streaming box
        self.streamingBox = QVBoxLayout()
        self.bottomLayout.addLayout(self.streamingBox)

        self.streamingLabel = QLabel("Streaming")
        self.streamingLabel.setMargin(10)
        title_font = self.streamingLabel.font()
        title_font.setPointSize(20)
        self.streamingLabel.setFont(title_font)
        self.streamingLabel.setAlignment(Qt.AlignHCenter)
        self.streamingBox.addWidget(self.streamingLabel)

        # Camera Selection
        self.cameraDropDown = QComboBox()
        self.cameras = self.get_available_cameras()
        self.cameraDropDown.addItems(tuple(self.cameras[1]))
        self.cameraDropDown.setCurrentIndex(self.selected_camera_index)
        self.cameraDropDown.currentIndexChanged.connect(self.camera_index_changed)
        self.streamingBox.addWidget(self.cameraDropDown)

        # Delay time selection
        self.delayLayout = QHBoxLayout()
        self.streamingBox.addLayout(self.delayLayout)
        self.delayLayout.setAlignment(Qt.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.delayLabel = QLabel("Delay")
        self.delayLabel.setMargin(10)
        self.delayLayout.addWidget(self.delayLabel)

        self.delayBox = QSpinBox()
        self.delayBox.setRange(0,60)
        self.delayBox.setSuffix("s")
        self.delayBox.setValue(self.delay)
        self.delayBox.valueChanged.connect(self.delay_value_changed)
        self.delayLayout.addWidget(self.delayBox)
        self.delayBox.setAlignment(Qt.AlignCenter)
        self.delayLabel.setAlignment(Qt.AlignCenter)

        # Set up the recording box
        self.recordingBox = QVBoxLayout()
        self.bottomLayout.addLayout(self.recordingBox)

        self.recordingLabel = QLabel("Recording")
        self.recordingLabel.setMargin(10)
        self.recordingLabel.setFont(title_font)
        self.recordingLabel.setAlignment(Qt.AlignHCenter)
        self.recordingBox.addWidget(self.recordingLabel)


        # Add layout to a container widger and set it as the central widget
        self.container = QWidget()
        self.container.setLayout(self.vLayout)
        self.setCentralWidget(self.container)


        print("UI Initiliased")

    def setup_camera(self):
        """Initialise Delay
        """
        self.frames = []


        """Initialize camera.
        """
        self.capture = cv2.VideoCapture(self.selected_camera_index)
        w = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.cameraAspectRatio = w/h

        self.capture.set(cv2.CAP_PROP_FPS, 60)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_size.width())
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_size.width()/self.cameraAspectRatio)

        self.start_time = time.time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.display_video_stream)
        timerTick =1/(VIDEO_FPS/60) # Convert fps to millisecond timer tick rate
        self.timer.start(timerTick)
        print("Camera Initiliased")

    def display_video_stream(self):
        #Read frame from camera and repaint QLabel widget.
        _, frame = self.capture.read()
        self.frames.append(frame)

        if time.time() - self.start_time > self.delay: # Only works if the delay is set when the program is loaded
            self.display_frame = self.frames.pop(0)

            self.display_frame = cv2.cvtColor(self.display_frame, cv2.COLOR_BGR2RGB)
            self.display_frame = cv2.flip(self.display_frame, 1)
            image = QImage(self.display_frame, self.display_frame.shape[1], self.display_frame.shape[0], 
                        self.display_frame.strides[0], QImage.Format_RGB888)
            self.pixmap = QPixmap.fromImage(image)
            
            self.scaledPixmap = self.pixmap.scaled(self.video_size.width(), self.video_size.height(), Qt.KeepAspectRatio, Qt.FastTransformation)
            
            w = self.primaryScreen.size().width()
            h = self.primaryScreen.size().height()
            self.scaledUpPixmap = self.pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.FastTransformation)

            self.imageLabel.setPixmap(self.scaledPixmap)
            self.fullscreen_image.setPixmap(self.scaledUpPixmap)
            

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.size = event.size()
        self.video_size = self.size*VIDEO_SCALE
    
    def moveEvent(self, event):
        super().moveEvent(event)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            if self.isFullScreened:
                self.unFullScreen()
            else:
                self.close()
        if e.key() == Qt.Key_F11:
            if self.isFullScreened:
                self.unFullScreen()
            else:
                self.fullScreen()

    def fullScreen(self):
        self.fullscreen_image.show()
        self.isFullScreened = True

    def unFullScreen(self):
        self.fullscreen_image.hide()
        self.isFullScreened = False

    def get_available_cameras(self):

        devices = FilterGraph().get_input_devices()

        available_cameras = []
        available_camera_indexes = []

        for device_index, device_name in enumerate(devices):
            available_camera_indexes.append(device_index)
            available_cameras.append(device_name)

        return available_camera_indexes, available_cameras
    
    def camera_index_changed(self, i):
        self.selected_camera_index = i

    def delay_value_changed(self, i):
        self.delay = i

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())