import mock
import shutil
import subprocess
from os import path
from mapcreator import building
from mapcreator.building import HeightMapStatus, SatelliteStatus
from mapcreator.state import State
from mapcreator.gdal_util import Gdalinfo
from test_persistence import DummyState

def setup_module(module):
    building.BUILD_DIR = '.test_mapcreator_build'
    building.FINALIZED_DIR = path.join(building.BUILD_DIR, 'finalized')

@mock.patch('subprocess.Popen')
def test_call_command_with_debug(mock_popen):
    status = HeightMapStatus(0, 'test.txt', DummyState())
    mock_popen.return_value.__enter__.return_value.communicate.return_value = (b'test output', b'test error')
    building.call_command('mycommand -abc', status, True)
    mock_popen.assert_called_once_with('mycommand -abc', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert 'mycommand' in str(status)
    assert 'test output' in str(status)
    assert 'test error' in str(status)

@mock.patch('subprocess.Popen')
def test_call_command_no_debug(mock_popen):
    status = HeightMapStatus(0, 'test.txt', DummyState())
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

@mock.patch('mapcreator.building.call_command')
@mock.patch('mapcreator.gdal_util.Gdalinfo.for_file')
def test_process_heightfiles_with_gdal(mock_forfile, mock_call):
    ginfo_for_testing = Gdalinfo()
    ginfo_for_testing.minX = -99
    ginfo_for_testing.minY = -99
    ginfo_for_testing.maxX = 99
    ginfo_for_testing.maxY = 3
    mock_forfile.return_value = ginfo_for_testing
    state = State()
    state.set_window(0, 7, 2, 1)
    status = HeightMapStatus(0, ['test.txt'], state)
    building.process_heightfiles_with_gdal(status)
    mock_forfile.assert_called_once_with('test.txt')
    outpath = path.join(building.BUILD_DIR, building.INTERMEDIATE_HEIGHT_FILENAME)
    expected_command = 'gdalwarp -tr 10 10 -te_srs EPSG:4326 -t_srs EPSG:3857 -r bilinear -te 0 1 2 7 test.txt {}'.format(outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.intermediate_files == [outpath]

@mock.patch('mapcreator.building.call_command')
@mock.patch('mapcreator.gdal_util.Gdalinfo.for_file')
def test_process_heightfiles_with_gdal_with_no_files_in_window(mock_forfile, mock_call):
    ginfo_for_testing = Gdalinfo()
    ginfo_for_testing.minX = -99
    ginfo_for_testing.minY = -99
    ginfo_for_testing.maxX = 0
    ginfo_for_testing.maxY = 0
    mock_forfile.return_value = ginfo_for_testing
    state = State()
    state.set_window(1, 7, 2, 1)
    status = HeightMapStatus(0, ['test.txt'], state)
    building.process_heightfiles_with_gdal(status)
    mock_forfile.assert_called_once_with('test.txt')
    mock_call.assert_not_called()
    assert status.intermediate_files == []

@mock.patch('mapcreator.building.call_command')
def test_translate(mock_call):
    target_path = path.join(building.FINALIZED_DIR, building.FINAL_HEIGHT_FILENAME)
    metadata_path = path.join(building.FINALIZED_DIR, building.FINAL_HEIGHT_METADATA_FILENAME)
    def add_mock_files(a, b, c):
        open(target_path, 'w').close()
        open(metadata_path, 'w').close()
    mock_call.side_effect = add_mock_files
    building.init_build()
    status = HeightMapStatus(2, ['test.txt', 'test2.txt'], DummyState())
    status.add_intermediate_file('testIntermediate.tif')
    building.translate_heightfile(status)
    expected_command = 'gdal_translate -of ENVI testIntermediate.tif {}'.format(target_path)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert path.exists(path.join(building.FINALIZED_DIR, 'heightfile.bin'))
    assert path.exists(path.join(building.FINALIZED_DIR, 'heightfile.hdr'))
    assert status.result_files == [target_path, metadata_path]


@mock.patch('mapcreator.building.call_command')
@mock.patch('mapcreator.gdal_util.Gdalinfo.for_file')
def test_process_satellite_with_gdal(mock_forfile, mock_call):
    ginfo_for_testing = Gdalinfo()
    ginfo_for_testing.minX = -99
    ginfo_for_testing.minY = -99
    ginfo_for_testing.maxX = 99
    ginfo_for_testing.maxY = 99
    mock_forfile.return_value = ginfo_for_testing
    state = State()
    state.set_window(0, 7, 2, 1)
    
    status = SatelliteStatus(0, ['test.tif', 'test2.tif'], state)
    building.process_satellite_with_gdal(status)
    mock_forfile.assert_any_call('test.tif')
    mock_forfile.assert_any_call('test2.tif')
    outpath = path.join(building.BUILD_DIR, building.INTERMEDIATE_SATELLITE_FILENAME)
    expected_command = 'gdalwarp -tr 10 10 -te_srs EPSG:4326 -t_srs EPSG:3857 -r bilinear -te 0 1 2 7 test.tif test2.tif {}'.format(outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.intermediate_files == [outpath]

@mock.patch('mapcreator.building.call_command')
@mock.patch('mapcreator.gdal_util.Gdalinfo.for_file')
def test_process_satellite_with_no_images_in_window(mock_forfile, mock_call):
    ginfo_for_testing = Gdalinfo()
    ginfo_for_testing.minX = 10
    ginfo_for_testing.minY = 10
    ginfo_for_testing.maxX = 99
    ginfo_for_testing.maxY = 99
    mock_forfile.return_value = ginfo_for_testing
    state = State()
    state.set_window(0, 7, 2, 1)
    
    status = SatelliteStatus(0, ['test.tif', 'test2.tif'], state)
    building.process_satellite_with_gdal(status)
    mock_forfile.assert_any_call('test.tif')
    mock_forfile.assert_any_call('test2.tif')
    mock_call.assert_not_called()
    assert status.result_files == []

@mock.patch('mapcreator.building.call_command')
def test_translate_satellite_to_png(mock_call):
    state = State()
    status = SatelliteStatus(0, ['test.tif', 'test2.tif'], state)
    status.add_intermediate_file('intermediate.tiff')
    building.translate_satellite(status)
    
    outpath = path.join(building.FINALIZED_DIR, building.FINAL_SATELLITE_FILENAME.format(0))
    expected_command = 'gdal_translate -of {} {} {}'.format(building.SATELLITE_OUTPUT_FORMAT, 'intermediate.tiff', outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.result_files == [outpath]

def teardown_function(function):
    if path.exists(building.BUILD_DIR):
        shutil.rmtree(building.BUILD_DIR)