import heapq
from src.core.settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT

COLS = MAP_WIDTH // TILE_SIZE
ROWS = MAP_HEIGHT // TILE_SIZE


def find_path(start_world, end_world, obstacles, tile_map=None):
    """Return a smoothed list of world-space (x, y) waypoints from start to end.
    Returns [] if no path exists or start == end."""
    blocked = _build_grid(obstacles, tile_map)

    start = _clamp(_world_to_grid(start_world))
    end = _clamp(_world_to_grid(end_world))

    if start == end:
        return []

    if blocked[end[1]][end[0]]:
        end = _nearest_walkable(blocked, end)
        if end is None:
            return []

    if blocked[start[1]][start[0]]:
        start = _nearest_walkable(blocked, start)
        if start is None:
            return []

    path = _astar(blocked, start, end)
    if not path:
        return []

    path = _smooth(path, blocked)
    return [_grid_to_world(p) for p in path]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_grid(obstacles, tile_map=None):
    blocked = [[False] * COLS for _ in range(ROWS)]
    
    # 1. Block by tile type (Water)
    if tile_map:
        for x in range(COLS):
            for y in range(ROWS):
                # Using 2 as hardcoded TILE_WATER for speed, or could import it
                if tile_map[x][y] == 2:
                    blocked[y][x] = True

    # 2. Block by obstacle rects (Entities)
    for obs in obstacles:
        c0 = max(0, obs.left // TILE_SIZE)
        c1 = min(COLS - 1, (obs.right - 1) // TILE_SIZE)
        r0 = max(0, obs.top // TILE_SIZE)
        r1 = min(ROWS - 1, (obs.bottom - 1) // TILE_SIZE)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                blocked[r][c] = True
    return blocked


def _world_to_grid(pos):
    return (int(pos[0] // TILE_SIZE), int(pos[1] // TILE_SIZE))


def _grid_to_world(pos):
    return (pos[0] * TILE_SIZE + TILE_SIZE // 2, pos[1] * TILE_SIZE + TILE_SIZE // 2)


def _clamp(pos):
    return (max(0, min(COLS - 1, pos[0])), max(0, min(ROWS - 1, pos[1])))


def _nearest_walkable(blocked, pos):
    """BFS outward from pos to find nearest unblocked tile."""
    from collections import deque
    visited = {pos}
    queue = deque([pos])
    while queue:
        cx, cy = queue.popleft()
        if not blocked[cy][cx]:
            return (cx, cy)
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
    return None


def _astar(blocked, start, end):
    """8-directional A* returning list of grid positions (col, row)."""
    open_set = []
    heapq.heappush(open_set, (0.0, 0.0, start, None))
    came_from = {}
    g_score = {start: 0.0}

    while open_set:
        _, g, pos, parent = heapq.heappop(open_set)

        if pos in came_from:
            continue
        came_from[pos] = parent

        if pos == end:
            path = []
            cur = pos
            while cur is not None:
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return path

        cx, cy = pos
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0),
                        (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < COLS and 0 <= ny < ROWS):
                continue
            if blocked[ny][nx]:
                continue
            # Prevent diagonal corner-cutting
            if dx != 0 and dy != 0 and (blocked[cy][nx] or blocked[ny][cx]):
                continue
            step = 1.414 if dx != 0 and dy != 0 else 1.0
            new_g = g + step
            neighbor = (nx, ny)
            if neighbor not in g_score or new_g < g_score[neighbor]:
                g_score[neighbor] = new_g
                h = abs(nx - end[0]) + abs(ny - end[1])
                heapq.heappush(open_set, (new_g + h, new_g, neighbor, pos))

    return []


def _smooth(path, blocked):
    """String-pull: skip waypoints that have direct line-of-sight to a further one."""
    if len(path) <= 2:
        return path
    smoothed = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1:
            if _has_los(blocked, path[i], path[j]):
                break
            j -= 1
        smoothed.append(path[j])
        i = j
    return smoothed


def _has_los(blocked, a, b):
    """Bresenham line walk — returns True if no blocked tile between a and b."""
    x0, y0 = a
    x1, y1 = b
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        if blocked[y][x]:
            return False
        if x == x1 and y == y1:
            return True
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
