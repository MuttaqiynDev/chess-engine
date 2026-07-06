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
    def __init__(self, root):
        self.root = root
        self.root.title("Abdulazizxon's Chess Engine")
        self.board = chess.Board()
        self.selected_sq = None
        
        # New State for Drag and Drop
        self.is_dragging = False
        self.drag_x = 0
        self.drag_y = 0
        
        self.highlights = set()
        self.arrows = set()
        self.drag_start_sq = None
        
        self.difficulty = tk.IntVar(value=3)
        
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
        
        self.undo_btn = tk.Button(self.controls, text="Undo", command=self.undo_move, width=10)
        self.undo_btn.pack(side=tk.LEFT, padx=20)
        
        self.restart_btn = tk.Button(self.controls, text="Restart", command=self.restart_game, width=10)
        self.restart_btn.pack(side=tk.LEFT, padx=10)
        
        tk.Label(self.controls, text="Difficulty (Depth):").pack(side=tk.LEFT, padx=(40, 5))
        self.diff_menu = tk.OptionMenu(self.controls, self.difficulty, 1, 2, 3, 4)
        self.diff_menu.pack(side=tk.LEFT)
        
        # --- RIGHT FRAME (Move History) ---
        tk.Label(self.right_frame, text="Move History", font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        self.history_scroll = tk.Scrollbar(self.right_frame)
        self.history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_text = tk.Text(self.right_frame, width=22, height=35, yscrollcommand=self.history_scroll.set, state=tk.DISABLED, font=("Courier", 14), bg="#2b2b2b", fg="#d4d4d4")
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_scroll.config(command=self.history_text.yview)
        
        self.load_images()
        self.draw_board()

    def load_images(self):
        img_dir = os.path.join(os.path.dirname(__file__), "images")
        if not os.path.exists(img_dir):
            print(f"Warning: images directory not found at {img_dir}")
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

    def undo_move(self):
        if len(self.board.move_stack) >= 2:
            self.board.pop()
            self.board.pop()
        elif len(self.board.move_stack) == 1:
            self.board.pop()
        self.selected_sq = None
        self.is_dragging = False
        self.clear_markup()
        self.draw_board()
        
    def restart_game(self):
        self.board.reset()
        self.selected_sq = None
        self.is_dragging = False
        self.clear_markup()
        self.draw_board()
        
    def clear_markup(self):
        self.highlights.clear()
        self.arrows.clear()

    def get_square_from_event(self, event):
        col = event.x // 80
        row = event.y // 80
        if col > 7 or row > 7: 
            return None
        return chess.square(col, 7 - row)

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
        self.clear_markup()
        if self.board.turn == chess.BLACK or self.board.is_game_over():
            self.draw_board()
            return
            
        sq = self.get_square_from_event(event)
        if sq is None: 
            self.draw_board()
            return
        
        if self.board.piece_at(sq) and self.board.color_at(sq) == chess.WHITE:
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
            if chess.square_rank(to_sq) == 7: 
                move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
                
        if move in self.board.legal_moves:
            self.board.push(move)
            self.selected_sq = None
            self.draw_board()
            self.root.update()
            
            if not self.board.is_game_over():
                self.root.after(50, self.engine_move)
            return True
        return False

    def engine_move(self):
        depth = self.difficulty.get()
        self.undo_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.diff_menu.config(state=tk.DISABLED)
        self.root.update()
        
        move = get_best_move(self.board, depth=depth)
        if move:
            self.board.push(move)
            
        self.undo_btn.config(state=tk.NORMAL)
        self.restart_btn.config(state=tk.NORMAL)
        self.diff_menu.config(state=tk.NORMAL)
        self.draw_board()
        if self.board.is_game_over():
            print("Game Over:", self.board.result())

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
        self.history_text.see(tk.END)

    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#eeeed2", "#769656"]
        highlight_colors = ["#eb6150", "#ca3d30"]
        select_colors = ["#f6f669", "#baca44"]
        
        for r in range(8):
            for c in range(8):
                sq = chess.square(c, 7 - r)
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
                    self.canvas.create_text(x0 + 8, y0 + 12, text=str(8 - r), fill=text_color, font=("Arial", 11, "bold"))
                if r == 7:
                    self.canvas.create_text(x0 + 70, y0 + 68, text=chr(ord('a') + c), fill=text_color, font=("Arial", 11, "bold"))
                
        dragged_piece = None
        for r in range(8):
            for c in range(8):
                sq = chess.square(c, 7 - r)
                x0, y0 = c * 80, r * 80
                
                piece = self.board.piece_at(sq)
                if piece:
                    if self.is_dragging and sq == self.selected_sq:
                        dragged_piece = piece
                        continue
                        
                    img = PIECE_IMAGES.get((piece.color, piece.piece_type))
                    if img:
                        self.canvas.create_image(x0 + 40, y0 + 40, image=img)
                    else:
                        char = UNICODE_PIECES[piece.symbol()]
                        self.canvas.create_text(x0 + 40, y0 + 40, text=char, font=("Arial", 60), fill="black")

        if self.selected_sq is not None:
            for move in self.board.legal_moves:
                if move.from_square == self.selected_sq:
                    to_sq = move.to_square
                    c = chess.square_file(to_sq)
                    r = 7 - chess.square_rank(to_sq)
                    x = c * 80 + 40
                    y = r * 80 + 40
                    
                    if self.board.piece_at(to_sq):
                        self.canvas.create_oval(x-35, y-35, x+35, y+35, outline="#888888", width=5)
                    else:
                        self.canvas.create_oval(x-12, y-12, x+12, y+12, fill="#888888", outline="")

        for start_sq, end_sq in self.arrows:
            c1, r1 = chess.square_file(start_sq), 7 - chess.square_rank(start_sq)
            c2, r2 = chess.square_file(end_sq), 7 - chess.square_rank(end_sq)
            x1, y1 = c1 * 80 + 40, r1 * 80 + 40
            x2, y2 = c2 * 80 + 40, r2 * 80 + 40
            self.canvas.create_line(x1, y1, x2, y2, fill="#ffaa00", width=6, arrow=tk.LAST, arrowshape=(16, 20, 6))
                    
        white_score = evaluate(self.board) if self.board.turn == chess.WHITE else -evaluate(self.board)
        
        if white_score > 90000:
            display_score = "M"
            clamped = 1000
        elif white_score < -90000:
            display_score = "-M"
            clamped = -1000
        else:
            display_score = f"{abs(white_score)/100:.1f}"
            clamped = max(-1000, min(1000, white_score))
            
        split_y = 320 - (clamped / 1000) * 320
        
        self.canvas.create_rectangle(640, 0, 680, split_y, fill="#333333", outline="")
        self.canvas.create_rectangle(640, split_y, 680, 640, fill="#f0f0f0", outline="")
        self.canvas.create_rectangle(640, 0, 680, 640, outline="gray")
        
        if display_score == "M":
            self.canvas.create_text(660, 620, text="M", fill="black", font=("Arial", 12, "bold"))
        elif display_score == "-M":
            self.canvas.create_text(660, 20, text="M", fill="white", font=("Arial", 12, "bold"))
        else:
            if white_score > 0:
                self.canvas.create_text(660, 620, text=f"+{display_score}", fill="black", font=("Arial", 10, "bold"))
            elif white_score < 0:
                self.canvas.create_text(660, 20, text=f"-{display_score}", fill="white", font=("Arial", 10, "bold"))
            else:
                self.canvas.create_text(660, 320, text="0.0", fill="gray", font=("Arial", 10, "bold"))
                
        if dragged_piece:
            img = PIECE_IMAGES.get((dragged_piece.color, dragged_piece.piece_type))
            if img:
                self.canvas.create_image(self.drag_x, self.drag_y, image=img)
            else:
                char = UNICODE_PIECES[dragged_piece.symbol()]
                self.canvas.create_text(self.drag_x, self.drag_y, text=char, font=("Arial", 60), fill="black")
                
        self.update_move_history()

if __name__ == "__main__":
    root = tk.Tk()
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    gui = ChessGUI(root)
    root.mainloop()
