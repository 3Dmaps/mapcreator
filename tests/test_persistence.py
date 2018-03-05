import json
import shutil
from os import path
from mock import patch
from mapcreator import persistence
from mapcreator.state import State

def setup_module(module):
    persistence.STATE_DIR = '.test_mapcreator'

class DummyState:
    def __init__(self):
        self.test = 'successful'
    def to_dict(self):
        return {'test': 'success'}
    @staticmethod
    def from_dict(d):
        new = DummyState()
        new.__dict__ = d
        return new
    def __str__(self):
        return '( A dummy state )'

def test_init_state():
    persistence.init_state()
    with open(path.join(persistence.STATE_DIR, persistence.STATE_FILE)) as f:
        content = json.load(f)
        assert content == State().__dict__

def test_save_state():
    persistence.save_state(DummyState())
    with open(path.join(persistence.STATE_DIR, persistence.STATE_FILE)) as f:
        content = json.load(f)
        assert content['test'] == 'success'

def test_load_state_with_existing_state():
    persistence.save_state(DummyState())
    state = persistence.load_state()
    assert state.test == 'success'

@patch('mapcreator.persistence.init_state', lambda: DummyState())
def test_load_state_with_no_existing_state():
    state = persistence.load_state()
    assert state.test == 'successful'

def teardown_function(function):
    if path.exists(persistence.STATE_DIR):
        shutil.rmtree(persistence.STATE_DIR)
