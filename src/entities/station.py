import pygame
from src.core.settings import TILE_SIZE

class Station:
    def __init__(self, x, y, station_type, name):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.station_type = station_type
        self.name = name
        
        self.is_processing = False
        self.process_start_time = 0
        self.process_duration = 0
        
        self.input_item = None
        self.output_item = None
        self.items_to_process = 0
        self.processed_items = 0
        
        self.color = (150, 150, 150)
        if self.station_type == "furnace":
            self.color = (80, 40, 20)
        elif self.station_type == "workbench":
            self.color = (120, 80, 40)
            
    def start_processing(self, input_item, output_item, count, duration):
        self.input_item = input_item
        self.output_item = output_item
        self.items_to_process += count
        self.process_duration = duration
        if not self.is_processing:
            self.is_processing = True
            self.process_start_time = pygame.time.get_ticks()

    def update(self):
        if self.is_processing and self.items_to_process > 0:
            current_time = pygame.time.get_ticks()
            if current_time - self.process_start_time >= self.process_duration:
                self.items_to_process -= 1
                self.processed_items += 1
                if self.items_to_process > 0:
                    self.process_start_time = current_time
                else:
                    self.is_processing = False
                    
    def collect(self, player):
        if self.processed_items > 0:
            player.inventory.add_item(self.output_item, self.processed_items)
            collected = self.processed_items
            self.processed_items = 0
            return collected
        return 0

    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        pygame.draw.rect(surface, self.color, draw_rect)
        if self.is_processing:
            # draw processing indicator
            pygame.draw.circle(surface, (255, 100, 0), draw_rect.center, 5)
        elif self.processed_items > 0:
            # draw ready indicator
            pygame.draw.circle(surface, (0, 255, 0), draw_rect.center, 5)
