import mock
import shutil
import subprocess
from os import path
from mapcreator import building
from mapcreator.building import BuildStatus
from mapcreator.state import State
from test_persistence import DummyState

def setup_module(module):
    building.BUILD_DIR = '.test_mapcreator_build'
    building.FINALIZED_DIR = path.join(building.BUILD_DIR, 'finalized')

@mock.patch('subprocess.Popen')
def test_call_command_with_debug(mock_popen):
    status = BuildStatus(0, 'test.txt', DummyState())
    mock_popen.return_value.__enter__.return_value.communicate.return_value = (b'test output', b'test error')
    building.call_command('mycommand -abc', status, True)
    mock_popen.assert_called_once_with('mycommand -abc', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert 'mycommand' in str(status)
    assert 'test output' in str(status)
    assert 'test error' in str(status)

@mock.patch('subprocess.Popen')
def test_call_command_no_debug(mock_popen):
    status = BuildStatus(0, 'test.txt', DummyState())
    mock_popen.return_value.__enter__.return_value.communicate.return_value = (b'test output', b'test error')
    building.call_command('mycommand --do-test -- -1 2 3', status, False)
    mock_popen.assert_called_once_with('mycommand --do-test -- -1 2 3', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert 'mycommand' not in str(status)
    assert 'test output' not in str(status)
    assert 'test error' in str(status)

def test_init_build():
    building.init_build()
    assert path.exists(building.BUILD_DIR)
    assert path.exists(building.FINALIZED_DIR)

def test_init_build_cleans_up():
    building.init_build()
    t1path = path.join(building.BUILD_DIR, 'test1')
    t2path = path.join(building.FINALIZED_DIR, 'test2')
    open(t1path, 'w').close()
    open(t2path, 'w').close()
    assert path.exists(t1path)
    assert path.exists(t2path)
    building.init_build()
    assert not path.exists(t1path)
    assert not path.exists(t2path)

def test_output_path_for_initial_file():
    test_path = path.abspath('myfile.x')
    assert path.join(building.BUILD_DIR, '[0]myfile.x') == building.get_output_path(test_path)

def test_output_path_for_initial_file_with_new_extension():
    test_path = path.abspath('myfile.x')
    assert path.join(building.BUILD_DIR, '[0]myfile.x.y') == building.get_output_path(test_path, 'y')

def test_output_path_for_temp_file():
    test_path = path.join(building.BUILD_DIR, '[7]myfile.x.y')
    assert path.join(building.BUILD_DIR, '[8]myfile.x.y') == building.get_output_path(test_path)

def test_output_path_for_temp_file_with_new_extension():
    test_path = path.join(building.BUILD_DIR, '[11]myfile.x.y')
    assert path.join(building.BUILD_DIR, '[12]myfile.x.y.z') == building.get_output_path(test_path, 'z')

@mock.patch('mapcreator.building.call_command')
def test_prepare(mock_call):
    status = BuildStatus(0, 'test.txt', DummyState())
    building.prepare(status)
    expected_command = 'gdal_translate -of GTiff test.txt {}'.format(building.get_output_path('test.txt', 'tiff'))
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_file == building.get_output_path('test.txt', 'tiff')

@mock.patch('mapcreator.building.call_command')
def test_cut_projection_window(mock_call):
    state = State()
    state.set_window(1, 2, 3, 4)
    status = BuildStatus(0, 'test.txt', state)
    building.cut_projection_window(status)
    expected_command = 'gdalwarp -te 1 4 3 2 test.txt {}'.format(building.get_output_path('test.txt'))
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_file == building.get_output_path('test.txt')

@mock.patch('mapcreator.building.call_command')
def test_cut_projection_window_when_no_window(mock_call):
    status = BuildStatus(0, 'test.txt', State())
    building.cut_projection_window(status)
    mock_call.assert_not_called()
    assert status.current_file == 'test.txt'

@mock.patch('mapcreator.building.call_command')
def test_reproject(mock_call):
    status = BuildStatus(0, 'test.txt', DummyState())
    building.reproject(status)
    expected_command = 'gdalwarp -tr 10 10 -t_srs EPSG:3857 -r bilinear test.txt {}'.format(building.get_output_path('test.txt'))
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_file == building.get_output_path('test.txt')

@mock.patch('mapcreator.building.call_command', side_effect=lambda a, b, c: open(building.get_output_path('test.txt', 'hdr'), 'w').close())
def test_translate(mock_call):
    building.init_build()
    status = BuildStatus(2, 'test.txt', DummyState())
    building.translate(status)
    expected_command = 'gdal_translate -of ENVI test.txt {}'.format(building.get_output_path('test.txt', 'bin'))
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_file == building.get_output_path('test.txt', 'bin')
    assert path.exists(path.join(building.FINALIZED_DIR, 'heightfile2.hdr'))
    assert status.result_files == [path.join(building.FINALIZED_DIR, 'heightfile2.hdr')]

@mock.patch('mapcreator.building.rename')
def test_finalize(mock_rename):
    building.init_build()
    status = BuildStatus(99, 'test.txt', DummyState())
    status.current_file = building.get_output_path('test.txt', 'bin')
    status.add_result_file(path.join(building.FINALIZED_DIR, 'heightfile99.hdr'))
    building.finalize(status)
    mock_rename.assert_called_once_with(building.get_output_path('test.txt', 'bin'), path.join(building.FINALIZED_DIR, 'heightfile99.bin'))
    assert status.current_file == path.join(building.FINALIZED_DIR, 'heightfile99.bin')
    assert len(status.result_files) == 2
    assert path.join(building.FINALIZED_DIR, 'heightfile99.hdr') in status.result_files
    assert path.join(building.FINALIZED_DIR, 'heightfile99.bin') in status.result_files

def test_finalize_when_no_changes():
    status = BuildStatus(99, 'test.txt', DummyState())
    try:
        building.finalize(status)
        assert False # Should have thrown an exception before this
    except RuntimeError:
        pass
    except:
        assert False # Wrong kind of an error thrown

def teardown_function(function):
    if path.exists(building.BUILD_DIR):
        shutil.rmtree(building.BUILD_DIR)