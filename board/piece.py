from enum import Enum


class Piece(Enum):
    whitePawn = 'white-pawn',
    blackPawn = 'black-pawn',
    whiteKing = 'white-king',
    blackKing = 'black-king',
    blackBishop = 'black-bishop',
    blackKnight = 'black-knight',
    blackQueen = 'black-queen',
    blackRook = 'black-rook',
    whiteBishop = 'white-bishop',
    whiteKnight = 'white-knight',
    whiteQueen = 'white-queen',
    whiteRook = 'white-rook',
    empty = 'empty'


possible_promotions = [Piece.blackQueen, Piece.blackRook, Piece.blackBishop, Piece.blackKnight, Piece.whiteRook,
                       Piece.whiteBishop, Piece.whiteKing, Piece.whiteQueen]

filter_promotions = ['white-pawn', 'black-pawn', 'white-king', 'black-king', ]


def piece_to_promotion(piece):
    piece_name = piece.value[0].split('-')[1]

    match piece_name:
        case 'knight':
            return 'n'
        case 'queen':
            return 'q'
        case 'bishop':
            return 'b'
        case 'rook':
            return 'r'
