import pygame
import os
from src.systems.inventory import Inventory
from src.core.settings import TILE_SIZE

class Shop:
    """General Store NPC for buying/selling items with fixed prices."""
    
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE * 2, TILE_SIZE * 2)  # 2x2 tile entity like bank
        
        # Shop inventory (stores items for sale and quantity)
        self.inventory = Inventory()
        self._init_shop_inventory()
        
        # Buy prices (% of sell price) — e.g., 0.4 = shop buys at 40% of sell price
        self.buy_prices = {
            "bones": 5,
            "raw_fish": 8,
            "cooked_fish": 10,
            "wood": 4,
            "stone": 3,
            "iron_ore": 15,
            "iron_bar": 40,
            "bread": 4,
            "coins": 1,  # Coins buy/sell at face value
        }
        
        # Sell prices (items for sale with fixed prices in coins)
        self.sell_prices = {
            "bronze_sword": 100,
            "arrows": 1,  # 1 coin per arrow (or 10 coins per 10)
            "bread": 5,
            "raw_fish": 10,
            "bronze_axe": 50,
            "bronze_pickaxe": 50,
            "iron_ore": 20,
            "wood": 5,
            "rope": 20,
            "rod": 25,
        }
        
        self.image = None
        self._load_sprite()
    
    def _init_shop_inventory(self):
        """Populate shop with starting inventory."""
        self.inventory.add_item("bronze_sword", 5)
        self.inventory.add_item("arrows", 50)
        self.inventory.add_item("bread", 20)
        self.inventory.add_item("raw_fish", 15)
        self.inventory.add_item("bronze_axe", 3)
        self.inventory.add_item("bronze_pickaxe", 3)
        self.inventory.add_item("iron_ore", 10)
        self.inventory.add_item("wood", 25)
        self.inventory.add_item("rope", 10)
        self.inventory.add_item("rod", 5)
    
    def _load_sprite(self):
        """Load sprite asset if available."""
        sprite_path = os.path.join("assets", "sprites", "shop.png")
        if os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
            except pygame.error:
                pass
    
    def can_buy_item(self, item_name):
        """Check if player can buy this item from the shop."""
        return item_name in self.sell_prices and self.inventory.get_item_count(item_name) > 0
    
    def get_buy_price(self, item_name):
        """Get price for purchasing an item from shop."""
        return self.sell_prices.get(item_name, 0)
    
    def can_sell_item(self, item_name):
        """Check if shop will buy this item from player."""
        return item_name in self.buy_prices
    
    def get_sell_price(self, item_name):
        """Get price for selling an item to shop."""
        return self.buy_prices.get(item_name, 0)
    
    def draw(self, surface, camera=None):
        """Draw the shop on the map."""
        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.image:
            surface.blit(self.image, draw_rect)
        else:
            # Fallback: draw a brown shop block with a sign
            pygame.draw.rect(surface, (180, 120, 60), draw_rect)  # Tan color
            pygame.draw.rect(surface, (100, 60, 30), draw_rect, 4)  # Brown border
            
            # Draw shop sign: "$" in gold
            font = pygame.font.SysFont(None, 40)
            text = font.render("$", True, (255, 215, 0))
            text_rect = text.get_rect(center=draw_rect.center)
            surface.blit(text, text_rect)
