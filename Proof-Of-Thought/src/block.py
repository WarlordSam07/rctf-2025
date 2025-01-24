import time
import hashlib

"""
Block Class
"""
class Block:
    def __init__(self, previous_hash, transactions, worker_id, signature, round_number, winning_score):
        self.previous_hash = previous_hash
        self.transactions = transactions 
        self.worker_id = worker_id
        self.signature = signature  
        self.timestamp = time.time()
        self.round_number = round_number
        self.score = winning_score

    def compute_hash(self):
        block_string = f"{self.previous_hash}{[tx.answer for tx in self.transactions]}{self.worker_id}{self.timestamp}{self.round_number}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def display(self):
        print(f"""
        +-------------------------------------------------------------------+
        | {self.compute_hash()}  |
        | Worker: {self.worker_id} - Score: {str(self.score).rjust(2, '0')}          |
        +-------------------------------------------------------------------+
        """)