import pyray as rl

class Visualiser:
    def __init__(self, game, fps=5):
        self.game = game
        self.cell_size = 30
        self.fps = fps
        
        # Suppress Raylib console output
        rl.set_trace_log_level(rl.LOG_NONE)
        
        # Calculate window dimensions
        self.window_width = game.width * self.cell_size
        self.window_height = game.height * self.cell_size + 60  # Extra space for score
        
        # Initialize window
        rl.init_window(self.window_width, self.window_height, "Snake AI - Watch Your Code Play!")
        rl.set_target_fps(fps)
        
        # Define colors
        self.BLACK = rl.BLACK
        self.WHITE = rl.WHITE
        self.GREEN = rl.GREEN
        self.DARK_GREEN = rl.Color(0, 180, 0, 255)
        self.RED = rl.RED
        self.GRAY = rl.GRAY
        self.DARK_GRAY = rl.Color(64, 64, 64, 255)
        self.YELLOW = rl.YELLOW
    
    def is_running(self):
        return not rl.window_should_close()
    
    def update(self):
        rl.begin_drawing()
        rl.clear_background(self.BLACK)
        
        # Draw grid lines (subtle)
        for x in range(self.game.width + 1):
            rl.draw_line(
                x * self.cell_size, 0,
                x * self.cell_size, self.game.height * self.cell_size,
                self.DARK_GRAY
            )
        for y in range(self.game.height + 1):
            rl.draw_line(
                0, y * self.cell_size,
                self.game.width * self.cell_size, y * self.cell_size,
                self.DARK_GRAY
            )
        
        # Draw walls
        for x, y in self.game.state.walls:
            rl.draw_rectangle(
                x * self.cell_size + 2, 
                y * self.cell_size + 2, 
                self.cell_size - 4, 
                self.cell_size - 4, 
                self.GRAY
            )
        
        # Draw food (pulsing effect)
        for x, y in self.game.state.food:
            # Draw a red circle for food
            rl.draw_circle(
                x * self.cell_size + self.cell_size // 2,
                y * self.cell_size + self.cell_size // 2,
                self.cell_size // 3,
                self.RED
            )
            # Add a smaller yellow center for visibility
            rl.draw_circle(
                x * self.cell_size + self.cell_size // 2,
                y * self.cell_size + self.cell_size // 2,
                self.cell_size // 6,
                self.YELLOW
            )
        
        # Draw snake
        for i, (x, y) in enumerate(self.game.state.snake.body):
            # Head is brighter green
            color = self.GREEN if i == 0 else self.DARK_GREEN
            
            # Draw snake segment
            rl.draw_rectangle(
                x * self.cell_size + 2,
                y * self.cell_size + 2,
                self.cell_size - 4,
                self.cell_size - 4,
                color
            )
            
            # Draw eyes on the head
            if i == 0:
                # Determine eye position based on direction
                dir_idx = self.game.state.snake.direction_idx
                eye_offset = [
                    (8, 8), (16, 8),    # Up: eyes at top
                    (20, 8), (20, 16),  # Right: eyes on right
                    (8, 20), (16, 20),  # Down: eyes at bottom
                    (8, 8), (8, 16)     # Left: eyes on left
                ][dir_idx * 2:dir_idx * 2 + 2]
                
                for ex, ey in eye_offset:
                    rl.draw_circle(
                        x * self.cell_size + ex,
                        y * self.cell_size + ey,
                        2,
                        self.WHITE
                    )
        
        # Draw info bar
        info_y = self.game.height * self.cell_size + 10
        
        # Score
        rl.draw_text(f"Score: {self.game.state.score}", 10, info_y, 24, self.WHITE)
        
        # Speed indicator
        rl.draw_text(f"Speed: {self.fps} FPS", 200, info_y, 20, self.WHITE)
        
        # Controls hint
        rl.draw_text("Close window to stop", self.window_width - 180, info_y, 16, self.GRAY)
        
        # Instructions at bottom
        rl.draw_text("Modify simple_ai.py to change the AI behavior!", 10, info_y + 30, 16, self.GRAY)
        
        # Draw game over overlay
        if self.game.state.game_over:
            # Semi-transparent overlay
            overlay_color = rl.Color(0, 0, 0, 180)
            rl.draw_rectangle(0, 0, self.window_width, self.game.height * self.cell_size, overlay_color)
            
            # Game over text
            msg = "GAME OVER!"
            msg_width = rl.measure_text(msg, 40)
            msg_x = (self.window_width - msg_width) // 2
            msg_y = (self.game.height * self.cell_size) // 2 - 40
            rl.draw_text(msg, msg_x, msg_y, 40, self.RED)
            
            # Final score
            score_msg = f"Final Score: {self.game.state.score}"
            score_width = rl.measure_text(score_msg, 24)
            score_x = (self.window_width - score_width) // 2
            rl.draw_text(score_msg, score_x, msg_y + 50, 24, self.WHITE)
            
            # Restart hint
            hint = "Close window and run again"
            hint_width = rl.measure_text(hint, 16)
            hint_x = (self.window_width - hint_width) // 2
            rl.draw_text(hint, hint_x, msg_y + 80, 16, self.GRAY)
        
        rl.end_drawing()
    
    def close(self):
        rl.close_window()
    
    def set_fps(self, fps):
        self.fps = fps
        rl.set_target_fps(fps)