
# Sample Game

Small 2D top-down bullet hell game with a roguelike boss ladder:

- Boss HP scales up every level.
- After each boss clear, pick **1 of 3** random upgrades.
- Difficulty (Easy/Normal/Hard) sets the base boss HP and heal pickup frequency.

## Requirements

- Python 3
- macOS/Windows/Linux

Dependencies are in `requirements.txt`.

## Install

### Option A: Recommended (virtual environment)

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Option B: System install

```bash
python3 -m pip install -r requirements.txt
```

## Run

```bash
python3 main.py
```

If you see `ModuleNotFoundError: No module named 'pygame'`, you installed `pygame` into a different Python environment than the one running `main.py`. Using the `.venv` setup above avoids that.

## Controls

- **Move**: `WASD` or arrow keys
- **Slow/focus**: hold `Shift`
- **Shoot**: hold `Z` or `Space`
- **Super**: `X`
- **Pause**: `P`

## Menus

- Start menu has **Play**, **Options**, and **Quit**.
- Options let you change **player/enemy colors** and **difficulty**.

## Roguelike flow

- Defeat the boss to reach a **Level Cleared** upgrade screen.
- Pick an upgrade by clicking or pressing `1`/`2`/`3`.
- Boss bullet patterns are randomized per level.
