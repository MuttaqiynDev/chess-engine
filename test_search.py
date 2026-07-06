import chess
from search import get_best_move
import time

board = chess.Board()
# 1. e4 e5 2. Nf3 Nc6 3. Bc4 (Out of opening book usually around move 3-5 depending on book)
board.push_san("a4")
board.push_san("a5")
board.push_san("h4")

start = time.time()
move = get_best_move(board, depth=6)
print(f"Finished in {time.time() - start:.2f}s. Best move: {move}")
