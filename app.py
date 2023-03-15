from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QVBoxLayout, QPushButton, QWidget, QComboBox, QSpinBox, QHBoxLayout
from PySide6.QtGui import QIcon

from pygrabber.dshow_graph import FilterGraph
import sys, os

basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'mycompany.myproduct.subproduct.version'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

class StartupWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.selected_camera_index = 0
        self.delay = 10

        self.setWindowTitle("Vizan")
        self.layout = QVBoxLayout()
        self.label = QLabel("Simple video replay application for sports video analysis.")
        self.label.setMargin(10)
        self.layout.addWidget(self.label)
        self.label.setAlignment(Qt.AlignCenter)

        self.cameraDropDown = QComboBox()
        self.cameras = self.get_available_cameras()
        print(tuple(self.cameras[1]))
        self.cameraDropDown.addItems(tuple(self.cameras[1]))
        self.cameraDropDown.currentIndexChanged.connect(self.camera_index_changed)
        self.layout.addWidget(self.cameraDropDown)


        self.delayLayout = QHBoxLayout()
        self.layout.addLayout(self.delayLayout)

        self.delayLabel = QLabel("Delay")
        self.delayLabel.setMargin(10)
        self.delayLayout.addWidget(self.delayLabel)

        self.delayBox = QSpinBox()
        self.delayBox.setRange(0,60)
        self.delayBox.setSuffix("s")
        self.delayBox.setValue(10)
        self.delayBox.valueChanged.connect(self.delay_value_changed)
        self.delayLayout.addWidget(self.delayBox)
        self.delayBox.setAlignment(Qt.AlignCenter)
        self.delayLabel.setAlignment(Qt.AlignCenter)


        self.button = QPushButton("Start")
        self.button.setIcon(QIcon(os.path.join(basedir, "content", "gopro.png")))
        self.button.pressed.connect(self.start)
        self.layout.addWidget(self.button)

        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.setFixedSize(QSize(400, 300))

        self.show()

    def start(self):
        self.button.setText("Starting...")
        self.button.setEnabled(False)
        pythonFileTarget = os.path.join(basedir, 'Vizan.py')
        os.system('python ' + pythonFileTarget + ' -s ' + str(self.cameras[0][self.selected_camera_index]) + ' -d ' + str(self.delay))

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            print("Escape!")

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(basedir, 'VizanIcon.ico')))
    w = StartupWindow()
    app.exec_()