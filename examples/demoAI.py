"""
The AI that plays the arcade demo in `snake play`.

Simple and readable on purpose: BFS to the nearest food, but never step into
a cell that doesn't leave enough room to fit the whole snake. If no food can
be reached safely, take whichever safe move has the most room.

Room is measured as if the cells next to enemy heads were already taken,
because an enemy can step into one of them before our next move and shut
the only way out.
"""

from collections import deque

from snake.logic import GameState, Turn, DIRECTIONS

TURNS = (Turn.STRAIGHT, Turn.LEFT, Turn.RIGHT)


def demoAI(state: GameState) -> Turn:
    me = state.snake
    blocked = blocked_cells(state)
    risky = blocked | next_to_enemy_heads(state)

    # the moves that survive this turn, with how much room each one leaves
    options = []
    for turn in TURNS:
        cell = me.get_next_head(turn)
        if cell in blocked or not in_bounds(cell, state):
            continue
        reachable = flood_fill(cell, risky | {me.head}, state)
        options.append((turn, cell, len(reachable), me.body[-1] in reachable))

    if not options:
        return Turn.STRAIGHT  # nothing survives, so it doesn't matter

    # safe = room to coil the whole body up, or we can get back to our tail
    safe = [o for o in options if o[2] >= len(me.body) + 2 or o[3]]

    # head for the nearest food, if the first step towards it is safe
    if safe:
        next_step = first_step_to_food(me.head, risky, state)
        for turn, cell, _, _ in safe:
            if cell == next_step:
                return turn

    # otherwise take the move with the most room
    pool = safe or options
    return max(pool, key=lambda o: o[2])[0]


def blocked_cells(state: GameState):
    """Walls plus every snake body, minus our own tail (it moves out of the way)"""
    blocked = set(state.walls)
    for enemy in state.enemies:
        blocked |= enemy.body_set
    blocked |= set(list(state.snake.body)[:-1])
    return blocked


def next_to_enemy_heads(state: GameState):
    """Cells an enemy could move into before our next turn"""
    cells = set()
    for enemy in state.enemies:
        for dx, dy in DIRECTIONS:
            cells.add((enemy.head[0] + dx, enemy.head[1] + dy))
    return cells


def in_bounds(cell, state):
    return 0 <= cell[0] < state.width and 0 <= cell[1] < state.height


def neighbours(cell, blocked, state):
    for dx, dy in DIRECTIONS:
        nxt = (cell[0] + dx, cell[1] + dy)
        if in_bounds(nxt, state) and nxt not in blocked:
            yield nxt


def flood_fill(start, blocked, state):
    """The set of cells that can be reached from start"""
    seen = {start}
    queue = deque([start])
    while queue:
        for nxt in neighbours(queue.popleft(), blocked, state):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def first_step_to_food(head, blocked, state):
    """BFS from the head; returns the first cell on the path to the nearest food"""
    parent = {head: None}
    queue = deque([head])
    while queue:
        cell = queue.popleft()
        if cell in state.food:
            while parent[cell] != head:
                cell = parent[cell]
            return cell
        for nxt in neighbours(cell, blocked, state):
            if nxt not in parent:
                parent[nxt] = cell
                queue.append(nxt)
    return None
