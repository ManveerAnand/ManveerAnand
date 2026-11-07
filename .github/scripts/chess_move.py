"""Play one move of the README chess game: visitors are white, Manveer is black.

Issue titles look like  chess|<code>|e2e4  (visitors need the access code).
Usage:
  python chess_move.py            # TITLE and AUTHOR come from the environment
  python chess_move.py --reset    # start a new game
Writes chess/state.json, chess/board.svg, the README's chess block, and a
reply file in the temp dir (the comment posted back on the issue). The title is untrusted
input, so it is only ever parsed here, never passed through a shell.
"""
import json
import os
import re
import sys
import tempfile
import urllib.parse

import chess
import chess.svg

OWNER = "ManveerAnand"
CODE = "40549fMA"
REPO = "https://github.com/ManveerAnand/ManveerAnand"
HERE = os.path.join(os.path.dirname(__file__), "..", "..")
STATE = os.path.join(HERE, "chess", "state.json")
BOARD = os.path.join(HERE, "chess", "board.svg")
REPLY = os.path.join(os.environ.get("RUNNER_TEMP", tempfile.gettempdir()), "chess-reply.md")
README = os.path.join(HERE, "README.md")
START, END = "<!-- CHESS:START -->", "<!-- CHESS:END -->"


def load():
    if not os.path.exists(STATE):
        return {"fen": chess.STARTING_FEN, "moves": [], "games": 0}
    with open(STATE, encoding="utf-8") as f:
        return json.load(f)


def save(state, board):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)
    last = chess.Move.from_uci(state["moves"][-1]["uci"]) if state["moves"] else None
    svg = chess.svg.board(board, size=360, lastmove=last, colors={
        "square light": "#93a6c4", "square dark": "#3c5296",
        "square light lastmove": "#fcca1b", "square dark lastmove": "#c9a114",
        "margin": "#080c18", "coord": "#edf4ff"})
    with open(BOARD, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    write_readme(state, board)


def move_link(move, board):
    title = f"chess|ENTER-CODE|{move.uci()}"
    body = ("Replace ENTER-CODE in the title with the access code from my terminal, "
            "then press Submit. Your move is played within a minute or so.")
    q = urllib.parse.urlencode({"title": title, "body": body})
    return f'<a href="{REPO}/issues/new?{q}">{board.san(move)}</a>'


def write_readme(state, board):
    lines = ['<p align="center"><img src="./chess/board.svg" width="360" alt="Current chess board" /></p>', ""]
    recent = state["moves"][-6:]
    if recent:
        log = " · ".join(f'{m["san"]} <sub>@{m["by"]}</sub>' for m in recent)
        lines += [f'<p align="center"><sub>last moves: {log}</sub></p>', ""]
    if board.turn == chess.WHITE:
        moves = sorted(board.legal_moves, key=lambda m: board.san(m))
        lines += ['<p align="center"><b>Your move (white).</b> Pick one, swap in the access code, submit.</p>', "",
                  '<p align="center">' + " ".join(move_link(m, board) for m in moves) + "</p>"]
    else:
        lines += ['<p align="center"><b>Waiting for Manveer (black)…</b> Come back in a bit.</p>']
    with open(README, encoding="utf-8") as f:
        text = f.read()
    i, j = text.index(START) + len(START), text.index(END)
    text = text[:i] + "\n" + "\n".join(lines) + "\n" + text[j:]
    with open(README, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def reply(msg):
    with open(REPLY, "w", encoding="utf-8", newline="\n") as f:
        f.write(msg + "\n")
    print(msg)


def play(title, author):
    m = re.fullmatch(r"\s*chess\|([^|]*)\|([a-h][1-8][a-h][1-8][qrbn]?)\s*", title or "")
    if not m:
        return reply("That title doesn't look like a move. Use a move link from my README.")
    code, uci = m.group(1).strip(), m.group(2)
    is_owner = author.lower() == OWNER.lower()
    if not is_owner and code != CODE:
        return reply("Access denied: wrong code. It's printed in my terminal, after `ssh guest@manveer.world`.")
    state = load()
    board = chess.Board(state["fen"])
    if board.turn == chess.BLACK and not is_owner:
        return reply("It's Manveer's turn (black). Check back after he moves.")
    if board.turn == chess.WHITE and is_owner:
        return reply("White is for visitors. Wait for someone to move.")
    move = chess.Move.from_uci(uci)
    if move not in board.legal_moves:
        return reply(f"`{uci}` isn't a legal move right now. Pick one from the README.")
    san = board.san(move)
    board.push(move)
    state["moves"].append({"uci": uci, "san": san, "by": author})
    state["fen"] = board.fen()
    msg = f"Manveer played **{san}**. White to move." if is_owner else f"Played **{san}**. Thanks @{author}!"
    if board.is_game_over():
        result = board.result()
        msg += f" Game over: {result}. A new game has started."
        state = {"fen": chess.STARTING_FEN, "moves": [], "games": state.get("games", 0) + 1}
        board = chess.Board()
    elif board.turn == chess.BLACK:
        msg += f" Your move, @{OWNER}."
    save(state, board)
    reply(msg)


if __name__ == "__main__":
    if "--reset" in sys.argv:
        save({"fen": chess.STARTING_FEN, "moves": [], "games": 0}, chess.Board())
    else:
        play(os.environ.get("TITLE", ""), os.environ.get("AUTHOR", ""))
