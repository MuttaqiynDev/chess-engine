from evaluate import evaluate

def quiescence_search(board, alpha, beta):
    """Quiescence search to resolve captures and avoid horizon effect."""
    stand_pat = evaluate(board)
    
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
        
    # Only search captures in quiescence
    captures = [m for m in board.legal_moves if board.is_capture(m)]
    
    for move in captures:
        board.push(move)
        score = -quiescence_search(board, -beta, -alpha)
        board.pop()
        
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
            
    return alpha
