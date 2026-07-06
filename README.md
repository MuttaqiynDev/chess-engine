# Python Chess Engine

**Created by Abdulazizxon Saydaliyev**

A fully-functional, lightweight Python chess engine with a custom Tkinter Graphical User Interface.

## Features
* **Custom Engine**: Implements Alpha-Beta Negamax search, MVV-LVA move ordering, and Quiescence Search to prevent horizon-effect blunders.
* **Positional Intelligence**: Uses PeSTO's Piece-Square Tables for strong positional and developmental understanding.
* **Modern GUI**: Built in Tkinter, featuring:
  * Smooth drag-and-drop piece movement (and click-to-move fallback)
  * Dynamic Evaluation bar showing real-time engine advantage
  * Interactive arrows (right-click and drag) and square highlights (right-click)
  * Visual indicators for legal moves and captures
  * Difficulty selector (controls engine search depth)
  * Undo and Restart functionality

## Prerequisites
* Python 3.8+
* Native macOS/Linux/Windows support

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd chess-engine
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

To launch the GUI and play against the engine:
```bash
python3 gui.py
```

## Graphics Note
By default, the engine uses robust Unicode characters to render the chess pieces. 
If you wish to use custom images (like classic PNG piece sets), the engine will automatically look for them in the `~/Downloads/pieces-png/` directory (named `white-king.png`, `black-pawn.png`, etc.). If they are found, it uses Pillow (PIL) to elegantly scale and render them onto the board.
