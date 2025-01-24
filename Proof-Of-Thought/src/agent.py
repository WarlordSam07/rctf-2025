#!/opt/homebrew/bin/python3.10
import sys
import uuid
import json
import ollama

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from utils import *
from transaction import Transaction

MAX_INPUT_LEN = 550

"""
Agent Class
"""
class Agent:
    def __init__(self, is_malicious=False):
        self.id = str(uuid.uuid4())
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.stake = 0
        self.role = None  # 'worker' (answer proposer) or 'miner' (answer evaluator)
        self.is_malicious = is_malicious

    def sign_data(self, data):
        signature = self.private_key.sign(
            data.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return signature

    def verify_signature(self, public_key, signature, data):
        try:
            public_key.verify(
                signature,
                data.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def read_user_input(self, sentinel="END"):
        lines = []
        while True:
            line = input()
            if sentinel in line:
                break
            lines.append(line.strip())
        return "\n".join(lines)

    def generate_proposal(self, task):
        if self.is_malicious:
            if self.role.value == "worker":
                answer = self.read_user_input()
            else:
                answer = self.generate_statement(task)
        else:
            answer = self.generate_statement(task)
        
        if len(answer) > MAX_INPUT_LEN:
            answer = answer[:MAX_INPUT_LEN]

        if answer == "":
            return (None, None)
        else:
            signature = self.sign_data(answer)
            return (answer, Transaction(self.id, answer, signature))

    def generate_statement(self, prompt, model_name='llama3.1:latest'):
        try:
            # Construct the command to run Ollama
            response = ollama.chat(
                model = model_name,  
                messages = [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature':0.7,
                },
            )
            content = response.get('message', {}).get('content', "")
            return content.strip()
        except Exception as e:
            print(f"[!] Error generating text with Ollama: {e}")
            return ""

    def evaluate_proposals(self, transactions, agent_dict, evaluation_prompt):
        evaluations = {}
        for tx in transactions:
            proposer = agent_dict[tx.proposer_id]
            if not self.verify_signature(proposer.public_key, tx.signature, tx.answer):
                continue
            print(" >", print_underline(tx.proposer_id))
            score = self.multi_metric_evaluation(evaluation_prompt.format(answer=tx.answer))
            evaluations[tx.proposer_id] = score
        return evaluations

    def multi_metric_evaluation(self, prompt):
        score_text, _tx = self.generate_proposal(prompt)
        print('   >',score_text, '<')
        try:
            score = float(score_text.strip().split()[0])
            if score < 0.0:
                score = 0.0
            if score > 11.0:
                score = 10.0
        except Exception:
            score = 0.0
        return score

    def select_preferred_evaluation(self, miner_evaluations):
        top_scores = []
        max_score = 0
        for miner_id, evaluations in miner_evaluations.items():
            if miner_id == self.id:
                for worker_id, score in evaluations.items():
                    if score > max_score:
                        max_score = score
                        top_scores = []
                        top_scores.append(worker_id)
                    elif score == max_score:
                        top_scores.append(worker_id)
                    else:
                        continue
        return (top_scores, max_score)