import cv2

from board import leftmost_square_from_pieces
from predictor import Predictor

if __name__ == '__main__':
    predictor = Predictor('rtdetr')

    for i in range(12):
        print('\n')
        print(f'//// {i}')
        img = cv2.imread(f'tmp/h8/{i+1}.jpg')
        results = predictor.detect(img, f'{i}')
        pieces_points = predictor.predictions_to_pieces_points(results)
        leftmost_box, rightmost_box, class_left, class_right = predictor.find_closest_pieces(pieces_points)
        print(class_left, class_right)
        print(leftmost_square_from_pieces[(class_left.split('-')[0], class_right.split('-')[0])])
