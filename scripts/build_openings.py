import urllib.request
import csv
import json
import chess
import os

import ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def build_db():
    print("Downloading and compiling Lichess Opening Database...")
    openings = {}
    
    letters = ['a', 'b', 'c', 'd', 'e']
    
    for letter in letters:
        url = f"https://raw.githubusercontent.com/lichess-org/chess-openings/master/{letter}.tsv"
        print(f"Fetching {url}...")
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ctx) as response:
                lines = response.read().decode('utf-8').splitlines()
                reader = csv.DictReader(lines, delimiter='\t')
                
                for row in reader:
                    name = row['name']
                    pgn = row['pgn']
                    
                    board = chess.Board()
                    try:
                        tokens = pgn.split()
                        for token in tokens:
                            if '.' in token:
                                continue
                            board.push_san(token)
                            
                        epd = board.epd()
                        openings[epd] = name
                    except Exception as e:
                        continue
        except Exception as e:
            print(f"Error fetching {letter}.tsv: {e}")
            
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "openings.json")
    with open(out_path, "w") as f:
        json.dump(openings, f)
        
    print(f"Successfully compiled {len(openings)} openings into {out_path}!")

if __name__ == "__main__":
    build_db()
