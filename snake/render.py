import pyray as rl
from snake.logic import GameState
from collections import deque
import copy


class SnakeRenderer:
    def __init__(
        self, cell_size=40, render_fps=60, moves_per_second=10, fullscreen=False
    ):
        """
        Initialize the raylib renderer for Snake game with Google Snake theme and buffered smooth movement.

        Args:
            cell_size: Size of each grid cell in pixels (ignored when fullscreen)
            render_fps: Target render frames per second
            moves_per_second: How many game moves to play per second
            fullscreen: Fill the screen, sizing cells to fit and centring the board
        """
        self.cell_size = cell_size
        self.fullscreen = fullscreen
        # top-left corner of the board in window pixels
        self.origin_x = 0
        self.origin_y = 0
        self.render_fps = render_fps
        self.moves_per_second = moves_per_second
        self.move_duration = 1.0 / moves_per_second
        self.padding = 20
        self.window_initialized = False

        # State buffer for smooth playback
        self.state_buffer = deque()
        self.current_state = None
        self.next_state = None
        self.interpolation_progress = 0.0

        # Previous body positions for interpolation (player + enemies by ID)
        self.prev_player_body = None
        self.prev_enemy_bodies = {}  # Changed to dict keyed by snake ID

        # Restart handling
        self.restart_requested = False

        # Optional message drawn over the board (used by interactive play)
        self.message = None
        self.message_corner = False

        # Game over overlay settings (interactive play tweaks these)
        self.show_game_over = True
        self.game_over_hint = "Press R to restart"

        # Google Snake theme colors
        self.BG_BOARD = rl.Color(170, 215, 81, 255)  # Light green board
        self.BG_FRAME = rl.Color(87, 138, 52, 255)  # Dark green frame
        self.CHECKER_LIGHT = rl.Color(162, 209, 73, 255)  # Lighter checker
        self.SNAKE_COLOR = rl.Color(58, 103, 240, 255)  # Google blue snake
        self.ENEMY_COLOR = rl.Color(231, 71, 71, 255)  # Red enemy snakes
        self.APPLE_RED = rl.Color(231, 71, 71, 255)  # Bright red apple
        self.APPLE_GREEN = rl.Color(100, 180, 50, 255)  # Green leaf
        self.WHITE = rl.WHITE
        self.BLACK = rl.BLACK
        self.WALL_COLOR = rl.Color(87, 138, 52, 255)  # Dark green walls

    def _init_window(self, width, height):
        """Initialize the raylib window (done on first render)"""
        if not self.window_initialized:
            rl.set_trace_log_level(rl.LOG_NONE)

            if self.fullscreen:
                # borderless windowed keeps the desktop resolution, which is
                # far better behaved than exclusive fullscreen on macOS
                rl.init_window(800, 600, "WAI Snake")
                rl.toggle_borderless_windowed()
                window_width = rl.get_screen_width()
                window_height = rl.get_screen_height()
                if (window_width, window_height) == (800, 600):
                    monitor = rl.get_current_monitor()
                    window_width = rl.get_monitor_width(monitor)
                    window_height = rl.get_monitor_height(monitor)
                    rl.set_window_size(window_width, window_height)

                # biggest square cell that fits the board on screen
                self.cell_size = min(
                    (window_width - self.padding * 2) // width,
                    (window_height - self.padding * 2) // height,
                )
                game_width = width * self.cell_size
                game_height = height * self.cell_size
                self.origin_x = (window_width - game_width) // 2
                self.origin_y = (window_height - game_height) // 2
            else:
                game_width = width * self.cell_size
                game_height = height * self.cell_size
                window_width = game_width + (self.padding * 2)
                window_height = game_height + (self.padding * 2)
                self.origin_x = self.padding
                self.origin_y = self.padding
                rl.init_window(window_width, window_height, "WAI Snake")

            rl.set_target_fps(self.render_fps)
            self.window_initialized = True
            self.game_width = game_width
            self.game_height = game_height
            self.window_width = window_width
            self.window_height = window_height
            # how much bigger than the default 40px cell everything is drawn
            self.scale = self.cell_size / 40

    def push(self, state: GameState):
        """
        Add a new game state to the render buffer and display current frame.

        Args:
            state: GameState object containing snake, food, walls, etc.
        """
        # Initialize window on first render
        if not self.window_initialized:
            self._init_window(state.width, state.height)

        # Add state to buffer (make a copy to avoid reference issues)
        state_copy = self._copy_state(state)
        self.state_buffer.append(state_copy)

        # Initialize current state if needed
        if self.current_state is None:
            self.current_state = self.state_buffer.popleft()
            self.prev_player_body = deque(self.current_state.snake.body)
            # Store previous bodies by snake ID
            self.prev_enemy_bodies = {}
            for enemy in self.current_state.enemies:
                if enemy is not None and enemy.body:
                    self.prev_enemy_bodies[enemy.id] = deque(enemy.body)

        # Process buffered states and render
        self._process_and_render()

    def update(self):
        """
        Process and render one frame without adding a new state.
        Call this to keep the renderer running without new game states.
        Returns False if window should close, True otherwise.
        """
        if not self.window_initialized:
            return True

        if rl.window_should_close():
            return False

        self._process_and_render()
        return True

    def should_restart(self):
        """Check if restart was requested and clear the flag"""
        if self.restart_requested:
            self.restart_requested = False
            return True
        return False

    def is_idle(self):
        """True when every pushed state has been fully played back.

        Interactive play uses this to step the game exactly once per
        move_duration so the snake moves in real time.
        """
        return self.next_state is None and len(self.state_buffer) == 0

    # keys that steer the player snake, mapped to Direction indices
    DIRECTION_KEYS = {
        rl.KEY_UP: 0,
        rl.KEY_RIGHT: 1,
        rl.KEY_DOWN: 2,
        rl.KEY_LEFT: 3,
        rl.KEY_W: 0,
        rl.KEY_D: 1,
        rl.KEY_S: 2,
        rl.KEY_A: 3,
    }

    def poll_direction(self):
        """Return the Direction index of an arrow/WASD key pressed this frame, else None"""
        if not self.window_initialized:
            return None
        for key, direction in self.DIRECTION_KEYS.items():
            if rl.is_key_pressed(key):
                return direction
        return None

    def set_message(self, text, corner=False):
        """Show (or clear with None) a message: centred, or small in the top-right corner"""
        self.message = text
        self.message_corner = corner

    def set_speed(self, moves_per_second):
        """Change how quickly pushed states are played back"""
        self.moves_per_second = moves_per_second
        self.move_duration = 1.0 / moves_per_second

    def poll_space(self):
        """True on the frame the space bar is pressed"""
        return self.window_initialized and rl.is_key_pressed(rl.KEY_SPACE)

    def reset(self):
        """Clear the state buffer and reset to current state"""
        self.state_buffer.clear()
        self.next_state = None
        self.interpolation_progress = 0.0
        self.prev_enemy_bodies = {}  # Clear the enemy body cache

    def is_window_open(self):
        """Check if the renderer window is still open"""
        # If not initialized yet, return True so the loop can start and initialize it
        if not self.window_initialized:
            return True
        return not rl.window_should_close()

    def _copy_state(self, state):
        """Create a deep copy of the game state"""
        return copy.deepcopy(state)

    def _process_and_render(self):
        """Process buffer and render the current interpolated frame"""
        # Check if window should close
        if rl.window_should_close():
            self.close()
            return

        # Check for restart/quit keys on every frame
        if rl.is_key_pressed(rl.KEY_R):
            self.restart_requested = True

        # Get delta time
        dt = rl.get_frame_time()

        # Advance interpolation
        if self.next_state is not None:
            self.interpolation_progress += dt / self.move_duration

            # If we've completed the interpolation, move to next state
            if self.interpolation_progress >= 1.0:
                self.current_state = self.next_state
                self.prev_player_body = deque(self.current_state.snake.body)

                # Update previous enemy bodies by ID
                self.prev_enemy_bodies = {}
                for enemy in self.current_state.enemies:
                    if enemy is not None and enemy.body:
                        self.prev_enemy_bodies[enemy.id] = deque(enemy.body)

                self.next_state = None
                self.interpolation_progress = 0.0

        # Try to get next state from buffer
        if self.next_state is None and len(self.state_buffer) > 0:
            self.next_state = self.state_buffer.popleft()
            self.interpolation_progress = 0.0

        # Calculate current alpha for rendering
        alpha = self.interpolation_progress if self.next_state is not None else 1.0

        # Render the current frame
        self._render_frame(alpha)

    def _render_frame(self, alpha):
        """Render a single frame with interpolation"""
        # Use current state for rendering (or next if current is None)
        state = (
            self.current_state if self.current_state is not None else self.next_state
        )
        if state is None:
            return

        rl.begin_drawing()

        # Dark green frame background
        rl.clear_background(self.BG_FRAME)

        # Light green game board
        rl.draw_rectangle(
            self.origin_x, self.origin_y, self.game_width, self.game_height, self.BG_BOARD
        )

        # Subtle checkerboard pattern
        for x in range(state.width):
            for y in range(state.height):
                if (x + y) % 2 == 0:
                    rl.draw_rectangle(
                        self.origin_x + x * self.cell_size,
                        self.origin_y + y * self.cell_size,
                        self.cell_size,
                        self.cell_size,
                        self.CHECKER_LIGHT,
                    )

        # Walls (dark green squares)
        for x, y in state.walls:
            wall_x = self.origin_x + x * self.cell_size
            wall_y = self.origin_y + y * self.cell_size
            rl.draw_rectangle(
                wall_x, wall_y, self.cell_size, self.cell_size, self.WALL_COLOR
            )

        # Food (apples with details)
        for fx, fy in state.food:
            self._draw_apple(fx, fy)

        # Draw enemy snakes first (so player snake appears on top)
        self._draw_enemy_snakes_smooth(alpha)

        # Draw player snake
        self._draw_player_snake_smooth(alpha)

        # UI elements (Google Snake style)
        self._draw_ui(state)

        # Game over overlay
        if not state.snake.isAlive and self.show_game_over:
            self._draw_game_over(state)

        # Optional message overlay (drawn last so it sits above everything)
        if self.message:
            self._draw_message(self.message, self.message_corner)

        # Buffer indicator (optional debug info)
        # buffer_text = f"Buffer: {len(self.state_buffer)}"
        # rl.draw_text(buffer_text, self.window_width - 150, self.window_height - 30, 16,
        #            rl.Color(255, 255, 255, 150))

        rl.end_drawing()

    def _draw_player_snake_smooth(self, alpha):
        """Draw player snake with smooth interpolation between current and next state"""
        if self.current_state is None or not self.current_state.snake.body:
            return

        # Always draw player snake even if dead (for game over screen)
        curr_body = list(self.current_state.snake.body)

        # If we have a next state, interpolate towards it
        if self.next_state is not None and self.next_state.snake.body:
            prev_body = (
                list(self.prev_player_body) if self.prev_player_body else curr_body
            )
            next_body = list(self.next_state.snake.body)

            # Ensure bodies match length
            while len(prev_body) < len(next_body):
                prev_body.append(prev_body[-1] if prev_body else next_body[0])
            while len(prev_body) > len(next_body):
                prev_body.pop()

            # Draw segments with interpolation
            for i in range(len(next_body) - 1, -1, -1):
                is_head = i == 0
                is_tail = i == len(next_body) - 1

                # Interpolate between prev and next position
                prev_x, prev_y = prev_body[i]
                next_x, next_y = next_body[i]

                interp_x = prev_x + (next_x - prev_x) * alpha
                interp_y = prev_y + (next_y - prev_y) * alpha

                direction = self.next_state.snake.direction if is_head else None
                self._draw_segment_smooth(
                    interp_x, interp_y, is_head, direction, is_tail, self.SNAKE_COLOR
                )
        else:
            # No next state, just draw current state
            direction = self.current_state.snake.direction
            for i in range(len(curr_body) - 1, -1, -1):
                is_head = i == 0
                is_tail = i == len(curr_body) - 1
                x, y = curr_body[i]
                self._draw_segment_smooth(
                    float(x),
                    float(y),
                    is_head,
                    direction if is_head else None,
                    is_tail,
                    self.SNAKE_COLOR,
                )

    def _draw_enemy_snakes_smooth(self, alpha):
        """Draw all enemy snakes with smooth interpolation using ID-based matching"""
        if self.current_state is None:
            return

        # Build a map of next state enemies by ID for easy lookup
        next_enemies_by_id = {}
        if self.next_state is not None:
            for enemy in self.next_state.enemies:
                if enemy is not None and enemy.isAlive:
                    next_enemies_by_id[enemy.id] = enemy

        for curr_enemy in self.current_state.enemies:
            # Skip None or empty enemies
            if curr_enemy is None or not curr_enemy.body:
                continue

            # Skip already dead enemies
            if not curr_enemy.isAlive:
                continue

            curr_body = list(curr_enemy.body)
            snake_id = curr_enemy.id

            # Check if this snake exists in next state
            if self.next_state is not None:
                if snake_id in next_enemies_by_id:
                    # Snake survives - interpolate normally
                    next_enemy = next_enemies_by_id[snake_id]

                    # Get previous body for this snake ID
                    prev_body = list(self.prev_enemy_bodies.get(snake_id, curr_body))
                    next_body = list(next_enemy.body)

                    # Ensure bodies match length
                    while len(prev_body) < len(next_body):
                        prev_body.append(prev_body[-1] if prev_body else next_body[0])
                    while len(prev_body) > len(next_body):
                        prev_body.pop()

                    # Draw segments with interpolation
                    for i in range(len(next_body) - 1, -1, -1):
                        is_head = i == 0
                        is_tail = i == len(next_body) - 1

                        prev_x, prev_y = prev_body[i]
                        next_x, next_y = next_body[i]

                        interp_x = prev_x + (next_x - prev_x) * alpha
                        interp_y = prev_y + (next_y - prev_y) * alpha

                        direction = next_enemy.direction if is_head else None
                        self._draw_segment_smooth(
                            interp_x,
                            interp_y,
                            is_head,
                            direction,
                            is_tail,
                            self.ENEMY_COLOR,
                        )
                else:
                    # Snake dies in next frame - fade out effect
                    fade_alpha = int(255 * (1.0 - alpha * 0.7))  # Fade to 30% opacity
                    fade_color = rl.Color(
                        self.ENEMY_COLOR.r,
                        self.ENEMY_COLOR.g,
                        self.ENEMY_COLOR.b,
                        fade_alpha,
                    )

                    direction = curr_enemy.direction
                    for i in range(len(curr_body) - 1, -1, -1):
                        is_head = i == 0
                        is_tail = i == len(curr_body) - 1
                        x, y = curr_body[i]
                        self._draw_segment_smooth(
                            float(x),
                            float(y),
                            is_head,
                            direction if is_head else None,
                            is_tail,
                            fade_color,
                        )
            else:
                # No next state - just draw current state
                direction = curr_enemy.direction
                for i in range(len(curr_body) - 1, -1, -1):
                    is_head = i == 0
                    is_tail = i == len(curr_body) - 1
                    x, y = curr_body[i]
                    self._draw_segment_smooth(
                        float(x),
                        float(y),
                        is_head,
                        direction if is_head else None,
                        is_tail,
                        self.ENEMY_COLOR,
                    )

    def _draw_segment_smooth(self, x, y, is_head, direction, is_tail, color):
        """Draw a snake segment at interpolated position (x, y can be floats)"""
        size = self.cell_size - self.cell_size // 5
        cx = self.origin_x + x * self.cell_size + self.cell_size // 2
        cy = self.origin_y + y * self.cell_size + self.cell_size // 2
        px = int(cx - size / 2)
        py = int(cy - size / 2)

        if is_head:
            rl.draw_rectangle_rounded(rl.Rectangle(px, py, size, size), 0.5, 8, color)

            # Draw eyes based on direction (with alpha support for fading)
            eye_size = 6 * self.scale
            pupil_size = 3 * self.scale

            # Extract alpha from color for eye colors
            alpha_val = color.a if hasattr(color, "a") else 255
            eye_white = rl.Color(255, 255, 255, alpha_val)
            eye_black = rl.Color(0, 0, 0, alpha_val)

            if direction == 0:  # Up
                eye1_x, eye1_y = px + size // 3, py + size // 3
                eye2_x, eye2_y = px + 2 * size // 3, py + size // 3
            elif direction == 1:  # Right
                eye1_x, eye1_y = px + 2 * size // 3, py + size // 3
                eye2_x, eye2_y = px + 2 * size // 3, py + 2 * size // 3
            elif direction == 2:  # Down
                eye1_x, eye1_y = px + size // 3, py + 2 * size // 3
                eye2_x, eye2_y = px + 2 * size // 3, py + 2 * size // 3
            else:  # Left (3)
                eye1_x, eye1_y = px + size // 3, py + size // 3
                eye2_x, eye2_y = px + size // 3, py + 2 * size // 3

            rl.draw_circle(eye1_x, eye1_y, eye_size, eye_white)
            rl.draw_circle(eye2_x, eye2_y, eye_size, eye_white)
            rl.draw_circle(eye1_x, eye1_y, pupil_size, eye_black)
            rl.draw_circle(eye2_x, eye2_y, pupil_size, eye_black)
        else:
            roundness = 0.4 if is_tail else 0.3
            rl.draw_rectangle_rounded(
                rl.Rectangle(px, py, size, size), roundness, 8, color
            )

    def _draw_apple(self, x, y):
        """Draw an apple with highlight, stem, and leaf"""
        cx = self.origin_x + x * self.cell_size + self.cell_size // 2
        cy = self.origin_y + y * self.cell_size + self.cell_size // 2
        radius = self.cell_size // 3
        k = self.scale

        # Main apple body
        rl.draw_circle(cx, cy, radius, self.APPLE_RED)

        # Highlight
        rl.draw_circle(
            int(cx - 5 * k), int(cy - 5 * k), radius // 3, rl.Color(255, 180, 180, 255)
        )

        # Stem
        rl.draw_rectangle(
            int(cx - 1 * k),
            int(cy - radius - 5 * k),
            max(3, int(3 * k)),
            max(6, int(6 * k)),
            rl.Color(139, 69, 19, 255),
        )

        # Leaf (simple triangle)
        rl.draw_triangle(
            rl.Vector2(float(cx + 2 * k), float(cy - radius - 2 * k)),
            rl.Vector2(float(cx + 8 * k), float(cy - radius - 4 * k)),
            rl.Vector2(float(cx + 6 * k), float(cy - radius + 2 * k)),
            self.APPLE_GREEN,
        )

    def _draw_ui(self, state):
        """Draw UI elements (score and snake length) in Google Snake style"""
        # Apple icon and score
        k = self.scale
        bx, by = self.origin_x + 20, self.origin_y + 15
        rl.draw_circle(bx, by, 12 * k, self.APPLE_RED)
        rl.draw_circle(
            int(bx - 3 * k), int(by - 3 * k), 4 * k, rl.Color(255, 180, 180, 255)
        )  # highlight
        rl.draw_rectangle(
            int(bx - 2 * k), int(by - 13 * k), max(3, int(3 * k)), max(6, int(6 * k)),
            rl.Color(139, 69, 19, 255),
        )  # stem
        rl.draw_text(
            f"{state.snake.score}", int(bx + 20 * k), int(by - 10 * k), int(28 * k), self.WHITE
        )

    def _draw_message(self, text, corner=False):
        """Draw a message on a translucent banner, centred or tucked top-right"""
        font_size = int((18 if corner else 28) * self.scale)
        pad = int((8 if corner else 16) * self.scale)
        text_width = rl.measure_text(text, font_size)
        box_w = text_width + pad * 2
        box_h = font_size + pad * 2
        if corner:
            box_x = self.origin_x + self.game_width - box_w
            box_y = self.origin_y
        else:
            box_x = (self.window_width - box_w) // 2
            box_y = (self.window_height - box_h) // 2
        rl.draw_rectangle_rounded(
            rl.Rectangle(box_x, box_y, box_w, box_h), 0.3, 8, rl.Color(0, 0, 0, 160)
        )
        rl.draw_text(text, box_x + pad, box_y + pad, font_size, self.WHITE)

    def _draw_game_over(self, state):
        """Draw game over overlay"""
        # Semi-transparent overlay
        rl.draw_rectangle(
            0, 0, self.window_width, self.window_height, rl.Color(0, 0, 0, 150)
        )

        # Game over text
        text = "GAME OVER"
        text_width = rl.measure_text(text, 64)
        rl.draw_text(
            text,
            (self.window_width - text_width) // 2,
            self.window_height // 2 - 80,
            64,
            self.WHITE,
        )

        # Score
        score_text = f"Score: {state.snake.score}"
        score_width = rl.measure_text(score_text, 36)
        rl.draw_text(
            score_text,
            (self.window_width - score_width) // 2,
            self.window_height // 2 - 10,
            36,
            self.WHITE,
        )

        # Restart hint
        restart_text = self.game_over_hint
        restart_width = rl.measure_text(restart_text, 24)
        rl.draw_text(
            restart_text,
            (self.window_width - restart_width) // 2,
            self.window_height // 2 + 40,
            24,
            self.WHITE,
        )

        # Quit hint
        quit_text = "Press ESC quit"
        quit_width = rl.measure_text(quit_text, 20)
        rl.draw_text(
            quit_text,
            (self.window_width - quit_width) // 2,
            self.window_height // 2 + 70,
            20,
            rl.Color(200, 200, 200, 255),
        )

    def close(self):
        """Close the raylib window"""
        if self.window_initialized:
            rl.close_window()
            self.window_initialized = False

    def is_key_pressed(self, key):
        """Check if a key is pressed (for game controls)"""
        return rl.is_key_pressed(key)

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
