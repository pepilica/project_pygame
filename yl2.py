import pygame
import copy
from random import randint
from queue import Queue
import random
import os
import sys


GAME = None
LEVELS = {'Easy': [(9, 9), 10], 'Medium': [(16, 16), 40], 'Difficult': [(16, 30), 99]}
DIFFICULTY = None
SCREEN = None


def initialize():
    global SCREEN, DIFFICULTY
    SCREEN = pygame.display.set_mode((640, 480))
    DIFFICULTY = 'Easy'
    pygame.init()


def set_resolution(w, h):
    global SCREEN
    SCREEN = pygame.display.set_mode(w, h)


def set_difficulty(dif):
    global DIFFICULTY
    DIFFICULTY = dif[::]


def reset():
    global GAME
    initialize()
    GAME = None


def terminate():
    pygame.quit()
    sys.exit()


def load_image(name, colorkey=None):
    fullname = os.path.join('visual', name)
    image = pygame.image.load(fullname).convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Settings:
    def __init__(self):
        pass


class StartScreen:
    def __init__(self):
        global SCREEN
        h, w = SCREEN.get_size()
        screen = SCREEN
        font = pygame.font.Font(None, 30)
        running = True
        while running:
            top = 30
            for event in pygame.event.get():
                if event == pygame.QUIT:
                    running = False
            screen.fill((0, 0, 0))
            string_rendered = font.render('Сапер', 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            top += 10
            intro_rect.top = top
            intro_rect.x = w // 2 + intro_rect.width // 2
            top += intro_rect.height
            screen.blit(string_rendered, intro_rect)
            button('Начать игру', w // 2, top, 150, 40, (127, 127, 127), (200, 200, 200), screen, main)
            top += 60
            pygame.display.flip()
        terminate()


class Cell(object):
    def __init__(self, is_mine, is_visible=False, is_flagged=False):
        self.is_mine = is_mine
        self.is_visible = is_visible
        self.is_flagged = is_flagged

    def show(self):
        self.is_visible = True

    def flag(self):
        self.is_flagged = not self.is_flagged

    def place_mine(self):
        self.is_mine = True


class Minesweeper(tuple):
    def __init__(self, tup):
        super().__init__()
        self.is_playing = True
        self.left = 10
        self.top = 100
        self.cell_size = 30

    # настройка внешнего вида
    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def render(self, scr):
        for y, row in enumerate(self):
            for x, elem in enumerate(row):
                if elem.is_visible:
                    if elem.is_mine:
                        pygame.draw.ellipse(scr, (255, 0, 0), (self.left + self.cell_size * x,
                                                               self.top + self.cell_size * y,
                                                               self.cell_size, self.cell_size))
                    elif GAME.count_surrounding(y, x):
                        font = pygame.font.Font(None, 25)
                        text = font.render(str(GAME.count_surrounding(y, x)), 1, (100, 255, 100))
                        scr.blit(text, (self.left + x * self.cell_size + 5, self.top + y * self.cell_size + 5))
                    else:
                        pygame.draw.rect(scr, (127, 127, 127), (self.left + self.cell_size * x,
                                                                self.top + self.cell_size * y,
                                                                self.cell_size, self.cell_size))
                elif elem.is_flagged:
                    pygame.draw.rect(scr, (0, 0, 255), (self.left + self.cell_size * x,
                                                        self.top + self.cell_size * y,
                                                        self.cell_size, self.cell_size))
                pygame.draw.rect(scr, (255, 255, 255), (self.left + self.cell_size * x,
                                                        self.top + self.cell_size * y,
                                                        self.cell_size, self.cell_size), 1)

    def get_cell(self, pos):
        x, y = pos
        x -= self.left
        y -= self.top
        x //= self.cell_size
        y //= self.cell_size
        if 0 <= x <= len(self[0]) and 0 <= y <= len(self):
            return x, y
        return None

    def get_click(self, mouse_pos, state=True):
        if GAME.is_playing and not GAME.is_solved:
            cell = self.get_cell(mouse_pos)
            self.on_click(cell, state)

    def on_click(self, cell, open=True):
        if cell is not None:
            x, y = cell
            if open:
                GAME.show(y, x)
            else:
                GAME.flag(y, x)

    def mine_repr(self, row_id, col_id):
        cell = self[row_id][col_id]
        if cell.is_visible:
            if cell.is_mine:
                return "[*]"
            else:
                surr = self.count_surrounding(row_id, col_id)
                return f'[{surr}]' if surr else "[ ]"
        elif cell.is_flagged:
            return "[F]"
        else:
            return "[X]"

    def __str__(self):
        board_string = ("Мины: " + str(self.remaining_mines) + "\n  " +
                        "".join([f'[{str(i)}]' for i in range(len(self))]) + '\n')
        for (row_id, row) in enumerate(self):
            board_string += ("\n" + str(row_id) + " " +
                             "".join(self.mine_repr(row_id, col_id)
                                     for (col_id, _) in enumerate(row)) +
                             " " + str(row_id))
        board_string += "\n\n  " + "".join([f'[{str(i)}]' for i in range(len(self))])
        return board_string

    def show(self, row_id, col_id):
        cell = self[row_id][col_id]
        if not cell.is_visible:
            cell.show()
            if cell.is_mine and not cell.is_flagged:
                self.is_playing = False
                for _, row in enumerate(self):
                    for elem in row:
                        if not elem.is_flagged and elem.is_mine:
                            elem.show()
            elif self.count_surrounding(row_id, col_id) == 0:
                for (surr_row, surr_col) in self.get_neighbours(row_id, col_id):
                    if self.is_in_range(surr_row, surr_col):
                        self.show(surr_row, surr_col)

    def flag(self, row_id, col_id):
        cell = self[row_id][col_id]
        if not cell.is_visible:
            cell.flag()
            return True
        return False

    def place_mine(self, row_id, col_id):
        self[row_id][col_id].place_mine()

    def count_surrounding(self, row_id, col_id):
        return sum(1 for (surr_row, surr_col) in self.get_neighbours(row_id, col_id)
                   if (self.is_in_range(surr_row, surr_col) and
                       self[surr_row][surr_col].is_mine))

    def get_neighbours(self, row_id, col_id):
        SURROUNDING = ((-1, -1), (-1, 0), (-1, 1),
                       (0, -1), (0, 1),
                       (1, -1), (1, 0), (1, 1))
        return ((row_id + surr_row, col_id + surr_col) for (surr_row, surr_col) in SURROUNDING)

    def is_in_range(self, row_id, col_id):
        return 0 <= row_id < len(self) and 0 <= col_id < len(self)

    @property
    def remaining_mines(self):
        remaining = 0
        for row in self:
            for cell in row:
                if cell.is_mine:
                    remaining += 1
                if cell.is_flagged:
                    remaining -= 1
        return remaining

    @property
    def is_solved(self):
        return all((cell.is_visible or cell.is_mine) for row in self for cell in row)


def create_board(width, height):
    board = Minesweeper(tuple([tuple([Cell(False) for i in range(width)])
                               for j in range(height)]))
    return board


def reset_board():
    global GAME
    size = LEVELS[DIFFICULTY][0]
    GAME = create_board(*size)


def create_mines(board, mines, x, y):
    if x is not None and y is not None:
        width, height = len(board), len(board[0])
        available_pos = list(range((height - 1) * (width - 1)))
        available_pos.remove(y * height + x)
        for i in range(mines):
            new_pos = random.choice(available_pos)
            available_pos.remove(new_pos)
            (row_id, col_id) = (new_pos % width, new_pos // height)
            board.place_mine(row_id, col_id)
    return board


def button(msg, x, y, w, h, ic, ac, screen, action=None):
    global DIFFICULTY
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(screen, ac, (x, y, w, h))
        if click[0] == 1 and action is not None:
            if msg in LEVELS.keys():
                DIFFICULTY = msg
            action()
    else:
        pygame.draw.rect(screen, ic, (x, y, w, h))

    smallText = pygame.font.Font("freesansbold.ttf", 20)
    textSurf, textRect = text_objects(msg, smallText)
    textRect.center = ((x + (w / 2)), (y + (h / 2)))
    screen.blit(textSurf, textRect)


def text_objects(text, font):
    textSurface = font.render(text, True, (0, 0, 0))
    return textSurface, textSurface.get_rect()


def main():
    global GAME
    screen = SCREEN
    dif = DIFFICULTY
    size, mines = LEVELS[dif]
    v = 10
    fps = 60
    fill = False
    GAME = create_board(*size)
    running = True
    a = pygame.time.Clock()
    x, y, = 0, 0
    dx, dy = 0, 0
    while running:
        moving = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not moving:
                    moving = True
                    x, y = event.pos
            if event.type == pygame.MOUSEBUTTONUP:
                moving = False
                if event.button == 1:
                    if not fill and GAME.get_cell(event.pos):
                        GAME = create_mines(GAME, mines, *GAME.get_cell(event.pos))
                        fill = True
                    GAME.get_click(event.pos, True)
                if event.button == 3:
                    if not fill and GAME.get_cell(event.pos):
                        GAME = create_mines(GAME, mines, *GAME.get_cell(event.pos))
                        fill = True
                    GAME.get_click(event.pos, False)
            if event.type == pygame.MOUSEMOTION:
                if moving:
                    x1, y1 = event.pos
                    dx, dy = x1 - x, y1 - y
        print(dx, dy)
        screen.fill((0, 0, 0))
        GAME.render(screen)
        button("GO!", 160, 10, 50, 50, (0, 0, 127), (0, 0, 255), screen, main)
        if GAME.is_solved:
            print("Вы выиграли")
        elif not GAME.is_playing:
            print("Вы проиграли")
        a.tick(v)
        pygame.display.flip()
    terminate()


if __name__ == '__main__':
    initialize()
    StartScreen()