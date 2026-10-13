"""Explainability helpers: interpretable score components and a principal variation."""
from .board import WHITE, BLACK, is_king, owner
from .ai import AlphaBetaAgent


def evaluation_breakdown(state, perspective=None):
    """Return signed feature contributions for a chosen side's perspective."""
    perspective = perspective or state.turn
    other = BLACK if perspective == WHITE else WHITE
    terms = {"material": 0.0, "kings": 0.0, "mobility": 0.0, "centre_control": 0.0}
    for r, row in enumerate(state.board):
        for c, p in enumerate(row):
            who = owner(p)
            if who is None:
                continue
            sign = 1 if who == perspective else -1
            if is_king(p):
                terms["kings"] += sign * 175
            else:
                terms["material"] += sign * 100
            if 2 <= r <= 5 and 2 <= c <= 5:
                terms["centre_control"] += sign * (8 if is_king(p) else 5)
    # Mobility is computed using the same legal-move API used by the game.
    from dataclasses import replace
    own_state = replace(state, turn=perspective)
    opp_state = replace(state, turn=other)
    terms["mobility"] = 2.0 * (len(own_state.legal_moves()) - len(opp_state.legal_moves()))
    terms["total"] = sum(terms.values())
    return terms


def principal_variation(state, depth=4, max_plies=8):
    """Practical PV display: repeatedly follow the best move at the requested depth."""
    current, line = state, []
    for _ in range(max_plies):
        if current.winner() is not None:
            break
        agent = AlphaBetaAgent(depth=max(1, depth))
        move = agent.choose_move(current)
        line.append({"player": current.turn, "move": str(move),
                     "evaluation": round(agent.search_value(current, max(1, depth)), 2)})
        current = current.apply(move)
    return line
