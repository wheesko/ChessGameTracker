from enum import Enum


class Change(Enum):
    empty_to_occupied = 'empty_to_occupied',
    occupied_to_empty = 'occupied_to_empty'
    color_change = 'color_change'
