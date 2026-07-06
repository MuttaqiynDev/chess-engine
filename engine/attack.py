import chess

def get_attacks(board, square):
    """Returns the attack bitboard for a given square."""
    return board.attacks(square)
