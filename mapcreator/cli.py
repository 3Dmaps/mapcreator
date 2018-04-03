import click
import subprocess
from os import path
from mapcreator import building
from mapcreator import persistence
from mapcreator.cli_util import *
from mapcreator.echoes import *
from mapcreator.state import FileAddResult


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
    add_files(files, 'add_height_file')

@click.command()
@click.argument('files', nargs=-1)
def add_osm_files(files):
    """Adds open street map files to the project"""
    if len(files) == 0:
        warn('No files were specified.')
        info('Try mapcreator add_osm_files [file 1] [file 2] ... [file n]')
        return
    add_files(files, 'add_osm_file')

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
@click.option('--output', '-o', default='3dmapdata.zip', help='Output file name. Default: 3dmapdata.zip')
@click.option('--force', '-f', is_flag=True, help='Build even if output file already exists')
@click.option('--debug', '-d', is_flag=True, help='Causes debug information to be printed during the build')
@click.option('--clean/--no-clean', default=True, help='Specifies whether to clean temporary build files after building')
def build(output, force, debug, clean):
    """
    Builds the project.
    Transforms and translates all output files to format used by the 3DMaps-application and packages them for easy transportation.
    """

    if path.exists(output) and not force:
        error('File {} already exists!'.format(output))
        info('If you wish to build and overwrite this file, do:')
        info('mapcreator build --force')
        return

    if not persistence.state_exists(): 
        warn('No project found in current working directory.')
        return
    state = load_or_error()
    if not state: return
    if not state.has_height_files():
        error('No height files have been added to the current project! There\'s nothing to build!')
        return
    
    if not build_init_or_error(): return

    highlight('STARTING BUILD')
    info('Output file is {}'.format(output))

    outfiles = []
    has_errors = False
    current_height_files = combine_files(state.height_files)
    state.set_height_files(current_height_files)
    #info('Length of height files: ' + str(len(current_height_files)))
    build_outfiles, build_has_errors = do_build(
        state.height_files, building.BuildStatus, building.BUILD_ACTIONS, state, debug
        )
    has_errors |= build_has_errors
    outfiles.extend(build_outfiles)

    osm_outfiles, osm_has_errors = do_build(
        state.osm_files, building.OSMStatus, building.OSM_ACTIONS, state, debug
    )
    has_errors |= osm_has_errors
    outfiles.extend(osm_outfiles)

    info('Building package...')
    try:
        building.package(output, outfiles)
    except Exception as e:
        error('Unable to create package: {}'.format(e))
        has_errors = True
    if clean:
        info('Cleaning up...')
        if not build_clean_or_error():
            has_errors = True
    else:
        info('Not cleaning temporary build files')
    if has_errors:
        warn('Build done (but there were errors)')
    else:
        success('BUILD SUCCESSFUL!')

@click.command()
def clean_temp_files():
    """Cleans up temporary build files"""
    if not building.temp_build_files_exist():
        info('No temporary build files to clean up.')
        return
    info('Cleaning up temporary build files...')
    if build_clean_or_error():
        success('Cleaned up!')

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
cli.add_command(add_osm_files)
cli.add_command(set_window)
cli.add_command(status)
cli.add_command(reset)
cli.add_command(build)
cli.add_command(clean_temp_files)
