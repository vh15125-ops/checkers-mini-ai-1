import math
import copy


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

EMPTY = 0

# Black pieces = AI
BLACK = 1
BLACK_KING = 2

# Red pieces = Human
RED = -1
RED_KING = -2

BOARD_SIZE = 8


# ---------------------------------------------------------
# BOARD SETUP
# ---------------------------------------------------------

def create_board():
    """
    Create the standard 8x8 checkers board.

    Black pieces start at the top.
    Red pieces start at the bottom.
    """

    board = [[EMPTY for _ in range(BOARD_SIZE)]
             for _ in range(BOARD_SIZE)]

    # Black pieces
    for row in range(3):
        for col in range(BOARD_SIZE):
            if (row + col) % 2 == 1:
                board[row][col] = BLACK

    # Red pieces
    for row in range(5, 8):
        for col in range(BOARD_SIZE):
            if (row + col) % 2 == 1:
                board[row][col] = RED

    return board


# ---------------------------------------------------------
# DISPLAY BOARD
# ---------------------------------------------------------

def print_board(board):
    """
    Display the board in the terminal.
    """

    print("\n    0 1 2 3 4 5 6 7")
    print("   -----------------")

    for row in range(BOARD_SIZE):
        print(f"{row} |", end=" ")

        for col in range(BOARD_SIZE):
            piece = board[row][col]

            if piece == BLACK:
                symbol = "b"
            elif piece == BLACK_KING:
                symbol = "B"
            elif piece == RED:
                symbol = "r"
            elif piece == RED_KING:
                symbol = "R"
            else:
                symbol = "."

            print(symbol, end=" ")

        print(f"| {row}")

    print("   -----------------")
    print("    0 1 2 3 4 5 6 7")
    print()


# ---------------------------------------------------------
# PIECE HELPERS
# ---------------------------------------------------------

def is_black(piece):
    return piece in (BLACK, BLACK_KING)


def is_red(piece):
    return piece in (RED, RED_KING)


def is_king(piece):
    return abs(piece) == 2


def belongs_to_player(piece, player):
    if player == BLACK:
        return is_black(piece)

    return is_red(piece)


def opponent(player):
    return RED if player == BLACK else BLACK


# ---------------------------------------------------------
# MOVE DIRECTIONS
# ---------------------------------------------------------

def get_directions(piece):
    """
    Normal pieces can only move forward.

    Kings can move in all four diagonal directions.
    """

    if is_king(piece):
        return [
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1)
        ]

    if piece == BLACK:
        return [
            (1, -1),
            (1, 1)
        ]

    return [
        (-1, -1),
        (-1, 1)
    ]


def inside_board(row, col):
    return (
        0 <= row < BOARD_SIZE and
        0 <= col < BOARD_SIZE
    )


# ---------------------------------------------------------
# CAPTURE GENERATION
# ---------------------------------------------------------

def get_capture_moves(board, player):
    """
    Find ALL legal capture moves.

    Checkers requires captures whenever one is available.

    Each move is represented as:

        [(start_row, start_col),
         (end_row, end_col),
         (captured_row, captured_col), ...]
    """

    capture_moves = []

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):

            piece = board[row][col]

            if not belongs_to_player(piece, player):
                continue

            find_captures(
                board,
                row,
                col,
                player,
                [],
                capture_moves
            )

    return capture_moves


def find_captures(
    board,
    row,
    col,
    player,
    path,
    results
):
    """
    Recursively search for multiple jumps.

    This is important because a player may be forced
    to continue capturing after the first jump.
    """

    piece = board[row][col]

    found_capture = False

    for dr, dc in get_directions(piece):

        middle_row = row + dr
        middle_col = col + dc

        landing_row = row + 2 * dr
        landing_col = col + 2 * dc

        if not inside_board(landing_row, landing_col):
            continue

        if not inside_board(middle_row, middle_col):
            continue

        middle_piece = board[middle_row][middle_col]
        landing_piece = board[landing_row][landing_col]

        # Opponent piece must be between us and empty landing square
        if (
            belongs_to_player(middle_piece, opponent(player))
            and landing_piece == EMPTY
        ):

            found_capture = True

            new_board = copy.deepcopy(board)

            # Move piece
            new_board[landing_row][landing_col] = piece
            new_board[row][col] = EMPTY

            # Remove captured piece
            new_board[middle_row][middle_col] = EMPTY

            new_path = path + [
                (
                    (landing_row, landing_col),
                    (middle_row, middle_col)
                )
            ]

            # Continue searching for another jump
            next_captures = []

            find_captures(
                new_board,
                landing_row,
                landing_col,
                player,
                new_path,
                next_captures
            )

            if next_captures:
                results.extend(next_captures)
            else:
                results.append(new_path)


# ---------------------------------------------------------
# NORMAL MOVE GENERATION
# ---------------------------------------------------------

def get_normal_moves(board, player):
    """
    Generate normal non-capturing moves.
    """

    moves = []

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):

            piece = board[row][col]

            if not belongs_to_player(piece, player):
                continue

            for dr, dc in get_directions(piece):

                new_row = row + dr
                new_col = col + dc

                if (
                    inside_board(new_row, new_col)
                    and board[new_row][new_col] == EMPTY
                ):
                    moves.append([
                        ((new_row, new_col), None)
                    ])

    return moves


# ---------------------------------------------------------
# LEGAL MOVES
# ---------------------------------------------------------

def get_legal_moves(board, player):
    """
    Generate legal moves.

    IMPORTANT CHECKERS RULE:

    If at least one capture exists,
    normal moves are NOT allowed.
    """

    captures = get_capture_moves(board, player)

    if captures:
        return captures

    return get_normal_moves(board, player)


# ---------------------------------------------------------
# APPLY MOVE
# ---------------------------------------------------------

def apply_move(board, move, player):
    """
    Apply a move to the board.

    Handles both normal moves and multiple captures.
    """

    new_board = copy.deepcopy(board)

    # Find the starting position.
    # We reconstruct it from the move information.

    # For normal move, find source based on destination.
    if len(move) == 1 and move[0][1] is None:

        destination = move[0][0]

        # Find the piece that can make this move
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):

                piece = new_board[row][col]

                if not belongs_to_player(piece, player):
                    continue

                for dr, dc in get_directions(piece):

                    if (
                        (row + dr, col + dc)
                        == destination
                    ):
                        new_board[destination[0]][destination[1]] = piece
                        new_board[row][col] = EMPTY

                        # Promotion
                        promote_piece(
                            new_board,
                            destination[0],
                            destination[1]
                        )

                        return new_board

    # Capture move
    #
    # We need the starting position.
    #
    # The capture path only stores destinations,
    # so locate a player's piece that can produce
    # this exact path.

    target_path = move

    for start_row in range(BOARD_SIZE):
        for start_col in range(BOARD_SIZE):

            piece = new_board[start_row][start_col]

            if not belongs_to_player(piece, player):
                continue

            test_board = copy.deepcopy(new_board)

            current_row = start_row
            current_col = start_col

            valid = True

            for destination, captured in target_path:

                dest_row, dest_col = destination
                cap_row, cap_col = captured

                dr = dest_row - current_row
                dc = dest_col - current_col

                if abs(dr) != 2 or abs(dc) != 2:
                    valid = False
                    break

                if (
                    test_board[cap_row][cap_col] == EMPTY
                    or not belongs_to_player(
                        test_board[cap_row][cap_col],
                        opponent(player)
                    )
                ):
                    valid = False
                    break

                if test_board[dest_row][dest_col] != EMPTY:
                    valid = False
                    break

                test_board[dest_row][dest_col] = piece
                test_board[current_row][current_col] = EMPTY
                test_board[cap_row][cap_col] = EMPTY

                current_row = dest_row
                current_col = dest_col

            if valid:
                promote_piece(
                    test_board,
                    current_row,
                    current_col
                )

                return test_board

    return new_board


def promote_piece(board, row, col):
    """
    Convert a normal piece into a king.
    """

    piece = board[row][col]

    # Black reaches bottom
    if piece == BLACK and row == BOARD_SIZE - 1:
        board[row][col] = BLACK_KING

    # Red reaches top
    elif piece == RED and row == 0:
        board[row][col] = RED_KING


# ---------------------------------------------------------
# GAME STATE
# ---------------------------------------------------------

def count_pieces(board, player):
    count = 0

    for row in board:
        for piece in row:
            if belongs_to_player(piece, player):
                count += 1

    return count


def game_over(board, player):
    """
    Game is over if player has no pieces
    or no legal moves.
    """

    if count_pieces(board, player) == 0:
        return True

    return len(get_legal_moves(board, player)) == 0


# ---------------------------------------------------------
# EVALUATION FUNCTION
# ---------------------------------------------------------

def evaluate(board):
    """
    Evaluate the board from BLACK/AI's perspective.

    Positive score = good for AI.
    Negative score = good for human.
    """

    score = 0

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):

            piece = board[row][col]

            if piece == BLACK:
                # Basic piece value
                score += 100

                # Reward advancing toward promotion
                score += row * 5

            elif piece == BLACK_KING:
                score += 175

            elif piece == RED:
                score -= 100

                # Red moves toward row 0
                score -= (BOARD_SIZE - 1 - row) * 5

            elif piece == RED_KING:
                score -= 175

    return score


# ---------------------------------------------------------
# MINIMAX + ALPHA-BETA
# ---------------------------------------------------------

def minimax(board, depth, alpha, beta, maximizing_player):
    """
    Minimax adversarial search with alpha-beta pruning.

    AI = BLACK = maximizing player
    Human = RED = minimizing player
    """

    if depth == 0:
        return evaluate(board), None

    if game_over(board, BLACK):
        return -100000, None

    if game_over(board, RED):
        return 100000, None

    if maximizing_player:
        player = BLACK
        best_score = -math.inf
        best_move = None

        legal_moves = get_legal_moves(board, player)

        for move in legal_moves:

            next_board = apply_move(
                board,
                move,
                player
            )

            score, _ = minimax(
                next_board,
                depth - 1,
                alpha,
                beta,
                False
            )

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, best_score)

            # Alpha-beta pruning
            if beta <= alpha:
                break

        return best_score, best_move

    else:
        player = RED
        best_score = math.inf
        best_move = None

        legal_moves = get_legal_moves(board, player)

        for move in legal_moves:

            next_board = apply_move(
                board,
                move,
                player
            )

            score, _ = minimax(
                next_board,
                depth - 1,
                alpha,
                beta,
                True
            )

            if score < best_score:
                best_score = score
                best_move = move

            beta = min(beta, best_score)

            # Alpha-beta pruning
            if beta <= alpha:
                break

        return best_score, best_move


# ---------------------------------------------------------
# MOVE FORMATTING
# ---------------------------------------------------------

def describe_move(move):
    """
    Convert internal move format into readable text.
    """

    if len(move) == 1:
        destination = move[0][0]

        return f"Move to {destination}"

    text = "Capture sequence: "

    for destination, captured in move:
        text += (
            f"capture {captured} -> "
            f"land {destination}; "
        )

    return text


# ---------------------------------------------------------
# HUMAN MOVE INPUT
# ---------------------------------------------------------

def human_move(board):
    """
    Ask the human player to select one legal move.
    """

    legal_moves = get_legal_moves(
        board,
        RED
    )

    print("\nYour legal moves:")

    for i, move in enumerate(legal_moves):
        print(
            f"{i}: {describe_move(move)}"
        )

    while True:

        try:
            choice = int(
                input("\nChoose move number: ")
            )

            if 0 <= choice < len(legal_moves):
                return legal_moves[choice]

            print("Invalid move number.")

        except ValueError:
            print("Please enter a number.")


# ---------------------------------------------------------
# MAIN GAME LOOP
# ---------------------------------------------------------

def play_game():
    """
    Main human vs AI game.
    """

    board = create_board()

    # Search depth.
    # Increase this for stronger AI,
    # but it will take longer.
    AI_DEPTH = 4

    print("\n================================")
    print("       CHECKERS MINI AI")
    print("================================")

    print("\nYou are RED (r/R).")
    print("AI is BLACK (b/B).")
    print("Lowercase = normal piece.")
    print("Uppercase = king.")
    print("\nIMPORTANT:")
    print("Captures are mandatory.")

    current_player = RED

    while True:

        print_board(board)

        if game_over(board, current_player):

            winner = opponent(current_player)

            if winner == BLACK:
                print("AI wins!")
            else:
                print("You win!")

            break

        if current_player == RED:

            move = human_move(board)

            board = apply_move(
                board,
                move,
                RED
            )

        else:

            print(
                "\nAI is thinking..."
            )

            score, move = minimax(
                board,
                AI_DEPTH,
                -math.inf,
                math.inf,
                True
            )

            print(
                f"AI evaluation: {score}"
            )

            print(
                f"AI move: {describe_move(move)}"
            )

            board = apply_move(
                board,
                move,
                BLACK
            )

        current_player = opponent(
            current_player
        )


# ---------------------------------------------------------
# PROGRAM ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    play_game()