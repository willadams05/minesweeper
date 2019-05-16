import sys, pygame
import numpy as np
from enum import Enum
import time

class Color(Enum):
    RED = (255, 0, 0)
    GREEN = (0, 128, 0)
    BLUE = (0, 0, 255)
    LIGHTGREY = (155, 155, 155)
    DARKGREY = (105, 105, 105)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    MAROON = (128, 0, 0)
    NAVY = (0, 0, 128)
    TURQUOISE = (64, 224, 208)
    ROYAL = (65, 105, 225)


class Helpers:
    def __init__(self):
        pass

    @staticmethod
    def pretty_print(matrix):
        s = [[str(e) for e in row] for row in matrix]
        lens = [max(map(len, col)) for col in zip(*s)]
        fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
        table = [fmt.format(*row) for row in s]
        print('\n'.join(table))


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
        self.screen = self.font = None
        self.flag = self.bomb = self.ximg = None
        self.first_click = True
        self.color_map = {
            1: Color.BLUE.value,
            2: Color.GREEN.value,
            3: Color.RED.value,
            4: Color.NAVY.value,
            5: Color.MAROON.value,
            6: Color.TURQUOISE.value,
            7: Color.BLACK.value,
            8: Color.DARKGREY.value
        }

    def initialize(self):
        pygame.init()

        # Set the font for displaying bomb numbers
        self.font = pygame.font.SysFont('arialblack', 20)
        self.bomb = pygame.image.load("Images/bomb.png")
        self.flag = pygame.image.load("Images/flag.png")
        self.redx = pygame.image.load("Images/redx.png")
        self.set_dims(self.diff)
        self.create_board()

    def set_bombs(self, diff, clicked_r, clicked_c):
        # Set the number of bombs
        if diff == "intermediate":
            self.num_bombs = 40
        elif diff == "expert":
            self.num_bombs = 99
        else:
            self.num_bombs = 10

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
            # If this position is bomb-free and was not the first-clicked position, add a bomb
            if self.map[r][c] != '*' and (r != clicked_r or c != clicked_c):
                self.map[r][c] = '*'
            # Otherwise, find a new bomb location
            else:
                while self.map[r][c] == '*' or (r == clicked_r and c == clicked_c):
                    r = np.random.randint(self.dims[0])
                    c = np.random.randint(self.dims[1])
                self.map[r][c] = '*'

        # Set the neighboring bomb numbers for each index
        for r in range(self.dims[0]):
            for c in range(self.dims[1]):
                if self.has_bomb(r, c):
                    continue
                else:
                    self.map[r][c] = self.find_bombs(r,c)


        # Display remaining bombs in the top-left corner
        width = self.size[0]
        height = self.size[1]
        self.screen.blit(self.bomb, ((width / 4)-35, (height / 8) - 35))
        self.screen.blit(self.font.render(': {0}'.format(self.remaining_bombs),
                                          True, Color.BLUE.value), (width / 4, (height / 8) - 30))
        # Helpers.pretty_print(self.map)


    # Finds all neighboring bombs around a given position
    # Need to check all 8 neighboring bombs, unless the position is along a wall or in a corner
    def find_bombs(self, r, c):
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

    # Sets the dimensions of the map depending on the difficulty
    def set_dims(self, diff):
        if diff == "intermediate":
            self.dims = (16,16)
        elif diff == "expert":
            self.dims = (16,30)
        else:
            self.dims = (8,8)

    def create_board(self):
        # Set the screen size (reverse dimensions because size is width x height)
        self.size = [x * 45 for x in self.dims[::-1]]
        print(self.size)
        self.screen = pygame.display.set_mode(self.size)
        self.screen.fill(Color.LIGHTGREY.value)

        # Initialize top layer of tiles
        rows = self.dims[0]
        cols = self.dims[1]
        self.tiles = [[0 for x in range(cols)] for y in range(rows)]
        self.map = [[0 for x in range(cols)] for y in range(rows)]
        length = 35
        scaling_factor = 9
        left = self.size[0] / scaling_factor
        top = self.size[1] / (scaling_factor/1.2)
        for r in range(rows):
            for c in range(cols):
                rect = left,top,length,length
                self.tiles[r][c] = Tile(rect)
                # Draw tile with border rectangle
                pygame.draw.rect(self.screen, Color.ROYAL.value, rect)
                pygame.draw.rect(self.screen, Color.DARKGREY.value, rect, 1)
                left += length
            left = self.size[0] / scaling_factor
            top += length

    # Function to update the board after a tile is clicked
    def update_board(self, r, c):
        tile = self.tiles[r][c]
        tile.set_clicked()

        rect = tile.rect
        center = (rect.x + 12, rect.y + 4)

        num = self.map[r][c]

        # If a bomb is clicked, player loses
        if num == '*':
            self.defeat()
            return

        # Color in the clicked square
        pygame.draw.rect(self.screen, Color.LIGHTGREY.value, rect)
        pygame.draw.rect(self.screen, Color.DARKGREY.value, rect, 1)

        self.remaining_tiles -= 1

        # If the player has clicked all non-bomb tiles, player wins
        if self.remaining_tiles == 0:
            self.victory()
            return

        if num != 0:
            self.screen.blit(self.font.render('{0}'.format(num), True, self.get_color(num)), center)
        else:
            rows, cols = self.get_neighbors(r, c)
            for i in rows:
                for j in cols:
                    # If the current tile has been updated, continue
                    if self.tiles[i][j].is_clicked:
                        continue
                    # Update board for all unclicked neighbors (not including self)
                    if i != r or j != c:
                        self.update_board(i, j)

    # Function to refresh the game state at each timestep
    def refresh(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            # Change the border color of the box to simulate clicking animation
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                tile, r, c = self.get_clicked(pos)

                # If the tile has been clicked before (or clicking outside the tiles), ignore the click
                if tile is None or tile.is_clicked:
                    continue
                else:
                    # Draw a white border around the clicked tile
                    pygame.draw.rect(self.screen, Color.WHITE.value, tile.rect, 1)

            # Once releasing mouse, determine if it was a right or left click
            elif event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                tile, r, c = self.get_clicked(pos)

                # If the tile has been clicked before (or clicking outside the tiles), ignore the click
                if tile is None or tile.is_clicked:
                    continue

                # Draw original border around the tile
                pygame.draw.rect(self.screen, Color.DARKGREY.value, tile.rect, 1)
                # Update map if left-clicking
                if event.button == 1:

                    # If the tile has been flagged, ignore the click but still show the animation
                    if tile.is_flagged:
                        continue

                    tile.set_clicked()

                    pygame.draw.rect(self.screen, Color.WHITE.value, tile.rect, 1)

                    # Set the bomb map after first mouse click (so first click can't be a bomb)
                    if self.first_click:
                        self.set_bombs(self.diff, r, c)
                        self.first_click = False

                    self.update_board(r, c)
                # Add/remove a flag if right-clicking
                else:
                    if tile.is_flagged:
                        pygame.draw.rect(self.screen, Color.ROYAL.value, tile.rect)
                        pygame.draw.rect(self.screen, Color.DARKGREY.value, tile.rect, 1)
                        tile.set_unflagged()
                        if self.remaining_bombs != -1:
                            self.remaining_bombs += 1
                    # Only use flag if not all flags have been used
                    elif self.remaining_bombs != 0:
                        tile.set_flagged()
                        self.screen.blit(self.flag, tile.rect)
                        if self.remaining_bombs != -1:
                            self.remaining_bombs -= 1
                    if self.remaining_bombs != -1:
                        # Draw grey rectangle over old number and re-draw number of remaining bombs
                        width = self.size[0]
                        height = self.size[1]
                        pygame.draw.rect(self.screen, Color.LIGHTGREY.value, (width/4,(height / 8) - 30,40,30))
                        self.screen.blit(self.font.render(': {0}'.format(self.remaining_bombs),
                                                          True, Color.BLUE.value), (width / 4, (height / 8) - 30))
        pygame.display.flip()

    # Displays bombs and incorrect flags and prompts the user to play again
    def defeat(self):
        self.font = pygame.font.SysFont('arialblack', self.dims[0]*2)
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
                    # if tile.is_flagged:
                    #     continue
                    self.screen.blit(self.bomb, rect)
        self.screen.blit(self.font.render('Game Over', True, Color.RED.value), (width / 2.5, height / 12.5))
        # TODO: Add quit / restart buttons
        # TODO: sys.exit()
        # TODO: restart with command line args

    # Displays "victory" and prompts the user to play again
    def victory(self):
        self.font = pygame.font.SysFont('arialblack', self.dims[0]*2)
        width = self.size[0]
        height = self.size[1]
        self.screen.blit(self.font.render('Victory', True, Color.GREEN.value), (width / 2.5, height / 12.5))

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
        return self.color_map[num]

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
    # TODO: Initialize the game with sys args
    game = Game("intermediate")
    game.initialize()

    # TODO: Refresh on a timer
    while 1:
        game.refresh()


if __name__ == "__main__":
    main()
