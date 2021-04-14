import pygame
from colores.colores import *

class Boton():
	def __init__(self, x, y, image):
		self.image = image
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.clicked = False

	def draw(self, screen):
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False


		#draw button
		screen.blit(self.image, self.rect)

		return action

class Window():
    def __init__(self, width, height):
        self.width = width
        self.height = height

class Grid():
    def __init__(self, width, height):
        self.width = width
        self.height = height    

class Juego():
 
    def __init__(self, window, grid, title_size):
        self.window = window
        self.grid = grid
        self.title_size = title_size
        self.COLUMNAS = 10
        self.FILAS = 20

    def draw_grid(self, background):
        """Draw the background grid."""
        grid_color = gris
        # Vertical lines.
        for i in range(self.COLUMNAS+1):
            x = self.title_size * i
            pygame.draw.line(
                background, grid_color, (x, 0), (x, self.grid.height)
            )
        # Horizontal liens.
        for i in range(self.FILAS+1):
            y = self.title_size * i
            pygame.draw.line(
                background, grid_color, (0, y), (self.grid.width, y)
            )