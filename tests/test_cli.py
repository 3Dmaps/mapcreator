import click
import mapcreator
from click.testing import CliRunner
from mock import patch
from mapcreator.state import State, FileAddResult
from mapcreator.cli import cli
from mapcreator.state import State
from test_persistence import DummyState


def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(cli, ['hello'])
    assert result.exit_code == 0
    assert 'Hello world' in result.output

@patch('mapcreator.persistence.state_exists', lambda: False)
def test_status_when_state_not_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'No project found in current working directory' in result.output

@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.state_path', lambda: 'my_persistence_location')
@patch('mapcreator.persistence.load_state', lambda: DummyState())
def test_status_when_state_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'CURRENT PROJECT STATE' in result.output
    assert 'my_persistence_location' in result.output
    assert str(DummyState()) in result.output


@patch('mapcreator.persistence.state_exists', lambda: False)
@patch('mapcreator.persistence.init_state', return_value = DummyState())
def test_init_when_state_not_exists(mock_init):
    runner = CliRunner()
    result = runner.invoke(cli, ['init'])
    mock_init.assert_called_once_with()
    assert result.exit_code == 0
    assert 'Project initialized' in result.output

@patch('mapcreator.persistence.state_exists', lambda: True)
def test_init_when_state_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ['init'])
    assert result.exit_code == 0
    assert 'Project already exists, no initialization done.' in result.output

@patch('mapcreator.persistence.save_state')
def test_add_zero_height_files(mock_save):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_height_files'])
    mock_save.assert_not_called()
    assert result.exit_code == 0
    assert 'No files were specified.' in result.output

@patch('mapcreator.cli.add_files')
def test_add_height_files(mock_add):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_height_files', 'test1.txt', 'test2.txt'])
    mock_add.assert_called_once_with(('test1.txt', 'test2.txt'), 'add_height_file')
    assert result.exit_code == 0

@patch('mapcreator.persistence.save_state')
def test_add_zero_osm_files(mock_save):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_osm_files'])
    mock_save.assert_not_called()
    assert result.exit_code == 0
    assert 'No files were specified.' in result.output

@patch('mapcreator.cli.add_files')
def test_add_osm_files(mock_add):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_osm_files', 'test1.xml', 'test2.xml'])
    mock_add.assert_called_once_with(('test1.xml', 'test2.xml'), 'add_osm_file')
    assert result.exit_code == 0

@patch('mapcreator.persistence.save_state')
def test_add_zero_satellite_files(mock_save):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_satellite_files'])
    mock_save.assert_not_called()
    assert result.exit_code == 0
    assert 'No files were specified.' in result.output

@patch('mapcreator.cli.add_files')
def test_add_satellite_files(mock_add):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_satellite_files', 'test1.tif', 'test2.tif'])
    mock_add.assert_called_once_with(('test1.tif', 'test2.tif'), 'add_satellite_file')
    assert result.exit_code == 0

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_area_color')
@patch('mapcreator.persistence.save_state')
def test_add_area_color(mock_save, mock_state):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_area_color', 'mytag', '77', '88', '99'])
    mock_state.assert_called_once_with('mytag', 77, 88, 99)
    mock_save.assert_called()
    assert result.exit_code == 0
    assert 'SUCCESS' in result.output
    assert 'mytag' in result.output
    assert str((77, 88, 99)) in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_area_color')
@patch('mapcreator.persistence.save_state')
def test_add_area_color_invalid_color(mock_save, mock_state):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_area_color', 'mytag', '77', '256', '99'])
    mock_state.assert_not_called()
    mock_save.assert_not_called()
    assert result.exit_code == 0
    assert 'SUCCESS' not in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_area_color')
@patch('mapcreator.persistence.save_state')
def test_add_area_colors_no_colors(mock_save, mock_state):
    runner = CliRunner()
    result = runner.invoke(cli, ['add_area_colors'], input='\n')
    mock_state.assert_not_called()
    mock_save.assert_not_called()
    assert result.exit_code == 0
    assert 'SUCCESS' not in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_area_color')
@patch('mapcreator.persistence.save_state')
def test_add_area_colors_one_valid_color(mock_save, mock_state):
    runner = CliRunner()
    instring = 'how to hack runescape\noh crap this isnt google\ntest 1 2 3\ntag 999 999 999\n\n'
    result = runner.invoke(cli, ['add_area_colors'], input=instring)
    mock_state.assert_called_once_with('test', 1, 2, 3)
    mock_save.assert_called()
    assert result.exit_code == 0
    assert 'SUCCESS' not in result.output
    assert '1 colors were added' in result.output
    assert 'out of total 4 lines given' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_area_color')
@patch('mapcreator.persistence.save_state')
def test_add_area_colors_many_colors(mock_save, mock_state):
    runner = CliRunner()
    instring = 'river 0 0 255\nforest 0 255 0\nvolcano 255 0 0\n\n'
    result = runner.invoke(cli, ['add_area_colors'], input=instring)
    mock_state.assert_any_call('river', 0, 0, 255)
    mock_state.assert_any_call('forest', 0, 255, 0)
    mock_state.assert_any_call('volcano', 255, 0, 0)
    mock_save.assert_called()
    assert result.exit_code == 0
    assert 'SUCCESS' in result.output
    assert '3 colors' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'set_window')
@patch('mapcreator.persistence.save_state')
def test_set_window(mock_save, mock_state): 
    # Making sure that everything is float is done by Click, so no need to test those seperately
    runner = CliRunner()
    result = runner.invoke(cli, ['set_window', '--', '100.0', '-101.0', '92.5', '-93.5'])
    mock_state.assert_called_once_with(100.0, -101.0, 92.5, -93.5)
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: Window set to' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'set_height_system')
@patch('mapcreator.persistence.save_state')
def test_set_height_system(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['set_height_system', '1234'])
    mock_state.assert_called_once_with('EPSG:1234')
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: Forced source height file coordinate system set to' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'set_satellite_system')
@patch('mapcreator.persistence.save_state')
def test_set_satellite_system(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['set_satellite_system', '12345'])
    mock_state.assert_called_once_with('EPSG:12345')
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: Forced source satellite/aerial file coordinate system set to' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'set_height_resolution')
@patch('mapcreator.persistence.save_state')
def test_set_height_resolution(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['set_height_resolution', '20'])
    mock_state.assert_called_once_with(20)
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: Height output resolution set to' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'set_height_resolution')
@patch('mapcreator.persistence.save_state')
def test_set_invalid_height_resolution(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['set_height_resolution', '1100'])
    mock_state.assert_not_called()
    assert mock_save.call_count == 0
    assert result.exit_code == 0
    assert 'ERROR: Invalid resolution' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'set_satellite_resolution')
@patch('mapcreator.persistence.save_state')
def test_set_satellite_resolution(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['set_satellite_resolution', '500.5'])
    mock_state.assert_called_once_with(500.5)
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: Satellite/aerial image output resolution set to' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'set_satellite_resolution')
@patch('mapcreator.persistence.save_state')
def test_set_invalid_satellite_resolution(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['set_satellite_resolution', '0.05'])
    mock_state.assert_not_called()
    assert mock_save.call_count == 0
    assert result.exit_code == 0
    assert 'ERROR: Invalid resolution' in result.output


@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'clear_area_colors')
@patch('mapcreator.persistence.save_state')
def test_clear_area_colors(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['clear_area_colors'])
    mock_state.assert_called()
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: Area colors cleared successfully!' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'clear_height_files')
@patch('mapcreator.persistence.save_state')
def test_clear_height_files(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['clear_height_files'])
    mock_state.assert_called()
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: All height files cleared successfully!' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'clear_osm_files')
@patch('mapcreator.persistence.save_state')
def test_clear_osm_files(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['clear_osm_files'])
    mock_state.assert_called()
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: All open street map files cleared successfully!' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'clear_satellite_files')
@patch('mapcreator.persistence.save_state')
def test_clear_satellite_files(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['clear_satellite_files'])
    mock_state.assert_called()
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: All satellite files cleared successfully!' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'clear_satellite_system')
@patch('mapcreator.persistence.save_state')
def test_clear_satellite_system(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['clear_satellite_system'])
    mock_state.assert_called()
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: Forced source satellite/aerial file coordinate system cleared!' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'clear_height_system')
@patch('mapcreator.persistence.save_state')
def test_clear_height_system(mock_save, mock_state): 
    runner = CliRunner()
    result = runner.invoke(cli, ['clear_height_system'])
    mock_state.assert_called()
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS: Forced source height file coordinate system cleared!' in result.output


@patch('os.path.exists', lambda s: True)
@patch('mapcreator.building.init_build', side_effect = RuntimeError('Shouldn\'t have run this!'))
def test_build_does_nothing_if_target_exists_and_not_force(mock_init):
    runner = CliRunner()
    result = runner.invoke(cli, ['build', '-o', 'test.zip'])
    assert result.exit_code == 0
    assert 'File test.zip already exists' in result.output
    assert 'STARTING BUILD' not in result.output
    mock_init.assert_not_called()

@patch('os.path.exists', lambda s: False)
@patch('mapcreator.persistence.state_exists', lambda: False)
@patch('mapcreator.building.init_build', side_effect = RuntimeError('Shouldn\'t have run this!'))
def test_build_does_nothing_if_state_doesnt_exist(mock_init):
    runner = CliRunner()
    result = runner.invoke(cli, ['build'])
    assert result.exit_code == 0
    assert 'No project found' in result.output
    assert 'STARTING BUILD' not in result.output
    mock_init.assert_not_called()

@patch('os.path.exists', lambda s: False)
@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.load_state', side_effect = OSError('Whoops!'))
@patch('mapcreator.building.init_build', side_effect = RuntimeError('Shouldn\'t have run this!'))
def test_build_does_nothing_if_state_fails_load(mock_init, mock_load):
    runner = CliRunner()
    result = runner.invoke(cli, ['build'])
    assert result.exit_code == 0
    assert 'ERROR' in result.output
    assert 'STARTING BUILD' not in result.output
    mock_init.assert_not_called()

@patch('os.path.exists', lambda s: False)
@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.load_state', lambda: State())
@patch('mapcreator.building.init_build', side_effect = RuntimeError('Shouldn\'t have run this!'))
def test_build_does_nothing_if_state_has_no_files(mock_init):
    runner = CliRunner()
    result = runner.invoke(cli, ['build'])
    assert result.exit_code == 0
    assert 'No files have been added to the current project' in result.output
    assert 'STARTING BUILD' not in result.output
    mock_init.assert_not_called()

@patch('os.path.exists', lambda s: False)
@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.load_state', lambda: State.from_dict({'height_files': ['a', 'b'], 'osm_files': [], 'satellite_files': []}))
@patch('mapcreator.building.init_build', side_effect = RuntimeError('Shouldn\'t have run this!'))
def test_build_does_nothing_if_state_has_no_window(mock_init):
    runner = CliRunner()
    result = runner.invoke(cli, ['build'])
    assert result.exit_code == 0
    assert 'No window has been set for the current project' in result.output
    assert 'STARTING BUILD' not in result.output
    mock_init.assert_not_called()

@patch('os.path.exists', lambda s: False)
@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.load_state', lambda: State.from_dict({'height_files': ['a', 'b'], 'osm_files': [], 'satellite_files': [], 'window': {'ulx': 0, 'uly': 1, 'lrx': 1, 'lry': 0}}))
@patch('mapcreator.building.init_build', side_effect = OSError('Shouldn\'t have run this!'))
def test_build_does_nothing_if_init_fails(mock_init):
    runner = CliRunner()
    result = runner.invoke(cli, ['build'])
    assert result.exit_code == 0
    assert 'ERROR' in result.output
    assert 'STARTING BUILD' not in result.output
    mock_init.assert_called_once_with()

@patch('os.path.exists', lambda s: False)
@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.load_state', lambda: State.from_dict({'height_files': ['a', 'b', 'c'], 'osm_files': [], 'satellite_files': [], 'window': {'ulx': 0, 'uly': 1, 'lrx': 1, 'lry': 0}}))
@patch('mapcreator.building.init_build', lambda: True)
@patch('mapcreator.building.cleanup', lambda: True)
@patch('mapcreator.building.package')
def test_build_works_correctly(mock_package):
    def check_action_a(status, debug):
        assert status.index == 0
        assert debug
        for f in map(lambda s: s*2, status.current_files):
            status.add_next_file(f)
        status.next()
    def check_action_b(status, debug):
        assert len(status.current_files) == 3
        files = ['aa', 'bb', 'cc']
        for f in files: 
            assert f in status.current_files
            status.add_result_file(f)
            status.add_result_file(f + '1')
    mapcreator.building.HEIGHTMAP_ACTIONS = (check_action_a, check_action_b)
    runner = CliRunner()
    result = runner.invoke(cli, ['build', '-do', 'test2.zip'])
    assert result.exit_code == 0
    assert 'SUCCESS' in result.output
    mock_package.assert_called_once_with('test2.zip', ['aa', 'aa1', 'bb', 'bb1', 'cc', 'cc1'])

@patch('os.path.exists', lambda s: True)
@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.load_state', lambda: State.from_dict({'height_files': ['a', 'b', 'c'], 'osm_files': [], 'satellite_files': [], 'window': {'ulx': 0, 'uly': 1, 'lrx': 1, 'lry': 0}}))
@patch('mapcreator.building.init_build', lambda: True)
@patch('mapcreator.building.cleanup', lambda: True)
@patch('mapcreator.building.package')
def test_build_throws_errors_correctly(mock_package):
    def check_action_a(status, debug):
        assert status.index == 0
        assert not debug
        for f in map(lambda s: s*2, status.current_files):
            status.add_next_file(f)
        status.next()
    def check_action_b(status, debug):
        assert len(status.current_files) == 3
        files = ['aa', 'bb', 'cc']
        for f in files: 
            assert f in status.current_files
            status.add_result_file(f)
            status.add_result_file(f + '1')
        status.output.write('Hecking cool')
        raise ValueError('Oh no!')
    mapcreator.building.HEIGHTMAP_ACTIONS = (check_action_a, check_action_b)
    runner = CliRunner()
    result = runner.invoke(cli, ['build', '-fo', 'test2.zip'])
    assert result.exit_code == 0
    assert str(ValueError('Oh no!')) in result.output
    assert 'Hecking cool' in result.output
    assert 'Build done (but there were errors)' in result.output
    assert 'SUCCESS' not in result.output
    mock_package.assert_called_once_with('test2.zip', ['aa', 'aa1', 'bb', 'bb1', 'cc', 'cc1'])

@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.clear_state')
def test_reset_when_state_exists(mock_clear):
    runner = CliRunner()
    result = runner.invoke(cli, ['reset'])
    mock_clear.assert_called_once_with()
    assert result.exit_code == 0
    assert 'Project has been reset.' in result.output

@patch('mapcreator.persistence.state_exists', lambda: False)
@patch('mapcreator.persistence.clear_state')
def test_reset_when_state_not_exists(mock_clear):
    runner = CliRunner()
    result = runner.invoke(cli, ['reset'])
    mock_clear.assert_not_called() # Don't call if no persistence exists
    assert result.exit_code == 0
    assert 'No project found in current working directory. No need to reset!' in result.output

