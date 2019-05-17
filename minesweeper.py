import sys, pygame
import numpy as np
from enum import Enum
import time
import os


class Color(Enum):
    RED = (255, 0, 0)
    GREEN = (0, 128, 0)
    LIGHTGREEN = (0, 200, 0)
    BLUE = (0, 0, 255)
    GREY = (155, 155, 155)
    LIGHTGREY = (200, 200, 200)
    DARKGREY = (105, 105, 105)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BROWN = (111, 62, 21)
    LIGHTBROWN = (138, 78, 29)
    MAROON = (128, 0, 0)
    NAVY = (0, 0, 128)
    TURQUOISE = (64, 224, 208)
    BLUEGREEN = (48, 92, 109)


color_map = {
    "tile": Color.GREY.value,
    "clicked": Color.LIGHTGREY.value,
    "border": Color.BROWN.value,
    "outerborder": Color.LIGHTBROWN.value,
    "clickborder": Color.WHITE.value,
    "background": Color.BLUEGREEN.value,
    "text": Color.WHITE.value,
    "Victory!": Color.LIGHTGREEN.value,
    "Defeat!": Color.RED.value
}


class Button:
    def __init__(self, screen, rect, text, text_size = 20, color = color_map["text"]):
        self.screen = screen
        self.rect = rect
        self.text = text
        self.text_size = text_size
        self.color = color

    def draw(self):
        font = pygame.font.SysFont('arialblack', self.text_size)
        pygame.draw.rect(self.screen, color_map["background"], self.rect)
        pygame.draw.rect(self.screen, color_map["outerborder"], self.rect, 8)
        pygame.draw.rect(self.screen, color_map["border"], self.rect, 3)
        self.screen.blit(font.render(self.text, True, self.color),
                         (self.rect.centerx - self.rect.width / 4.5, self.rect.centery - self.rect.height / 2.5))


class Tile:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.is_clicked = False
        self.is_flagged = False

    def set_clicked(self):
        self.is_clicked = True

    def set_flagged(self):
        self.is_flagged = True

    def set_unflagged(self):
        self.is_flagged = False


class Menu:
    def __init__(self):
        self.font = pygame.font.SysFont('arialblack', 20)
        self.screen = pygame.display.set_mode((400, 500))
        self.logo = pygame.image.load("Images/better_logo.png")
        self.easy = pygame.Rect(100, 150, 200, 50)
        self.medium = pygame.Rect(100, 250, 200, 50)
        self.hard = pygame.Rect(100, 350, 200, 50)
        self.difficulty = None
        self.create_menu()

    def create_menu(self):
        self.screen.fill(color_map["background"])
        self.screen.blit(self.logo, (10, 25))
        Button(self.screen, self.easy, "Easy").draw()
        Button(self.screen, self.medium, "Medium").draw()
        Button(self.screen, self.hard, "Hard").draw()

    def refresh(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if self.easy.collidepoint(pos):
                    self.difficulty = "easy"
                elif self.medium.collidepoint(pos):
                    self.difficulty = "medium"
                elif self.hard.collidepoint(pos):
                    self.difficulty = "hard"

        pygame.display.flip()


class Game:
    def __init__(self, diff):
        """Args:
            param diff: The difficulty level for the game (affects map size and # of bombs)
        """
        self.diff = diff
        self.map = [[]]
        self.tiles = [[]]
        self.num_bombs = self.remaining_bombs = self.remaining_tiles = -1
        self.dims = self.size = (0,0)
        self.minutes = self.seconds = 0
        self.old_time = 0
        self.screen = self.yes_rect = self.no_rect = None
        self.font = pygame.font.SysFont('arialblack', 20)
        self.logo = pygame.image.load("Images/better_logo.png")
        self.bomb = pygame.image.load("Images/bomb.png")
        self.flag = pygame.image.load("Images/flag.png")
        self.redx = pygame.image.load("Images/redx.png")
        self.first_click = True
        self.game_over = False
        self.play_again = False
        self.number_map = {
            1: Color.BLUE.value,
            2: Color.GREEN.value,
            3: Color.RED.value,
            4: Color.NAVY.value,
            5: Color.MAROON.value,
            6: Color.TURQUOISE.value,
            7: Color.BLACK.value,
            8: Color.DARKGREY.value
        }
        # Change the dimensions of the screen depending on the difficulty
        self.set_dims(self.diff)
        self.create_board()

    # Sets the dimensions of the map depending on the difficulty
    def set_dims(self, diff):
        if diff == "medium":
            self.dims = (16,16)
        elif diff == "hard":
            self.dims = (16,30)
        else:
            self.dims = (8,8)

    def create_board(self):
        # Set the screen size (reverse dimensions because size is width x height)
        self.size = [x * 45 for x in self.dims[::-1]]
        self.screen = pygame.display.set_mode(self.size)
        self.screen.fill(color_map["background"])
        # Display logo on top of screen (if the screen is big enough)
        if self.diff == "medium":
            self.screen.blit(self.logo, (self.size[0]/4, 0))
            self.num_bombs = 40
        elif self.diff == "hard":
            self.screen.blit(self.logo, (self.size[0]/3, 0))
            self.num_bombs = 99
        else:
            self.num_bombs = 10

        # Initialize top layer of tiles
        rows = self.dims[0]
        cols = self.dims[1]
        self.tiles = [[0 for x in range(cols)] for y in range(rows)]
        self.map = [[0 for x in range(cols)] for y in range(rows)]

        # Draw the tiles on the screen
        length = 35
        scaling_factor = 9
        left = self.size[0] / scaling_factor
        top = self.size[1] / (scaling_factor / 1.2)
        for r in range(rows):
            for c in range(cols):
                rect = left,top,length,length
                self.tiles[r][c] = Tile(rect)
                # Draw tile with border rectangle
                pygame.draw.rect(self.screen, color_map["tile"], rect)
                pygame.draw.rect(self.screen, color_map["border"], rect, 1)
                left += length
            left = self.size[0] / scaling_factor
            top += length


        # Display remaining bombs in the top-left corner
        width = self.size[0]
        height = self.size[1]
        self.screen.blit(self.bomb, ((width / 4)-35, (height / 8) - 35))
        self.screen.blit(self.font.render(': {0}'.format(self.num_bombs),
                                          True, color_map["text"]), (width / 4, (height / 8) - 30))

        # Display the timer in the top-right corner
        self.screen.blit(self.font.render('{0}:{1:02d}'.format(self.minutes, self.seconds),
                                          True, color_map["text"]), (width / 1.4, (height / 8) - 30))

    def set_bombs(self, diff, clicked_r, clicked_c):
        # Note: remaining bombs does not display the actual number of bombs left on the map.
        # Rather, it displays num_bombs - num_flags (so if a player randomly flags 99 locations, remaining_bombs = 0)
        self.remaining_bombs = self.num_bombs
        self.remaining_tiles = (self.dims[0] * self.dims[1]) - self.num_bombs

        # Pick num_bombs random coordinates to place the bombs
        rows = np.random.randint(self.dims[0], size=self.num_bombs)
        cols = np.random.randint(self.dims[1], size=self.num_bombs)

        # Initialize map with bombs
        for i in range(self.num_bombs):
            r = rows[i]
            c = cols[i]
            # If this position is bomb-free and is not adjacent to the first-clicked position, add a bomb
            if self.map[r][c] != '*' and not (abs(r-clicked_r) + abs(c-clicked_c)) <= 2:
                self.map[r][c] = '*'
            # Otherwise, find a new bomb location
            else:
                while self.map[r][c] == '*' or (abs(r-clicked_r) + abs(c-clicked_c)) <= 2:
                    r = np.random.randint(self.dims[0])
                    c = np.random.randint(self.dims[1])
                self.map[r][c] = '*'

        # Set the neighboring bomb numbers for each index
        for r in range(self.dims[0]):
            for c in range(self.dims[1]):
                if self.has_bomb(r, c):
                    continue
                else:
                    self.map[r][c] = self.count_bombs(r,c)

    # Finds all neighboring bombs around a given position
    # Need to check all 8 neighboring bombs, unless the position is along a wall or in a corner
    def count_bombs(self, r, c):
        num_neighbors = 0
        rows, cols = self.get_neighbors(r, c)
        for i in rows:
            for j in cols:
                # Find bombs for all neighbors (not including self)
                if i != r or j != c:
                    if self.has_bomb(i, j):
                        num_neighbors += 1
        return num_neighbors

    # Returns true if the given position has a bomb
    def has_bomb(self, r, c):
        return self.map[r][c] == '*'

    #  Redraws the board each time a tile is left-clicked
    def update_board(self, r, c):
        tile = self.tiles[r][c]
        tile.set_clicked()

        rect = tile.rect

        num = self.map[r][c]
        # If a bomb is clicked, player loses
        if num == '*':
            self.defeat()
            return

        # Color in the clicked square
        pygame.draw.rect(self.screen, color_map["clicked"], rect)
        pygame.draw.rect(self.screen, color_map["border"], rect, 1)

        # Decrement remaining hidden tiles if a valid tile is clicked
        self.remaining_tiles -= 1

        center = (rect.x + 12, rect.y + 4)
        if num != 0:
            self.screen.blit(self.font.render('{0}'.format(num), True, self.get_color(num)), center)
        else:
            rows, cols = self.get_neighbors(r, c)
            for i in rows:
                for j in cols:
                    # If the current tile has been clicked, do not update again
                    if self.tiles[i][j].is_clicked:
                        continue
                    # Update board for all un-clicked neighbors (not including self)
                    if i != r or j != c:
                        self.update_board(i, j)

        # If the player has clicked all non-bomb tiles, player wins
        if self.remaining_tiles == 0:
            self.victory()
            return

    # Called every timestep to monitor mouseclicks and other player actions
    def refresh(self):
        if not self.first_click and not self.game_over:
            self.update_time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            # Changes the border color of the tile to simulate clicking animation
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                pos = pygame.mouse.get_pos()
                tile, r, c = self.get_clicked(pos)

                # If the tile has been clicked before (or clicking outside the tiles), ignore the click
                if tile is None or tile.is_clicked:
                    continue
                else:
                    # Draw a white border around the clicked tile
                    pygame.draw.rect(self.screen, color_map["clickborder"], tile.rect, 1)

            # Once releasing mouse, determine the appropriate action (if any)
            elif event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()

                # If the game is in the restart state, determine whether player clicks yes/no to play again
                if self.game_over:
                    if self.yes_rect.collidepoint(pos):
                        self.play_again = True
                        break
                    elif self.no_rect.collidepoint(pos):
                        sys.exit()
                    # Don't allow other buttons to be pressed while the play again menu is up
                    continue

                tile, r, c = self.get_clicked(pos)

                # If the tile has been clicked before (or clicking outside the tiles), ignore the click
                if tile is None or tile.is_clicked:
                    continue

                # Draw original border around the tile
                pygame.draw.rect(self.screen, color_map["border"], tile.rect, 1)

                if event.button == 1:
                    self.left_click(tile, r, c)
                else:
                    self.right_click(tile, r, c)

        pygame.display.flip()

    # Defines the functionality for a left-click
    def left_click(self, tile, r ,c):
        # If the tile has been flagged, ignore the click but still show the animation
        if tile.is_flagged:
            return

        tile.set_clicked()

        pygame.draw.rect(self.screen, color_map["clickborder"], tile.rect, 1)

        # Set the bomb map after first mouse click (so first click can't be a bomb)
        if self.first_click:
            self.set_bombs(self.diff, r, c)
            self.first_click = False

        # Update map if left-clicking
        self.update_board(r, c)

    # Defines the functionality for a right-click
    def right_click(self, tile, r ,c):
        # Add/remove a flag if right-clicking
        if tile.is_flagged:
            pygame.draw.rect(self.screen, color_map["tile"], tile.rect)
            pygame.draw.rect(self.screen, color_map["border"], tile.rect, 1)
            tile.set_unflagged()
            if self.remaining_bombs != -1:
                self.remaining_bombs += 1
        # Only use flag if not all flags have been used
        elif self.remaining_bombs != 0:
            # Draw the flag before checking if the first left-click has occurred
            tile.set_flagged()
            self.screen.blit(self.flag, tile.rect)
            if self.remaining_bombs != -1:
                self.remaining_bombs -= 1
        # If the bombs have been initialized, update the remaining bomb counter
        if self.remaining_bombs != -1:
            # Draw grey rectangle over old number and re-draw number of remaining bombs
            width = self.size[0]
            height = self.size[1]
            pygame.draw.rect(self.screen, color_map["background"], (width / 4, (height / 8) - 30, 40, 30))
            self.screen.blit(self.font.render(': {0}'.format(self.remaining_bombs),
                                              True, color_map["text"]), (width / 4, (height / 8) - 30))

    # Redraws the timer approximately every second
    def update_time(self):
        if self.old_time == 0:
            self.old_time = time.time()

        if time.time() - self.old_time > 1:
            self.old_time = 0
            if self.seconds == 60:
                self.seconds = 0
                self.minutes += 1
            else:
                self.seconds += 1
            width = self.size[0]
            height = self.size[1]
            pygame.draw.rect(self.screen, color_map["background"], (width / 1.4, (height / 8) - 30, 50, 30))
            self.screen.blit(self.font.render('{0}:{1:02d}'.format(self.minutes, self.seconds),
                                              True, color_map["text"]), (width / 1.4, (height / 8) - 30))

    # Displays bombs and incorrect flags and prompts the user to play again
    def defeat(self):
        self.game_over = True
        font = pygame.font.SysFont('arialblack', self.dims[0]*2)
        width = self.size[0]
        height = self.size[1]
        # Display all bombs that weren't flagged upon losing
        for r in range(self.dims[0]):
            for c in range(self.dims[1]):
                tile = self.tiles[r][c]
                rect = tile.rect
                # If the tile was incorrectly flagged, display red X over flag
                if tile.is_flagged and not self.has_bomb(r, c):
                    self.screen.blit(self.redx, rect)
                elif self.has_bomb(r, c):
                    if tile.is_flagged:
                        continue
                    self.screen.blit(self.bomb, rect)
        self.restart("Defeat!")

    # Displays "victory" and prompts the user to play again
    def victory(self):
        self.game_over = True
        font = pygame.font.SysFont('arialblack', self.dims[0]*2)
        width = self.size[0]
        height = self.size[1]
        self.restart("Victory!")

    # Prompts the user to play again or quit after winning/losing
    def restart(self, outcome):
        width = self.size[0]
        height = self.size[1]
        result = pygame.Rect(width / 4, height / 5, width / 2, height / 10)
        play_again = pygame.Rect(width / 4, height / 3, width / 2, height / 10)
        self.yes_rect = pygame.Rect(width / 4, height / 2, width / 6, height / 12)
        self.no_rect = pygame.Rect(width / 1.7, height / 2, width / 6, height / 12)
        font_size = self.dims[0] * 2
        Button(self.screen, result, outcome, font_size, color_map[outcome]).draw()
        Button(self.screen, play_again, "Play Again?", font_size).draw()
        Button(self.screen, self.yes_rect, "Yes", font_size).draw()
        Button(self.screen, self.no_rect, "No", font_size).draw()

    # Helper function that finds which rectangle was most recently clicked
    def get_clicked(self, pos):
        for r in range(len(self.tiles)):
            for c in range(len(self.tiles[0])):
                tile = self.tiles[r][c]
                if tile.rect.collidepoint(pos):
                    return tile, r, c
        return None, 0, 0

    # Helper function that returns a color based on the number of nearby bombs
    def get_color(self, num):
        return self.number_map[num]

    # Helper function that returns array of valid neighboring indices
    def get_neighbors(self, r, c):
        rows = [r-1, r, r+1]
        cols = [c-1, c, c+1]
        # Check if the current row is the last row on the map
        # Do this check first so that rows still has 3 elements
        if r == self.dims[0]-1:
            rows.pop(2)
        elif r == 0:
            rows.pop(0)
        if c == self.dims[1]-1:
            cols.pop(2)
        elif c == 0:
            cols.pop(0)
        return rows, cols


def main():
    # Set the top-left corner of the pygame screen
    x = 200
    y = 100
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x, y)

    pygame.init()

    while 1:
        menu = Menu()
        while menu.difficulty is None:
            menu.refresh()

        game = Game(menu.difficulty)
        while not game.play_again:
            game.refresh()


if __name__ == "__main__":
    main()
