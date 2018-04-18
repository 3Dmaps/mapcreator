import click

IDENTIFIER_SIZE = 7
PROGRESS_BAR_TEMPLATE = (' ' * (IDENTIFIER_SIZE + 1)) + '%(label)s [%(bar)s] %(info)s'

def format_echo(identifier, s):
    if identifier:
        format_string = "{:>" + str(IDENTIFIER_SIZE) + "}: {}"
    else:
        format_string = "{:" + str(IDENTIFIER_SIZE + 1) + "} {}"
    return format_string.format(identifier, s)

def info(s):
    click.echo(format_echo('', s))

def highlight(s):
    click.secho(format_echo('', s), fg='cyan')

def warn(s):
    click.secho(format_echo('WARNING', s), fg='yellow')

def error(s):
    click.secho(format_echo('ERROR', s), bg='red')

def success(s):
    click.secho(format_echo('SUCCESS', s), bg='green')

def prettyinput():
    return input(' '*(IDENTIFIER_SIZE + 2))
