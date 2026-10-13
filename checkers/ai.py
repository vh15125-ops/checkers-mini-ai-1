"""Adversarial search agent: minimax + alpha-beta pruning.

Forced captures inside the search
---------------------------------
1. The move generator (board.py) returns ONLY captures when one exists, so
   the search tree automatically respects the mandatory-capture rule at every
   ply (for both players), and multi-jump chains are single moves.
2. Horizon-effect guard: when depth runs out while the side to move is
   still *forced to capture*, the position is "noisy". We keep searching
   (capture extension, like quiescence search) until the position is quiet
   or max_extension extra plies were used. Otherwise the agent could stop
   one ply before a recapture and misjudge a trade.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .board import BLACK, WHITE, DRAW_PLIES, Move, State, is_king, owner

WIN = 100_000
MAN, KING = 100, 175


class SearchTimeout(Exception):
    pass


@dataclass
class SearchStats:
    nodes: int = 0
    cutoffs: int = 0
    extensions: int = 0       # capture extensions beyond nominal depth
    depth_reached: int = 0


def evaluate(state: State, color: str) -> float:
    """Static evaluation from `color`'s point of view (positive = good)."""
    score = 0.0
    for r in range(8):
        for c in range(8):
            p = state.board[r][c]
            who = owner(p)
            if who is None:
                continue
            centre = 2 <= r <= 5 and 2 <= c <= 5
            if is_king(p):
                v = KING + (4 if centre else 0)                        # kings like the centre
            else:
                advance = (7 - r) if who == WHITE else r               # rows progressed
                v = MAN + 4 * advance
                if (who == WHITE and r == 7) or (who == BLACK and r == 0):
                    v += 8                                             # back-row guard
                if centre:
                    v += 3                                             # centre control
            if c in (0, 7):
                v += 2                                                 # edge pieces are safe
            score += v if who == color else -v
    return score


def _order(moves: List[Move]) -> List[Move]:
    # Longer capture chains first: better pruning, strong moves tried early.
    return sorted(moves, key=lambda m: -len(m.captured))


class AlphaBetaAgent:
    def __init__(self, depth: int = 6, time_limit: Optional[float] = None,
                 use_pruning: bool = True, max_extension: int = 8):
        self.depth = depth
        self.time_limit = time_limit
        self.use_pruning = use_pruning
        self.max_extension = max_extension
        self.stats = SearchStats()
        self._deadline: Optional[float] = None
        self._root_color = WHITE

    # ---------- public API ----------
    def choose_move(self, state: State) -> Move:
        """Iterative deepening alpha-beta; returns the best move found."""
        moves = state.legal_moves()
        if not moves:
            raise ValueError("no legal moves")
        self.stats = SearchStats()
        if len(moves) == 1:                      # forced (e.g. only one capture)
            return moves[0]
        self._root_color = state.turn
        self._deadline = time.monotonic() + self.time_limit if self.time_limit else None
        moves = _order(moves)
        best = moves[0]
        for d in range(1, self.depth + 1):
            try:
                move, score = self._root(state, moves, d)
            except SearchTimeout:
                break
            best = move
            self.stats.depth_reached = d
            moves = [best] + [m for m in moves if m != best]   # PV move first next round
            if abs(score) > WIN - 1000:                        # forced win/loss found
                break
        return best

    def search_value(self, state: State, depth: int) -> float:
        """Minimax value of `state` for the side to move (used for testing)."""
        self.stats = SearchStats()
        self._deadline = None
        self._root_color = state.turn
        return self._search(state, depth, -math.inf, math.inf, 0, 0)

    # ---------- internals ----------
    def _root(self, state: State, moves: List[Move], depth: int) -> Tuple[Move, float]:
        alpha, beta = -math.inf, math.inf
        best, best_score = moves[0], -math.inf
        for m in moves:
            score = self._search(state.apply(m), depth - 1, alpha, beta, 1, 0)
            if score > best_score:
                best, best_score = m, score
            alpha = max(alpha, best_score)
        return best, best_score

    def _search(self, state: State, depth: int, alpha: float, beta: float,
                ply: int, ext: int) -> float:
        self.stats.nodes += 1
        if self._deadline and self.stats.nodes % 256 == 0 and time.monotonic() > self._deadline:
            raise SearchTimeout

        moves = state.legal_moves()
        maximizing = state.turn == self._root_color
        if not moves:                                    # side to move is stuck -> loses
            return -(WIN - ply) if maximizing else (WIN - ply)
        if state.quiet_plies >= DRAW_PLIES:
            return 0.0

        if depth <= 0:
            # Forced capture pending -> position is noisy: extend instead of evaluating.
            if moves[0].is_capture and ext < self.max_extension:
                self.stats.extensions += 1
                ext += 1
            else:
                return evaluate(state, self._root_color)

        moves = _order(moves)
        if maximizing:
            value = -math.inf
            for m in moves:
                value = max(value, self._search(state.apply(m), depth - 1, alpha, beta, ply + 1, ext))
                if self.use_pruning:
                    alpha = max(alpha, value)
                    if alpha >= beta:
                        self.stats.cutoffs += 1
                        break
            return value
        value = math.inf
        for m in moves:
            value = min(value, self._search(state.apply(m), depth - 1, alpha, beta, ply + 1, ext))
            if self.use_pruning:
                beta = min(beta, value)
                if alpha >= beta:
                    self.stats.cutoffs += 1
                    break
        return value
