from engine.bitboard_core cimport CBoard, U64, U16, U8, WHITE, BLACK, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING

cdef extern from *:
    int __builtin_popcountll(unsigned long long)
    int __builtin_ctzll(unsigned long long)
    void* memset(void* dest, int ch, size_t count)

cdef int popcount(U64 bb):
    return __builtin_popcountll(bb)

cdef int bit_scan_forward(U64 bb):
    return __builtin_ctzll(bb) if bb else 64

cdef void set_bit(U64* bb, int sq):
    bb[0] |= (1ULL << sq)

cdef void clear_bit(U64* bb, int sq):
    bb[0] &= ~(1ULL << sq)

cdef int test_bit(U64 bb, int sq):
    return (bb & (1ULL << sq)) != 0

cdef void init_board_from_fen(CBoard* board, const char* fen_bytes):
    memset(board, 0, sizeof(CBoard))
    board.ep_square = 64
    
    board.pieces[WHITE][PAWN] = 0x000000000000FF00ULL
    board.pieces[WHITE][KNIGHT] = 0x0000000000000042ULL
    board.pieces[WHITE][BISHOP] = 0x0000000000000024ULL
    board.pieces[WHITE][ROOK] = 0x0000000000000081ULL
    board.pieces[WHITE][QUEEN] = 0x0000000000000008ULL
    board.pieces[WHITE][KING] = 0x0000000000000010ULL

    board.pieces[BLACK][PAWN] = 0x00FF000000000000ULL
    board.pieces[BLACK][KNIGHT] = 0x4200000000000000ULL
    board.pieces[BLACK][BISHOP] = 0x2400000000000000ULL
    board.pieces[BLACK][ROOK] = 0x8100000000000000ULL
    board.pieces[BLACK][QUEEN] = 0x0800000000000000ULL
    board.pieces[BLACK][KING] = 0x1000000000000000ULL
    
    board.colors[WHITE] = 0x000000000000FFFFULL
    board.colors[BLACK] = 0xFFFF000000000000ULL
    board.occupied = board.colors[WHITE] | board.colors[BLACK]
    
    board.turn = WHITE
    board.castling = 15
    board.ep_square = 64
    board.halfmove_clock = 0
    board.fullmove_number = 1

cdef void print_board(CBoard* board):
    cdef int rank, file, sq
    cdef str piece_chars = "PNBRQK"
    print("\n  +---+---+---+---+---+---+---+---+")
    for rank in range(7, -1, -1):
        line = f"{rank+1} |"
        for file in range(8):
            sq = rank * 8 + file
            c_char = ' '
            for pt in range(6):
                if test_bit(board.pieces[WHITE][pt], sq):
                    c_char = piece_chars[pt]
                    break
                elif test_bit(board.pieces[BLACK][pt], sq):
                    c_char = piece_chars[pt].lower()
                    break
            line += f" {c_char} |"
        print(line)
        print("  +---+---+---+---+---+---+---+---+")
    print("    a   b   c   d   e   f   g   h\n")

def test_print():
    cdef CBoard board
    init_board_from_fen(&board, b"")
    print_board(&board)
