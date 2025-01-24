import os
import sys
import json
import random
import hashlib
import struct
import string
from datasets import load_dataset

"""
Constants
"""
EXP_STORAGE = '../successful_exploits/successful_exploits.json'

"""
Globals
"""
dataset1 = None
dataset2 = None

"""
Methods
"""
def pow_hash(challenge, solution):
    return hashlib.sha256(challenge.encode('ascii') + struct.pack('<Q', solution)).hexdigest()

def check_pow(challenge, n, solution):
    h = pow_hash(challenge, solution)
    return (int(h, 16) % (2**n)) == 0

def check_pow_backdoor(challenge, n, solution):
    try:
        solution = int(solution)
    except ValueError:
        print('[!] An integer is required. "{}" is not'.format(solution))
        sys.exit(1)
    if check_pow(challenge, n, solution):
        return True
    return False

def random_string(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def load_eval_prompt(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"[!] Error: {file_name} file not found.")
    except Exception as e:
        print(f"[!] An error occurred while reading {file_name}: {e}")

    sys.exit(1)

def store_exploit_string(exploit_inputs, team_name):
    if not os.path.exists(EXP_STORAGE):
        data = {"Submissions": {}}
    else:
        with open(EXP_STORAGE, 'r') as f:
            data = json.load(f)
    
    data["Submissions"][team_name] = exploit_inputs
    
    with open(EXP_STORAGE, 'w') as f:
        json.dump(data, f, indent=4)


def print_red(text):
    return f"\033[91m{text}\033[0m"

def print_yellow(text):
    return f"\033[93m{text}\033[0m"

def print_blue(text):
    return f"\033[94m{text}\033[0m"

def print_green(text):
    return f"\033[92m{text}\033[0m"

def print_bold(text):
    return f"\033[1m{text}\033[0m"

def print_underline(text):
    return f"\033[4m{text}\033[0m"

def load_task():
    global dataset1, dataset2

    try:
        choice = random.choice([1, 2])
        if choice == 1:
            if dataset1 == None:
                dataset1 = load_gsm8k()
            task = dataset1['train'][random.randint(0, len(dataset1['train']))]['question']
        else:
            if dataset2 == None:
                dataset2 = load_mmlu()
            task = dataset2['auxiliary_train'][random.randint(0, len(dataset2['auxiliary_train']))]['question']
        
        return (choice, task)

    except Exception as e:
        print(f"[!] Error loading task: {e}\n")
        return (0, "Solve the following math problem: What is 12 multiplied by 15?")

def load_gsm8k():
    return load_dataset('gsm8k', 'main')

def load_mmlu():
    return load_dataset('cais/mmlu', 'all')