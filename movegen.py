import chess

def generate_legal_moves(board):
    """Generates all legal moves for the current position."""
    return list(board.legal_moves)
