"""Independent declarative-style checkers rule base used for cross-checking.

Predicates exposed: on_board, owns, opponent_piece, legal_step, legal_jump,
forced_capture, promotion, and rule_based_moves. This reference implementation
intentionally does not call State.legal_moves().
"""
from .board import EMPTY, WHITE, BLACK, Move, State, directions, is_king, owner, promotion_row


def on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def owns(piece, color):
    return piece != EMPTY and owner(piece) == color


def opponent_piece(piece, color):
    return piece != EMPTY and owner(piece) not in (None, color)


def legal_step(board, color, r, c, nr, nc):
    piece = board[r][c]
    return (owns(piece, color) and (nr-r, nc-c) in directions(piece)
            and on_board(nr, nc) and board[nr][nc] == EMPTY)


def legal_jump(board, color, r, c, nr, nc, captured=()):
    piece = board[r][c]
    dr, dc = nr-r, nc-c
    if abs(dr) != 2 or abs(dc) != 2 or (dr//2, dc//2) not in directions(piece):
        return False
    mr, mc = r + dr//2, c + dc//2
    return (on_board(nr, nc) and board[nr][nc] == EMPTY and
            opponent_piece(board[mr][mc], color) and (mr, mc) not in captured)


def promotion(piece, landing_row):
    return piece in ('w', 'b') and landing_row == promotion_row(owner(piece))


def _captures(board, color, r, c):
    piece = board[r][c]
    out = []
    def walk(pos, path, taken):
        rr, cc = pos
        found = False
        for dr, dc in directions(piece):
            nr, nc = rr + 2*dr, cc + 2*dc
            if not on_board(nr, nc):
                continue
            mr, mc = rr + dr, cc + dc
            if board[mr][mc] == EMPTY or owner(board[mr][mc]) == color or (mr, mc) in taken:
                continue
            if board[nr][nc] != EMPTY:
                continue
            found = True
            new_path = path + ((nr, nc),)
            new_taken = taken + ((mr, mc),)
            if promotion(piece, nr):
                out.append(Move(new_path, new_taken))
            else:
                walk((nr, nc), new_path, new_taken)
        if not found and taken:
            out.append(Move(path, taken))
    walk((r,c), ((r,c),), ())
    return out


def forced_capture(state):
    return any(_captures(state.board, state.turn, r, c)
               for r in range(8) for c in range(8)
               if owns(state.board[r][c], state.turn))


def rule_based_moves(state):
    """Generate complete legal moves from the rule predicates, independently."""
    board, color = state.board, state.turn
    captures = []
    steps = []
    for r in range(8):
        for c in range(8):
            if not owns(board[r][c], color):
                continue
            captures.extend(_captures(board, color, r, c))
            for dr, dc in directions(board[r][c]):
                nr, nc = r+dr, c+dc
                if on_board(nr,nc) and legal_step(board,color,r,c,nr,nc):
                    steps.append(Move(((r,c),(nr,nc))))
    return captures if captures else steps
