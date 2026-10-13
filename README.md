# Checkers Mini AI - Adversarial Search

A Python implementation of a Checkers AI using adversarial search.

## Features

- Standard 8x8 checkers board
- Legal move generation
- Mandatory capture rule
- Multiple-jump captures
- King promotion
- Minimax adversarial search
- Alpha-beta pruning
- Board evaluation function
- Human vs AI gameplay

## AI Technique

The AI uses Minimax with Alpha-Beta pruning.

The AI plays as Black and tries to maximize the evaluation score.

The human player plays as Red and tries to minimize the evaluation score.

## Forced Capture

Checkers requires a player to capture whenever a capture is available.

The program handles this using:

```python
def get_legal_moves(board, player):
    captures = get_capture_moves(board, player)

    if captures:
        return captures

    return get_normal_moves(board, player)