import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from checkers import AlphaBetaAgent, State, WHITE, BLACK  # noqa: E402


def pos(rows, turn=WHITE):
    return State.from_rows(rows, turn)


class RulesTests(unittest.TestCase):
    def test_initial_moves(self):
        moves = State.initial().legal_moves()
        self.assertEqual(len(moves), 7)
        self.assertFalse(any(m.is_capture for m in moves))

    def test_capture_is_mandatory(self):
        # White has a capture AND free simple moves (piece on g3) - must capture.
        s = pos(["........", "........", "........", "........",
                 "...b....", "..w...w.", "........", "........"])
        moves = s.legal_moves()
        self.assertEqual(len(moves), 1)
        self.assertTrue(moves[0].is_capture)
        self.assertEqual(moves[0].end, (3, 4))

    def test_multi_jump_is_single_move(self):
        s = pos(["........", "........", "........", "....b...",
                 "........", "..b.....", ".w......", "........"])
        moves = s.legal_moves()
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0].path, ((6, 1), (4, 3), (2, 5)))
        self.assertEqual(s.apply(moves[0]).count(BLACK), 0)

    def test_promotion_ends_jump(self):
        s = pos(["........", "..b.b...", ".....w..", "........",
                 "........", "........", "........", "........"])
        moves = s.legal_moves()
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(moves[0].path), 2)      # stops on the crowning square
        self.assertEqual(s.apply(moves[0]).board[0][3], "W")

    def test_no_moves_is_loss(self):
        blocked = pos(["........", "........", "........", "........",
                       "........", "........", ".b......", "w.w....."], BLACK)
        self.assertEqual(blocked.winner(), WHITE)


class SearchTests(unittest.TestCase):
    def test_agent_plays_forced_capture(self):
        s = pos(["........", "........", "........", "........",
                 "...b....", "..w...w.", "........", "........"])
        self.assertTrue(AlphaBetaAgent(depth=4).choose_move(s).is_capture)

    def test_alphabeta_matches_minimax_with_fewer_nodes(self):
        s = State.initial()
        ab, mm = AlphaBetaAgent(use_pruning=True), AlphaBetaAgent(use_pruning=False)
        self.assertEqual(ab.search_value(s, 4), mm.search_value(s, 4))
        self.assertLess(ab.stats.nodes, mm.stats.nodes)

    def test_full_game_terminates_with_legal_moves_only(self):
        s, a = State.initial(), AlphaBetaAgent(depth=3)
        for _ in range(400):
            if s.winner():
                break
            m = a.choose_move(s)
            self.assertIn(m, s.legal_moves())
            s = s.apply(m)
        self.assertIsNotNone(s.winner())


if __name__ == "__main__":
    unittest.main()
