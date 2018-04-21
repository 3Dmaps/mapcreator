import mock
import shutil
import subprocess
from os import path
from mapcreator import building
from mapcreator.building import HeightMapStatus, OSMStatus, SatelliteStatus
from mapcreator.state import State
from mapcreator.gdal_util import Gdalinfo
from mapcreator.osm import OSMData
from util import get_resource_path, assert_xml_equal
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
@mock.patch('mapcreator.gdal_util.Gdalinfo.for_file')
def test_check_projection_window(mock_forfile, mock_call):
    ginfo_for_testing = Gdalinfo()
    ginfo_for_testing.minX = -99
    ginfo_for_testing.minY = -99
    ginfo_for_testing.maxX = 99
    ginfo_for_testing.maxY = 3
    mock_forfile.return_value = ginfo_for_testing
    state = State()
    state.set_window(0, 7, 2, 1)
    status = HeightMapStatus(0, ['test.txt'], state)
    building.check_projection_window(status)
    mock_forfile.assert_called_once_with('test.txt')
    assert status.current_files == ['test.txt']

@mock.patch('mapcreator.building.call_command')
@mock.patch('mapcreator.gdal_util.Gdalinfo.for_file')
def test_no_projection_windows(mock_forfile, mock_call):
    ginfo_for_testing = Gdalinfo()
    ginfo_for_testing.minX = -99
    ginfo_for_testing.minY = -99
    ginfo_for_testing.maxX = -10
    ginfo_for_testing.maxY = -10
    mock_forfile.return_value = ginfo_for_testing
    state = State()
    state.set_window(0, 7, 2, 1)
    status = HeightMapStatus(0, ['test.txt'], state)
    building.check_projection_window(status)
    mock_forfile.assert_called_once_with('test.txt')
    assert status.current_files == []

@mock.patch('mapcreator.building.call_command')
def test_check_projection_window_when_no_window(mock_call):
    status = HeightMapStatus(0, ['test.txt', 'test2.txt'], State())
    building.check_projection_window(status)
    mock_call.assert_not_called()
    assert status.current_files == []
 
@mock.patch('mapcreator.building.call_command')
def test_process_heightfiles_with_gdal(mock_call):
    state = State()
    state.set_window(0, 7, 2, 1)
    status = HeightMapStatus(0, ['test.txt'], state)
    building.process_heightfiles_with_gdal(status)
    outpath = path.join(building.BUILD_DIR, building.INTERMEDIATE_HEIGHT_FILENAME)
    expected_command = 'gdalwarp -tr 10 10 -te_srs EPSG:4326 -t_srs EPSG:3857 -r bilinear -te 0 1 2 7 test.txt {}'.format(outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_files == [outpath]

@mock.patch('mapcreator.building.call_command')
def test_process_heightfiles_with_gdal_reso30(mock_call):
    state = State()
    state.set_window(0, 7, 2, 1)
    state.set_height_resolution(30)
    status = HeightMapStatus(0, ['test.txt'], state)
    building.process_heightfiles_with_gdal(status)
    outpath = path.join(building.BUILD_DIR, building.INTERMEDIATE_HEIGHT_FILENAME)
    expected_command = 'gdalwarp -tr 30 30 -te_srs EPSG:4326 -t_srs EPSG:3857 -r bilinear -te 0 1 2 7 test.txt {}'.format(outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_files == [outpath]

@mock.patch('mapcreator.building.call_command')
def test_process_heightfiles_with_gdal_with_no_files(mock_call):
    state = State()
    state.set_window(0, 7, 2, 1)
    status = HeightMapStatus(0, [], state)
    building.process_heightfiles_with_gdal(status)
    mock_call.assert_not_called()
    assert status.current_files == []

@mock.patch('mapcreator.building.call_command')
def test_process_heightfiles_with_forced_coordinate_system(mock_call):
    state = State()
    state.set_window(0, 7, 2, 1)
    state.set_height_system('EPSG:9876')
    status = HeightMapStatus(0, ['test.txt'], state)
    building.process_heightfiles_with_gdal(status)
    outpath = path.join(building.BUILD_DIR, building.INTERMEDIATE_HEIGHT_FILENAME)
    expected_command = 'gdalwarp -s_srs EPSG:9876 -tr 10 10 -te_srs EPSG:4326 -t_srs EPSG:3857 -r bilinear -te 0 1 2 7 test.txt {}'.format(outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_files == [outpath]

@mock.patch('mapcreator.building.call_command')
def test_translate_heightfile(mock_call):
    def add_mock_files(a, b, c):
        open(building.get_output_path('test.txt', 'hdr'), 'w').close()
        open(building.get_output_path('test2.txt', 'hdr'), 'w').close()
    mock_call.side_effect = add_mock_files
    building.init_build()
    status = HeightMapStatus(2, ['test.txt', 'test2.txt'], DummyState())
    building.translate_heightfiles(status)
    outpath1 = path.join(building.FINALIZED_DIR, building.FINAL_HEIGHT_FILENAME_FORMAT.format(0))
    metapath1 = path.join(building.FINALIZED_DIR, building.FINAL_HEIGHT_METADATA_FORMAT.format(0))
    outpath2 = path.join(building.FINALIZED_DIR, building.FINAL_HEIGHT_FILENAME_FORMAT.format(1))
    metapath2 = path.join(building.FINALIZED_DIR, building.FINAL_HEIGHT_METADATA_FORMAT.format(1))
    expected_command = 'gdal_translate -of ENVI test.txt {}'.format(outpath1)
    expected_command_2 = 'gdal_translate -of ENVI test2.txt {}'.format(outpath2)
    mock_call.assert_any_call(expected_command, status, False)
    mock_call.assert_any_call(expected_command_2, status, False)
    assert status.result_files == [outpath1, metapath1, outpath2, metapath2]

def test_insert_colors():
    data = OSMData.load(get_resource_path('test_osm_terrains_input.xml'))
    state = State()
    state.add_area_color('meadow', 0, 255, 0)
    status = OSMStatus(0, ['asd'], state)
    status.osmdata = [data]
    building.insert_colors(status)
    outpath = path.join(building.BUILD_DIR, 'result.xml')
    data.save(outpath)
    assert_xml_equal(get_resource_path('test_osm_terrain_colors_expected.xml'), outpath)

@mock.patch('mapcreator.building.call_command')
def test_process_satellite_with_gdal(mock_call):
    state = State()
    state.set_window(0, 7, 2, 1)
    
    status = SatelliteStatus(0, ['test.tif', 'test2.tif'], state)
    building.process_satellite_with_gdal(status)
    outpath = path.join(building.FINALIZED_DIR, building.INTERMEDIATE_SATELLITE_FORMAT.format(0))
    expected_command = 'gdalwarp -tr 10 10 -te_srs EPSG:4326 -t_srs EPSG:3857 -r bilinear -te 0 1 2 7 test.tif test2.tif {}'.format(outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_files == [outpath]

@mock.patch('mapcreator.building.call_command')
def test_process_satellite_with_forced_coordinate_system(mock_call):
    state = State()
    state.set_window(0, 7, 2, 1)
    state.set_satellite_system('EPSG:9876')
    
    status = SatelliteStatus(0, ['test.tif', 'test2.tif'], state)
    building.process_satellite_with_gdal(status)
    outpath = path.join(building.FINALIZED_DIR, building.INTERMEDIATE_SATELLITE_FORMAT.format(0))
    expected_command = 'gdalwarp -s_srs EPSG:9876 -tr 10 10 -te_srs EPSG:4326 -t_srs EPSG:3857 -r bilinear -te 0 1 2 7 test.tif test2.tif {}'.format(outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.current_files == [outpath]

@mock.patch('mapcreator.building.call_command')
def test_translate_satellite_to_png(mock_call):
    state = State()
    status = SatelliteStatus(0, ['intermediate.tiff'], state)
    building.translate_satellite_to_png(status)
    
    outpath = path.join(building.FINALIZED_DIR, building.FINAL_SATELLITE_FORMAT.format(0))
    expected_command = 'gdal_translate -of {} {} {}'.format(building.SATELLITE_OUTPUT_FORMAT, 'intermediate.tiff', outpath)
    mock_call.assert_called_once_with(expected_command, status, False)
    assert status.result_files == [outpath]

def teardown_function(function):
    if path.exists(building.BUILD_DIR):
        pass
    #    shutil.rmtree(building.BUILD_DIR)