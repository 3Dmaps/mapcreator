import click
import decorator
from click.testing import CliRunner
from mapcreator.cli import cli

def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(cli, ['hello'])
    assert result.exit_code == 0
    assert 'Hello world' in result.output
