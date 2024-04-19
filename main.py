import tkinter
from gameTracker import ChessGameTracker


def key_pressed(event, game_tracker):
    if event.char == 'a':  # Check if 'a' was pressed
        game_tracker.process_move_mock()


if __name__ == '__main__':
    root = tkinter.Tk()
    root.geometry('1200x1200')

    gt = ChessGameTracker('games', root)
    root.bind('<KeyPress>', lambda e: key_pressed(event=e, game_tracker=gt))
    root.mainloop()
