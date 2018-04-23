import click
import sys, traceback
from mapcreator import building
from mapcreator import persistence
from mapcreator import echoes
from mapcreator.state import FileAddResult


"""
The x_or_error functions return a falsy value if an error was thrown.
If everything went OK, they return either True or resulting state, depending on the function.
"""

def init_or_error():
    try:
        state = persistence.init_state()
    except Exception as e:
        echoes.error('Unable to initialize project: {}'.format(e))
        return None
    else:
        return state

def load_or_error():
    try:
        state = persistence.load_state()
    except Exception as e:
        echoes.error('Unable to load or initialize the project: {}'.format(e))
        return None
    else:
        return state

def save_or_error(state):
    try:
        persistence.save_state(state)
    except Exception as e:
        echoes.error('Unable to save changes to the project! No changes done!')
        echoes.error('What went wrong: {}'.format(e))
        return None
    else:
        return state

def clear_or_error():
    try:
        persistence.clear_state()
    except Exception as e:
        echoes.error('Unable to reset project: {}'.format(e))
        return False
    else:
        return True

def build_init_or_error():
    try:
        building.init_build()
    except Exception as e:
        echoes.error('Unable to initialize build: {}'.format(e))
        return False
    else:
        return True

def build_clean_or_error():
    try:
        building.cleanup()
    except Exception as e:
        echoes.error('Unable to clean temporary build files: {}'.format(e))
        return False
    else: 
        return True

def add_files(files, add_method_name):
    state = load_or_error()
    if not state: return
    echoes.info('Adding files to project...')
    count = 0
    for fpath in files:
        result = getattr(state, add_method_name)(fpath) # Call method whose name is add_method_name
        if result == FileAddResult.DOESNT_EXIST:
            echoes.error('File "{}" doesn\'t exist!'.format(fpath))
        elif result == FileAddResult.ALREADY_ADDED:
            echoes.warn('{} has already been added to this project'.format(fpath))
        elif result == FileAddResult.SUCCESS:
            echoes.info('"{}" added'.format(fpath))
            count += 1
        else:
            echoes.error('Unrecognized FileAddResult {} when trying to add {}!'.format(result, fpath))
    if count > 0:
        if not save_or_error(state): return
        if count == len(files):
            echoes.success("{} files added to the project successfully!".format(len(files)))
        else:
            echoes.warn("{} files (out of {}) added to the project successfully".format(count, len(files)))
    else:
        echoes.warn('No files were added.')

def clear_files(clear_method_name, files_type):
    state = load_or_error()
    if not state: return
    echoes.info('Clearing {} files...'.format(files_type))
    getattr(state, clear_method_name)() # Call method whose name is clear_method_name
    if save_or_error(state):
        echoes.success('All {} files cleared successfully!'.format(files_type))
    

def parse_color(line, debug = False):
    PARSER = [str, int, int, int]
    parts = line.split(' ')
    if len(parts) != len(PARSER):
        echoes.error("Invalid number of arguments on a line!")
        echoes.error("(Should be {}, was {})".format(len(PARSER), len(parts)))
        if debug: echoes.info("Line was: {}".format(line))
        return None
    try:
        for i, func in enumerate(PARSER):
            parts[i] = func(parts[i])
    except ValueError as e:
        echoes.error("Invalid color format!")
        echoes.error("({})".format(e))
        if debug: echoes.info("Line was: {}".format(line))
        return None
    return parts

def validate_color(r, g, b):
    for value in (r, g, b):
        if value < 0 or value > 255:
            echoes.error("Invalid color value {}!".format(value))
            echoes.info("(Should be between 0 and 255)")
            return False
    return True

def validate_resolution(reso, lower, upper):
    if reso < lower or reso > upper:
        echoes.error("Invalid resolution {}!".format(reso))
        echoes.info("(Should be between {} and {})".format(lower, upper))
        return False
    return True

def do_build(files, statusclass, actions, state, debug = False):
    has_errors = False
    outfiles = []
    echoes.info('Processing...')
    buildstatus = statusclass(0, files, state)
    errors = []
    with click.progressbar(actions, bar_template=echoes.PROGRESS_BAR_TEMPLATE, show_eta=False) as bar:
        for action in bar:
            try:
                action(buildstatus, debug)
            except Exception as e:
                errors.append(e)
                if debug:
                    e_type, e_value, e_traceback = sys.exc_info()
                    errors.extend(traceback.format_tb(e_traceback))
                has_errors = True
    if errors:
        echoes.error('Exceptions caught:')
        for e in errors:
            echoes.error(e)
    for line in str(buildstatus).split('\n'):
        echoes.info(line)
    outfiles.extend(buildstatus.get_result_files())
    return (outfiles, has_errors)