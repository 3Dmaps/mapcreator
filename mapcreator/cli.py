import click

@click.group()
def cli():
    pass

@click.command()
def hello():
    click.secho('Hello world!', fg='green')

cli.add_command(hello)
