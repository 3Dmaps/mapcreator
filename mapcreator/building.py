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
    def __init__(self, index, heightfiles, state):
        self.index = index
        self.metaindex = index
        self.output = StringIO()
        self.original_files = heightfiles
        self.current_files = heightfiles
        self.next_files = []
        self.state = state
        self.result_files = []
    def add_next_file(self, f):
        self.next_files.append(f)
    def next(self):
        self.current_files = self.next_files
        self.next_files = []
    def add_result_file(self, f):
        self.result_files.append(f)
    def get_result_files(self):
        return self.result_files
    def get_index(self):
        ret = self.index
        self.index += 1
        return ret
    def get_metaindex(self):
        ret = self.metaindex
        self.metaindex += 1
        return ret
    def __str__(self):
        lines = ['Build results for {}:'.format(', '.join(map(path.basename, self.original_files)))]
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
    First convert the files to GTiff (GDALs standard format) to make sure that everything works as expected
    """ 
    for cf in buildstatus.current_files:
        outpath = get_output_path(cf, INTERNAL_FILE_EXTENSION)
        command = 'gdal_translate -of {} {} {}'.format(INTERNAL_FORMAT, cf, outpath)
        call_command(command, buildstatus, debug)
        buildstatus.add_next_file(outpath)
    buildstatus.next()

def cut_projection_window(buildstatus, debug = False):
    if buildstatus.state.has_window():
        for cf in buildstatus.current_files:
            outpath = get_output_path(cf)
            gdal_info = gdal_util.Gdalinfo.for_file(cf)
            cut_projection_window = buildstatus.state.get_window_string_lowerleft_topright_cut(gdal_info)
            if cut_projection_window:
                command = 'gdalwarp -te {} {} {}'.format(cut_projection_window, cf, outpath)
                call_command(command, buildstatus, debug)
                buildstatus.add_next_file(outpath)
        buildstatus.next()
        

def reproject(buildstatus, debug = False):
    for cf in buildstatus.current_files:
        outpath = get_output_path(cf)
        command = 'gdalwarp -tr {} {} -t_srs {} -r bilinear {} {}'.format(OUTPUT_CELLSIZE, OUTPUT_CELLSIZE, PROJECTION_IDENTIFIER, cf, outpath)
        call_command(command, buildstatus, debug)
        buildstatus.add_next_file(outpath)
    buildstatus.next()

def merge(buildstatus, debug = False):
    """
    Merge source map files into a single file.
    """ 
    combined_file_name = INTERMEDIATE_FILENAME_FORMAT.format('_combined')
    single_path = path.join(BUILD_DIR, combined_file_name)
    sourcefiles_as_string = ' '.join(buildstatus.current_files)
    command = 'gdalwarp {} {}'.format(sourcefiles_as_string, single_path)
    call_command(command, buildstatus, debug)
    buildstatus.add_next_file(single_path)
    buildstatus.next()

def translate(buildstatus, debug = False):
    for cf in buildstatus.current_files:
        outpath = get_output_path(cf, OUTPUT_FILE_EXTENSION)
        metapath = get_output_path(cf, METADATA_FILE_EXTENSION)

        command = 'gdal_translate -of {} {} {}'.format(OUTPUT_FORMAT, cf, outpath)
        call_command(command, buildstatus, debug)

        finalized_metaname = FINAL_METADATA_FORMAT.format(buildstatus.get_metaindex())
        finalized_metapath = path.join(FINALIZED_DIR, finalized_metaname)
        rename(metapath, finalized_metapath)

        buildstatus.add_next_file(outpath)
        buildstatus.add_result_file(finalized_metapath)
    buildstatus.next()


def finalize(buildstatus, debug = False):
    if buildstatus.current_files == buildstatus.original_files:
        raise RuntimeError('No actions have been done --> Not finalizing anything')
    for cf in buildstatus.current_files:
        final_filename = FINAL_FILENAME_FORMAT.format(buildstatus.get_index())
        final_path = path.join(FINALIZED_DIR, final_filename)
        rename(cf, final_path)
        buildstatus.add_next_file(final_path)
        buildstatus.add_result_file(final_path)
    buildstatus.next()

class OSMStatus:
    def __init__(self, index, inpaths, state):
        self.state = state
        self.paths = inpaths
        self.index = index
        self.osmdata = []
        self.results = []
    def add_osm_data(self, osmdata):
        self.osmdata.append(osmdata)
    def add_result_file(self, f):
        self.results.append(f)
    def get_index(self):
        ret = self.index
        self.index += 1
        return ret
    def get_result_files(self):
        return self.results
    def __str__(self):
        return 'Converted {} to {}'.format(
            ', '.join(map(path.basename, self.paths)),
            ', '.join(map(path.basename, self.results))
        )

def load_osm(osmstatus, debug = False):
    for infile in osmstatus.paths:
        osmstatus.add_osm_data(OSMData.load(infile))

def add_filters(osmstatus, debug = False):
    for data in osmstatus.osmdata:
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
    map(lambda data: data.do_filter(), osmstatus.osmdata)

def prepare_write(osmstatus, debug = False):
    map(lambda data: data.prepare_for_save(), osmstatus.osmdata)

def write(osmstatus, debug = False): #TODO: Combine these instead of saving multiple output files
    for data in osmstatus.osmdata:
        outpath = path.join(FINALIZED_DIR, FINAL_OSM_FORMAT.format(osmstatus.get_index()))
        data.save(outpath)
        osmstatus.add_result_file(outpath)

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
    prepare, cut_projection_window, reproject, merge, translate, finalize
)

OSM_ACTIONS = (
    load_osm, add_filters, apply_filters, prepare_write, write
)