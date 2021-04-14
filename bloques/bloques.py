from collections import OrderedDict
import random
import pygame
from pygame import Rect
import numpy as np

from excepciones.excepciones import *
from colores.colores import *

class Block(pygame.sprite.Sprite):
    
    @staticmethod
    def collide(block, group):
        """
        Check if the specified block collides with some other block
        in the group.
        """
        for other_block in group:
            # Ignore the current block which will always collide with itself.
            if block == other_block:
                continue
            if pygame.sprite.collide_mask(block, other_block) is not None:
                return True
        return False
    
    def __init__(self,juego):
        super().__init__()
        self.juego = juego
        self.current = True
        self.struct = np.array(self.struct)
        self._draw()
    
    def _draw(self, x=4, y=0):
        width = len(self.struct[0]) * self.juego.title_size
        height = len(self.struct) * self.juego.title_size
        self.image = pygame.surface.Surface([width, height])
        self.image.set_colorkey((0, 0, 0))
        # Position and size
        self.rect = Rect(0, 0, width, height)
        self.x = x
        self.y = y
        for y, row in enumerate(self.struct):
            for x, col in enumerate(row):
                if col:
                    pygame.draw.rect(
                        self.image,
                        self.color,
                        Rect(x*self.juego.title_size + 1, y*self.juego.title_size + 1,
                             self.juego.title_size - 2, self.juego.title_size - 2)
                    )
        self._create_mask()
    
    def redraw(self):
        self._draw(self.x, self.y)
    
    def _create_mask(self):
        """
        Create the mask attribute from the main surface.
        The mask is required to check collisions. This should be called
        after the surface is created or update.
        """
        self.mask = pygame.mask.from_surface(self.image)
        
    @property
    def group(self):
        return self.groups()[0]
    
    @property
    def x(self):
        return self._x
    
    @x.setter
    def x(self, value):
        self._x = value
        self.rect.left = value*self.juego.title_size
    
    @property
    def y(self):
        return self._y
    
    @y.setter
    def y(self, value):
        self._y = value
        self.rect.top = value*self.juego.title_size
    
    def move_left(self, group):
        self.x -= 1
        # Check if we reached the left margin.
        if self.x < 0 or Block.collide(self, group):
            self.x += 1
    
    def move_right(self, group):
        self.x += 1
        # Check if we reached the right margin or collided with another
        # block.
        if self.rect.right > self.juego.grid.width or Block.collide(self, group):
            # Rollback.
            self.x -= 1
    
    def move_down(self, group):
        self.y += 1
        # Check if the block reached the bottom or collided with 
        # another one.
        if self.rect.bottom > self.juego.grid.height or Block.collide(self, group):
            # Rollback to the previous position.
            self.y -= 1
            self.current = False
            raise BottomReached
    
    def rotate(self, group):
        self.image = pygame.transform.rotate(self.image, 90)
        # Once rotated we need to update the size and position.
        self.rect.width = self.image.get_width()
        self.rect.height = self.image.get_height()
        self._create_mask()
        # Check the new position doesn't exceed the limits or collide
        # with other blocks and adjust it if necessary.
        while self.rect.right > self.juego.grid.width:
            self.x -= 1
        while self.rect.left < 0:
            self.x += 1
        while self.rect.bottom > self.juego.grid.height:
            self.y -= 1
        while True:
            if not Block.collide(self, group):
                break
            self.y -= 1
        self.struct = np.rot90(self.struct)
    
    def update(self):
        if self.current:
            self.move_down()

class OBlock(Block):
    color = amarillo
    struct = (
        (1, 1),
        (1, 1),
    )

class TBlock(Block):
    color = violeta
    struct = (
        (0, 1, 0),
        (1, 1, 1),
    )

class IBlock(Block):
    color = celeste
    struct = (
        (1, 1, 1, 1),

    )

class LBlock(Block):
    color = azul
    struct = (
        (1, 0, 0),
        (1, 1, 1),
    )

class JBlock(Block):
    color = naranja
    struct = (
        (0, 0, 1),
        (1, 1, 1),
    )
    
class ZBlock(Block):
    color = rojo
    struct = (
        (1, 1, 0),
        (0, 1, 1),
    )

class SBlock(Block):
    color = verde
    struct = (
        (0, 1, 1),
        (1, 1, 0),
    )

class BlocksGroup(pygame.sprite.OrderedUpdates):
    bolsa = []
    bolsa_vacia = True
    bloque = None
    @staticmethod
    def get_random_block(juego):
        if BlocksGroup.bolsa_vacia:
            BlocksGroup.bolsa_vacia = False
            BlocksGroup.bolsa = [OBlock, TBlock, IBlock, LBlock, JBlock, ZBlock, SBlock]
            random.shuffle(BlocksGroup.bolsa)
            BlocksGroup.bloque = BlocksGroup.bolsa[0](juego)
            BlocksGroup.bolsa.pop(0)
        else:
            if len(BlocksGroup.bolsa) <= 0:
                BlocksGroup.bolsa_vacia = True
                BlocksGroup.get_random_block(juego)
            else:
                BlocksGroup.bloque = BlocksGroup.bolsa[0](juego)
                BlocksGroup.bolsa.pop(0)
        return BlocksGroup.bloque
    
    def __init__(self,juego, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.juego = juego
        self._reset_grid()
        self._ignore_next_stop = False
        self.score = 0
        self.next_block = None
        # Not really moving, just to initialize the attribute.
        self.stop_moving_current_block()
        # The first block.
        self._create_new_block()
    
    def _check_line_completion(self):
        """
        Check each line of the grid and remove the ones that
        are complete.
        """
        # Start checking from the bottom.
        for i, row in enumerate(self.grid[::-1]):
            if all(row):
                self.score += 5
                # Get the blocks affected by the line deletion and
                # remove duplicates.
                affected_blocks = list(
                    OrderedDict.fromkeys(self.grid[-1 - i]))
                
                for block, y_offset in affected_blocks:
                    # Remove the block tiles which belong to the
                    # completed line.
                    block.struct = np.delete(block.struct, y_offset, 0)
                    self.sonidoLineaCompleta = pygame.mixer.Sound("sonidos/completo.mp3")
                    self.sonidoLineaCompleta.play()
                    if block.struct.any():
                        # Once removed, check if we have empty columns
                        # since they need to be dropped.
                        block.struct, x_offset = \
                            remove_empty_columns(block.struct)
                        # Compensate the space gone with the columns to
                        # keep the block's original position.
                        block.x += x_offset
                        # Force update.
                        block.redraw()
                    else:
                        # If the struct is empty then the block is gone.
                        self.remove(block)
                
                # Instead of checking which blocks need to be moved
                # once a line was completed, just try to move all of
                # them.
                for block in self:
                    # Except the current block.
                    if block.current:
                        continue
                    # Pull down each block until it reaches the
                    # bottom or collides with another block.
                    while True:
                        try:
                            block.move_down(self)
                        except BottomReached:
                            break
                
                self.update_grid()
                # Since we've updated the grid, now the i counter
                # is no longer valid, so call the function again
                # to check if there're other completed lines in the
                # new grid.
                self._check_line_completion()
                break
    
    def _reset_grid(self):
        self.grid = [[0 for _ in range(self.juego.COLUMNAS)] for _ in range(self.juego.FILAS)]
    
    def _create_new_block(self):
        new_block = self.next_block or BlocksGroup.get_random_block(self.juego)
        if Block.collide(new_block, self):
            raise TopReached
        self.add(new_block)
        self.next_block = BlocksGroup.get_random_block(self.juego)
        self.update_grid()
        self._check_line_completion()
    
    def update_grid(self):
        self._reset_grid()
        for block in self:
            for y_offset, row in enumerate(block.struct):
                for x_offset, digit in enumerate(row):
                    # Prevent replacing previous blocks.
                    if digit == 0:
                        continue
                    rowid = block.y + y_offset
                    colid = block.x + x_offset
                    self.grid[rowid][colid] = (block, y_offset)
    
    @property
    def current_block(self):
        return self.sprites()[-1]
    
    def update_current_block(self):
        try:
            self.current_block.move_down(self)
        except BottomReached:
            self.stop_moving_current_block()
            self._create_new_block()
        else:
            self.update_grid()
    
    def move_current_block(self):
        # First check if there's something to move.
        if self._current_block_movement_heading is None:
            return
        action = {
            pygame.K_DOWN: self.current_block.move_down,
            pygame.K_SPACE: self.current_block.move_down,
            pygame.K_LEFT: self.current_block.move_left,
            pygame.K_RIGHT: self.current_block.move_right
        }
        try:
            # Each function requires the group as the first argument
            # to check any possible collision.
            action[self._current_block_movement_heading](self)
        except BottomReached:
            self.stop_moving_current_block()
            self._create_new_block()
        else:
            self.update_grid()
    
    def start_moving_current_block(self, key):
        if self._current_block_movement_heading is not None:
            self._ignore_next_stop = True
        self._current_block_movement_heading = key
    
    def stop_moving_current_block(self):
        if self._ignore_next_stop:
            self._ignore_next_stop = False
        else:
            self._current_block_movement_heading = None
    
    def rotate_current_block(self):
        # Prevent SquareBlocks rotation.
        if not isinstance(self.current_block, OBlock):
            self.current_block.rotate(self)
            self.update_grid()

def remove_empty_columns(arr, _x_offset=0, _keep_counting=True):
    """
    Remove empty columns from arr (i.e. those filled with zeros).
    The return value is (new_arr, x_offset), where x_offset is how
    much the x coordinate needs to be increased in order to maintain
    the block's original position.
    """
    for colid, col in enumerate(arr.T):
        if col.max() == 0:
            if _keep_counting:
                _x_offset += 1
            # Remove the current column and try again.
            arr, _x_offset = remove_empty_columns(
                np.delete(arr, colid, 1), _x_offset, _keep_counting)
            break
        else:
            _keep_counting = False
    return arr, _x_offset