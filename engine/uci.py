import sys
import chess
from engine.search import get_best_move

def uci_loop():
    board = chess.Board()
    
    while True:
        try:
            line = sys.stdin.readline().strip()
        except EOFError:
            break
        if not line:
            continue
            
        tokens = line.split()
        if not tokens: continue
        
        cmd = tokens[0]
        
        if cmd == "uci":
            print("id name PythonEngine")
            print("id author Antigravity")
            print("uciok")
            sys.stdout.flush()
        elif cmd == "isready":
            print("readyok")
            sys.stdout.flush()
        elif cmd == "position":
            if "startpos" in tokens:
                board.set_fen(chess.STARTING_FEN)
                if "moves" in tokens:
                    moves_idx = tokens.index("moves")
                    for m in tokens[moves_idx+1:]:
                        board.push(chess.Move.from_uci(m))
            elif "fen" in tokens:
                fen_start = tokens.index("fen") + 1
                if "moves" in tokens:
                    moves_idx = tokens.index("moves")
                    fen = " ".join(tokens[fen_start:moves_idx])
                    board.set_fen(fen)
                    for m in tokens[moves_idx+1:]:
                        board.push(chess.Move.from_uci(m))
                else:
                    fen = " ".join(tokens[fen_start:])
                    board.set_fen(fen)
        elif cmd == "go":
            # Search for best move at depth 3 for fast response
            move = get_best_move(board, depth=3)
            if move:
                print(f"bestmove {move.uci()}")
            else:
                print("bestmove 0000")
            sys.stdout.flush()
        elif cmd == "quit":
            break
