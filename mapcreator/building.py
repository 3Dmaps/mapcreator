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

INTERNAL_FILE_EXTENSION = 'tif'

LATLON_DATUM_IDENTIFIER = 'EPSG:4326'
PROJECTION_IDENTIFIER = 'EPSG:3857'
OUTPUT_CELLSIZE = 10

HEIGHT_OUTPUT_FORMAT = 'ENVI'
HEIGHT_OUTPUT_FILE_EXTENSION = 'bin'
HEIGHT_METADATA_FILE_EXTENSION = 'hdr'
SATELLITE_OUTPUT_FORMAT = 'PNG'
OSM_FILE_EXTENSION = 'xml'
SATELLITE_FILE_EXTENSION = 'tif'
SATELLITE_OUTPUT_FILE_EXTENSION = 'png'

INTERMEDIATE_HEIGHT_FILENAME = 'heightfile.' + INTERNAL_FILE_EXTENSION
INTERMEDIATE_SATELLITE_FILENAME = 'heightfile_satellite.' + SATELLITE_FILE_EXTENSION
FINAL_HEIGHT_FILENAME = 'heightfile.' + HEIGHT_OUTPUT_FILE_EXTENSION
FINAL_HEIGHT_METADATA_FILENAME = 'heightfile.' + HEIGHT_METADATA_FILE_EXTENSION
FINAL_OSM_FORMAT = 'heightfile_{}_trails.' + OSM_FILE_EXTENSION
FINAL_SATELLITE_FILENAME = 'heightfile_satellite.' + SATELLITE_OUTPUT_FILE_EXTENSION

# General functions, not tied to a file type
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

def package(package_name, files):
    with ZipFile(package_name, 'w', ZIP_DEFLATED) as package:
        for f in files:
            package.write(f, path.basename(f))

def temp_build_files_exist():
    return path.exists(BUILD_DIR)

def cleanup():
    shutil.rmtree(BUILD_DIR)

# HeightMap status and actions
class HeightMapStatus:
    def __init__(self, index, heightfiles, state):
        self.output = StringIO()
        self.original_files = heightfiles
        self.files_in_window = []
        self.state = state
        self.intermediate_files = []
        self.result_files = []
    
    def add_file_in_window(self, f):
        self.files_in_window.append(f)
    def add_intermediate_file(self, f):
        self.intermediate_files.append(f)
    def add_result_file(self, f):
        self.result_files.append(f)
    def get_result_files(self):
        return self.result_files
    def __str__(self):
        lines = []
        if self.original_files == []:
            lines.append('No height files were processed.')
        else:
            lines.append('Build results for {}:'.format(', '.join(map(path.basename, self.original_files))))
            if self.result_files:
                lines.append('-Files created: {}'.format(', '.join(map(path.basename, self.result_files))))
            else:
                lines.append('-No files were created')
            if self.output.getvalue():
                lines.append('-Messages from GDAL:')
                lines.extend(self.output.getvalue().split('\n'))
        return '\n'.join(lines)

def process_heightfiles_with_gdal(heightMapStatus, debug = False):
    outpath = path.join(BUILD_DIR, INTERMEDIATE_HEIGHT_FILENAME)

    # Check which height files lie in the window and call GDAL with only them as input files. NOTE: this is slow, could we skip this and just give all files to GDAL?
    for heightfile in heightMapStatus.original_files:
        gdal_info = gdal_util.Gdalinfo.for_file(heightfile)
        if heightMapStatus.state.get_window_string_lowerleft_topright_cut(gdal_info):
            heightMapStatus.add_file_in_window(heightfile)
    if heightMapStatus.files_in_window:
        heightfiles = ' '.join(heightMapStatus.files_in_window)
        projection_window = heightMapStatus.state.get_window_string_lowerleft_topright()
        command = 'gdalwarp -tr {} {} -te_srs {} -t_srs {} -r bilinear -te {} {} {}'.format(OUTPUT_CELLSIZE, OUTPUT_CELLSIZE, LATLON_DATUM_IDENTIFIER, PROJECTION_IDENTIFIER, projection_window, heightfiles, outpath)
        call_command(command, heightMapStatus, debug)
        heightMapStatus.add_intermediate_file(outpath)

def translate_heightfile(heightMapStatus, debug = False):
    if heightMapStatus.intermediate_files:
        outpath = path.join(FINALIZED_DIR, FINAL_HEIGHT_FILENAME)
        metapath = path.join(FINALIZED_DIR, FINAL_HEIGHT_METADATA_FILENAME)
        command = 'gdal_translate -of {} {} {}'.format(HEIGHT_OUTPUT_FORMAT, ' '.join(heightMapStatus.intermediate_files), outpath)
        call_command(command, heightMapStatus, debug)
        heightMapStatus.add_result_file(outpath)
        heightMapStatus.add_result_file(metapath)

# Open Street Map (OSM) XML-file status and actions
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
        if self.results:
            return 'Converted {} to {}'.format(
                ', '.join(map(path.basename, self.paths)),
                ', '.join(map(path.basename, self.results))
            )
        else:
            return 'No OSM files were processed.'
        

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

# Satellite image status and actions
class SatelliteStatus:
    def __init__(self, index, satellitefiles, state):
        self.output = StringIO()
        self.original_files = satellitefiles
        self.files_in_window = []
        self.state = state
        self.intermediate_files = []
        self.result_files = []
    def add_file_in_window(self, f):
        self.files_in_window.append(f)
    def add_intermediate_file(self, f):
        self.intermediate_files.append(f)
    def add_result_file(self, f):
        self.result_files.append(f)
    def get_result_files(self):
        return self.result_files
    
    def __str__(self):
        lines = []
        if self.original_files == []:
            lines.append('No satellite files were processed.')
        else:
            lines.append('Build results for {}:'.format(', '.join(map(path.basename, self.original_files))))
            if self.result_files:
                lines.append('-Files created: {}'.format(', '.join(map(path.basename, self.result_files))))
            else:
                lines.append('-No files were created')
            if self.output.getvalue():
                lines.append('-Messages from GDAL:')
                lines.extend(self.output.getvalue().split('\n'))
        return '\n'.join(lines)

def process_satellite_with_gdal(satellitestatus, debug = False):
    outpath = path.join(BUILD_DIR, INTERMEDIATE_SATELLITE_FILENAME.format(0))
    
    # Check which satellite files lie in the window and call GDAL with only them as input files. NOTE: this is slow, could we skip this and just give all files to GDAL?
    for satfile in satellitestatus.original_files:
        gdal_info = gdal_util.Gdalinfo.for_file(satfile)
        if satellitestatus.state.get_window_string_lowerleft_topright_cut(gdal_info):
            satellitestatus.add_file_in_window(satfile)
    if satellitestatus.files_in_window:
        satfiles = ' '.join(satellitestatus.files_in_window)
        projection_window = satellitestatus.state.get_window_string_lowerleft_topright()
        command = 'gdalwarp -tr {} {} -te_srs {} -t_srs {} -r bilinear -te {} {} {}'.format(OUTPUT_CELLSIZE, OUTPUT_CELLSIZE, LATLON_DATUM_IDENTIFIER, PROJECTION_IDENTIFIER, projection_window, satfiles, outpath)
        call_command(command, satellitestatus, debug)
        satellitestatus.add_intermediate_file(outpath)

def translate_satellite(satellitestatus, debug = False):
    if satellitestatus.intermediate_files:
        outpath = path.join(FINALIZED_DIR, FINAL_SATELLITE_FILENAME.format(0))
        command = 'gdal_translate -of {} {} {}'.format(SATELLITE_OUTPUT_FORMAT, ' '.join(satellitestatus.intermediate_files), outpath)
        call_command(command, satellitestatus, debug)
        satellitestatus.add_result_file(outpath)    


HEIGHTMAP_ACTIONS = (
    process_heightfiles_with_gdal, translate_heightfile
)

OSM_ACTIONS = (
    load_osm, add_filters, apply_filters, prepare_write, write
)

SATELLITE_ACTIONS = (
    process_satellite_with_gdal, translate_satellite
)
