import chess

def get_zobrist_key(board):
    """Returns a unique hash key for the current position."""
    # python-chess fen() is sufficient for a unique state representation
    # though technically slower than incremental zobrist hashing.
    return hash(board.fen())
