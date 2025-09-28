# Simplified visualizer with smooth motion via path sampling
# Controller is mandatory - visualizer always manages game logic

import pyray as rl
import math
from collections import deque

class Visualiser:
    def __init__(self, game, controller, logic_fps=5, render_fps=60):
        """
        game: SnakeGame instance (must expose .width, .height, .state with snake/food/walls/score/game_over)
        controller: callable () -> Turn that supplies the next move each logic tick
        logic_fps: moves per second
        render_fps: target render frame rate
        """
        self.game = game
        self.controller = controller
        
        # Timing
        self.logic_fps = max(1e-6, float(logic_fps))
        self.render_fps = int(render_fps)
        self.tick = 1.0 / self.logic_fps
        self.accum = 0.0
        self.time = 0.0
        
        # Grid rendering
        self.cell_size = 40
        self.padding = 20
        self.game_width = game.width * self.cell_size
        self.game_height = game.height * self.cell_size
        self.window_width = self.game_width + (self.padding * 2)
        self.window_height = self.game_height + (self.padding * 2)
        
        # Interpolation state
        self.prev_body = deque(self._current_body())
        
        # Slider state (positioned top right)
        self.slider_x = self.window_width - 150
        self.slider_y = 35
        self.slider_width = 100
        self.slider_min_fps = 1
        self.slider_max_fps = 30
        self.slider_dragging = False
        self.slider_pos = (logic_fps - self.slider_min_fps) / (self.slider_max_fps - self.slider_min_fps)
        
        # Raylib init
        rl.set_trace_log_level(rl.LOG_NONE)
        rl.init_window(self.window_width, self.window_height, "WAI Snake Comp")
        rl.set_target_fps(self.render_fps)
        
        # Colors (Exact Google Snake theme)
        self.BG_BOARD = rl.Color(170, 215, 81, 255)  # Light green board
        self.BG_FRAME = rl.Color(87, 138, 52, 255)   # Dark green frame
        self.CHECKER_LIGHT = rl.Color(162, 209, 73, 255)  # Lighter checker
        self.SNAKE_COLOR = rl.Color(58, 103, 240, 255)  # Google blue snake
        self.APPLE_RED = rl.Color(231, 71, 71, 255)  # Bright red apple
        self.APPLE_GREEN = rl.Color(100, 180, 50, 255)  # Green leaf
        self.WHITE = rl.WHITE
        self.BLACK = rl.BLACK
        self.WALL_COLOR = rl.Color(87, 138, 52, 255)  # Dark green walls
        self.SLIDER_BLUE = rl.Color(58, 103, 240, 255)  # Match snake blue
        self.SLIDER_TRACK = rl.Color(200, 200, 200, 150)

    def is_running(self):
        return not rl.window_should_close()

    def update(self):
        dt = rl.get_frame_time()
        self.time += dt * 60.0
        
        # Handle slider
        self._handle_slider()
        
        # Step logic and get interpolation factor
        alpha = self._advance_logic(dt)
        
        # Render
        self._render(alpha)

    def close(self):
        rl.close_window()

    def set_logic_fps(self, fps):
        self.logic_fps = max(1e-6, float(fps))
        self.tick = 1.0 / self.logic_fps
        self.slider_pos = (fps - self.slider_min_fps) / (self.slider_max_fps - self.slider_min_fps)

    # ---- Private methods ----

    def _current_body(self):
        return [tuple(p) for p in self.game.state.snake.body]

    def _advance_logic(self, dt):
        """Step logic at fixed rate, return interpolation alpha"""
        self.accum += dt
        
        while self.accum >= self.tick and not self.game.state.game_over:
            self.prev_body = deque(self._current_body())
            turn = self.controller()
            self.game.move(turn)
            self.accum -= self.tick
        
        return max(0.0, min(1.0, self.accum / self.tick))

    def _render(self, alpha):
        rl.begin_drawing()
        
        # Dark green frame background
        rl.clear_background(self.BG_FRAME)
        
        # Light green game board
        rl.draw_rectangle(self.padding, self.padding, self.game_width, self.game_height, self.BG_BOARD)
        
        # Subtle checkerboard
        for x in range(self.game.width):
            for y in range(self.game.height):
                if (x + y) % 2 == 0:
                    rl.draw_rectangle(
                        self.padding + x * self.cell_size,
                        self.padding + y * self.cell_size,
                        self.cell_size, self.cell_size,
                        self.CHECKER_LIGHT
                    )
        
        # Walls (simple dark green squares)
        for x, y in self.game.state.walls:
            wall_x = self.padding + x * self.cell_size
            wall_y = self.padding + y * self.cell_size
            rl.draw_rectangle(wall_x, wall_y, self.cell_size, self.cell_size, self.WALL_COLOR)
        
        # Food
        for fx, fy in self.game.state.food:
            self._draw_apple(fx, fy)
        
        # Snake with smooth interpolation
        self._draw_snake(alpha)
        
        # UI (Google Snake style with icons)
        # Apple icon and count
        rl.draw_circle(40, 35, 12, self.APPLE_RED)
        rl.draw_circle(37, 32, 4, rl.Color(255, 180, 180, 255))  # highlight
        rl.draw_rectangle(38, 22, 3, 6, rl.Color(139, 69, 19, 255))  # stem
        rl.draw_text(f"{self.game.state.score}", 60, 25, 28, self.WHITE)
        
        # Snake icon and length
        rl.draw_rectangle_rounded(rl.Rectangle(120, 27, 30, 16), 0.5, 8, self.SNAKE_COLOR)
        rl.draw_circle(122, 35, 8, self.SNAKE_COLOR)  # head
        rl.draw_text(f"{len(self.game.state.snake.body)}", 160, 25, 28, self.WHITE)
        
        # Speed slider (far right)
        self._draw_slider()
        
        # Game over overlay
        if self.game.state.game_over:
            rl.draw_rectangle(0, 0, self.window_width, self.window_height, rl.Color(0, 0, 0, 150))
            
            # Simple centered text
            text = "GAME OVER"
            text_width = rl.measure_text(text, 64)
            rl.draw_text(text, (self.window_width - text_width) // 2, 
                        self.window_height // 2 - 50, 64, self.WHITE)
            
            score_text = f"Score: {self.game.state.score}"
            score_width = rl.measure_text(score_text, 36)
            rl.draw_text(score_text, (self.window_width - score_width) // 2, 
                        self.window_height // 2 + 20, 36, self.WHITE)
        
        rl.end_drawing()

    def _draw_snake(self, alpha):
        """Draw snake with smooth interpolation"""
        curr_body = self._current_body()
        prev_body = list(self.prev_body) if self.prev_body else curr_body
        
        # Build path: current head + previous body
        if not curr_body:
            return
        
        # Pad prev_body if snake grew
        if len(prev_body) < len(curr_body):
            tail = prev_body[-1] if prev_body else curr_body[0]
            prev_body = prev_body + [tail] * (len(curr_body) - len(prev_body))
        
        # Convert to pixel centers
        path = [curr_body[0]] + prev_body
        path_pts = [(self.padding + x * self.cell_size + self.cell_size / 2,
                     self.padding + y * self.cell_size + self.cell_size / 2) 
                    for x, y in path]
        
        # Get head direction for eyes
        head_pos = self._sample_path(path_pts, 0.0)
        ahead_pos = self._sample_path(path_pts, 0.25)
        head_dir = self._direction(head_pos, ahead_pos)
        
        # Draw segments from tail to head
        n = len(curr_body)
        for i in range(n - 1, -1, -1):
            s = i + (1.0 - alpha)
            cx, cy = self._sample_path(path_pts, s)
            is_head = (i == 0)
            is_tail = (i == n - 1)
            self._draw_segment(cx, cy, is_head, head_dir if is_head else None, is_tail)

    def _sample_path(self, path_pts, s):
        """Sample point at distance s along path"""
        if not path_pts:
            return 0.0, 0.0
        
        max_s = len(path_pts) - 1
        if s <= 0:
            return path_pts[0]
        if s >= max_s:
            return path_pts[-1]
        
        i = int(s)
        f = s - i
        x0, y0 = path_pts[i]
        x1, y1 = path_pts[i + 1]
        return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f

    def _direction(self, p0, p1):
        """Get direction from two points (0=UP, 1=RIGHT, 2=DOWN, 3=LEFT)"""
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        if abs(dx) > abs(dy):
            return 1 if dx > 0 else 3
        else:
            return 2 if dy > 0 else 0

    def _draw_segment(self, cx, cy, is_head, direction, is_tail):
        """Draw a snake segment"""
        size = self.cell_size - 8
        x = int(cx - size / 2)
        y = int(cy - size / 2)
        
        # All segments same color, just different roundness
        if is_head:
            rl.draw_rectangle_rounded(
                rl.Rectangle(x, y, size, size), 0.5, 8, self.SNAKE_COLOR
            )
            
            # Simple white eyes
            eye_size = 6
            pupil_size = 3
            if direction == 0:  # Up
                eye1_x, eye1_y = x + size // 3, y + size // 3
                eye2_x, eye2_y = x + 2 * size // 3, y + size // 3
            elif direction == 1:  # Right
                eye1_x, eye1_y = x + 2 * size // 3, y + size // 3
                eye2_x, eye2_y = x + 2 * size // 3, y + 2 * size // 3
            elif direction == 2:  # Down
                eye1_x, eye1_y = x + size // 3, y + 2 * size // 3
                eye2_x, eye2_y = x + 2 * size // 3, y + 2 * size // 3
            else:  # Left
                eye1_x, eye1_y = x + size // 3, y + size // 3
                eye2_x, eye2_y = x + size // 3, y + 2 * size // 3
            
            rl.draw_circle(eye1_x, eye1_y, eye_size, self.WHITE)
            rl.draw_circle(eye2_x, eye2_y, eye_size, self.WHITE)
            rl.draw_circle(eye1_x, eye1_y, pupil_size, self.BLACK)
            rl.draw_circle(eye2_x, eye2_y, pupil_size, self.BLACK)
        else:
            roundness = 0.4 if is_tail else 0.3
            rl.draw_rectangle_rounded(
                rl.Rectangle(x, y, size, size), roundness, 8, self.SNAKE_COLOR
            )

    def _draw_apple(self, x, y):
        """Draw a simple apple"""
        cx = self.padding + x * self.cell_size + self.cell_size // 2
        cy = self.padding + y * self.cell_size + self.cell_size // 2
        
        radius = self.cell_size // 3
        
        # Apple
        rl.draw_circle(cx, cy, radius, self.APPLE_RED)
        # Small highlight
        rl.draw_circle(cx - 5, cy - 5, radius // 3, rl.Color(255, 180, 180, 255))
        # Simple stem
        rl.draw_rectangle(cx - 1, cy - radius - 5, 3, 6, rl.Color(139, 69, 19, 255))
        # Simple leaf (triangle)
        rl.draw_triangle(
            rl.Vector2(float(cx + 2), float(cy - radius - 2)),
            rl.Vector2(float(cx + 8), float(cy - radius - 4)),
            rl.Vector2(float(cx + 6), float(cy - radius + 2)),
            self.APPLE_GREEN
        )

    def _handle_slider(self):
        """Handle slider interaction"""
        mouse_x = rl.get_mouse_x()
        mouse_y = rl.get_mouse_y()
        
        handle_x = self.slider_x + int(self.slider_pos * self.slider_width)
        handle_radius = 8
        
        # Check if mouse over handle
        dist = math.sqrt((mouse_x - handle_x)**2 + (mouse_y - self.slider_y)**2)
        mouse_over = dist <= handle_radius + 2
        
        if rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT) and mouse_over:
            self.slider_dragging = True
        
        if rl.is_mouse_button_released(rl.MOUSE_BUTTON_LEFT):
            self.slider_dragging = False
        
        if self.slider_dragging:
            new_pos = max(0, min(1, (mouse_x - self.slider_x) / self.slider_width))
            if abs(new_pos - self.slider_pos) > 0.001:
                self.slider_pos = new_pos
                new_fps = self.slider_min_fps + new_pos * (self.slider_max_fps - self.slider_min_fps)
                self.set_logic_fps(new_fps)

    def _draw_slider(self):
        """Draw a simple blue speed slider"""
        # Slider track (thicker)
        rl.draw_rectangle_rounded(
            rl.Rectangle(self.slider_x, self.slider_y - 3, self.slider_width, 6),
            1.0, 8, self.SLIDER_TRACK
        )
        
        # Blue fill (thicker)
        fill_width = int(self.slider_pos * self.slider_width)
        if fill_width > 0:
            rl.draw_rectangle_rounded(
                rl.Rectangle(self.slider_x, self.slider_y - 3, fill_width, 6),
                1.0, 8, self.SLIDER_BLUE
            )
        
        # Handle (simple white circle)
        handle_x = self.slider_x + int(self.slider_pos * self.slider_width)
        handle_radius = 8 if not self.slider_dragging else 10
        
        rl.draw_circle(handle_x, self.slider_y, handle_radius, self.WHITE)