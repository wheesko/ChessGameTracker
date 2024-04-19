import cv2
import torch

from ultralytics import RTDETR


class Prediction:
    point = []
    name = ''
    conf = 0

    def __init__(self, point, name, conf):
        self.point = point
        self.name = name
        self.conf = conf


def bounding_box_bottom_middle(point_left, point_right):
    x_left = point_left[0]
    y_left = point_left[1]
    x_right = point_right[0]
    y_right = point_right[1]
    height = y_left - y_right
    return [int((x_left + x_right) * 0.5), y_right + int(height * 0.15)]


def _predictions_to_pieces_points_yolo(predictions):
    results = []

    for prediction in predictions:
        x = prediction['xmin']
        y = prediction['ymin']
        x1 = prediction['xmax']
        y1 = prediction['ymax']
        name = prediction['name']
        x = int(x)
        y = int(y)
        x1 = int(x1)
        y1 = int(y1)

        midpoint = bounding_box_bottom_middle([x, y], [x1, y1])
        results.append(Prediction(midpoint, name, prediction['confidence']))

    return results


def _find_closest_yolo(results):
    highest_x = results[0]['xmax'] * results[0]['ymax']
    rightmost_box = None
    lowest_x = results[0]['xmin'] * (1 / results[0]['ymin'])
    leftmost_box = None

    for box in results:
        current_x_min = box['xmin']
        current_x_max = box['xmax']
        current_y_min = box['ymin']
        current_y_max = box['ymax']

        prod_min = current_x_min * (1 / current_y_min)
        prod_max = current_x_max * current_y_max
        if prod_max >= highest_x:
            highest_x = prod_max
            rightmost_box = box

        if prod_min <= lowest_x:
            lowest_x = prod_min
            leftmost_box = box

    return (
        leftmost_box,
        rightmost_box,
        leftmost_box['name'],
        rightmost_box['name']
    )


def _find_closest_rtdetr(results):
    boxes = results[0].boxes
    highest_x = boxes[0].xyxy[0][2].item() * boxes[0].xyxy[0][3].item()
    rightmost_box = None
    lowest_x = boxes[0].xyxy[0][0].item() * (1 / boxes[0].xyxy[0][1].item())
    leftmost_box = None

    for box in boxes:
        current_x_min = box.xyxy[0][0].item()
        current_x_max = box.xyxy[0][2].item()
        current_y_min = box.xyxy[0][1].item()
        current_y_max = box.xyxy[0][3].item()
        prod_min = current_x_min * (1 / current_y_min)
        prod_max = current_x_max * current_y_max

        if prod_max >= highest_x:
            highest_x = prod_max
            rightmost_box = box

        if prod_min <= lowest_x:
            lowest_x = prod_min
            leftmost_box = box

    return (
        leftmost_box,
        rightmost_box,
        results[0].names[leftmost_box.cls[0].item()],
        results[0].names[rightmost_box.cls[0].item()]
    )

def _find_closest_rtdetr_points(pieces_points):
    highest_x = pieces_points[0].point[0] * pieces_points[0].point[1]
    rightmost_box = None
    lowest_x = pieces_points[0].point[0] * (1 / pieces_points[0].point[1])
    leftmost_box = None

    for piece_point in pieces_points:
        current_x = piece_point.point[0]
        current_y = piece_point.point[1]
        prod_min = current_x * (1 / current_y)
        prod_max = current_x * current_y

        if prod_max >= highest_x:
            highest_x = prod_max
            rightmost_box = piece_point

        if prod_min <= lowest_x:
            lowest_x = prod_min
            leftmost_box = piece_point

    return (
        leftmost_box,
        rightmost_box,
        leftmost_box.name,
        rightmost_box.name
    )

def _predictions_to_pieces_points_rtdetr(predictions):
    boxes = predictions[0].boxes
    names = predictions[0].names
    results = []

    for box in boxes:
        x, y, w, h = box.xyxy[0]
        name = names[box.cls[0].item()]
        x = int(x.item())
        y = int(y.item())
        x1 = int(w.item())
        y1 = int(h.item())

        midpoint = bounding_box_bottom_middle([x, y], [x1, y1])
        results.append(Prediction(midpoint, name, box.conf[0].item()))

    return results


class Predictor:
    model = None

    def __init__(self, model_type):
        self.model_type = model_type

        if model_type == 'yolo':
            yolov7_model_path = 'models/yolov7_last.pt'

            device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            self.model = torch.hub.load("WongKinYiu/yolov7", "custom", f"{yolov7_model_path}", trust_repo=True)
            self.model.conf = 0.75
            self.model.iou = 0.45

        if model_type == 'rtdetr':
            self.model = RTDETR('models/rt-detr-best.pt')

    def detect(self, img, savedir=''):
        if self.model_type == 'yolo':
            img1 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.model(img1)
            formatted = results.pandas().xyxy[0].to_dict(orient="records")
            results.save('tmp/' + savedir)
            return formatted

        if self.model_type == 'rtdetr':
            print(self.model.device)
            return self.model(img, iou=0.1, conf=0.1, line_width=1)

    def find_closest_pieces(self, results):
        if self.model_type == 'yolo':
            return _find_closest_yolo(results)
        if self.model_type == 'rtdetr':
            return _find_closest_rtdetr_points(results)

    def predictions_to_pieces_points(self, results):
        if self.model_type == 'yolo':
            return _predictions_to_pieces_points_yolo(results)
        if self.model_type == 'rtdetr':
            return _predictions_to_pieces_points_rtdetr(results)


if __name__ == '__main__':
    predictor = Predictor('rtdetr')

    predictor.detect(cv2.imread('tmp/testnow.jpeg'))