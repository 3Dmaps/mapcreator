import json
import shutil
from os import path, makedirs
from mapcreator.state import State

STATE_DIR = '.mapcreator'
STATE_FILE = 'state.json'

def init_state():
    initial_state = State()
    save_state(initial_state)
    return initial_state

def state_path():
    return path.join(STATE_DIR, STATE_FILE)

def state_exists():
    return path.exists(state_path())

def load_state():
    if state_exists():
        with open(state_path(), 'r') as infile:
            return State.from_dict(json.load(infile))
    else:
        return init_state()

def save_state(state):
    if not path.exists(STATE_DIR):
        makedirs(STATE_DIR)
    with open(state_path(), 'w') as outfile:
        json.dump(state.to_dict(), outfile)

def clear_state():
    shutil.rmtree(STATE_DIR)
    