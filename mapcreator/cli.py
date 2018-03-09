import click
import subprocess
from os import path
from mapcreator import persistence
from mapcreator.cli_util import *
from mapcreator.echoes import *
from mapcreator.state import FileAddResult
from subprocess import run
from subprocess import call
@click.group()
def cli():
    """
    An utility for creating correctly formatted data for the 3Dmaps application.

    To get more information of what some command does, try
    mapcreator [command] --help

    Part of Software production project course, Spring 2018, University of Helsinki.
    """
    pass

@click.command()
def hello():
    """Says 'Hello world!', very successfully!"""
    success('Hello world!')

@click.command()
@click.option('--force', '-f', is_flag=True, help='Force initialization, even if project already exists')
def init(force):
    """
    Initializes the project. 
    A project is also automatically initialized by any command that needs persistence,
    so calling init is just a more verbose way to do it.
    """
    if persistence.state_exists() and not force:
        warn('Project already exists, no initialization done.')
        info('If you want to reset the project and initialize a new project, do:')
        info('mapcreator init --force')
        return
    info('Initializing project...')
    if init_or_error():
        success('Project initialized!')

@click.command()
@click.argument('files', nargs=-1)
def add_height_files(files):
    """Adds given height data files to the project"""
    if len(files) == 0:
        warn('No files were specified.')
        info('Try mapcreator add_height_files [file 1] [file 2] ... [file n]')
        return
    state = load_or_error()
    if not state: return
    info('Adding files to project...')
    count = 0
    for fpath in files:
        result = state.add_height_file(fpath)
        if result == FileAddResult.DOESNT_EXIST:
            error('File "{}" doesn\'t exist!'.format(fpath))
        elif result == FileAddResult.ALREADY_ADDED:
            warn('{} has already been added to this project'.format(fpath))
        elif result == FileAddResult.SUCCESS:
            info('"{}" added'.format(fpath))
            count += 1
        else:
            error('Unrecognized FileAddResult {} when trying to add {}!'.format(result, fpath))
    if count > 0:
        if not save_or_error(state): return
        if count == len(files):
            success("{} files added to the project successfully!".format(len(files)))
        else:
            warn("{} files (out of {}) added to the project successfully".format(count, len(files)))
    else:
        warn('No files were added.')

@click.command()
@click.argument('ulx', type=float)
@click.argument('uly', type=float)
@click.argument('lrx', type=float)
@click.argument('lry', type=float)
def set_window(ulx, uly, lrx, lry):
    """
    Specifies projection subwindow. 
    Uses upper left (ulx, uly) and lower right (lrx, lry) corners.

    If any of the coordinates is negative, you'll need to seperate the arguments from the command
    with a double dash; for example
    
    mapcreator set_window -- 110.3 -13.2 110.5 -12.1
    """
    state = load_or_error()
    if not state: return
    info('Setting window to {} -> {}'.format((ulx, uly), (lrx, lry)))
    state.set_window(ulx, uly, lrx, lry)
    if save_or_error(state):
        success('Window set to {} -> {}'.format((ulx, uly), (lrx, lry)))

@click.command()
@click.option('--output', '-o', default='3dmapdata.txt')
def build(output):
    
    #state = load_or_error()
    if not persistence.state_exists(): 
        info('No project found in current working directory.')
        return
    if load_or_error():
        state = load_or_error()
        
        for line in state.height_files:
            
            subprocess.call('gdalwarp -te {} {} {} {} {} {}.bil'.format(state.window['ulx'], state.window['uly'], state.window['lrx'], state.window['lry'],line, line + 'output'))
            subprocess.call('gdalwarp -t_srs EPSG:3857 -r bilinear {0} {0}output2.bil'.format(line))
            subprocess.call('gdal_translate -of ENVI {0} {0}output3.bil'.format(line))
                       
            #VAIHEESSA
            # gdalwarp -te 1 1 5 5 -t_srs EPSG:3857 -r bilinear n36w113.img output200.img on myös mahdollista
            
           
    # TODO: Use GDAL etc. to do the actual conversion


@click.command()
def status():
    """Shows the status of the current project"""
    if persistence.state_exists():
        highlight('CURRENT PROJECT STATE')
        info('-Persistence location: {}'.format(path.abspath(persistence.state_path())))
        state = persistence.load_state()
        for line in str(state).split('\n'):
            info(line)
    else:
        info('No project found in current working directory.')

@click.command()
def reset():
    """Clears the current project."""
    if not persistence.state_exists():
        info("No project found in current working directory. No need to reset!")
        return
    info('Resetting project...')
    if clear_or_error():
        success('Project has been reset.')

cli.add_command(hello)
cli.add_command(init)
cli.add_command(add_height_files)
cli.add_command(set_window)
cli.add_command(status)
cli.add_command(reset)
cli.add_command(build)
