import chess
import time

def perft(board, depth):
    if depth == 0:
        return 1
    nodes = 0
    for move in board.legal_moves:
        board.push(move)
        nodes += perft(board, depth - 1)
        board.pop()
    return nodes

def run_perft(depth):
    board = chess.Board()
    print(f"Running perft depth {depth}...")
    start = time.time()
    nodes = perft(board, depth)
    print(f"Depth {depth}: {nodes} nodes in {time.time() - start:.2f}s")
    return nodes

if __name__ == "__main__":
    run_perft(3)
