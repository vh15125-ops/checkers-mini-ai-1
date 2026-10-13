"""Compare procedural move generation against the independent rule-base on 20 positions."""
import argparse, json, os, random
from checkers import State, AlphaBetaAgent
from checkers.rulebase import rule_based_moves
from checkers.explain import evaluation_breakdown, principal_variation


def signature(moves):
    return sorted((m.path,m.captured) for m in moves)


def reachable_positions(count=20, seed=23):
    rng=random.Random(seed); state=State.initial(); positions=[]
    while len(positions)<count:
        if state.winner() is not None:
            state=State.initial()
        positions.append(state)
        legal=state.legal_moves()
        if not legal: state=State.initial(); continue
        state=state.apply(rng.choice(legal))
    return positions


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--positions',type=int,default=20); ap.add_argument('--output',default='outputs')
    args=ap.parse_args(); os.makedirs(args.output,exist_ok=True)
    states=reachable_positions(args.positions)
    rows=[]
    for i,s in enumerate(states,1):
        procedural=s.legal_moves(); declarative=rule_based_moves(s)
        ok=signature(procedural)==signature(declarative)
        rows.append({'position':i,'turn':s.turn,'procedural_moves':len(procedural),'rulebase_moves':len(declarative),'agreement':ok})
        if not ok:
            print('MISMATCH at position',i,'procedural=',procedural,'rulebase=',declarative)
            raise SystemExit(1)
    path=os.path.join(args.output,'rulebase_agreement.json')
    with open(path,'w',encoding='utf-8') as f: json.dump({'tested':len(rows),'all_agree':all(x['agreement'] for x in rows),'positions':rows},f,indent=2)
    print(f'PASS: rule base and procedural generator agree on {len(rows)} positions. Report: {path}')
    # Explain a move from a reachable mid-game position so feature terms are meaningful.
    state=State.initial(); rng=random.Random(91)
    for _ in range(8):
        legal=state.legal_moves()
        if not legal or state.winner() is not None: state=State.initial(); continue
        state=state.apply(rng.choice(legal))
    agent=AlphaBetaAgent(depth=4); move=agent.choose_move(state)
    breakdown=evaluation_breakdown(state,state.turn)
    explanation={'position':'reachable mid-game position after deterministic playout','side_to_move':state.turn,'chosen_move':str(move),
                 'forced_capture':bool(state.legal_moves()[0].is_capture),
                 'evaluation_breakdown':breakdown,'principal_variation':principal_variation(state,depth=3,max_plies=6)}
    with open(os.path.join(args.output,'explained_move.json'),'w',encoding='utf-8') as f: json.dump(explanation,f,indent=2)
    print('\nEXPLAINED MOVE')
    print('Chosen move:',move,'| side:',state.turn,'| forced capture:',explanation['forced_capture'])
    for k,v in breakdown.items(): print(f'  {k}: {v:.1f}')
    print('Principal variation:', ' -> '.join(x['move'] for x in explanation['principal_variation']))
    print('Explanation saved to outputs/explained_move.json')

if __name__=='__main__': main()
