import tkinter as tk
import chess
import os
from search import get_best_move
from evaluate import evaluate
from PIL import Image, ImageTk

UNICODE_PIECES = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
}

PIECE_NAMES = {
    chess.PAWN: 'pawn',
    chess.KNIGHT: 'knight',
    chess.BISHOP: 'bishop',
    chess.ROOK: 'rook',
    chess.QUEEN: 'queen',
    chess.KING: 'king'
}

PIECE_IMAGES = {}

class ChessGUI:
    def __init__(self, root, mode="PvB"):
        self.root = root
        self.mode = mode
        mode_title = "Play vs Bot" if mode == "PvB" else "2 Player Local" if mode == "PvP" else "Bot vs Bot Simulation" if mode == "BvB" else "Play vs Myself"
        self.root.title(f"Abdulazizxon's Chess Engine - {mode_title}")
        
        self.board = chess.Board()
        self.selected_sq = None
        self.view_index = -1 # -1 means live
        
        self.is_dragging = False
        self.drag_x = 0
        self.drag_y = 0
        
        self.highlights = set()
        self.arrows = set()
        self.drag_start_sq = None
        
        # Mode specific variables
        self.player_color = chess.WHITE
        self.difficulty = tk.IntVar(value=4)
        self.bvb_white_depth = tk.IntVar(value=4)
        self.bvb_black_depth = tk.IntVar(value=4)
        self.bvb_running = False
        self.bvb_paused = False
        
        import json
        self.openings_db = {}
        try:
            with open(os.path.join(os.path.dirname(__file__), "data", "openings.json"), "r") as f:
                self.openings_db = json.load(f)
        except Exception as e:
            print(f"Could not load openings database: {e}")
            
        self.user_book = {}
        try:
            with open(os.path.join(os.path.dirname(__file__), "data", "user_book.json"), "r") as f:
                self.user_book = json.load(f)
        except Exception as e:
            print(f"Could not load user book: {e}")
        
        # Root layout
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.left_frame = tk.Frame(self.main_container)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.right_frame = tk.Frame(self.main_container)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        # --- LEFT FRAME (Board + Controls) ---
        self.canvas = tk.Canvas(self.left_frame, width=680, height=640)
        self.canvas.pack(side=tk.TOP)
        
        self.canvas.bind("<Button-1>", self.left_click)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.drag_release)
        self.canvas.bind("<Button-2>", self.right_click_press)
        self.canvas.bind("<Button-3>", self.right_click_press)
        self.canvas.bind("<ButtonRelease-2>", self.right_click_release)
        self.canvas.bind("<ButtonRelease-3>", self.right_click_release)
        
        self.controls = tk.Frame(self.left_frame, pady=10)
        self.controls.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.undo_btn = tk.Button(self.controls, text="Undo", command=self.undo_move, width=6)
        self.undo_btn.pack(side=tk.LEFT, padx=(2, 2))
        
        self.restart_btn = tk.Button(self.controls, text="Restart", command=self.restart_game, width=6)
        self.restart_btn.pack(side=tk.LEFT, padx=(2, 2))
        
        if self.mode in ["PvB", "PvM"]:
            self.switch_btn = tk.Button(self.controls, text="Flip Sides", command=self.switch_sides, width=8)
            self.switch_btn.pack(side=tk.LEFT, padx=(2, 10))
            tk.Label(self.controls, text="Depth:").pack(side=tk.LEFT)
            self.diff_menu = tk.OptionMenu(self.controls, self.difficulty, 1, 2, 3, 4, 5, 6, 7, 8)
            self.diff_menu.pack(side=tk.LEFT)
        elif self.mode == "PvP":
            self.switch_btn = tk.Button(self.controls, text="Flip Board", command=self.switch_sides, width=8)
            self.switch_btn.pack(side=tk.LEFT, padx=(2, 10))
        elif self.mode == "BvB":
            tk.Label(self.controls, text="W-Depth:").pack(side=tk.LEFT)
            self.w_menu = tk.OptionMenu(self.controls, self.bvb_white_depth, 1, 2, 3, 4, 5, 6, 7, 8)
            self.w_menu.pack(side=tk.LEFT)
            
            tk.Label(self.controls, text="B-Depth:").pack(side=tk.LEFT)
            self.b_menu = tk.OptionMenu(self.controls, self.bvb_black_depth, 1, 2, 3, 4, 5, 6, 7, 8)
            self.b_menu.pack(side=tk.LEFT)
            
            self.sim_btn = tk.Button(self.controls, text="Start Sim", command=self.toggle_sim, width=8)
            self.sim_btn.pack(side=tk.LEFT, padx=(10, 5))
        
        # --- RIGHT FRAME (Move History) ---
        tk.Label(self.right_frame, text="Move History", font=("Arial", 16, "bold")).pack(pady=(0, 5))
        
        self.opening_label = tk.Label(self.right_frame, text="Starting Position", font=("Arial", 12, "italic"), fg="#a0a0a0")
        self.opening_label.pack(pady=(0, 10))
        
        self.history_scroll = tk.Scrollbar(self.right_frame)
        self.history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_text = tk.Text(self.right_frame, width=22, height=35, yscrollcommand=self.history_scroll.set, state=tk.DISABLED, font=("Courier", 14), bg="#2b2b2b", fg="#d4d4d4")
        self.history_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.history_scroll.config(command=self.history_text.yview)
        
        self.nav_frame = tk.Frame(self.right_frame, bg="#2b2b2b")
        self.nav_frame.pack(fill=tk.X, pady=(5, 0), side=tk.BOTTOM)
        
        self.prev_btn = tk.Button(self.nav_frame, text="<", command=self.view_prev, width=5)
        self.prev_btn.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        
        self.nav_label = tk.Label(self.nav_frame, text="Live", fg="#d4d4d4", bg="#2b2b2b", font=("Arial", 12))
        self.nav_label.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = tk.Button(self.nav_frame, text=">", command=self.view_next, width=5)
        self.next_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=5)
        
        self.load_images()
        self.draw_board()

    def view_prev(self):
        max_idx = len(self.board.move_stack)
        if max_idx == 0: return
        
        if self.view_index == -1:
            self.view_index = max_idx - 1
        elif self.view_index > 0:
            self.view_index -= 1
        self.draw_board()

    def view_next(self):
        max_idx = len(self.board.move_stack)
        if self.view_index == -1: return
        
        if self.view_index < max_idx - 1:
            self.view_index += 1
        else:
            self.view_index = -1
        self.draw_board()

    def get_view_board(self):
        if self.view_index == -1:
            return self.board
            
        max_idx = len(self.board.move_stack)
        if self.view_index >= max_idx:
            self.view_index = -1
            return self.board
            
        temp_board = chess.Board()
        for i, move in enumerate(self.board.move_stack):
            if i >= self.view_index:
                break
            temp_board.push(move)
        return temp_board

    def toggle_sim(self):
        if not self.bvb_running:
            self.bvb_running = True
            self.bvb_paused = False
            self.sim_btn.config(text="Pause Sim")
            self.engine_move()
        else:
            self.bvb_paused = not self.bvb_paused
            if self.bvb_paused:
                self.sim_btn.config(text="Resume Sim")
            else:
                self.sim_btn.config(text="Pause Sim")
                self.engine_move()

    def load_images(self):
        img_dir = os.path.join(os.path.dirname(__file__), "images")
        if not os.path.exists(img_dir):
            return
            
        for color in [chess.WHITE, chess.BLACK]:
            color_prefix = "white" if color == chess.WHITE else "black"
            for p_type, p_name in PIECE_NAMES.items():
                filename = f"{color_prefix}-{p_name}.png"
                path = os.path.join(img_dir, filename)
                if os.path.exists(path):
                    img = Image.open(path).convert("RGBA")
                    img = img.resize((70, 70), Image.Resampling.LANCZOS)
                    PIECE_IMAGES[(color, p_type)] = ImageTk.PhotoImage(img)

    def switch_sides(self):
        self.player_color = chess.BLACK if self.player_color == chess.WHITE else chess.WHITE
        if self.mode in ["PvB", "PvM"]:
            self.restart_game()
        else:
            self.draw_board()

    def undo_move(self):
        if self.mode == "BvB":
            self.bvb_paused = True
            if self.bvb_running:
                self.sim_btn.config(text="Resume Sim")
        
        if self.mode in ["PvB", "PvM"]:
            if len(self.board.move_stack) >= 2:
                self.board.pop()
                self.board.pop()
            elif len(self.board.move_stack) == 1:
                self.board.pop()
        else:
            if len(self.board.move_stack) >= 1:
                self.board.pop()
                
        self.selected_sq = None
        self.is_dragging = False
        self.view_index = -1
        self.clear_markup()
        self.draw_board()
        
    def restart_game(self):
        self.board.reset()
        self.selected_sq = None
        self.is_dragging = False
        self.bvb_running = False
        self.bvb_paused = False
        self.view_index = -1
        if self.mode == "BvB":
            self.sim_btn.config(text="Start Sim")
            
        self.clear_markup()
        self.draw_board()
        if self.mode in ["PvB", "PvM"] and self.player_color == chess.BLACK:
            self.root.after(50, self.engine_move)
        
    def clear_markup(self):
        self.highlights.clear()
        self.arrows.clear()

    def get_square_from_grid(self, c, r):
        if self.player_color == chess.BLACK:
            return chess.square(7 - c, r)
        else:
            return chess.square(c, 7 - r)

    def get_square_from_event(self, event):
        c = event.x // 80
        r = event.y // 80
        if c > 7 or r > 7: 
            return None
        return self.get_square_from_grid(c, r)

    def right_click_press(self, event):
        sq = self.get_square_from_event(event)
        if sq is not None:
            self.drag_start_sq = sq

    def right_click_release(self, event):
        sq = self.get_square_from_event(event)
        if sq is not None and self.drag_start_sq is not None:
            if sq == self.drag_start_sq:
                if sq in self.highlights:
                    self.highlights.remove(sq)
                else:
                    self.highlights.add(sq)
            else:
                arrow = (self.drag_start_sq, sq)
                if arrow in self.arrows:
                    self.arrows.remove(arrow)
                else:
                    self.arrows.add(arrow)
        self.drag_start_sq = None
        self.draw_board()

    def left_click(self, event):
        if self.mode == "BvB":
            return
            
        if self.view_index != -1:
            return # Cannot drag while viewing history
            
        self.clear_markup()
        
        if self.mode in ["PvB", "PvM"]:
            if self.board.turn != self.player_color or self.board.is_game_over(claim_draw=True):
                self.draw_board()
                return
                
        if self.board.is_game_over(claim_draw=True):
            self.draw_board()
            return
            
        sq = self.get_square_from_event(event)
        if sq is None: 
            self.draw_board()
            return
        
        color_to_move = self.board.turn
        if self.board.piece_at(sq) and self.board.color_at(sq) == color_to_move:
            self.selected_sq = sq
            self.is_dragging = True
            self.drag_x = event.x
            self.drag_y = event.y
        else:
            if self.selected_sq is not None:
                self.attempt_move(self.selected_sq, sq)
            else:
                self.selected_sq = None
        self.draw_board()

    def drag_motion(self, event):
        if self.is_dragging and self.selected_sq is not None:
            self.drag_x = event.x
            self.drag_y = event.y
            self.draw_board()

    def drag_release(self, event):
        if not self.is_dragging: 
            return
        self.is_dragging = False
        
        sq = self.get_square_from_event(event)
        if sq is not None and sq != self.selected_sq:
            self.attempt_move(self.selected_sq, sq)
        self.draw_board()

    def attempt_move(self, from_sq, to_sq):
        move = chess.Move(from_sq, to_sq)
        if self.board.piece_at(from_sq) and self.board.piece_at(from_sq).piece_type == chess.PAWN:
            if chess.square_rank(to_sq) == 7 and self.board.turn == chess.WHITE: 
                move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
            elif chess.square_rank(to_sq) == 0 and self.board.turn == chess.BLACK:
                move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
                
        if move in self.board.legal_moves:
            self.board.push(move)
            self.selected_sq = None
            self.view_index = -1
            self.draw_board()
            self.root.update()
            
            if not self.board.is_game_over(claim_draw=True):
                if self.mode in ["PvB", "PvM"]:
                    self.root.after(50, self.engine_move)
            return True
        return False

    def engine_move(self):
        if self.board.is_game_over(claim_draw=True):
            self.bvb_running = False
            if self.mode == "BvB": self.sim_btn.config(text="Start Sim", state=tk.NORMAL)
            self.draw_board()
            return
            
        if self.mode == "BvB" and self.bvb_paused:
            self.sim_btn.config(state=tk.NORMAL)
            return
            
        if self.mode == "PvP":
            return
            
        if self.mode == "BvB":
            depth = self.bvb_white_depth.get() if self.board.turn == chess.WHITE else self.bvb_black_depth.get()
            self.sim_btn.config(state=tk.DISABLED)
            self.w_menu.config(state=tk.DISABLED)
            self.b_menu.config(state=tk.DISABLED)
        else:
            depth = self.difficulty.get()
            self.switch_btn.config(state=tk.DISABLED)
            self.diff_menu.config(state=tk.DISABLED)
            
        self.undo_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.root.update()
        
        import time
        start_time = time.time()
        
        move = None
        if self.mode == "PvM":
            epd = self.board.epd()
            if epd in self.user_book:
                import random
                rand_val = random.random()
                cumulative = 0
                for uci, prob in self.user_book[epd].items():
                    cumulative += prob
                    if rand_val <= cumulative:
                        move = chess.Move.from_uci(uci)
                        break
                        
        if not move:
            move = get_best_move(self.board, depth=depth)
            
        calc_time = time.time() - start_time
        
        delay_ms = 0
        if self.mode == "BvB":
            if calc_time < 0.5:
                delay_ms = int((0.5 - calc_time) * 1000)
                
        if delay_ms > 0:
            self.root.after(delay_ms, lambda: self.finish_engine_move(move))
        else:
            self.finish_engine_move(move)

    def finish_engine_move(self, move):
        if move and move in self.board.legal_moves:
            self.board.push(move)
        elif move:
            return # Ignore if a race condition fed an illegal move
            
        self.undo_btn.config(state=tk.NORMAL)
        self.restart_btn.config(state=tk.NORMAL)
        
        if self.mode == "BvB":
            self.sim_btn.config(state=tk.NORMAL)
            self.w_menu.config(state=tk.NORMAL)
            self.b_menu.config(state=tk.NORMAL)
        elif self.mode in ["PvB", "PvM"]:
            self.switch_btn.config(state=tk.NORMAL)
            self.diff_menu.config(state=tk.NORMAL)
            
        self.draw_board()
        if self.board.is_game_over(claim_draw=True):
            self.bvb_running = False
            if self.mode == "BvB": self.sim_btn.config(text="Start Sim")
            result = self.board.result(claim_draw=True)
            print("Game Over:", result)
        else:
            if self.mode == "BvB" and not self.bvb_paused:
                self.root.after(50, self.engine_move)

    def update_move_history(self):
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        
        temp_board = chess.Board()
        move_text = ""
        
        for i, move in enumerate(self.board.move_stack):
            san = temp_board.san(move)
            temp_board.push(move)
            
            if i % 2 == 0:
                move_text += f"{(i // 2) + 1}. {san:<7}"
            else:
                move_text += f"{san}\n"
                
        self.history_text.insert(tk.END, move_text)
        self.history_text.config(state=tk.DISABLED)
        
        if self.view_index == -1:
            self.history_text.see(tk.END)

    def get_opening_name(self):
        temp = chess.Board()
        last_known = "Starting Position"
        if temp.epd() in self.openings_db:
            last_known = self.openings_db[temp.epd()]
            
        limit = len(self.board.move_stack) if self.view_index == -1 else self.view_index
        for i, move in enumerate(self.board.move_stack):
            if i >= limit:
                break
            temp.push(move)
            epd = temp.epd()
            if epd in self.openings_db:
                last_known = self.openings_db[epd]
                
        return last_known

    def draw_board(self):
        self.canvas.delete("all")
        view_board = self.get_view_board()
        
        opening_name = self.get_opening_name()
        self.opening_label.config(text=opening_name)
        
        if self.view_index == -1:
            self.nav_label.config(text="Live")
        else:
            self.nav_label.config(text=f"Move {self.view_index} / {len(self.board.move_stack)}")
            
        colors = ["#eeeed2", "#769656"]
        highlight_colors = ["#eb6150", "#ca3d30"]
        select_colors = ["#f6f669", "#baca44"]
        
        for r in range(8):
            for c in range(8):
                sq = self.get_square_from_grid(c, r)
                color_idx = (r + c) % 2
                color = colors[color_idx]
                
                x0, y0 = c * 80, r * 80
                x1, y1 = x0 + 80, y0 + 80
                
                if self.selected_sq == sq:
                    color = select_colors[color_idx]
                elif sq in self.highlights:
                    color = highlight_colors[color_idx]
                    
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
                
                text_color = colors[1 - color_idx]
                if c == 0:
                    rank_text = str(r + 1) if self.player_color == chess.BLACK else str(8 - r)
                    self.canvas.create_text(x0 + 8, y0 + 12, text=rank_text, fill=text_color, font=("Arial", 11, "bold"))
                if r == 7:
                    file_text = chr(ord('h') - c) if self.player_color == chess.BLACK else chr(ord('a') + c)
                    self.canvas.create_text(x0 + 70, y0 + 68, text=file_text, fill=text_color, font=("Arial", 11, "bold"))
                
        dragged_piece = None
        for r in range(8):
            for c in range(8):
                sq = self.get_square_from_grid(c, r)
                x0, y0 = c * 80, r * 80
                
                piece = view_board.piece_at(sq)
                if piece:
                    if self.is_dragging and sq == self.selected_sq and self.view_index == -1:
                        dragged_piece = piece
                        continue
                        
                    img = PIECE_IMAGES.get((piece.color, piece.piece_type))
                    if img:
                        self.canvas.create_image(x0 + 40, y0 + 40, image=img)
                    else:
                        char = UNICODE_PIECES[piece.symbol()]
                        self.canvas.create_text(x0 + 40, y0 + 40, text=char, font=("Arial", 60), fill="black")

        if self.selected_sq is not None and self.view_index == -1:
            for move in view_board.legal_moves:
                if move.from_square == self.selected_sq:
                    to_sq = move.to_square
                    if self.player_color == chess.BLACK:
                        c, r = 7 - chess.square_file(to_sq), chess.square_rank(to_sq)
                    else:
                        c, r = chess.square_file(to_sq), 7 - chess.square_rank(to_sq)
                    x = c * 80 + 40
                    y = r * 80 + 40
                    
                    if view_board.piece_at(to_sq):
                        self.canvas.create_oval(x-35, y-35, x+35, y+35, outline="#888888", width=5)
                    else:
                        self.canvas.create_oval(x-12, y-12, x+12, y+12, fill="#888888", outline="")

        for start_sq, end_sq in self.arrows:
            if self.player_color == chess.BLACK:
                c1, r1 = 7 - chess.square_file(start_sq), chess.square_rank(start_sq)
                c2, r2 = 7 - chess.square_file(end_sq), chess.square_rank(end_sq)
            else:
                c1, r1 = chess.square_file(start_sq), 7 - chess.square_rank(start_sq)
                c2, r2 = chess.square_file(end_sq), 7 - chess.square_rank(end_sq)
                
            x1, y1 = c1 * 80 + 40, r1 * 80 + 40
            x2, y2 = c2 * 80 + 40, r2 * 80 + 40
            self.canvas.create_line(x1, y1, x2, y2, fill="#ffaa00", width=6, arrow=tk.LAST, arrowshape=(16, 20, 6))
                    
        white_score = evaluate(view_board) if view_board.turn == chess.WHITE else -evaluate(view_board)
        
        if white_score > 90000:
            display_score = "M"
            clamped = 1000
        elif white_score < -90000:
            display_score = "-M"
            clamped = -1000
        else:
            display_score = f"{abs(white_score)/100:.1f}"
            clamped = max(-1000, min(1000, white_score))
            
        if self.player_color == chess.BLACK:
            top_fill, bottom_fill = "#f0f0f0", "#333333"
            top_text, bottom_text = "white", "black"
            split_y = 320 + (clamped / 1000) * 320
        else:
            top_fill, bottom_fill = "#333333", "#f0f0f0"
            top_text, bottom_text = "white", "black"
            split_y = 320 - (clamped / 1000) * 320
        
        self.canvas.create_rectangle(640, 0, 680, split_y, fill=top_fill, outline="")
        self.canvas.create_rectangle(640, split_y, 680, 640, fill=bottom_fill, outline="")
        self.canvas.create_rectangle(640, 0, 680, 640, outline="gray")
        
        if display_score == "M":
            self.canvas.create_text(660, 620, text="M", fill=bottom_text, font=("Arial", 12, "bold"))
        elif display_score == "-M":
            self.canvas.create_text(660, 20, text="M", fill=top_text, font=("Arial", 12, "bold"))
        else:
            if white_score > 0:
                y_pos = 620 if self.player_color == chess.WHITE else 20
                color = bottom_text if self.player_color == chess.WHITE else top_text
                self.canvas.create_text(660, y_pos, text=f"+{display_score}", fill=color, font=("Arial", 10, "bold"))
            elif white_score < 0:
                y_pos = 20 if self.player_color == chess.WHITE else 620
                color = top_text if self.player_color == chess.WHITE else bottom_text
                self.canvas.create_text(660, y_pos, text=f"-{display_score}", fill=color, font=("Arial", 10, "bold"))
            else:
                self.canvas.create_text(660, 320, text="0.0", fill="gray", font=("Arial", 10, "bold"))
                
        if dragged_piece:
            img = PIECE_IMAGES.get((dragged_piece.color, dragged_piece.piece_type))
            if img:
                self.canvas.create_image(self.drag_x, self.drag_y, image=img)
            else:
                char = UNICODE_PIECES[dragged_piece.symbol()]
                self.canvas.create_text(self.drag_x, self.drag_y, text=char, font=("Arial", 60), fill="black")
                
        if self.board.is_game_over(claim_draw=True) and self.view_index == -1:
            result = self.board.result(claim_draw=True)
            text = "DRAW"
            if result == "1-0":
                text = "WHITE WINS"
            elif result == "0-1":
                text = "BLACK WINS"
            self.canvas.create_rectangle(140, 280, 500, 360, fill="#2b2b2b", outline="gray", width=3)
            self.canvas.create_text(320, 320, text=text, font=("Arial", 36, "bold"), fill="#d4d4d4")
                
        self.update_move_history()


app_state = {"mode": None}

class StartupMenu:
    def __init__(self, r):
        self.r = r
        self.r.title("Chess Engine Menu")
        self.r.geometry("400x500")
        tk.Label(r, text="Select Game Mode", font=("Arial", 24, "bold")).pack(pady=40)
        tk.Button(r, text="Play vs Bot", font=("Arial", 16), width=20, height=2, command=lambda: self.launch("PvB")).pack(pady=10)
        tk.Button(r, text="Play vs Myself", font=("Arial", 16), width=20, height=2, command=lambda: self.launch("PvM")).pack(pady=10)
        tk.Button(r, text="2 Player Local", font=("Arial", 16), width=20, height=2, command=lambda: self.launch("PvP")).pack(pady=10)
        tk.Button(r, text="Bot vs Bot Simulation", font=("Arial", 16), width=20, height=2, command=lambda: self.launch("BvB")).pack(pady=10)
        
    def launch(self, mode):
        app_state["mode"] = mode
        self.r.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    menu = StartupMenu(root)
    root.mainloop()
    
    if app_state["mode"] is not None:
        game_root = tk.Tk()
        game_root.lift()
        game_root.attributes('-topmost', True)
        game_root.after_idle(game_root.attributes, '-topmost', False)
        gui = ChessGUI(game_root, mode=app_state["mode"])
        game_root.mainloop()
