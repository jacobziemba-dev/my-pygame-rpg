import os
import pygame

def get_path(path):
    # Base path relative to the project root
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    full_path = os.path.normpath(os.path.join(base_path, path))
    return full_path

def import_folder(path: str) -> list:
    full_path = get_path(path)
    surface_list = []

    if not os.path.exists(full_path):
        return surface_list

    # Sort files to ensure frames are in correct order (0.png, 1.png, etc.)
    for _, __, img_files in os.walk(full_path):
        for image in sorted(img_files, key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x):
            if image.endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(full_path, image)
                try:
                    image_surf = pygame.image.load(img_path).convert_alpha()
                    surface_list.append(image_surf)
                except pygame.error:
                    pass

    return surface_list
