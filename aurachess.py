import customtkinter as ctk
import tkinter as tk
import os, json
import chess
from gui import ChessGUI

class AuraChess(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AuraChess - The AI Chess Lab")
        self.geometry("1100x700")
        
        # Grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AuraChess", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.dashboard_btn = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard)
        self.dashboard_btn.grid(row=1, column=0, padx=20, pady=10)
        
        self.play_btn = ctk.CTkButton(self.sidebar_frame, text="Play AI", command=self.show_play)
        self.play_btn.grid(row=2, column=0, padx=20, pady=10)
        
        self.pvm_btn = ctk.CTkButton(self.sidebar_frame, text="Play Persona", command=self.show_pvm)
        self.pvm_btn.grid(row=3, column=0, padx=20, pady=10)
        
        self.pvp_btn = ctk.CTkButton(self.sidebar_frame, text="Play Local", command=self.show_pvp)
        self.pvp_btn.grid(row=4, column=0, padx=20, pady=10)
        
        self.analyze_btn = ctk.CTkButton(self.sidebar_frame, text="PGN Analyzer", command=self.show_analyzer)
        self.analyze_btn.grid(row=5, column=0, padx=20, pady=10)
        
        self.trainer_btn = ctk.CTkButton(self.sidebar_frame, text="Aura Trainer", command=self.show_trainer)
        self.trainer_btn.grid(row=6, column=0, padx=20, pady=10)
        
        # Frames
        self.dashboard_frame = DashboardFrame(self, self)
        self.play_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.analyzer_frame = AnalyzerFrame(self, self)
        self.trainer_frame = TrainerFrame(self, self)
        
        # Default
        self.current_frame = None
        self.show_dashboard()

    def select_frame_by_name(self, name):
        if self.current_frame:
            self.current_frame.grid_forget()
        
        if name == "dashboard":
            self.current_frame = self.dashboard_frame
            self.dashboard_frame.refresh_stats()
        elif name == "play":
            for widget in self.play_frame.winfo_children():
                widget.destroy()
            ChessGUI(self.play_frame, mode="PvB")
            self.current_frame = self.play_frame
        elif name == "pvm":
            for widget in self.play_frame.winfo_children():
                widget.destroy()
            ChessGUI(self.play_frame, mode="PvM")
            self.current_frame = self.play_frame
        elif name == "pvp":
            for widget in self.play_frame.winfo_children():
                widget.destroy()
            ChessGUI(self.play_frame, mode="PvP")
            self.current_frame = self.play_frame
        elif name == "analyze":
            self.current_frame = self.analyzer_frame
        elif name == "trainer":
            self.current_frame = self.trainer_frame
            self.trainer_frame.load_cards()
            
        self.current_frame.grid(row=0, column=1, sticky="nsew")

    def show_dashboard(self): self.select_frame_by_name("dashboard")
    def show_play(self): self.select_frame_by_name("play")
    def show_pvm(self): self.select_frame_by_name("pvm")
    def show_pvp(self): self.select_frame_by_name("pvp")
    def show_analyzer(self): self.select_frame_by_name("analyze")
    def show_trainer(self): self.select_frame_by_name("trainer")


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        
        self.title = ctk.CTkLabel(self, text="Welcome to AuraChess Lab", font=ctk.CTkFont(size=32, weight="bold"))
        self.title.grid(row=0, column=0, padx=20, pady=40)
        
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=1, column=0, padx=40, pady=20, sticky="nsew")
        
        self.stats_label = ctk.CTkLabel(self.stats_frame, text="", font=ctk.CTkFont(size=18), justify="left")
        self.stats_label.pack(padx=20, pady=20)
        
    def refresh_stats(self):
        book_path = os.path.join(os.path.dirname(__file__), "data", "user_book.json")
        try:
            with open(book_path, "r") as f:
                user_book = json.load(f)
                num_positions = len(user_book)
                
                START_EPD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -"
                white_openings = user_book.get(START_EPD, {})
                sorted_white = sorted(white_openings.items(), key=lambda x: x[1], reverse=True)[:3]
                
                import chess
                e4_board = chess.Board()
                e4_board.push(chess.Move.from_uci("e2e4"))
                d4_board = chess.Board()
                d4_board.push(chess.Move.from_uci("d2d4"))
                
                e4_responses = user_book.get(e4_board.epd(), {})
                d4_responses = user_book.get(d4_board.epd(), {})
                
                sorted_e4 = sorted(e4_responses.items(), key=lambda x: x[1], reverse=True)[:3]
                sorted_d4 = sorted(d4_responses.items(), key=lambda x: x[1], reverse=True)[:3]
                
                text = f"Your Digital Persona is active.\nPositions Modeled: {num_positions:,}\n\n"
                
                text += "Your Preferred Openings (White):\n"
                for move, prob in sorted_white: text += f" • {move}: {prob*100:.1f}%\n"
                    
                text += "\nYour Responses to 1. e4 (Black):\n"
                for move, prob in sorted_e4: text += f" • {move}: {prob*100:.1f}%\n"
                    
                text += "\nYour Responses to 1. d4 (Black):\n"
                for move, prob in sorted_d4: text += f" • {move}: {prob*100:.1f}%\n"
                
                self.stats_label.configure(text=text)
        except Exception as e:
            self.stats_label.configure(text=f"No user data found. Run build_user_book.py\n{e}")


class AnalyzerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        self.title = ctk.CTkLabel(self.top_frame, text="PGN Engine Analyzer", font=ctk.CTkFont(size=24, weight="bold"))
        self.title.pack(side="left")
        
        self.load_btn = ctk.CTkButton(self.top_frame, text="Load PGN", command=self.load_pgn)
        self.load_btn.pack(side="right")
        
        self.graph_frame = ctk.CTkFrame(self)
        self.graph_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        self.status_lbl = ctk.CTkLabel(self.graph_frame, text="Load a PGN to generate an evaluation profile...")
        self.status_lbl.pack(expand=True)
        
    def load_pgn(self):
        import tkinter.filedialog as fd
        path = fd.askopenfilename(filetypes=[("PGN Files", "*.pgn")])
        if path:
            self.status_lbl.configure(text="Analyzing game... Please wait.")
            self.update()
            import threading
            threading.Thread(target=self.analyze, args=(path,), daemon=True).start()
            
    def analyze(self, path):
        import chess.pgn
        from engine.evaluate import evaluate
        scores = []
        with open(path, "r") as f:
            game = chess.pgn.read_game(f)
            if not game: return
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
                score = evaluate(board)
                if board.turn == chess.WHITE:
                    real_score = score
                else:
                    real_score = -score
                scores.append(real_score)
                
        self.after(0, lambda: self.draw_graph(scores))
        
    def draw_graph(self, scores):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
            
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        fig, ax = plt.subplots(figsize=(8, 4), facecolor='#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        ax.plot(scores, color='#1f538d', linewidth=2)
        ax.fill_between(range(len(scores)), scores, 0, where=[s >= 0 for s in scores], color='white', alpha=0.3, interpolate=True)
        ax.fill_between(range(len(scores)), scores, 0, where=[s < 0 for s in scores], color='black', alpha=0.3, interpolate=True)
        
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('#555555')
            
        ax.set_title("Evaluation Profile", color='white')
        ax.set_ylabel("Advantage", color='white')
        
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

class TrainerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.title = ctk.CTkLabel(self, text="Aura Auto-Trainer (Spaced Repetition)", font=ctk.CTkFont(size=24, weight="bold"))
        self.title.grid(row=0, column=0, padx=20, pady=20)
        
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=1, column=0, padx=40, pady=20, sticky="nsew")
        
        self.status = ctk.CTkLabel(self.content, text="Loading mistakes...", font=ctk.CTkFont(size=16))
        self.status.pack(pady=(20, 5))
        
        self.refresh_btn = ctk.CTkButton(self.content, text="Refresh Flashcards", command=self.load_cards)
        self.refresh_btn.pack(pady=(0, 20))
        
        self.board_container = ctk.CTkFrame(self.content, fg_color="transparent")
        self.board_container.pack(fill="both", expand=True)
        
    def load_cards(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), "data", "flashcards.json"), "r") as f:
                self.cards = json.load(f)
                
            if not self.cards:
                self.status.configure(text="No mistakes found! Run theory_analyzer.py")
                return
                
            self.status.configure(text=f"Found {len(self.cards)} opening mistakes to review.")
            self.card_index = 0
            self.show_card()
            
        except Exception as e:
            self.status.configure(text=f"Error loading flashcards: {e}")

    def show_card(self):
        try:
            if not hasattr(self, 'cards'): return
            
            for widget in self.board_container.winfo_children():
                widget.destroy()
                
            if self.card_index >= len(self.cards):
                self.status.configure(text="You've finished your daily review!")
                return
                
            card = self.cards[self.card_index]
            self.status.configure(text=f"Reviewing {self.card_index + 1} / {len(self.cards)}")
            
            def on_next():
                self.card_index += 1
                self.show_card()
                
            ChessGUI(self.board_container, mode="Trainer", epd=card["epd"], 
                     correct_move=card["correct_move"], user_move=card["user_move"], on_next=on_next)
        except Exception as e:
            self.status.configure(text=f"Error loading flashcard: {e}")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = AuraChess()
    app.mainloop()
