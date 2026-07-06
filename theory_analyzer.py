import urllib.request
import urllib.parse
import json
import chess
import chess.pgn
import io
import ssl
import time
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_games(username):
    headers = {'User-Agent': 'python-chess-engine/1.0'}
    req = urllib.request.Request(f"https://api.chess.com/pub/player/{username.lower()}/games/archives", headers=headers)
    with urllib.request.urlopen(req, context=ctx) as response:
        archives = json.loads(response.read().decode('utf-8'))['archives']
        
    url = archives[-1]
    print(f"Fetching {url}...")
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        return data['games']

def get_master_moves(epd):
    url = f"https://explorer.lichess.ovh/masters?fen={urllib.parse.quote(epd)}"
    req = urllib.request.Request(url, headers={"User-Agent": "AuraChess/1.0"})
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return None

def build_flashcards():
    username = "AbdulazizxonChess"
    games = fetch_games(username)
    
    # Check if flashcards already exist to append
    flashcards = []
    seen_epds = set()
    if os.path.exists("data/flashcards.json"):
        with open("data/flashcards.json", "r") as f:
            flashcards = json.load(f)
            for card in flashcards:
                seen_epds.add(card['epd'])
    
    print(f"Analyzing {len(games)} recent games for opening mistakes...")
    
    added_count = 0
    for game_data in reversed(games): # Most recent games first
        pgn_str = game_data.get('pgn')
        if not pgn_str: continue
        
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        if not game: continue
        
        headers = game.headers
        white_player = headers.get("White", "").lower()
        target_color = chess.WHITE if white_player == username.lower() else chess.BLACK
        
        board = game.board()
        ply_count = 0
        
        for move in game.mainline_moves():
            if ply_count > 16: break # Only check first 8 full moves
            
            if board.turn == target_color:
                epd = board.epd()
                if epd not in seen_epds:
                    seen_epds.add(epd)
                    
                    # Check Lichess
                    time.sleep(0.1) # Rate limit
                    master_data = get_master_moves(epd)
                    if master_data and master_data.get('white', 0) + master_data.get('black', 0) + master_data.get('draws', 0) > 50:
                        master_moves = master_data.get('moves', [])
                        
                        if master_moves:
                            top_move = master_moves[0]['uci']
                            
                            user_move_uci = move.uci()
                            user_in_masters = False
                            total_master_plays = sum(m['white'] + m['black'] + m['draws'] for m in master_moves)
                            
                            if total_master_plays > 50:
                                if user_move_uci != top_move:
                                    print(f"Mistake found! User played {user_move_uci}, Master prefers {top_move}")
                                    flashcards.append({
                                        "epd": epd,
                                        "user_move": user_move_uci,
                                        "correct_move": top_move,
                                        "interval": 1,
                                        "next_review": 0
                                    })
                                    added_count += 1
                                    break # Stop analyzing this game
            
            board.push(move)
            ply_count += 1
            
        if added_count >= 10: # Fetch 10 mistakes
            break

    os.makedirs("data", exist_ok=True)
    with open("data/flashcards.json", "w") as f:
        json.dump(flashcards, f, indent=4)
    print(f"Generated {added_count} new personalized opening flashcards!")

if __name__ == "__main__":
    build_flashcards()
