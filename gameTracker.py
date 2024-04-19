import os
import tkinter
from datetime import datetime
import time

import cairosvg
import chess
import chess.svg
import cv2
from PIL import ImageTk, Image

import config
from board.boardState import Board
from chesscog.corner_detection.detect_corners import find_corners
from LiveChess2FEN.detectboard.detect_board import detect, compute_corners
from predictor import Predictor
from webcam import VideoCapture


class ChessGameTracker:
    webcam = VideoCapture(config.settings.CAMERA_URL)
    board_corners = []
    square_corners = []
    move_index = 0
    game_save_path = ''
    game_directory = ''
    predictor = Predictor('rtdetr')
    game = chess.Board()
    board = None

    def __init__(self, game_save_path, tkinter_instance):
        self.game_save_path = game_save_path
        self.tkinter_instance = tkinter_instance

    def reset_game(self):
        self.square_corners = []
        self.board_corners = []
        self.move_index = 0
        self.game_save_path = ''

    def show_image(self, img):
        image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (780, 540), interpolation=cv2.INTER_LINEAR)
        image = ImageTk.PhotoImage(image=Image.fromarray(image))
        label_image = tkinter.Label(self.tkinter_instance, image=image)
        label_image.image = image
        label_image.place(x=0, y=0)

    def show_board(self, img):
        image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (600, 600), interpolation=cv2.INTER_LINEAR)
        image = ImageTk.PhotoImage(image=Image.fromarray(image))
        label_image = tkinter.Label(self.tkinter_instance, image=image)
        label_image.image = image
        label_image.place(x=781, y=0)

    def _draw_pieces_points(self, img, pieces_points):
        for piece_point in pieces_points:
            cv2.circle(img, (piece_point.point[0], piece_point.point[1]), 10, (255, 0, 0), -1)

    def initialize_board(self, img):
        self.find_square_and_board_corners(img)
        predictions = self.predictor.detect(img)
        pieces_points = self.predictor.predictions_to_pieces_points(predictions)
        leftmost_box, rightmost_box, class_left, class_right = self.predictor.find_closest_pieces(pieces_points)
        self._draw_pieces_points(img, pieces_points)
        board = Board(self.square_corners, class_left.split('-')[0], class_right.split('-')[0])
        self.board = board

    def find_square_and_board_corners(self, img):

        # Find board corners using chesscog
        corners = find_corners(config.settings, img)
        # Find board and square corners using LiveChess2FEN
        board = detect(img, corners.astype(int).tolist())
        bc, sc = compute_corners(board)

        self.board_corners = bc
        self.square_corners = sc

        return bc, sc

    def make_game_directory(self):
        current_date_time = datetime.now().strftime("%Y%m%d-%H%M")
        self.game_directory = f'{self.game_save_path}/{current_date_time}'
        if not os.path.exists(self.game_directory):
            os.mkdir(f'{self.game_save_path}/{current_date_time}')

    def save_game_move(self, image):
        if self.game_directory == '':
            self.make_game_directory()
        cv2.imwrite(f'{self.game_directory}/{self.move_index}.jpg', image)

    def draw_corners(self, img):
        for corner in self.board_corners:
            cv2.circle(img, (int(corner[0]), int(corner[1])), 20, (0, 255, 0), -1)
        for corner in self.square_corners:
            cv2.circle(img, (int(corner[0]), int(corner[1])), 10, (0, 0, 255), -1)

    def process_move(self):
        self.move_index += 1
        img = self.webcam.read()

        if img is None:
            print('No frame found')

        if len(self.board_corners) == 0 or len(self.square_corners) == 0:
            start = round(time.time() * 1000)
            self.initialize_board(img)
            print('Initialization took {} ms'.format(round(time.time() * 1000) - start))
        else:
            start = round(time.time() * 1000)

            predictions = self.predictor.detect(img)
            predictions = self.predictor.predictions_to_pieces_points(predictions)

            print('Predictions took {} ms'.format(round(time.time() * 1000) - start))

            start1 = round(time.time() * 1000)

            changed_squares = self.board.get_changed_squares(predictions)
            move_uci, update_squares = self.board.get_move(changed_squares, predictions, self.game.legal_moves)
            move_uci = chess.Move.from_uci(move_uci)

            print('Move took {} ms'.format(round(time.time() * 1000) - start1))

            self.game.push(move_uci)
            self.board.update_board(update_squares)

            print('Full detection took {} ms'.format(round(time.time() * 1000) - start))
            print(self.game.unicode(invert_color=True, borders=True))
            print(self.game.fen())
            print()

            svg = chess.svg.board(self.game, lastmove=self.game.peek(), size=600).encode()
            cairosvg.svg2png(svg, write_to='tmp/current_svg.png')
            current_svg = cv2.imread('tmp/current_svg.png')

            self.show_board(current_svg)

        self.draw_corners(img)
        self.show_image(img)

        self.save_game_move(img)

    def process_move_mock(self):
        img = cv2.imread(f'mock/{self.move_index + 1}.jpg')
        self.move_index += 1

        if img is None:
            print('No frame found')

        if len(self.board_corners) == 0 or len(self.square_corners) == 0:
            start = round(time.time() * 1000)
            self.initialize_board(img)
            print('Initialization took {} ms'.format(round(time.time() * 1000) - start))
        else:
            start = round(time.time() * 1000)
            predictions = self.predictor.detect(img)
            predictions = self.predictor.predictions_to_pieces_points(predictions)
            print('Predictions took {} ms'.format(round(time.time() * 1000) - start))

            start1 = round(time.time() * 1000)
            changed_squares = self.board.get_changed_squares(predictions)
            move_uci, update_squares = self.board.get_move(changed_squares, predictions, self.game.legal_moves)
            move_uci = chess.Move.from_uci(move_uci)
            print('Move took {} ms'.format(round(time.time() * 1000) - start1))

            self.game.push(move_uci)
            self.board.update_board(update_squares)
            print('Full detection took {} ms'.format(round(time.time() * 1000) - start))

            svg = chess.svg.board(self.game, lastmove=self.game.peek(), size=600).encode()
            cairosvg.svg2png(svg, write_to='tmp/current_svg.png')
            current_svg = cv2.imread('tmp/current_svg.png')
            print('\n')
            self.show_board(current_svg)

        # self.draw_corners(img)
        self.show_image(img)

        self.save_game_move(img)
