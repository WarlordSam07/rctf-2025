"""
Transaction Class
"""
class Transaction:
    def __init__(self, proposer_id, answer, signature):
        self.proposer_id = proposer_id
        self.answer = answer
        self.signature = signature 