import click
from mapcreator import persistence
from mapcreator.echoes import *


"""
The x_or_error functions return a falsy value if an error was thrown.
If everything went OK, they return either True or resulting state, depending on the function.
"""

def init_or_error():
    try:
        state = persistence.init_state()
    except Exception as e:
        error('Unable to initialize project: {}'.format(e))
        return None
    else:
        return state

def load_or_error():
    try:
        state = persistence.load_state()
    except Exception as e:
        error('Unable to load or initialize the project: {}'.format(e))
        return None
    else:
        return state

def save_or_error(state):
    try:
        persistence.save_state(state)
    except Exception as e:
        error('Unable to save changes to the project! No changes done!')
        error('What went wrong: {}'.format(e))
        return None
    else:
        return True

def clear_or_error():
    try:
        persistence.clear_state()
    except Exception as e:
        error('Unable to reset project: {}'.format(e))
        return False
    else:
        return True