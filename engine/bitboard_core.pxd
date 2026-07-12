ctypedef unsigned long long U64
ctypedef unsigned short U16
ctypedef unsigned char U8

cdef enum:
    WHITE = 0
    BLACK = 1
    BOTH = 2
    PAWN = 0
    KNIGHT = 1
    BISHOP = 2
    ROOK = 3
    QUEEN = 4
    KING = 5

cdef struct CBoard:
    U64 pieces[2][6]  # [color][piece_type]
    U64 colors[2]     # [color]
    U64 occupied
    int turn          # 0 (White) or 1 (Black)
    int castling      # 4 bits: 1=WK, 2=WQ, 4=BK, 8=BQ
    int ep_square     # 0-63, or 64 if none
    int halfmove_clock
    int fullmove_number
    U64 hash_key

cdef void init_board_from_fen(CBoard* board, const char* fen)
cdef void print_board(CBoard* board)
cdef int popcount(U64 bb)
cdef int bit_scan_forward(U64 bb)
cdef void set_bit(U64* bb, int sq)
cdef void clear_bit(U64* bb, int sq)
cdef int test_bit(U64 bb, int sq)
