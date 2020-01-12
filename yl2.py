import pygame
import random
import os
import sys


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


GAME = None
LEVELS = {'Easy': [(9, 9), 10], 'Medium': [(16, 16), 40], 'Hard': [(25, 25), 99]}
DIFFICULTY = None
SCREEN = None
sys.setrecursionlimit(10000)
START = [False, False]
FILL = False
TEXTURE = load_image('texture.png')
CELL


def initialize(start=True):
    global SCREEN
    SCREEN = pygame.display.set_mode((640, 480))
    if start:
        pygame.init()


def get_resolution():
    return SCREEN.get_size()


def set_resolution(w, h):
    global SCREEN
    SCREEN = pygame.display.set_mode((w, h))
    print((w, h) == pygame.display.get_surface().get_size())


def reset():
    initialize(False)


def set_difficulty(dif):
    global DIFFICULTY
    DIFFICULTY = dif[::]


def terminate():
    pygame.quit()
    sys.exit(0)


class StartScreen:
    def __init__(self):
        global SCREEN
        SCREEN = pygame.display.set_mode((640, 480))
        h, w = SCREEN.get_size()
        screen = SCREEN
        font = pygame.font.Font(None, 30)
        running = True
        easy = Button('Easy', w // 2, 150, 150, 40, (0, 127, 0), (100, 255, 100), screen, main)
        medium = Button('Medium', w // 2, 200, 150, 40, (127, 127, 0), (255, 255, 100), screen, main)
        hard = Button('Hard', w // 2, 250, 150, 40, (127, 0, 0), (255, 100, 100), screen, main)
        exit = Button("Выйти", w // 2, 350, 150, 40, (0, 0, 127), (100, 100, 255), screen, terminate)
        while running:
            top = 50
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            screen.fill((0, 0, 0))
            string_rendered = font.render('Сапер', 1, pygame.Color('white'))
            intro_rect = string_rendered.get_rect()
            easy.update()
            medium.update()
            hard.update()
            exit.update()
            intro_rect.y = 50
            intro_rect.x = w // 2 + intro_rect.width // 2
            screen.blit(string_rendered, intro_rect)
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
    def __new__(cls, board):
        return super(Minesweeper, cls).__new__(cls, board)

    def __init__(self, tup):
        super().__init__()
        self.is_playing = True
        self.left = 10
        self.top = 100
        self.cell_size = 16

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
        if 0 <= x < len(self[0]) and 0 <= y < len(self):
            print(x, y)
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
            elif cell.is_flagged:
                cell.is_flagged = False
                cell.is_visible = False
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
        print(self[row_id][col_id] is None)
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
    board = Minesweeper(tuple(tuple(Cell(False) for i in range(width))
                              for j in range(height)))
    return board


def reset_board():
    global GAME, START, FILL
    fill, START = False, [False, False]
    size = LEVELS[DIFFICULTY][0]
    GAME = create_board(*size)


def create_mines(board, mines, x, y):
    if x is not None and y is not None:
        width, height = len(board[0]), len(board)
        available_pos = list(range((height - 1) * (width - 1)))
        print(max(available_pos))
        available_pos.remove(y * (height - 1) + x)
        for i in range(mines):
            new_pos = random.choice(available_pos)
            available_pos.remove(new_pos)
            (row_id, col_id) = (new_pos % width, new_pos // height)
            board.place_mine(row_id, col_id)
    return board


class Button:
    def __init__(self, msg, x, y, w, h, ic, ac, screen, action=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.ic = ic
        self.ac = ac
        self.screen = screen
        self.action = action
        self.msg = msg
        print('Created')

    def update(self):
        global DIFFICULTY
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if self.x + self.w > mouse[0] > self.x and self.y + self.h > mouse[1] > self.y:
            pygame.draw.rect(self.screen, self.ac, (self.x, self.y, self.w, self.h))
            if click[0] == 1 and self.action is not None:
                if self.msg in LEVELS.keys():
                    DIFFICULTY = self.msg
                self.action()
        else:
            pygame.draw.rect(self.screen, self.ic, (self.x, self.y, self.w, self.h))
        smallText = pygame.font.Font(None, 20)
        textSurf, textRect = text_objects(self.msg, smallText)
        textRect.center = ((self.x + (self.w / 2)), (self.y + (self.h / 2)))
        self.screen.blit(textSurf, textRect)


def text_objects(text, font):
    textSurface = font.render(text, True, (0, 0, 0))
    return textSurface, textSurface.get_rect()


def main():
    global GAME
    screen = SCREEN
    started1 = False
    size, mines = LEVELS[DIFFICULTY]
    set_resolution(size[0] * 16 + 10 * 2, size[1] * 16 + 125)
    fps = 60
    fill = False
    GAME = create_board(size[0], size[1])
    running = True
    a = pygame.time.Clock()
    restart = Button("Заново", size[0] * 15 - 50, 5, 100, 50, (255, 255, 75), (255, 255, 75), screen, main)
    return_btn = Button('<', 5, 5, 50, 50, (255, 0, 0), (127, 75, 75), screen, StartScreen)
    started = False
    while running:
        CELL_TEXTURE = pygame.sprite.Group
        moving = False
        for event in pygame.event.get():
            if started and started1:
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and not moving:
                        moving = True
                if event.type == pygame.MOUSEBUTTONUP:
                    moving = False
                    if event.button == 1:
                        if not fill and GAME.get_cell(event.pos):
                            GAME = create_mines(GAME, mines, *GAME.get_cell(event.pos))
                            fill = True
                        GAME.get_click(event.pos, True)
                    if event.button == 3:
                        GAME.get_click(event.pos, False)
        screen.fill((0, 0, 0))
        restart.update()
        return_btn.update()
        GAME.render(screen)
        if GAME.is_solved:
            print("Вы выиграли")
        elif not GAME.is_playing:
            print("Вы проиграли")
        a.tick(fps)
        pygame.display.flip()
        if started:
            started1 = True
        started = True
    terminate()


if __name__ == '__main__':
    initialize()
    StartScreen()
