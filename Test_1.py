import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QSlider, QStyle, QMessageBox, QScrollArea
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QPolygon
from PyQt5.QtCore import Qt, QPoint, QTimer

class ParkingLotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.shapes = []
        self.video = None
        self.frame = None
        self.scaled_pixmap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

    def initUI(self):
        self.setWindowTitle('Parking Lot Management')
        self.showMaximized()

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(1600, 900)  # Kích thước cố định 16:9

        self.load_button = QPushButton('Load Video', self)
        self.load_shapes_button = QPushButton('Load Shapes', self)
        self.reset_button = QPushButton('Reset Shapes', self)
        self.play_button = QPushButton(self.style().standardIcon(QStyle.SP_MediaPlay), '', self)
        self.pause_button = QPushButton(self.style().standardIcon(QStyle.SP_MediaPause), '', self)
        self.stop_button = QPushButton(self.style().standardIcon(QStyle.SP_MediaStop), '', self)
        self.slider = QSlider(Qt.Horizontal, self)

        self.load_button.setFixedSize(100, 30)
        self.load_shapes_button.setFixedSize(100, 30)
        self.reset_button.setFixedSize(100, 30)
        self.play_button.setFixedSize(30, 30)
        self.pause_button.setFixedSize(30, 30)
        self.stop_button.setFixedSize(30, 30)

        self.load_button.clicked.connect(self.load_video)
        self.load_shapes_button.clicked.connect(self.load_shapes)
        self.reset_button.clicked.connect(self.reset_shapes)
        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.stop_button.clicked.connect(self.stop_video)
        self.slider.sliderReleased.connect(self.slider_released)

        button_layout = QVBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.load_shapes_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()

        video_layout = QVBoxLayout()
        video_layout.addWidget(self.image_label)
        video_layout.addWidget(self.slider)

        main_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        main_layout.addLayout(video_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.show()

    def load_video(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Video File', '', 'Videos (*.mp4 *.avi *.mov)')
        if file_name:
            self.video = cv2.VideoCapture(file_name)
            if self.video.isOpened():
                self.frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
                self.slider.setRange(0, self.frame_count - 1)
                self.timer.start(30)  # 30 ms for approximately 30 fps
            else:
                QMessageBox.critical(self, "Error", "Could not open video.")
                
    def next_frame(self):
        if self.video.isOpened():
            ret, self.frame = self.video.read()
            if ret:
                self.display_frame()
                self.slider.setValue(int(self.video.get(cv2.CAP_PROP_POS_FRAMES)))
            else:
                self.stop_video()

    def play_video(self):
        self.timer.start(30)

    def pause_video(self):
        self.timer.stop()

    def stop_video(self):
        self.timer.stop()
        if self.video:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, self.frame = self.video.read()
            if ret:
                self.display_frame()
            self.slider.setValue(0)

    def slider_released(self):
        if self.video:
            frame_number = self.slider.value()
            self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, self.frame = self.video.read()
            if ret:
                self.display_frame()

    def load_shapes(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Shape File', '', 'Text Files (*.txt)')
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    self.shapes = [eval(line.strip()) for line in file.readlines()]
                self.display_frame()
                self.show_shape_windows()
            except FileNotFoundError:
                QMessageBox.critical(self, "Error", "Shape file not found.")

    def reset_shapes(self):
        self.shapes = []
        self.display_frame()

    def display_frame(self):
        if self.frame is not None:
            frame_height, frame_width = self.frame.shape[:2]
            
            # Tính toán kích thước mới để đảm bảo tỷ lệ 16:9
            target_width = self.image_label.width()
            target_height = int(target_width * 9 / 16)
            
            if target_height > self.image_label.height():
                target_height = self.image_label.height()
                target_width = int(target_height * 16 / 9)
            
            resized_frame = cv2.resize(self.frame, (target_width, target_height))
            
            bytes_per_line = 3 * target_width
            q_img = QImage(resized_frame.data, target_width, target_height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            
            self.scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(self.scaled_pixmap)
            self.update()

    def resizeEvent(self, event):
        if hasattr(self, 'image_label') and self.image_label is not None:
            label_width = self.image_label.width()
            label_height = int(label_width * 9 / 16)

            if label_height > self.height():
                label_height = self.height()
                label_width = int(label_height * 16 / 9)

            self.image_label.setFixedSize(label_width, label_height)

            if hasattr(self, 'frame') and self.frame is not None:
                self.display_frame()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.scaled_pixmap:
            painter = QPainter(self.image_label.pixmap())
            for shape in self.shapes:
                pen = QPen(Qt.green, 2)
                painter.setPen(pen)
                points = [QPoint(int(x * self.scaled_pixmap.width() / self.frame.shape[1]),
                                 int(y * self.scaled_pixmap.height() / self.frame.shape[0])) for x, y in shape]
                polygon = QPolygon(points)
                painter.drawPolygon(polygon)
            self.image_label.update()

    def show_shape_windows(self):
        if self.frame is None or not self.shapes:
            return

        for shape in self.shapes:
            points = [(int(x), int(y)) for x, y in shape]
            min_x = min(points, key=lambda t: t[0])[0]
            max_x = max(points, key=lambda t: t[0])[0]
            min_y = min(points, key=lambda t: t[1])[1]
            max_y = max(points, key=lambda t: t[1])[1]

            box_frame = self.frame[min_y:max_y, min_x:max_x]
            self.show_box_window(box_frame, min_x, min_y)

    def show_box_window(self, box_frame, x, y):
        box_window = QMainWindow(self)
        box_window.setWindowTitle(f'Box at ({x},{y})')
        box_window.setGeometry(100, 100, box_frame.shape[1], box_frame.shape[0])

        label = QLabel(box_window)
        
        # Chuyển đổi từ BGR sang RGB
        box_frame_rgb = cv2.cvtColor(box_frame, cv2.COLOR_BGR2RGB)
        
        # Tạo QImage từ numpy array
        height, width, channel = box_frame_rgb.shape
        bytes_per_line = 3 * width
        q_img = QImage(box_frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        label.setPixmap(pixmap)
        label.setGeometry(0, 0, box_frame.shape[1], box_frame.shape[0])

        scroll_area = QScrollArea(box_window)
        scroll_area.setWidget(label)
        box_window.setCentralWidget(scroll_area)

        box_window.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ParkingLotApp()
    sys.exit(app.exec_())
