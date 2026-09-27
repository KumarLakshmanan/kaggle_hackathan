"""Experimental existing-worker variant of the single-goose coop probe."""

import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
DEST = ROOT / "exp_empty_coop_idle_worker_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"
MARKER = "# Kaggle's file loader selects the last newly inserted callable in source"

base_script = Path(__file__).with_name("build_empty_coop_goose_worker.py")
tree = ast.parse(base_script.read_text(encoding="utf8"))
tail_node = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "TAIL" for t in node.targets))
tail = ast.literal_eval(tail_node)
start = tail.index("        if 11 <= day <= 29 and hour == 1:")
end = tail.index("        if state['hand_day'] == day", start)
replacement = '''        if 11 <= day <= 29 and hour == 1:
            market = [list(o) for o in action.get('market', [])]
            parent_hires = sum(o and o[0] == 'HIRE' for o in market)
            count = len(farm['hands']) + parent_hires
            if count > 0:
                native = _IMPL.chassis.players.get(seat, {})
                route = native.get('route', 0)
                def burden(index):
                    score = 0
                    for future in range(step+1, min(day*24+23, 719)):
                        tape = _IMPL.chassis.routes[2 if future >= 648 else route]
                        commands = tape[future].get('hands', [])
                        command = commands[index] if index < len(commands) else ['PASS']
                        op = command[0] if command else 'PASS'
                        score += 5 if op not in ('PASS','NORTH','SOUTH','EAST','WEST') else 1 if op != 'PASS' else 0
                    return score
                state['hand_day'] = day
                state['hand_index'] = min(range(count), key=burden)
                _GOOSE_WORKER_STATS['goose_worker_selections'] += 1
                if len(market) < 10:
                    market.append(['BUY_PRODUCT', 'WHEAT', 1])
                    action = dict(action, market=market)
'''
tail = tail[:start] + replacement + tail[end:]
tail = tail.replace("goose_worker_hires", "goose_worker_selections")

raw = SOURCE.read_text(encoding="utf8")
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
assert raw.count(MARKER) == 1
candidate = raw.replace(MARKER, tail + MARKER)
ast.parse(candidate)
DEST.write_text(candidate, encoding="utf8")
print(DEST, hashlib.sha256(DEST.read_bytes()).hexdigest())
