import re
import subprocess
import shutil
from os import path, listdir, makedirs, rename, remove, devnull
from io import StringIO
from zipfile import ZipFile, ZIP_DEFLATED
from mapcreator import persistence

BUILD_DIR = path.join(persistence.STATE_DIR, 'build')
FINALIZED_DIR = path.join(BUILD_DIR, 'finalized')

OUTPUT_FILENAME_REGEX = re.compile(r'^\[(\d+)\](.*)')
OUTPUT_FILENAME_FORMAT = '[{}]{}'

INTERNAL_FORMAT = 'GTiff'
INTERNAL_FILE_EXTENSION = 'tiff'

PROJECTION_IDENTIFIER = 'EPSG:3857'
OUTPUT_CELLSIZE = 10

OUTPUT_FORMAT = 'ENVI'
OUTPUT_FILE_EXTENSION = 'bin'
METADATA_FILE_EXTENSION = 'hdr'

FINAL_FILENAME_FORMAT = 'heightfile{}.' + OUTPUT_FILE_EXTENSION
FINAL_METADATA_FORMAT = 'heightfile{}.' + METADATA_FILE_EXTENSION

class BuildStatus:
    def __init__(self, index, heightfile, state):
        self.index = index
        self.output = StringIO()
        self.original_file = heightfile
        self.current_file = heightfile
        self.state = state
        self.result_files = []
    def add_result_file(self, file):
        self.result_files.append(file)
    def __str__(self):
        lines = ['Build results for {}:'.format(path.basename(self.original_file))]
        if self.result_files:
            lines.append('-Files created: {}'.format(', '.join(map(path.basename, self.result_files))))
        else:
            lines.append('-No files were created')
        if self.output.getvalue():
            lines.append('-Messages from GDAL:')
            lines.extend(self.output.getvalue().split('\n'))
        return '\n'.join(lines)

def call_command(command, buildstatus, debug = False):
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        if debug: buildstatus.output.write('\n[{}]\n'.format(command))
        stdout, stderr = process.communicate()
        if debug: buildstatus.output.write(stdout.decode('utf-8'))
        buildstatus.output.write(stderr.decode('utf-8'))


def init_build():
    if temp_build_files_exist():
        cleanup()
    makedirs(BUILD_DIR)
    makedirs(FINALIZED_DIR)

def get_output_path(input_path, new_extension = ''):
    input_filename = path.basename(input_path)
    match = OUTPUT_FILENAME_REGEX.match(input_filename)
    if match:
        next_index = int(match.group(1)) + 1
        new_filename = OUTPUT_FILENAME_FORMAT.format(next_index, match.group(2))
    else:
        new_filename = OUTPUT_FILENAME_FORMAT.format(0, input_filename)
    new_filename += ('.' + new_extension if new_extension else '')
    return path.join(BUILD_DIR, new_filename)

def prepare(buildstatus, debug = False):
    """
    First convert the file to GTiff (GDALs standard format) to make sure that everything works as expected
    """ 
    outpath = get_output_path(buildstatus.current_file, INTERNAL_FILE_EXTENSION)
    command = 'gdal_translate -of {} {} {}'.format(INTERNAL_FORMAT, buildstatus.current_file, outpath)
    call_command(command, buildstatus, debug)
    buildstatus.current_file = outpath

def cut_projection_window(buildstatus, debug = False):
    if buildstatus.state.has_window():
        outpath = get_output_path(buildstatus.current_file)
        command = 'gdalwarp -te {} {} {}'.format(buildstatus.state.get_window_string_lowerleft_topright(), buildstatus.current_file, outpath)
        call_command(command, buildstatus, debug)
        buildstatus.current_file = outpath

def reproject(buildstatus, debug = False):
    outpath = get_output_path(buildstatus.current_file)
    command = 'gdalwarp -tr {} {} -t_srs {} -r bilinear {} {}'.format(OUTPUT_CELLSIZE, OUTPUT_CELLSIZE, PROJECTION_IDENTIFIER, buildstatus.current_file, outpath)
    call_command(command, buildstatus, debug)
    buildstatus.current_file = outpath

def translate(buildstatus, debug = False):
    outpath = get_output_path(buildstatus.current_file, OUTPUT_FILE_EXTENSION)
    metapath = get_output_path(buildstatus.current_file, METADATA_FILE_EXTENSION)

    command = 'gdal_translate -of {} {} {}'.format(OUTPUT_FORMAT, buildstatus.current_file, outpath)
    call_command(command, buildstatus, debug)

    finalized_metaname = FINAL_METADATA_FORMAT.format(buildstatus.index)
    finalized_metapath = path.join(FINALIZED_DIR, finalized_metaname)
    rename(metapath, finalized_metapath)

    buildstatus.current_file = outpath
    buildstatus.add_result_file(finalized_metapath)


def finalize(buildstatus, debug = False):
    if buildstatus.current_file == buildstatus.original_file:
        raise RuntimeError('No actions have been done --> Not finalizing anything')
    final_filename = FINAL_FILENAME_FORMAT.format(buildstatus.index)
    final_path = path.join(FINALIZED_DIR, final_filename)
    rename(buildstatus.current_file, final_path)
    buildstatus.current_file = final_path
    buildstatus.add_result_file(final_path)

def package(package_name, files):
    with ZipFile(package_name, 'w', ZIP_DEFLATED) as package:
        for f in files:
            package.write(f, path.basename(f))

def temp_build_files_exist():
    return path.exists(BUILD_DIR)

def cleanup():
    shutil.rmtree(BUILD_DIR)

BUILD_ACTIONS = (
    prepare, cut_projection_window, reproject, translate, finalize
)