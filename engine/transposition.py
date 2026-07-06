class TranspositionTable:
    def __init__(self):
        self.table = {}
        
    def store(self, key, depth, score, flag, best_move):
        self.table[key] = (depth, score, flag, best_move)
        
    def lookup(self, key):
        return self.table.get(key, None)
