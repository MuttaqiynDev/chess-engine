import urllib.request
import json
import chess
import chess.pgn
import io
import os
from collections import defaultdict

import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def build_user_book(username="AbdulazizxonChess"):
    print(f"Fetching archives for {username}...")
    headers = {'User-Agent': 'python-chess-engine/1.0 (abdulazizxonchess@gmail.com)'}
    req = urllib.request.Request(f"https://api.chess.com/pub/player/{username.lower()}/games/archives", headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            archives = json.loads(response.read().decode('utf-8'))['archives']
    except Exception as e:
        print(f"Error fetching archives: {e}")
        return
        
    # Get last 6 months
    archives = archives[-6:]
    
    user_book = defaultdict(lambda: defaultdict(int))
    total_games = 0
    
    for url in archives:
        print(f"Fetching {url}...")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, context=ctx) as response:
                data = json.loads(response.read().decode('utf-8'))
                games = data['games']
                
                for game_data in games:
                    pgn_str = game_data.get('pgn')
                    if not pgn_str:
                        continue
                        
                    pgn = io.StringIO(pgn_str)
                    game = chess.pgn.read_game(pgn)
                    if not game: continue
                    
                    total_games += 1
                    
                    headers_dict = game.headers
                    white_player = headers_dict.get("White", "").lower()
                    black_player = headers_dict.get("Black", "").lower()
                    
                    target_color = None
                    if white_player == username.lower():
                        target_color = chess.WHITE
                    elif black_player == username.lower():
                        target_color = chess.BLACK
                        
                    if target_color is None:
                        continue
                        
                    board = game.board()
                    for move in game.mainline_moves():
                        if board.turn == target_color:
                            epd = board.epd()
                            user_book[epd][move.uci()] += 1
                        board.push(move)
        except Exception as e:
            print(f"Error processing {url}: {e}")
            
    final_book = {}
    for epd, moves_dict in user_book.items():
        total = sum(moves_dict.values())
        final_book[epd] = {m: c/total for m, c in moves_dict.items()}
        
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "user_book.json")
    with open(out_path, "w") as f:
        json.dump(final_book, f)
        
    print(f"Successfully processed {total_games} games and saved {len(final_book)} positions to {out_path}")

if __name__ == "__main__":
    build_user_book()
