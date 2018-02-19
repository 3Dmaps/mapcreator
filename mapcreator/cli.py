import click
from clint.textui import colored, puts

@click.group()
def cli():
    pass

@click.command()
def hello():
    puts(colored.green('Hello world!'))

cli.add_command(hello)
