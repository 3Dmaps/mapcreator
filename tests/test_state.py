from mock import patch
from os import path
from mapcreator.state import State, FileAddResult

@patch('os.path.exists', return_value = True)
def test_add_height_file_when_success(mock_exists):
    state = State()
    result = state.add_height_file('mylittletestfile')
    mock_exists.assert_called()
    assert result == FileAddResult.SUCCESS
    assert 1 == len(state.height_files)
    assert path.abspath('mylittletestfile') in state.height_files

@patch('os.path.exists', return_value = True)
def test_add_height_file_can_add_multiple(mock_exists):
    state = State()
    for i in range(10):
        result = state.add_height_file('testfile{}'.format(i))
        assert FileAddResult.SUCCESS == result
    assert 10 == len(state.height_files)
    for i in range(10):
        assert path.abspath('testfile{}'.format(i)) in state.height_files

@patch('os.path.exists', return_value = True)
def test_add_height_file_when_already_added(mock_exists):
    state = State()
    state.add_height_file('mylittletestfile')
    result = state.add_height_file('mylittletestfile')
    assert result == FileAddResult.ALREADY_ADDED
    assert 1 == len(state.height_files)
    assert path.abspath('mylittletestfile') in state.height_files

@patch('os.path.exists', return_value = False)
def test_add_height_file_when_doesnt_exist(mock_exists):
    state = State()
    result = state.add_height_file('mylittletestfile')
    mock_exists.assert_called()
    assert result == FileAddResult.DOESNT_EXIST
    assert 0 == len(state.height_files)

def test_from_dict():
    state = State.from_dict({
        'height_files': ['foo', 'bar'],
        'window': {'ulx': 1, 'uly': 2,
                   'lrx': 3, 'lry': 4}
    })
    assert ['foo', 'bar'] == state.height_files
    assert (1, 2) == state.get_window_upper_left()
    assert (3, 4) == state.get_window_lower_right()

    
