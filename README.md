# Python Chess Engine

**Created by Abdulazizxon Saydaliyev**

A fully-functional, ultra-fast Python chess engine powered by Cython C-extensions with a custom Tkinter Graphical User Interface.

## Features
* **Cython-Optimized Core**: The engine's core math logic is statically typed and compiled into C (`.so` extensions) for massive performance gains, effortlessly supporting search depths from 1 to 8.
* **Algorithmic Intelligence**: Implements Alpha-Beta Negamax search, MVV-LVA move ordering, and Quiescence Search to prevent horizon-effect blunders.
* **Positional & Theoretical Mastery**: 
  * Uses PeSTO's Piece-Square Tables for strong positional and developmental understanding.
  * Integrated Polyglot Opening Book (`komodo.bin`) for Grandmaster-level variety and theoretical play in the opening phase.
* **Modern GUI**: Built natively in Tkinter, featuring:
  * Smooth drag-and-drop piece movement (and click-to-move fallback)
  * Scrollable Move History sidebar with standard algebraic notation
  * Dynamic Evaluation bar showing real-time engine advantage
  * Interactive arrows (right-click and drag) and square highlights (right-click)
  * Visual indicators for legal moves and captures
  * "Flip Sides" feature to play as Black (automatically inverts coordinates and UI)
  * Undo and Restart functionality

## Prerequisites
* Python 3.8+
* A C-Compiler (like Apple Clang or GCC) to compile the Cython extensions
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

4. Compile the engine into C-extensions:
   ```bash
   python3 setup.py build_ext --inplace
   ```

## Running the Game

To launch the GUI and play against the engine:
```bash
python3 gui.py
```

## Graphics
The engine uses custom PNG piece sets loaded automatically from the local `images/` directory. If the folder is missing, the GUI will gracefully fall back to using standard Unicode chess characters to render the board.
