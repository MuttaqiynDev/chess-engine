import tkinter as tk
import chess
import os
import time
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
    def __init__(self, root, mode="PvB", **kwargs):
        self.root = root
        self.mode = mode
        self.kwargs = kwargs
        try:
            self.root.title("AuraChess")
        except AttributeError:
            pass # Embedded in a CTKFrame
        
        self.board = chess.Board()
        if self.mode == "Trainer":
            epd = kwargs.get("epd", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -")
            self.board.set_epd(epd)
            self.correct_move = kwargs.get("correct_move", "")
            self.user_move = kwargs.get("user_move", "")
            self.on_next = kwargs.get("on_next", None)
            
        self.selected_sq = None
        self.view_index = -1 # -1 means live
        
        self.is_dragging = False
        self.drag_x = 0
        self.drag_y = 0
        
        self.highlights = set()
        self.arrows = set()
        self.drag_start_sq = None
        
        # Mode specific variables
        self.player_color = self.board.turn if self.mode == "Trainer" else chess.WHITE
        self.difficulty = tk.IntVar(value=4)
        self.bvb_white_depth = tk.IntVar(value=3)
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
        self.canvas = tk.Canvas(self.left_frame, width=680, height=640, bg="#d4d4d4", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, pady=20)
        
        self.canvas.bind("<Button-1>", self.left_click)
        self.canvas.bind("<B1-Motion>", self.drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.drag_release)
        self.canvas.bind("<Button-2>", self.right_click_press)
        self.canvas.bind("<Button-3>", self.right_click_press)
        self.canvas.bind("<ButtonRelease-2>", self.right_click_release)
        self.canvas.bind("<ButtonRelease-3>", self.right_click_release)
        
        self.controls = tk.Frame(self.left_frame, pady=10)
        self.controls.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.home_btn = tk.Button(self.controls, text="Home", command=self.go_home, width=5)
        self.home_btn.pack(side=tk.LEFT, padx=(2, 2))
        
        self.undo_btn = tk.Button(self.controls, text="Undo", command=self.undo_move, width=5)
        self.undo_btn.pack(side=tk.LEFT, padx=(2, 2))
        
        self.hint_btn = tk.Button(self.controls, text="Hint", command=self.show_hint, width=4)
        self.hint_btn.pack(side=tk.LEFT, padx=(2, 2))
        
        self.export_btn = tk.Button(self.controls, text="Export", command=self.export_pgn, width=5)
        self.export_btn.pack(side=tk.LEFT, padx=(2, 2))
        
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
            
        self.coach_enabled = tk.BooleanVar(value=False)
        self.coach_check = tk.Checkbutton(self.controls, text="Aura Coach", variable=self.coach_enabled, font=("Arial", 12, "bold"), fg="#ff4757")
        self.coach_check.pack(side=tk.LEFT, padx=(10, 5))
        
        # --- RIGHT FRAME (Move History) ---
        self.top_clock_lbl = tk.Label(self.right_frame, text="10:00", font=("Helvetica", 36, "bold"), bg="#1a1a1a", fg="white", pady=10)
        self.top_clock_lbl.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        tk.Label(self.right_frame, text="Move History", font=("Arial", 16, "bold"), bg="#2b2b2b", fg="white").pack(pady=(0, 5))
        
        self.opening_label = tk.Label(self.right_frame, text="Starting Position", font=("Arial", 12, "italic"), fg="#a0a0a0")
        self.opening_label.pack(pady=(0, 10))
        
        self.history_scroll = tk.Scrollbar(self.right_frame)
        self.history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_text = tk.Text(self.right_frame, width=22, height=35, yscrollcommand=self.history_scroll.set, state=tk.DISABLED, font=("Courier", 14), bg="#2b2b2b", fg="#d4d4d4")
        self.history_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.history_scroll.config(command=self.history_text.yview)
        
        self.nav_frame = tk.Frame(self.right_frame, bg="#2b2b2b")
        self.nav_frame.pack(fill=tk.X, pady=(5, 0), side=tk.BOTTOM)
        
        self.bottom_clock_lbl = tk.Label(self.right_frame, text="10:00", font=("Helvetica", 36, "bold"), bg="#1a1a1a", fg="white", pady=10)
        self.bottom_clock_lbl.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        self.white_time = 600.0
        self.black_time = 600.0
        self.clock_running = False
        self.last_time = time.time()
        if self.mode != "Trainer":
            self.update_clock()
        
        self.prev_btn = tk.Button(self.nav_frame, text="<", command=self.view_prev, width=5)
        self.prev_btn.pack(side=tk.LEFT, padx=(10, 5), pady=5)
        
        self.nav_label = tk.Label(self.nav_frame, text="Live", fg="#d4d4d4", bg="#2b2b2b", font=("Arial", 12))
        self.nav_label.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = tk.Button(self.nav_frame, text=">", command=self.view_next, width=5)
        self.next_btn.pack(side=tk.RIGHT, padx=(5, 10), pady=5)
        
        self.load_images()
        self.draw_board()

    def go_home(self):
        self.bvb_running = False
        if hasattr(self.root.master, "show_dashboard"):
            self.root.master.show_dashboard()
        else:
            self.root.destroy()
            
    def show_hint(self):
        if getattr(self, "engine_thinking", False) or self.board.is_game_over(claim_draw=True): 
            return
            
        def calc():
            from search import get_best_move
            move = get_best_move(self.board.copy(), depth=4)
            if move:
                self.root.after(0, lambda: self.draw_arrow(move))
                
        import threading
        threading.Thread(target=calc, daemon=True).start()

    def draw_arrow(self, move):
        self.canvas.delete("hint_arrow")
        if not move: return
        
        sq_size = 80
        f_col = chess.square_file(move.from_square)
        f_row = 7 - chess.square_rank(move.from_square)
        t_col = chess.square_file(move.to_square)
        t_row = 7 - chess.square_rank(move.to_square)
        
        if self.player_color == chess.BLACK:
            f_col, f_row = 7 - f_col, 7 - f_row
            t_col, t_row = 7 - t_col, 7 - t_row
            
        x1 = f_col * sq_size + sq_size//2
        y1 = f_row * sq_size + sq_size//2
        x2 = t_col * sq_size + sq_size//2
        y2 = t_row * sq_size + sq_size//2
        
        self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, width=6, fill="#2ecc71", tags="hint_arrow")
        self.root.after(2000, lambda: self.canvas.delete("hint_arrow"))

    def export_pgn(self):
        import tkinter.filedialog as fd
        import chess.pgn
        import datetime
        
        path = fd.asksaveasfilename(defaultextension=".pgn", filetypes=[("PGN Files", "*.pgn")])
        if not path: return
        
        game = chess.pgn.Game()
        game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game.headers["White"] = "Player" if self.player_color == chess.WHITE else "Aura Engine"
        game.headers["Black"] = "Player" if self.player_color == chess.BLACK else "Aura Engine"
        
        node = game
        for move in self.board.move_stack:
            node = node.add_variation(move)
            
        with open(path, "w") as f:
            f.write(str(game))

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
        self.white_time = 600.0
        self.black_time = 600.0
        self.clock_running = False
        if hasattr(self, 'update_clock_labels'):
            self.update_clock_labels()
            
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
        self.canvas.delete("hint_arrow")
        
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
                
        legal_moves = self.board.legal_moves
        if move in legal_moves:
            if self.mode == "Trainer":
                if move.uci() == self.correct_move:
                    self.show_blunder_warning(f"Correct!\\nTheory move is {self.correct_move}")
                else:
                    self.show_blunder_warning(f"Incorrect.\\nYou played {self.user_move}\\nGM move: {self.correct_move}")
                
                if hasattr(self, 'on_next') and self.on_next:
                    self.root.after(2000, self.on_next)
                    
                self.selected_sq = None
                self.draw_board()
                return False
                
            if self.coach_enabled.get():
                from quiescence import quiescence_search
                import os
                score_before = quiescence_search(self.board, -99999, 99999)
                temp = self.board.copy()
                temp.push(move)
                score_after = -quiescence_search(temp, -99999, 99999)
                
                if score_after < score_before - 250:
                    os.system('say "Watch out, that drops material!" &')
                    self.show_blunder_warning()
                    self.selected_sq = None
                    self.draw_board()
                    return False
                    
            self.board.push(move)
            self.update_move_history()
            self.start_clock()
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
        if getattr(self, "engine_thinking", False):
            return
            
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
            if hasattr(self, "switch_btn"):
                self.switch_btn.config(state=tk.DISABLED)
            if hasattr(self, "diff_menu"):
                self.diff_menu.config(state=tk.DISABLED)
            
        self.engine_thinking = True
        self.root.update()
        
        board_copy = self.board.copy()
        target_epd = self.board.epd()
        
        def calc_thread():
            import time
            start_time = time.time()
            
            move = None
            if self.mode == "PvM":
                epd = board_copy.epd()
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
                move = get_best_move(board_copy, depth=depth)
                
            calc_time = time.time() - start_time
            
            delay_ms = 0
            if self.mode == "BvB":
                if calc_time < 0.5:
                    delay_ms = int((0.5 - calc_time) * 1000)
                    
            if delay_ms > 0:
                self.root.after(delay_ms, lambda: self.finish_engine_move(move, target_epd))
            else:
                self.root.after(0, lambda: self.finish_engine_move(move, target_epd))

        import threading
        threading.Thread(target=calc_thread, daemon=True).start()

    def finish_engine_move(self, move, target_epd):
        self.engine_thinking = False
        
        # State Validator: If board changed while thinking (e.g. undo clicked), drop the move
        if self.board.epd() != target_epd:
            return
            
        if move and move in self.board.legal_moves:
            self.board.push(move)
            self.start_clock()
            
        if self.mode == "BvB":
            self.sim_btn.config(state=tk.NORMAL)
            self.w_menu.config(state=tk.NORMAL)
            self.b_menu.config(state=tk.NORMAL)
        elif self.mode in ["PvB", "PvM"]:
            if hasattr(self, "switch_btn"):
                self.switch_btn.config(state=tk.NORMAL)
            if hasattr(self, "diff_menu"):
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




    def start_clock(self):
        if not self.clock_running and self.mode in ["PvB", "PvM", "PvP"]:
            self.clock_running = True
            self.last_time = time.time()
            
    def update_clock(self):
        if self.board.is_game_over(claim_draw=True) or not self.clock_running:
            self.root.after(100, self.update_clock)
            return
            
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        
        if self.board.turn == chess.WHITE:
            self.white_time -= dt
            if self.white_time <= 0:
                self.white_time = 0
                self.clock_running = False
                self.game_over("Black wins on time!")
        else:
            self.black_time -= dt
            if self.black_time <= 0:
                self.black_time = 0
                self.clock_running = False
                self.game_over("White wins on time!")
                
        self.update_clock_labels()
        self.root.after(100, self.update_clock)
        
    def update_clock_labels(self):
        def format_time(t):
            m = int(t) // 60
            s = int(t) % 60
            return f"{m:02d}:{s:02d}"
            
        w_text = format_time(self.white_time)
        b_text = format_time(self.black_time)
        
        if self.player_color == chess.WHITE:
            self.bottom_clock_lbl.config(text=w_text)
            self.top_clock_lbl.config(text=b_text)
        else:
            self.bottom_clock_lbl.config(text=b_text)
            self.top_clock_lbl.config(text=w_text)
            
    def show_blunder_warning(self, msg="Aura Coach:\\nBlunder Prevented!"):
        self.canvas.create_rectangle(100, 240, 540, 400, fill="#2b2b2b", outline="#ff4757", width=4, tags="blunder_warning")
        self.canvas.create_text(320, 320, text=msg, fill="#ff4757", font=("Helvetica", 24, "bold"), justify="center", tags="blunder_warning")
        
        def safe_delete():
            try:
                self.canvas.delete("blunder_warning")
            except Exception:
                pass
                
        self.root.after(2000, safe_delete)

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
    while True:
        app_state["mode"] = None
        
        root = tk.Tk()
        root.lift()
        root.attributes('-topmost', True)
        root.after_idle(root.attributes, '-topmost', False)
        menu = StartupMenu(root)
        root.mainloop()
        
        if app_state["mode"] is None:
            break
            
        game_root = tk.Tk()
        game_root.lift()
        game_root.attributes('-topmost', True)
        game_root.after_idle(game_root.attributes, '-topmost', False)
        gui = ChessGUI(game_root, mode=app_state["mode"])
        game_root.mainloop()
