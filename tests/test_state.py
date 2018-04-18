from mock import patch
from os import path
from mapcreator.state import State, FileAddResult

@patch('os.path.exists', return_value = True)
def test_add_file_when_success(mock_exists):
    state = State()
    result = state.add_height_file('mylittletestfile')
    mock_exists.assert_called()
    assert result == FileAddResult.SUCCESS
    assert 1 == len(state.height_files)
    assert path.abspath('mylittletestfile') in state.height_files

@patch('os.path.exists', return_value = True)
def test_add_file_can_add_multiple(mock_exists):
    state = State()
    for i in range(10):
        result = state.add_osm_file('testfile{}'.format(i))
        assert FileAddResult.SUCCESS == result
    assert 10 == len(state.osm_files)
    for i in range(10):
        assert path.abspath('testfile{}'.format(i)) in state.osm_files

@patch('os.path.exists', return_value = True)
def test_add_file_when_already_added(mock_exists):
    state = State()
    state.add_height_file('mylittletestfile')
    result = state.add_height_file('mylittletestfile')
    assert result == FileAddResult.ALREADY_ADDED
    assert 1 == len(state.height_files)
    assert path.abspath('mylittletestfile') in state.height_files

@patch('os.path.exists', return_value = False)
def test_add_file_when_doesnt_exist(mock_exists):
    state = State()
    result = state.add_osm_file('mylittletestfile')
    mock_exists.assert_called()
    assert result == FileAddResult.DOESNT_EXIST
    assert 0 == len(state.osm_files)

def test_from_dict():
    state = State.from_dict({
        'height_files': ['foo', 'bar'],
        'osm_files': ['hello', 'world'],
        'window': {'ulx': 1, 'uly': 2,
                   'lrx': 3, 'lry': 4}
    })
    assert ['foo', 'bar'] == state.height_files
    assert ['hello', 'world'] == state.osm_files
    assert (1, 2) == state.get_window_upper_left()
    assert (3, 4) == state.get_window_lower_right()

@patch('os.path.exists', lambda x: True)
def test_has_height_files():
    state = State()
    assert not state.has_height_files()
    state.add_height_file('asd')
    assert state.has_height_files()

def test_has_window():
    state = State()
    assert not state.has_window()
    state.set_window(1, 2, 3, 4)
    assert state.has_window()

def test_window_string():
    state = State()
    assert state.get_window_string() == ''
    state.set_window(-1, 4, 1, 2)
    nums = list(map(int, state.get_window_string().split(' ')))
    assert len(nums) == 4
    assert nums[0] == -1
    assert nums[1] == 4
    assert nums[2] == 1
    assert nums[3] == 2

def test_has_height_system():
    state = State()
    assert not state.has_height_system()
    state.set_height_system('EPSG:1234')
    assert state.has_height_system()

def test_has_satellite_system():
    state = State()
    assert not state.has_satellite_system()
    state.set_satellite_system('EPSG:12345')
    assert state.has_satellite_system()

  
