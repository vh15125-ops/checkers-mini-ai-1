"""CSP-based round-robin scheduler and AI tournament runner.

Run: python tournament.py --games-per-round 2 --rooms 2
Outputs: outputs/tournament_schedule.csv, results.csv, game_logs.jsonl
"""
from __future__ import annotations
import argparse, csv, json, os
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Set, Tuple
from checkers import AlphaBetaAgent, State, WHITE, BLACK
from checkers.explain import evaluation_breakdown, principal_variation

@dataclass(frozen=True)
class Player:
    name: str
    depth: int
    unavailable: frozenset = frozenset()  # slot labels such as "R2-S1"

@dataclass
class GameSlot:
    round_no: int
    slot: str
    board: int


def round_robin(players: List[Player]):
    """Circle-method pairings; supports odd player counts with a bye."""
    names = [p.name for p in players]
    if len(names) % 2:
        names.append("BYE")
    rounds, arr = [], names[:]
    for _ in range(len(arr)-1):
        pairs = [(arr[i], arr[-1-i]) for i in range(len(arr)//2)]
        rounds.append([(a,b) for a,b in pairs if a != 'BYE' and b != 'BYE'])
        arr = [arr[0], arr[-1], *arr[1:-1]]
    return rounds


def schedule_csp(players: List[Player], rooms=2, slots_per_round=2):
    """Backtracking + forward checking over game-to-slot/board assignments."""
    pair_rounds = round_robin(players)
    by_name = {p.name:p for p in players}
    assignments, schedule = {}, []
    for round_no, pairings in enumerate(pair_rounds, 1):
        candidates = [GameSlot(round_no, f"R{round_no}-S{s+1}", b+1)
                     for s in range(slots_per_round) for b in range(rooms)]
        # Each player can only be in one game per round; pairings are already disjoint.
        domains = {i:[c for c in candidates
                      if c.slot not in by_name[a].unavailable and c.slot not in by_name[b].unavailable]
                   for i,(a,b) in enumerate(pairings)}
        if any(not d for d in domains.values()):
            raise ValueError(f"No available slot for round {round_no}; increase slots/rooms or change unavailability")
        chosen = {}
        def backtrack(remaining, used_slot_board):
            if not remaining:
                return True
            # MRV: choose the game with the fewest currently available slots.
            best = min(remaining, key=lambda i: sum((c.slot,c.board) not in used_slot_board for c in domains[i]))
            options = [c for c in domains[best] if (c.slot,c.board) not in used_slot_board]
            for c in options:
                # Forward check: every other unassigned game must retain a domain.
                used_slot_board.add((c.slot,c.board)); chosen[best] = c
                rest = [i for i in remaining if i != best]
                if all(any((x.slot,x.board) not in used_slot_board for x in domains[i]) for i in rest):
                    if backtrack(rest, used_slot_board): return True
                used_slot_board.remove((c.slot,c.board)); chosen.pop(best,None)
            return False
        if not backtrack(list(range(len(pairings))), set()):
            raise ValueError(f"CSP could not schedule round {round_no}; increase board/slot capacity")
        # Balance colours greedily: the player with fewer white assignments gets White.
        for i,(a,b) in enumerate(pairings):
            wa = sum(1 for g in schedule if g['white']==a)
            wb = sum(1 for g in schedule if g['white']==b)
            white, black = (a,b) if wa <= wb else (b,a)
            c = chosen[i]
            schedule.append({"round":round_no,"slot":c.slot,"board":c.board,"white":white,"black":black})
    return schedule


def run_tournament(players, schedule, output_dir='outputs', max_plies=180):
    os.makedirs(output_dir, exist_ok=True)
    lookup = {p.name:p for p in players}
    results, logs = [], []
    for game_no, item in enumerate(schedule, 1):
        state = State.initial(); moves_log=[]
        while state.winner() is None and len(moves_log) < max_plies:
            name = item['white'] if state.turn == WHITE else item['black']
            player = lookup[name]
            agent = AlphaBetaAgent(depth=player.depth)
            legal = state.legal_moves()
            move = agent.choose_move(state)
            assert move in legal
            moves_log.append({"ply":len(moves_log)+1,"player":name,"colour":state.turn,
                              "move":str(move),"forced_capture":bool(legal and legal[0].is_capture),
                              "search_depth":agent.stats.depth_reached,"nodes":agent.stats.nodes,
                              "evaluation_breakdown":evaluation_breakdown(state,state.turn),
                              "principal_variation":principal_variation(state,depth=min(player.depth,2),max_plies=4)})
            state = state.apply(move)
        outcome = state.winner()
        if outcome is None: outcome = 'draw' # tournament safety cap
        winner_name = item['white'] if outcome == WHITE else item['black'] if outcome == BLACK else 'draw'
        row = {**item,"game":game_no,"result":winner_name,"plies":len(moves_log)}
        results.append(row)
        logs.append({"game":game_no,"schedule":item,"result":row,"moves":moves_log})
    for filename, rows in [('tournament_schedule.csv',schedule),('results.csv',results)]:
        if rows:
            with open(os.path.join(output_dir,filename),'w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with open(os.path.join(output_dir,'game_logs.jsonl'),'w',encoding='utf-8') as f:
        for game in logs: f.write(json.dumps(game)+'\n')
    return results


def main():
    ap=argparse.ArgumentParser(description='CSP-scheduled checkers AI tournament')
    ap.add_argument('--rooms',type=int,default=2); ap.add_argument('--slots-per-round',type=int,default=2)
    ap.add_argument('--max-plies',type=int,default=120); ap.add_argument('--output',default='outputs')
    args=ap.parse_args()
    players=[Player('Depth-1',1),Player('Depth-2',2),Player('Depth-3',3),Player('Depth-4',4)]
    schedule=schedule_csp(players,args.rooms,args.slots_per_round)
    results=run_tournament(players,schedule,args.output,args.max_plies)
    print('\nTOURNAMENT SCHEDULE')
    for g in schedule: print(f"Round {g['round']} | {g['slot']} | Board {g['board']} | White {g['white']} vs Black {g['black']}")
    print('\nRESULTS')
    for r in results: print(f"Game {r['game']}: {r['white']} vs {r['black']} -> {r['result']} ({r['plies']} plies)")
    print(f"\nSaved CSV schedule/results and full accountability logs in: {args.output}/")

if __name__=='__main__': main()
