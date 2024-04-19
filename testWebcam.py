from ultralytics import RTDETR

import config
from webcam import VideoCapture

if __name__ == '__main__':
    model = RTDETR('models/rt-detr-best.pt')
    webcam = VideoCapture(config.settings.CAMERA_URL)

    while True:
        frame = webcam.read()
        if frame is None:
            print('bad')
            continue

        model(frame, iou=0.2, conf=0.5, show=True, line_width=2, show_labels=True)
