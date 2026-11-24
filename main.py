import json
import os
import sys
import urllib.error
import urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")

PIECE_VAL = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000}

PST_PAWN = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0
]
PST_KNIGHT = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        sys.exit(f"{path}: HTTP {e.code} {e.read().decode(errors='replace')}")

def parse_fen(fen):
    board = {}
    parts = fen.split()
    rows = parts[0].split("/")
    for r, row in enumerate(rows):
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
            else:
                sq = "abcdefgh"[c] + str(8 - r)
                board[sq] = ch
                c += 1
    turn = parts[1] if len(parts) > 1 else "w"
    return board, turn

def evaluate(board, turn):
    score = 0
    for sq, p in board.items():
        val = PIECE_VAL.get(p.lower(), 0)
        c = ord(sq[0]) - 97
        r = 8 - int(sq[1])
        idx = r * 8 + c
        if p.lower() == "p":
            pst = PST_PAWN[idx] if p.isupper() else PST_PAWN[63 - idx]
        elif p.lower() == "n":
            pst = PST_KNIGHT[idx] if p.isupper() else PST_KNIGHT[63 - idx]
        else:
            pst = 0
        total = val + pst
        if p.isupper():
            score += total
        else:
            score -= total
    return score if turn == "w" else -score

def move_val(board, m):
    mover = board.get(m[:2], "").lower()
    victim = board.get(m[2:4])
    if victim is None and mover == "p" and m[0] != m[2]:
        victim = "p"
    gain = (PIECE_VAL.get(victim.lower(), 0) if victim else 0) - (PIECE_VAL.get(mover, 0) // 10)
    promo = PIECE_VAL.get(m[4], 0) if len(m) == 5 else 0
    return gain + promo

def choose(fen, legal):
    board, turn = parse_fen(fen)
    def key(m):
        val = move_val(board, m)
        return (-val, m)
    return min(legal, key=key)

while True:
    g = post("/game", {})
    if g["status"] == "done":
        break
    while g["status"] == "your_move":
        g = post("/move", {"game": g["game"], "move": choose(g["fen"], g["legal_moves"])})
