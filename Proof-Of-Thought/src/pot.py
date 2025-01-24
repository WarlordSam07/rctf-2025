#!/opt/homebrew/bin/python3.10

# Copyright (c) 2025 Fineas Silaghi <https://github.com/Fineas>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# author: FeDEX

import json
import random
import argparse
from tabulate import tabulate

from enum import Enum
from agent import Agent
from block import Block
from utils import *

"""
Constants
"""
DEBUG = True
SEPARATOR_LEN = 72
ROUND_BONUS = 5
VOTE_REWARD = 25
EVAL_PROMPT = load_eval_prompt("../prompts/eval_prompt.txt")

"""
Globals
"""
blockchain = None
agent007 = None
inputs = {}

"""
Enums
"""
class Role(Enum):
    WORKER = 'worker' # answer proposer
    MINER = 'miner'   # answer evaluator

"""
Debug
"""
def display_banner():
    print(
        """
 ____                   __              __     _____ _                       _     _   
|  _ \ _ __ ___   ___  / _|       ___  / _|   |_   _| |__   ___  _   _  __ _| |__ | |_ 
| |_) | '__/ _ \ / _ \| |_ _____ / _ \| |_ _____| | | '_ \ / _ \| | | |/ _` | '_ \| __|
|  __/| | | (_) | (_) |  _|_____| (_) |  _|_____| | | | | | (_) | |_| | (_| | | | | |_ 
|_|   |_|  \___/ \___/|_|        \___/|_|       |_| |_| |_|\___/ \__,_|\__, |_| |_|\__|
                                                                       |___/           
        """
    )

def display_agents(agents_dict):
    i = 1
    table = []
    headers = ["No", "Agent ID", "Stake", "Role", "Malicious"]
    for agent_id, agent in agents_dict.items():
        table.append([i, print_blue(agent_id), print_green(agent.stake), agent.role, print_red("True") if agent.is_malicious else "False"])
        i += 1
    print(f" {print_bold('Agents')}")
    print(tabulate(table, headers, tablefmt="grid"))
    print("")

def display_workers_header():
    print(f" {print_bold('Workers')}")
    print("-"*SEPARATOR_LEN)

def display_miners_header():
    print(f"\n {print_bold('Miners')}")
    print("-"*SEPARATOR_LEN)

def display_consensus_header(status):
    print(f"\n {print_bold('Consensus') }-", print_green("REACHED") if status else print_red("NOT REACHED"))
    print("-"*SEPARATOR_LEN)

def display_round_results(round_no, evaluations):
    header_id = list(evaluations.keys())[0]
    headers = [f"ID - Round {round_no}"] + list(evaluations[header_id].keys())

    table = []
    for evaluator_id, scores in evaluations.items():
        row = [print_blue(evaluator_id)] + [scores[score_id] for score_id in headers[1:]]
        table.append(row)

    print(tabulate(table, headers, tablefmt="grid"))

def display_round(task, round_no, dataset):
    if dataset == 1:
        dataset = 'gsm8k' 
    elif dataset == 2:
        dataset = 'mmlu' 
    else:
        dataset = 'unknown' 
    print(f" {print_bold(f'Round {round_no} - {dataset}')}")
    print(f" {print_bold('Task')}: {task}")
    print("-"*SEPARATOR_LEN+'\n')

"""
Methods
"""
def assign_roles(agents, num_miners, flag=1):
    # Assign roles based on stake
    agents_sorted = sorted(agents, key=lambda x: x.stake, reverse=True)
    if flag:
        workers = agents_sorted[:num_miners]
        miners = agents_sorted[num_miners:]
    else:
        miners = agents_sorted[:num_miners]
        workers = agents_sorted[num_miners:]

    for agent in miners:
        agent.role = Role.MINER
    for agent in workers:
        agent.role = Role.WORKER

    return miners, workers

def debate_and_vote(miners, miner_evaluations):
    votes = {}
    voter_map = {}

    for miner in miners:
        preferred_workers, _score = miner.select_preferred_evaluation(miner_evaluations)
        for worker_id in preferred_workers:
            votes[worker_id] = votes.get(worker_id, 0) + 1

            if miner.id not in voter_map:
                voter_map[miner.id] = []
            voter_map[miner.id].append(miner.id)

    print(f"\n[*] Voting Results: {votes}\n")

    max_votes = max(votes, key=votes.get)
    max_votes = votes[max_votes]
    workers_max_votes = [k for k,v in votes.items() if v == max_votes]

    # Check if any worker has majority votes
    if len(workers_max_votes) == 1:
        if max_votes > len(miners) / 2:
            return max_votes, workers_max_votes[0], voter_map # Consensus reached
        else:
            return False, None, None # Consensus not consensus
    else:
        return False, None, None # Consensus not consensus

def consensus(miners, workers, transactions, agent_dict, max_rounds=2):
    round_number = 1
    while round_number < max_rounds:
        # Each miner evaluates all proposals
        miner_evaluations = {}
        for miner in miners:
            print(f"[*] Agent {print_blue(miner.id)} - {miner.role}", print_red("MALICIOUS") if miner.is_malicious else "")
            evals = miner.evaluate_proposals(transactions, agent_dict, EVAL_PROMPT)
            miner_evaluations[miner.id] = evals

        # === DEBUG ===
        display_round_results(round_number, miner_evaluations)

        # Debate and vote
        consensus_reached, winning_worker_id, winning_voters = debate_and_vote(miners, miner_evaluations)
        display_consensus_header(consensus_reached)
        if consensus_reached:
            # Winning worker creates the block
            winning_worker = next((w for w in workers if w.id == winning_worker_id), None)
            block = create_block(winning_worker, transactions, miner_evaluations, agent_dict, round_number, consensus_reached, winning_voters)
            return block 
        else:
            round_number += 1

    # If no consensus, return None
    return None

def create_block(winning_worker, transactions, evaluations, agent_dict, round_number, winning_score, winning_voters):
    previous_hash = blockchain[-1].compute_hash() if blockchain else '0' * 64
    signature = winning_worker.sign_data(previous_hash)
    block = Block(previous_hash, transactions, winning_worker.id, signature, round_number, winning_score)
    
    # Update stakes based on evaluations
    update_stakes(evaluations, winning_worker, agent_dict, round_number, winning_voters)

    blockchain.append(block)
    return block

def update_stakes(evaluations, miner, agent_dict, round_number, winning_voters):
    # Update miner stake based on evaluations
    for evaluator_id, evals in evaluations.items():
        for proposer_id, score in evals.items():
            proposer = agent_dict[proposer_id]
            if proposer.role == Role.WORKER:
                proposer.stake += score

    # Winning Miner gets bonus reward based
    miner.stake += ROUND_BONUS

    # Reward miners who voted for the winning response
    for voter_id in winning_voters:
        voter = agent_dict[voter_id]
        voter.stake +=  VOTE_REWARD

def simulate(arg_agn, arg_min, arg_mal, rounds=1):
    global agent007

    num_agents = arg_agn     # Number of agents
    num_miners = arg_min     # Number of miners
    num_malicious = arg_mal  # Number of malicious agents
    agents = []

    # == DEBUG == 
    display_banner()

    # Initialize agents
    for i in range(num_agents):
        if i < num_malicious:
            agent = Agent(is_malicious=True)
        else:
            agent = Agent(is_malicious=False)
        agents.append(agent)

    agent_dict = {agent.id: agent for agent in agents}
    agent007 = agents[0]

    # Initialize blockchain
    global blockchain
    blockchain = []

    # Run <rounds> Simulations
    for i in range(rounds):

        # Define the Task
        dataset, task = load_task()

        # === DEBUG === 
        display_round(task, i, dataset)

        '''
        role assignment, 
        proposal statement, 
        evaluation,
        and decision-making.
        '''

        # Assign Roles
        miners, workers = assign_roles(agents, num_miners)

        # === DEBUG === 
        display_agents(agent_dict)

        # === DEBUG ===
        display_workers_header()
        
        # Generate proposals
        transactions = []
        for worker in workers:
            print(f"[*] Agent {print_blue(worker.id)} - {worker.role}", print_red("MALICIOUS") if worker.is_malicious else "")
            answer, tx = worker.generate_proposal(task)
            if tx:
                print("    >", print_yellow(answer), '\n'+'-'*SEPARATOR_LEN)
                transactions.append(tx)
                if worker.is_malicious:
                    inputs[f"Round {i}"] = answer
            else:
                print("    > No proposal generated.\n")

        # === DEBUG ===
        display_miners_header()

        # Run the Consensus
        block = consensus(miners, workers, transactions, agent_dict)
        if block:
            print(f"[*] Winning worker: {print_blue(block.worker_id)}")
            print(f"[*] Block hash: {print_bold(block.compute_hash())}")
            print("[*] Final answer selected:")
            # Assuming the highest scored answer is selected
            highest_score = -1
            selected_answer = None
            for tx in block.transactions:
                proposer = agent_dict[tx.proposer_id]
                score = proposer.stake
                if score > highest_score:
                    highest_score = score
                    selected_answer = tx.answer
            print(print_green(selected_answer))
            print()
        else:
            print("Consensus not achieved within the maximum rounds.\n")

def init():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('-r', '--rounds', type=int, nargs='?', const=1, default=1, help='Number of rounds')
    p.add_argument('-a', '--agents', type=int, nargs='?', const=6, default=6, help='Number of agents')
    p.add_argument('-w', '--workers', type=int, nargs='?', const=3, default=3, help='Number of workers')
    p.add_argument('-m', '--malicious', type=int, nargs='?', const=1, default=1, help='Number of malicious agents')
    return p.parse_args()

if __name__ == "__main__":
    
    args = init()
    (rounds, arg_a, arg_w, arg_m) = (args.rounds, args.agents, args.workers, args.malicious)
    # print(f"Number of agents: {arg_a}")
    # print(f"Number of workers: {arg_w}")
    # print(f"Number of malicious agents: {arg_m}")

    n = 22
    challenge = random_string()
    print('[*] https://oooverflow.io/pow.py')
    print('[*] Challenge: {}'.format(challenge))
    print('[*] Solution: ')
    sys.stdout.flush()
    solution = input().strip()

    if not check_pow_backdoor(challenge, n, solution):
        print('[!] Invalid')
        sys.exit(1)

    simulate(arg_a, arg_w, arg_m, rounds=rounds)

    # === DEBUG ===
    print("< Chain Status >".rjust(50, ' '))
    for b in blockchain:
        b.display()
        if len(blockchain) > 1:
            print(' '*41+"|")

    if agent007.stake >= 114:
        print("[*] "+print_green("Congratulations!")+" You have successfully corrupted the consensus 👏")
        print("[*] Do you agree to submit your solution for research purposes? (y/n):")
        if input("> ").strip().lower() == 'y': # <3
            team_name = input("Enter your team name > ")
            store_exploit_string(inputs, team_name)
        
        print(os.getenv('FLAG'))