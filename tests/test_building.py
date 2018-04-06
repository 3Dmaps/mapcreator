import mock
import shutil
import subprocess
from os import path
from mapcreator import building
from mapcreator.building import BuildStatus
from mapcreator.state import State
from mapcreator.gdal_util import Gdalinfo
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
    status = BuildStatus(0, ['test.txt', 'test2.txt'], DummyState())
    building.prepare(status)
    expected_command = 'gdal_translate -of GTiff test.txt {}'.format(building.get_output_path('test.txt', 'tiff'))
    expected_command_2 = 'gdal_translate -of GTiff test2.txt {}'.format(building.get_output_path('test2.txt', 'tiff'))
    mock_call.assert_any_call(expected_command, status, False)
    mock_call.assert_any_call(expected_command_2, status, False)
    assert status.current_files == [building.get_output_path('test.txt', 'tiff'), building.get_output_path('test2.txt', 'tiff')]


@mock.patch('mapcreator.building.call_command')
@mock.patch('mapcreator.gdal_util.Gdalinfo.for_file')
def test_cut_projection_window(mock_forfile, mock_call):
    ginfo_for_testing = Gdalinfo()
    ginfo_for_testing.minX = -99
    ginfo_for_testing.minY = -99
    ginfo_for_testing.maxX = 99
    ginfo_for_testing.maxY = 3
    mock_forfile.return_value = ginfo_for_testing
    state = State()
    state.set_window(0, 7, 2, 1)
    status = BuildStatus(0, ['test.txt'], state)
    building.cut_projection_window(status)
    mock_forfile.assert_called_once_with('test.txt')
    expected_command = 'gdalwarp -te 0 1 2 3 test.txt {}'.format(building.get_output_path('test.txt'))
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_files == [building.get_output_path('test.txt')]


@mock.patch('mapcreator.building.call_command')
def test_cut_projection_window_when_no_window(mock_call):
    status = BuildStatus(0, ['test.txt', 'test2.txt'], State())
    building.cut_projection_window(status)
    mock_call.assert_not_called()
    assert status.current_files == ['test.txt', 'test2.txt']
 
@mock.patch('mapcreator.building.call_command')
def test_reproject(mock_call):
    test_files = ['test.txt', 'test2.txt', 'test3.txt']
    status = BuildStatus(0, test_files, DummyState())
    building.reproject(status)
    for f in test_files:
        expected_command = 'gdalwarp -tr 10 10 -t_srs EPSG:3857 -r bilinear {} {}'.format(f, building.get_output_path(f))
        mock_call.assert_any_call(expected_command, status, False)
    assert status.current_files == list(map(building.get_output_path, test_files))

@mock.patch('mapcreator.building.call_command')
def test_translate(mock_call):
    def add_mock_files(a, b, c):
        open(building.get_output_path('test.txt', 'hdr'), 'w').close()
        open(building.get_output_path('test2.txt', 'hdr'), 'w').close()
    mock_call.side_effect = add_mock_files
    building.init_build()
    status = BuildStatus(2, ['test.txt', 'test2.txt'], DummyState())
    building.translate(status)
    expected_command = 'gdal_translate -of ENVI test.txt {}'.format(building.get_output_path('test.txt', 'bin'))
    expected_command_2 = 'gdal_translate -of ENVI test2.txt {}'.format(building.get_output_path('test2.txt', 'bin'))
    mock_call.assert_any_call(expected_command, status, False)
    mock_call.assert_any_call(expected_command_2, status, False)
    assert status.current_files == [building.get_output_path('test.txt', 'bin'), building.get_output_path('test2.txt', 'bin')]
    assert path.exists(path.join(building.FINALIZED_DIR, 'heightfile2.hdr'))
    assert path.exists(path.join(building.FINALIZED_DIR, 'heightfile3.hdr'))
    assert status.result_files == [path.join(building.FINALIZED_DIR, 'heightfile2.hdr'),
                                   path.join(building.FINALIZED_DIR, 'heightfile3.hdr')]

@mock.patch('mapcreator.building.rename')
def test_finalize(mock_rename):
    building.init_build()
    status = BuildStatus(99, ['test.txt', 'test2.txt'], DummyState())
    status.current_files = [building.get_output_path('test.txt', 'bin'), building.get_output_path('test2.txt', 'bin')]
    building.finalize(status)
    mock_rename.assert_any_call(building.get_output_path('test.txt', 'bin'), path.join(building.FINALIZED_DIR, 'heightfile99.bin'))
    mock_rename.assert_any_call(building.get_output_path('test2.txt', 'bin'), path.join(building.FINALIZED_DIR, 'heightfile100.bin'))
    assert status.current_files == [path.join(building.FINALIZED_DIR, 'heightfile99.bin'), path.join(building.FINALIZED_DIR, 'heightfile100.bin')]
    assert len(status.result_files) == 2
    assert path.join(building.FINALIZED_DIR, 'heightfile99.bin') in status.result_files
    assert path.join(building.FINALIZED_DIR, 'heightfile100.bin') in status.result_files

def test_finalize_when_no_changes():
    status = BuildStatus(99, ['test.txt'], DummyState())
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