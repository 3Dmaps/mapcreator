import re
import subprocess
import shutil
from os import path, listdir, makedirs, rename, remove, devnull
from io import StringIO
from zipfile import ZipFile, ZIP_DEFLATED
from mapcreator import persistence, osm, gdal_util
from mapcreator.osm import OSMData

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
OSM_FILE_EXTENSION = 'xml'

INTERMEDIATE_FILENAME_FORMAT = 'heightfile{}.' + INTERNAL_FILE_EXTENSION
FINAL_FILENAME_FORMAT = 'heightfile{}.' + OUTPUT_FILE_EXTENSION
FINAL_METADATA_FORMAT = 'heightfile{}.' + METADATA_FILE_EXTENSION
FINAL_OSM_FORMAT = 'heightfile{}_trails.' + OSM_FILE_EXTENSION

class BuildStatus:
    def __init__(self, index, heightfile, state):
        self.index = index
        self.output = StringIO()
        self.original_file = heightfile
        self.current_file = heightfile
        self.state = state
        self.result_files = []
        self.window_exists = True
    def add_result_file(self, file):
        self.result_files.append(file)
    def get_result_files(self):
        return self.result_files
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
        gdal_info = gdal_util.Gdalinfo.for_file(buildstatus.current_file)
        cut_projection_window = buildstatus.state.get_window_string_lowerleft_topright_cut(gdal_info)
        if cut_projection_window:
            command = 'gdalwarp -te {} {} {}'.format(cut_projection_window, buildstatus.current_file, outpath)
            call_command(command, buildstatus, debug)
            buildstatus.current_file = outpath
        else:
            buildstatus.window_exists = False

def reproject(buildstatus, debug = False):
    if buildstatus.window_exists:
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
    if buildstatus.current_file == buildstatus.original_file or not buildstatus.window_exists:
        raise RuntimeError('No actions have been done --> Not finalizing anything')
    final_filename = INTERMEDIATE_FILENAME_FORMAT.format(buildstatus.index)
    final_path = path.join(FINALIZED_DIR, final_filename)
    rename(buildstatus.current_file, final_path)
    buildstatus.current_file = final_path
    buildstatus.add_result_file(final_path)

def merge_mapfiles(mapfiles):
    """
    Merge source map files into a single file.
    """ 
    combined_file_name = INTERMEDIATE_FILENAME_FORMAT.format('_combined')
    single_path = path.join(FINALIZED_DIR, combined_file_name)
    sourcefiles_as_string = ' '.join(mapfiles)
    command = 'gdalwarp {} {}'.format(sourcefiles_as_string, single_path)
    
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        stdout, stderr = process.communicate()
        print(stderr.decode('utf-8'))

    final_path, metapath = translate_merged(single_path)
    return final_path, metapath

def translate_merged(combined_file):
    combined_file_name = FINAL_FILENAME_FORMAT.format('_combined_bin')
    final_path = path.join(FINALIZED_DIR, combined_file_name)
    metapath = path.join(FINALIZED_DIR, FINAL_METADATA_FORMAT.format('_combined_bin'))

    command = 'gdal_translate -of {} {} {}'.format(OUTPUT_FORMAT, combined_file, final_path)

    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        stdout, stderr = process.communicate()
        print(stderr.decode('utf-8'))    

    return final_path, metapath

class OSMStatus:
    def __init__(self, index, inpath, state):
        self.state = state
        self.path = inpath
        self.index = index
        self.osmdata = None
        self.result = None
    def get_result_files(self):
        return [self.result]
    def __str__(self):
        return 'Converted {} to {}'.format(self.path, self.result)

def load_osm(osmstatus, debug = False):
    osmstatus.osmdata = OSMData.load(osmstatus.path)

def add_filters(osmstatus, debug = False):
    data = osmstatus.osmdata
    if osmstatus.state.has_window():
        ulx, uly = osmstatus.state.get_window_upper_left()
        lrx, lry = osmstatus.state.get_window_lower_right()
        minx = min(ulx, lrx)
        miny = min(uly, lry)
        maxx = max(ulx, uly)
        maxy = max(uly, lry)
        for f in (osm.areaFilter, osm.trailFilter):
            data.add_way_filter(f, osm.WayCoordinateFilter(minx, maxx, miny, maxy).filter) # Filter: f AND coordfilter

def apply_filters(osmstatus, debug = False):
    osmstatus.osmdata.do_filter()

def prepare_write(osmstatus, debug = False):
    osmstatus.osmdata.prepare_for_save()

def write(osmstatus, debug = False):
    outpath = path.join(FINALIZED_DIR, FINAL_OSM_FORMAT.format(osmstatus.index))
    osmstatus.osmdata.save(outpath)
    osmstatus.result = outpath

def package(package_name, files):
    with ZipFile(package_name, 'w', ZIP_DEFLATED) as package:
        for f in files:
            package.write(f, path.basename(f))

def temp_build_files_exist():
    return path.exists(BUILD_DIR)

def cleanup():
    shutil.rmtree(BUILD_DIR)

BUILD_ACTIONS = (
    # Removed translate when changing to merging map files
    #prepare, cut_projection_window, reproject, translate, finalize
    prepare, cut_projection_window, reproject, finalize
)

OSM_ACTIONS = (
    load_osm, add_filters, apply_filters, prepare_write, write
)