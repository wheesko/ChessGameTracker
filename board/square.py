from board.piece import Piece


class Square:
    square_coords = []
    piece = None
    predicted = False
    coord = ''
    change = None
    new_piece = None

    def __init__(self, square_coords):
        self.square_coords = square_coords

    def set_piece(self, piece):
        self.piece = piece

    def is_empty(self):
        return self.piece is Piece.empty

    def is_point_in_square(self, x, y):
        top_left, top_right, bottom_left, bottom_right = self.square_coords

        top_left_x, top_left_y = top_left
        bottom_right_x, bottom_right_y = bottom_right
        bottom_left_x, bottom_left_y = bottom_left
        top_right_x, top_right_y = top_right

        if x < top_left_x and x < bottom_left_x:
            return False

        if y < top_left_y and y < top_right_y:
            return False

        if x > top_right_x and x > bottom_right_x:
            return False

        if y > bottom_left_y and y > bottom_right_y:
            return False

        return True