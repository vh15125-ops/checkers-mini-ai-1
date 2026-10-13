"""Command-line checkers: play against the alpha-beta AI, or watch AI vs AI.

    python main.py                        # you = white, AI = black (AI moves first)
    python main.py --white ai --black ai  # AI vs AI demo
    python main.py --depth 8 --time 3     # stronger AI, max 3 s per move
"""
import argparse
import sys

from checkers import AlphaBetaAgent, State, WHITE, BLACK
from checkers.board import Move, parse_square

NAMES = {WHITE: "White", BLACK: "Black"}


def ask_human(state: State) -> Move:
    moves = state.legal_moves()
    if moves[0].is_capture:
        print(">> Capture is MANDATORY - only capturing moves are legal.")
    for i, m in enumerate(moves, 1):
        print(f"  {i:2}. {m}")
    while True:
        text = input(f"{NAMES[state.turn]} move (number, or e.g. c3-d4 / c3xe5xg7, q=quit): ").strip().lower()
        if text in ("q", "quit"):
            sys.exit(0)
        if text.isdigit() and 1 <= int(text) <= len(moves):
            return moves[int(text) - 1]
        try:
            squares = [parse_square(t) for t in text.replace("x", "-").replace(" ", "-").split("-") if t]
        except ValueError:
            squares = []
        if len(squares) >= 2:
            exact = [m for m in moves if list(m.path) == squares]
            if exact:
                return exact[0]
            ends = [m for m in moves if m.start == squares[0] and m.end == squares[-1]]
            if len(ends) == 1:
                return ends[0]
        print("Illegal move. Choose one of the listed moves.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Checkers mini AI (alpha-beta)")
    ap.add_argument("--white", choices=["human", "ai"], default="human")
    ap.add_argument("--black", choices=["human", "ai"], default="ai")
    ap.add_argument("--depth", type=int, default=6, help="max search depth in plies")
    ap.add_argument("--time", type=float, default=None, help="time limit per AI move (seconds)")
    args = ap.parse_args()

    players = {WHITE: args.white, BLACK: args.black}
    agent = AlphaBetaAgent(depth=args.depth, time_limit=args.time)
    state = State.initial()
    while True:
        print("\n" + str(state))
        result = state.winner()
        if result:
            print("\nDraw!" if result == "draw" else f"\n{NAMES[result]} wins!")
            return
        if players[state.turn] == "human":
            move = ask_human(state)
        else:
            forced = state.legal_moves()[0].is_capture
            move = agent.choose_move(state)
            s = agent.stats
            tag = " (mandatory capture)" if forced else ""
            print(f"\n{NAMES[state.turn]} AI plays {move}{tag}  "
                  f"[depth {s.depth_reached}, nodes {s.nodes}, cutoffs {s.cutoffs}, "
                  f"capture-extensions {s.extensions}]")
        state = state.apply(move)


if __name__ == "__main__":
    main()
