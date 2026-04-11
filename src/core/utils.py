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


def load_frames_from_sheet(
    path: str,
    frame_width: int,
    scale_to=None,
    frame_height: int = None,
    first_row_only: bool = False,
) -> list:
    """
    Load frames from a spritesheet: left-to-right, then top-to-bottom (row-major).

    - Multi-row grid: set frame_height to the cell height when the sheet is taller than one cell.
    - first_row_only: only the top row (e.g. one 15-frame walk/idle loop; full grid is for long clips).
    If scale_to is (w, h), each frame is scaled to that size.
    """
    full_path = get_path(path)
    surface_list = []

    if not os.path.exists(full_path) or frame_width <= 0:
        return surface_list

    try:
        sheet = pygame.image.load(full_path).convert_alpha()
    except pygame.error:
        return surface_list

    w, h = sheet.get_width(), sheet.get_height()
    if h <= 0 or w < frame_width:
        return surface_list

    fh = frame_height if frame_height is not None else h
    if fh <= 0 or fh > h:
        fh = h

    cols = w // frame_width
    rows = h // fh
    if first_row_only:
        rows = 1
    for row in range(rows):
        for col in range(cols):
            x = col * frame_width
            y = row * fh
            rect = pygame.Rect(x, y, frame_width, fh)
            frame = sheet.subsurface(rect).copy()
            if scale_to:
                frame = pygame.transform.scale(frame, scale_to)
            surface_list.append(frame)

    return surface_list
