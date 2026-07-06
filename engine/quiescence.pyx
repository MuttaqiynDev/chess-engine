from engine.evaluate import evaluate

cpdef int quiescence_search(board, int alpha, int beta):
    cdef int stand_pat = evaluate(board)
    
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
        
    captures = [m for m in board.legal_moves if board.is_capture(m)]
    
    cdef int score
    for move in captures:
        board.push(move)
        score = -quiescence_search(board, -beta, -alpha)
        board.pop()
        
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
            
    return alpha
