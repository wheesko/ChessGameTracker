import chess

from board.change import Change
from board.piece import Piece, piece_to_promotion, possible_promotions, filter_promotions
from board.square import Square

leftmost_square_from_pieces = {
    ('black', 'black'): 'h8',
    ('black', 'white'): 'a8',
    ('white', 'white'): 'a1',
    ('white', 'black'): 'h1'
}

# Returns how to iterate through rows and columns based on starting square
unindexed_to_indexed = {
    # a1 starting, means top left is a8, then decrease row index, increase column index
    'a1': lambda horizontal, vertical: (file_names[horizontal + 1], 8 - vertical),
    'h1': lambda horizontal, vertical: (file_names[vertical + 1], horizontal + 1),
    'h8': lambda horizontal, vertical: (file_names[8 - horizontal], vertical + 1),
    'a8': lambda horizontal, vertical: (file_names[8 - vertical], 8 - horizontal),
}

file_names = {
    1: 'a',
    2: 'b',
    3: 'c',
    4: 'd',
    5: 'e',
    6: 'f',
    7: 'g',
    8: 'h',
}


def _get_board_without_names(square_corners):
    unindexed_board = [[0 for i in range(8)] for j in range(8)]

    for horizont_index in range(8):
        for vert_index in range(8):
            square_corners_index_base = 9 * horizont_index + vert_index
            unindexed_board[horizont_index][vert_index] = [
                square_corners[square_corners_index_base],  # top_left
                square_corners[square_corners_index_base + 9],  # top_right
                square_corners[square_corners_index_base + 1],  # bottom_left
                square_corners[square_corners_index_base + 10]  # bottom_right
            ]

    return unindexed_board


def get_enum_member_by_value(enum_class, value):
    for name, member in enum_class.__members__.items():
        if member.value == value:
            return member
    raise ValueError(f"No matching enum found for value: {value}")


def _get_initial_piece(file, rank):
    if rank == 2:
        return Piece.whitePawn

    if rank == 7:
        return Piece.blackPawn

    if rank == 8:
        if file == 'a' or file == 'h':
            return Piece.blackRook
        if file == 'b' or file == 'g':
            return Piece.blackKnight
        if file == 'f' or file == 'c':
            return Piece.blackBishop
        if file == 'd':
            return Piece.blackQueen
        if file == 'e':
            return Piece.blackKing

    if rank == 1:
        if file == 'a' or file == 'h':
            return Piece.whiteRook
        if file == 'b' or file == 'g':
            return Piece.whiteKnight
        if file == 'f' or file == 'c':
            return Piece.whiteBishop
        if file == 'd':
            return Piece.whiteQueen
        if file == 'e':
            return Piece.whiteKing

    return Piece.empty


def get_predictions_in_square(square, predictions):
    results = []
    for prediction in predictions:
        if square.is_point_in_square(prediction.point[0], prediction.point[1]):
            results.append(prediction)
    return results


class Board:
    board = {}

    def __init__(self, square_corners, leftmost_piece_color, rightmost_piece_color):
        self._index_board(square_corners, leftmost_piece_color, rightmost_piece_color)

    def _index_board(self, square_corners, leftmost_piece_color, rightmost_piece_color):
        starting_square = leftmost_square_from_pieces[(leftmost_piece_color, rightmost_piece_color)]
        unindexed_board = _get_board_without_names(square_corners)

        indexed_board = {}
        for horizont_index in range(8):
            for vert_index in range(8):
                file, rank = unindexed_to_indexed[starting_square](horizont_index, vert_index)

                square = Square(unindexed_board[horizont_index][vert_index])
                square.piece = _get_initial_piece(file, rank)
                square.square_coords = unindexed_board[horizont_index][vert_index]
                square.predicted = False
                square.coord = (file + str(rank))

                indexed_board[(file + str(rank))] = square

        self.board = indexed_board

    def get_changed_squares(self, predictions):
        changed_squares = []
        for square in self.board.values():
            square_updated = False
            square.change = None
            for prediction in predictions:
                if square.is_point_in_square(prediction.point[0], prediction.point[1]):
                    if not square_updated and square.is_empty():
                        print('prediction found, square went from empty to piece ' + square.coord)
                        square.change = Change.empty_to_occupied
                        changed_squares.append(square)
                        square_updated = True
                        break

                    if prediction.name.startswith('white'):
                        if square.piece.value[0].startswith('black'):
                            print('prediction found, square went from black to white ' + square.coord)
                            square.change = Change.color_change
                            changed_squares.append(square)
                            square_updated = True
                            break

                    if prediction.name.startswith('black'):
                        if square.piece.value[0].startswith('white'):
                            print('prediction found, square went from white to black ' + square.coord)
                            square.change = Change.color_change
                            changed_squares.append(square)
                            square_updated = True
                            break

                    if prediction.name.split('-')[0] == square.piece.value[0].split('-')[0]:
                        # print('prediction found, square unchanged ' + square.coord)
                        square.change = None
                        square_updated = True
                        break

            if not square.is_empty() and not square_updated:
                print('prediction not found, square went from piece to empty ', square.coord)
                changed_squares.append(square)
                square.change = Change.occupied_to_empty

        return changed_squares

    def update_board(self, update_squares):
        for square in update_squares:
            print(square.coord + ': ' + square.piece.value[0] + '->' + square.new_piece.value[0])
            square.piece = square.new_piece
            self.board[square.coord] = square

    def get_move(self, changed_squares, predictions, legal_moves):
        from_square = None
        to_square = None

        # Castling
        if len(changed_squares) == 4:
            # find the king and rook
            king_square = None
            rook_square = None
            for changed_square in changed_squares:
                if changed_square.piece == Piece.blackKing or changed_square.piece == Piece.whiteKing:
                    king_square = changed_square

                if changed_square.piece == Piece.blackRook or changed_square.piece == Piece.whiteRook:
                    rook_square = changed_square

            # White castled
            if king_square.coord == 'e1':
                # Long castle
                if rook_square.coord == 'a1':
                    a1 = self.get_square('a1')
                    b1 = self.get_square('b1')
                    c1 = self.get_square('c1')
                    d1 = self.get_square('d1')
                    e1 = self.get_square('e1')
                    a1.new_piece = Piece.empty
                    b1.new_piece = Piece.empty
                    c1.new_piece = Piece.whiteKing
                    d1.new_piece = Piece.whiteRook
                    e1.new_piece = Piece.empty

                    return 'e1c1', [a1, b1, c1, d1, e1]
                if rook_square.coord == 'h1':
                    h1 = self.get_square('h1')
                    g1 = self.get_square('g1')
                    f1 = self.get_square('f1')
                    e1 = self.get_square('e1')
                    h1.new_piece = Piece.empty
                    g1.new_piece = Piece.whiteKing
                    f1.new_piece = Piece.whiteRook
                    e1.new_piece = Piece.empty
                    return 'e1g1', [h1, g1, f1, e1]
            # Black castled
            if king_square.coord == 'e8':
                # Long castle
                if rook_square.coord == 'a8':
                    a8 = self.get_square('a8')
                    b8 = self.get_square('b8')
                    c8 = self.get_square('c8')
                    d8 = self.get_square('d8')
                    e8 = self.get_square('e8')
                    a8.new_piece = Piece.empty
                    b8.new_piece = Piece.empty
                    c8.new_piece = Piece.blackKing
                    d8.new_piece = Piece.blackRook
                    e8.new_piece = Piece.empty
                    return 'e8c8', [a8, b8, c8, d8, e8]
                if rook_square.coord == 'h8':
                    h8 = self.get_square('h8')
                    g8 = self.get_square('g8')
                    f8 = self.get_square('f8')
                    e8 = self.get_square('e8')
                    h8.new_piece = Piece.empty
                    g8.new_piece = Piece.blackKing
                    f8.new_piece = Piece.blackRook
                    e8.new_piece = Piece.empty
                    return 'e8g8', [h8, g8, f8, e8]

        # en passant
        if len(changed_squares) == 3:
            square_to_empty = None
            is_en_passant = False
            for changed_square in changed_squares:
                if changed_square.change == Change.empty_to_occupied:
                    to_square = changed_square
                    if list(changed_square.coord)[1] == '6' or list(changed_square.coord)[1] == '3':
                        is_en_passant = True

            if is_en_passant:
                for changed_square in changed_squares:
                    if changed_square.coord != to_square.coord:
                        if (list(to_square.coord)[0] != list(changed_square.coord)[0]
                                and (
                                        changed_square.piece == Piece.whitePawn or changed_square.piece == Piece.blackPawn)):
                            from_square = changed_square
                        elif list(to_square.coord)[0] == list(changed_square.coord)[0]:
                            square_to_empty = changed_square

                to_square.new_piece = from_square.piece
                from_square.new_piece = Piece.empty
                square_to_empty.new_piece = Piece.empty

                return from_square.coord + to_square.coord, [from_square, to_square, square_to_empty]

        # Try to fix position if detected 3 changes, but only 2 of them are valid
        if len(changed_squares) == 3:
            # If to_square was not found in en_passant, means it should be a color change.
            if to_square is None:
                for changed_square in changed_squares:
                    if changed_square.change == Change.color_change:
                        to_square = changed_square

            for changed_square in changed_squares:
                # Starting square will always be empty
                if changed_square.change == Change.occupied_to_empty:
                    # if move_uci is not in legal moves, means it is not the starting square
                    move = chess.Move.from_uci(changed_square.coord + to_square.coord)
                    if move not in legal_moves:
                        print('Removed square, as it cannot be the starting square: ', changed_square.coord)
                        changed_squares.remove(changed_square)

            # If failed to find invalid starting square, let it fail
            if len(changed_squares) != 2:
                return

        # move piece or capture piece
        if len(changed_squares) == 2:
            square_a, square_b = changed_squares
            if square_a.is_empty() and square_b.is_empty():
                raise 'Invalid move'

            if square_a.change == Change.occupied_to_empty:
                from_square = square_a
                to_square = square_b
            else:
                from_square = square_b
                to_square = square_a

            to_square.new_piece = from_square.piece
            from_square.new_piece = Piece.empty
            move_uci = from_square.coord + to_square.coord

            to_square_rank = list(to_square.coord)[1]
            if (
                    (to_square_rank == '8' or to_square_rank == '1') and
                    (to_square.new_piece == Piece.blackPawn or to_square.new_piece == Piece.whitePawn)
            ):
                detected_promotions = get_predictions_in_square(to_square, predictions)
                print('detected promotion')
                highest_conf = -1
                highest_conf_pred = predictions[0].conf
                for prediction in detected_promotions:
                    if prediction.conf >= highest_conf and prediction.name not in filter_promotions:
                        highest_conf_pred = prediction

                for possible_promotion in possible_promotions:
                    if highest_conf_pred is not None and highest_conf_pred.name == possible_promotion.value[0]:
                        to_square.new_piece = possible_promotion
                        move_uci += piece_to_promotion(possible_promotion)

            return move_uci, [from_square, to_square]

    def get_square(self, coord):
        return self.board[coord]
