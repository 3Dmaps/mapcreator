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

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_height_file')
@patch('mapcreator.persistence.save_state', side_effect = lambda state: state) #Returns state, so save was successful
def test_add_height_files(mock_save, mock_state):
    mock_state.return_value = FileAddResult.SUCCESS
    runner = CliRunner()
    result = runner.invoke(cli, ['add_height_files','test1.txt','test2.txt'])
    mock_state.assert_any_call('test1.txt')
    mock_state.assert_any_call('test2.txt')
    assert mock_state.call_count == 2
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert 'SUCCESS' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_height_file')
@patch('mapcreator.persistence.save_state')
def test_add_height_files_no_files_exist(mock_save, mock_state):
    mock_state.return_value = FileAddResult.DOESNT_EXIST
    runner = CliRunner()
    result = runner.invoke(cli, ['add_height_files','test1.txt','test2.txt','test3.txt'])
    mock_state.assert_any_call('test1.txt')
    mock_state.assert_any_call('test2.txt')
    mock_state.assert_any_call('test3.txt')
    assert mock_state.call_count == 3
    assert mock_save.call_count == 0 # Don't save if there's no changes
    for i in range(1,3):
        assert 'File "test{}.txt" doesn\'t exist'.format(i) in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_height_file')
@patch('mapcreator.persistence.save_state')
def test_add_height_files_all_already_added(mock_save, mock_state):
    mock_state.return_value = FileAddResult.ALREADY_ADDED
    runner = CliRunner()
    result = runner.invoke(cli, ['add_height_files','test3.txt'])
    mock_state.assert_called_once_with('test3.txt')
    assert mock_save.call_count == 0
    assert 'test3.txt has already been added to this project' in result.output

@patch('mapcreator.persistence.load_state', lambda: State())
@patch.object(mapcreator.state.State, 'add_height_file')
@patch('mapcreator.persistence.save_state')
def test_add_height_files_some_files_ok(mock_save, mock_state):
    def add_side_effect(filename):
        if filename in ('1', '11', '21'):
            return FileAddResult.SUCCESS
        else:
            return (FileAddResult.ALREADY_ADDED, FileAddResult.DOESNT_EXIST)[int(filename) % 2]
    mock_state.side_effect = add_side_effect
    runner = CliRunner()
    runner_args = ['add_height_files']
    for i in range(25):
        runner_args.append(str(i))
    result = runner.invoke(cli, runner_args)
    assert mock_state.call_count == len(runner_args) - 1
    assert mock_save.call_count == 1
    assert result.exit_code == 0
    assert '3 files (out of 25) added to the project successfully' in result.output

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
def test_build_does_nothing_if_state_has_no_height_files(mock_init):
    runner = CliRunner()
    result = runner.invoke(cli, ['build'])
    assert result.exit_code == 0
    assert 'No height files' in result.output
    assert 'STARTING BUILD' not in result.output
    mock_init.assert_not_called()

@patch('os.path.exists', lambda s: False)
@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.load_state', lambda: State.from_dict({'height_files': ['a', 'b']}))
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
@patch('mapcreator.persistence.load_state', lambda: State.from_dict({'height_files': ['a', 'b', 'c']}))
@patch('mapcreator.building.init_build', lambda: True)
@patch('mapcreator.building.cleanup', lambda: True)
@patch('mapcreator.building.package')
def test_build_works_correctly(mock_package):
    def check_action_a(status, debug):
        assert status.index in range(3)
        assert debug
        status.current_file = status.current_file * 2
    def check_action_b(status, debug):
        file_to_index = {
            'aa': 0,
            'bb': 1,
            'cc': 2,
        }
        assert file_to_index[status.current_file] == status.index
        status.add_result_file(status.current_file)
        status.add_result_file(status.current_file + '1')
    mapcreator.building.BUILD_ACTIONS = (check_action_a, check_action_b)
    runner = CliRunner()
    result = runner.invoke(cli, ['build', '-do', 'test2.zip'])
    assert result.exit_code == 0
    assert 'SUCCESS' in result.output
    mock_package.assert_called_once_with('test2.zip', ['aa', 'aa1', 'bb', 'bb1', 'cc', 'cc1'])

@patch('os.path.exists', lambda s: True)
@patch('mapcreator.persistence.state_exists', lambda: True)
@patch('mapcreator.persistence.load_state', lambda: State.from_dict({'height_files': ['a', 'b', 'c']}))
@patch('mapcreator.building.init_build', lambda: True)
@patch('mapcreator.building.cleanup', lambda: True)
@patch('mapcreator.building.package')
def test_build_throws_errors_correctly(mock_package):
    def check_action_a(status, debug):
        assert status.index in range(3)
        assert not debug
        status.current_file = status.current_file * 2
    def check_action_b(status, debug):
        file_to_index = {
            'aa': 0,
            'bb': 1,
            'cc': 2,
        }
        if status.current_file == 'bb':
            raise ValueError('Oh no!')
        if status.current_file == 'cc':
            status.output.write('Hecking cool')
        assert file_to_index[status.current_file] == status.index
        status.add_result_file(status.current_file)
        status.add_result_file(status.current_file + '1')
    mapcreator.building.BUILD_ACTIONS = (check_action_a, check_action_b)
    runner = CliRunner()
    result = runner.invoke(cli, ['build', '-fo', 'test2.zip'])
    assert result.exit_code == 0
    assert str(ValueError('Oh no!')) in result.output
    assert 'Hecking cool' in result.output
    assert 'Build done (but there were errors)' in result.output
    assert 'SUCCESS' not in result.output
    mock_package.assert_called_once_with('test2.zip', ['aa', 'aa1', 'cc', 'cc1'])

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

