import click
import mapcreator
from click.testing import CliRunner
from mapcreator.cli import cli
from mapcreator.state import State
from os import path
from mock import patch
from imp import reload
from mapcreator.state import State, FileAddResult


def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(cli, ['hello'])
    assert result.exit_code == 0
    assert 'Hello world' in result.output

def test_status_when_state_not_exists():
    runner = CliRunner()
    runner.invoke(cli, ['reset'])
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0
    assert 'No project found in current working directory.' in result.output

def test_init_when_state_not_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ['init'])
    assert result.exit_code == 0
    assert 'Project initialized!' in result.output

def test_init_when_state_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ['init'])
    assert result.exit_code == 0
    assert 'Project already exists, no initialization done.' in result.output

def test_add_zero_height_files():
    runner = CliRunner()
    result = runner.invoke(cli, ['add_height_files'])
    assert result.exit_code == 0
    assert 'No files were specified.' in result.output

@patch.object(mapcreator.state.State, 'add_height_file')
def test_add_height_files(mock):
    runner = CliRunner()
    runner.invoke(cli, ['add_height_files','test.txt'])
    mock.return_value = FileAddResult.SUCCESS
    mock.assert_called_with('test.txt')

@patch.object(mapcreator.state.State, 'add_height_file')
def test_add_height_files_doesnt_exist(mock):
    runner = CliRunner()
    mock.return_value = FileAddResult.DOESNT_EXIST
    result = runner.invoke(cli, ['add_height_files','test2.txt'])
    assert 'File "test2.txt" doesn\'t exist!' in result.output

@patch.object(mapcreator.state.State, 'add_height_file')
def test_add_height_files_already_added(mock):
    runner = CliRunner()
    mock.return_value = FileAddResult.ALREADY_ADDED
    result = runner.invoke(cli, ['add_height_files','test3.txt'])
    assert 'test3.txt has already been added to this project' in result.output

def test_reset_when_state_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ['reset'])
    assert result.exit_code == 0
    assert 'Project has been reset.' in result.output

def test_reset_when_state_not_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ['reset'])
    assert result.exit_code == 0
    assert 'No project found in current working directory. No need to reset!' in result.output

