import click
from mapcreator import building
from mapcreator import persistence
from mapcreator import echoes


"""
The x_or_error functions return a falsy value if an error was thrown.
If everything went OK, they return either True or resulting state, depending on the function.
"""

def init_or_error():
    try:
        state = persistence.init_state()
    except Exception as e:
        echoes.error('Unable to initialize project: {}'.format(e))
        return None
    else:
        return state

def load_or_error():
    try:
        state = persistence.load_state()
    except Exception as e:
        echoes.error('Unable to load or initialize the project: {}'.format(e))
        return None
    else:
        return state

def save_or_error(state):
    try:
        persistence.save_state(state)
    except Exception as e:
        echoes.error('Unable to save changes to the project! No changes done!')
        echoes.error('What went wrong: {}'.format(e))
        return None
    else:
        return state

def clear_or_error():
    try:
        persistence.clear_state()
    except Exception as e:
        echoes.error('Unable to reset project: {}'.format(e))
        return False
    else:
        return True

def build_init_or_error():
    try:
        building.init_build()
    except Exception as e:
        echoes.error('Unable to initialize build: {}'.format(e))
        return False
    else:
        return True

def build_clean_or_error():
    try:
        building.cleanup()
    except Exception as e:
        echoes.error('Unable to clean temporary build files: {}'.format(e))
        return False
    else: 
        return True