"""Checkers (American / English draughts) rules engine.

Rules implemented
-----------------
* 8x8 board, play on dark squares ((row + col) odd). Row 0 is the TOP (rank 8).
* Men move/capture one step diagonally FORWARD; kings move/capture both ways.
* CAPTURES ARE MANDATORY: if any capture exists, only captures are legal.
* Multi-jumps: a capturing piece must keep jumping while it can. The whole
  chain is ONE move. A captured piece cannot be jumped twice.
* A man that reaches the far row becomes a king and its move ENDS there
  (even if, as a king, it could continue jumping).
* No legal moves = loss. 80 plies without a capture or a man move = draw.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

EMPTY = "."
WHITE, BLACK = "w", "b"            # colours; pieces: w/W and b/B (capital = king)
Square = Tuple[int, int]
DRAW_PLIES = 80

START_ROWS = (
    ".b.b.b.b",
    "b.b.b.b.",
    ".b.b.b.b",
    "........",
    "........",
    "w.w.w.w.",
    ".w.w.w.w",
    "w.w.w.w.",
)


def opponent(color: str) -> str:
    return BLACK if color == WHITE else WHITE


def owner(piece: str) -> Optional[str]:
    return None if piece == EMPTY else piece.lower()


def is_king(piece: str) -> bool:
    return piece in ("W", "B")


def promotion_row(color: str) -> int:
    return 0 if color == WHITE else 7


def directions(piece: str) -> Sequence[Tuple[int, int]]:
    if is_king(piece):
        return ((-1, -1), (-1, 1), (1, -1), (1, 1))
    return ((-1, -1), (-1, 1)) if piece == "w" else ((1, -1), (1, 1))


def sq_name(sq: Square) -> str:
    r, c = sq
    return "abcdefgh"[c] + str(8 - r)


def parse_square(text: str) -> Square:
    text = text.strip().lower()
    if len(text) != 2 or text[0] not in "abcdefgh" or text[1] not in "12345678":
        raise ValueError(f"bad square: {text!r}")
    return 8 - int(text[1]), "abcdefgh".index(text[0])


@dataclass(frozen=True)
class Move:
    """A complete move: the path of squares visited and the pieces captured."""
    path: Tuple[Square, ...]
    captured: Tuple[Square, ...] = ()

    @property
    def is_capture(self) -> bool:
        return bool(self.captured)

    @property
    def start(self) -> Square:
        return self.path[0]

    @property
    def end(self) -> Square:
        return self.path[-1]

    def __str__(self) -> str:
        sep = "x" if self.is_capture else "-"
        return sep.join(sq_name(s) for s in self.path)


@dataclass(frozen=True)
class State:
    board: Tuple[Tuple[str, ...], ...]
    turn: str = BLACK                 # black moves first (tradition)
    quiet_plies: int = 0              # plies since last capture / man move

    # ---------- construction ----------
    @staticmethod
    def initial() -> "State":
        return State.from_rows(START_ROWS, BLACK)

    @staticmethod
    def from_rows(rows: Sequence[str], turn: str = WHITE, quiet_plies: int = 0) -> "State":
        assert len(rows) == 8 and all(len(r) == 8 for r in rows)
        return State(tuple(tuple(r) for r in rows), turn, quiet_plies)

    # ---------- move generation ----------
    def legal_moves(self) -> List[Move]:
        """All legal moves. If ANY capture exists, ONLY captures are returned."""
        jumps: List[Move] = []
        simple: List[Move] = []
        for r in range(8):
            for c in range(8):
                if owner(self.board[r][c]) != self.turn:
                    continue
                jumps.extend(self._jump_moves(r, c))
                if not jumps:  # no point collecting simple moves once a jump exists
                    simple.extend(self._simple_moves(r, c))
        return jumps if jumps else simple

    def _simple_moves(self, r: int, c: int) -> List[Move]:
        out = []
        for dr, dc in directions(self.board[r][c]):
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr][nc] == EMPTY:
                out.append(Move(((r, c), (nr, nc))))
        return out

    def _jump_moves(self, r: int, c: int) -> List[Move]:
        piece = self.board[r][c]
        results: List[Move] = []
        self._dfs(piece, r, c, ((r, c),), (), results)
        return results

    def _dfs(self, piece: str, r: int, c: int, path, captured, results) -> None:
        me = owner(piece)
        extended = False
        for dr, dc in directions(piece):
            mr, mc, lr, lc = r + dr, c + dc, r + 2 * dr, c + 2 * dc
            if not (0 <= lr < 8 and 0 <= lc < 8):
                continue
            mid = self.board[mr][mc]
            if mid == EMPTY or owner(mid) == me or (mr, mc) in captured:
                continue                              # nothing to jump / already jumped
            land = self.board[lr][lc]
            # landing must be empty; the mover's own start square counts as empty
            if land != EMPTY and (lr, lc) != path[0]:
                continue
            extended = True
            new_path = path + ((lr, lc),)
            new_cap = captured + ((mr, mc),)
            if not is_king(piece) and lr == promotion_row(me):
                results.append(Move(new_path, new_cap))   # crowning ends the move
            else:
                self._dfs(piece, lr, lc, new_path, new_cap, results)
        if not extended and captured:                     # chain can't continue -> complete move
            results.append(Move(path, captured))

    # ---------- applying moves ----------
    def apply(self, move: Move) -> "State":
        grid = [list(row) for row in self.board]
        (sr, sc), (er, ec) = move.start, move.end
        piece = grid[sr][sc]
        was_man = not is_king(piece)
        grid[sr][sc] = EMPTY
        for cr, cc in move.captured:
            grid[cr][cc] = EMPTY
        if was_man and er == promotion_row(owner(piece)):
            piece = piece.upper()
        grid[er][ec] = piece
        reset = move.is_capture or was_man
        return State(tuple(tuple(r) for r in grid), opponent(self.turn),
                     0 if reset else self.quiet_plies + 1)

    # ---------- game status ----------
    def winner(self) -> Optional[str]:
        """WHITE / BLACK / 'draw' / None (game continues)."""
        if self.quiet_plies >= DRAW_PLIES:
            return "draw"
        if not self.legal_moves():
            return opponent(self.turn)
        return None

    def count(self, color: str) -> int:
        return sum(1 for row in self.board for p in row if owner(p) == color)

    def __str__(self) -> str:
        lines = ["    a b c d e f g h"]
        for r in range(8):
            cells = " ".join(self.board[r][c] if self.board[r][c] != EMPTY
                             else ("." if (r + c) % 2 else " ") for c in range(8))
            lines.append(f" {8 - r}  {cells}  {8 - r}")
        lines.append("    a b c d e f g h")
        return "\n".join(lines)
