import re
import subprocess
import shutil
from os import path, listdir, makedirs, rename, remove, devnull
from io import StringIO
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
from mapcreator import persistence, osm, gdal_util
from mapcreator.osm import OSMData

BUILD_DIR = path.join(persistence.STATE_DIR, 'build')
FINALIZED_DIR = path.join(BUILD_DIR, 'finalized')

OUTPUT_FILENAME_REGEX = re.compile(r'^\[(\d+)\](.*)')
OUTPUT_FILENAME_FORMAT = '[{}]{}'

INTERNAL_FORMAT = 'GTiff'
INTERNAL_FILE_EXTENSION = 'tiff'

LATLON_DATUM_IDENTIFIER = 'EPSG:4326'
PROJECTION_IDENTIFIER = 'EPSG:3857'

HEIGHT_OUTPUT_FORMAT = 'ENVI'
HEIGHT_OUTPUT_FILE_EXTENSION = 'bin'
HEIGHT_METADATA_FILE_EXTENSION = 'hdr'
SATELLITE_OUTPUT_FORMAT = 'PNG'
OSM_FILE_EXTENSION = 'xml'
SATELLITE_FILE_EXTENSION = 'tif'
SATELLITE_OUTPUT_FILE_EXTENSION = 'png'

INTERMEDIATE_HEIGHT_FILENAME = 'heightfile_intermediate.' + INTERNAL_FILE_EXTENSION
INTERMEDIATE_SATELLITE_FORMAT = 'heightfile{}_satellite.' + SATELLITE_FILE_EXTENSION
FINAL_HEIGHT_FILENAME_FORMAT = 'heightfile{}.' + HEIGHT_OUTPUT_FILE_EXTENSION
FINAL_HEIGHT_METADATA_FORMAT = 'heightfile{}.' + HEIGHT_METADATA_FILE_EXTENSION
FINAL_OSM_FORMAT = 'heightfile{}_trails.' + OSM_FILE_EXTENSION
FINAL_SATELLITE_FORMAT = 'heightfile{}_satellite.' + SATELLITE_OUTPUT_FILE_EXTENSION

OSM_RGB_KEY = "3dmapsrgb"
OSM_RGB_VALUE_FORMAT = "{0[0]} {0[1]} {0[2]}"

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

def check_projection_window(buildStatus, debug = False):
    if buildStatus.state.has_window():
        for cf in buildStatus.current_files:
            gdal_info = gdal_util.Gdalinfo.for_file(cf)
            cut_projection_window = buildStatus.state.get_window_string_lowerleft_topright_cut(gdal_info)
            if cut_projection_window:
                buildStatus.add_next_file(cf)
    buildStatus.next()

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

# Outputs only one combined file
def process_heightfiles_with_gdal(heightMapStatus, debug = False):
    if heightMapStatus.current_files:    
        outpath = path.join(BUILD_DIR, INTERMEDIATE_HEIGHT_FILENAME)
        command = 'gdalwarp {source_system_cmd}-tr {cellsize} {cellsize} -te_srs {latlon_datum_identifier} -t_srs {projection_identifier} -r bilinear -te {projection_window} {heightfiles} {outpath}'.format(
            source_system_cmd = '-s_srs {} '.format(heightMapStatus.state.height_coordinatesystem) if heightMapStatus.state.has_height_system() else '', 
            cellsize = heightMapStatus.state.height_resolution, 
            latlon_datum_identifier = LATLON_DATUM_IDENTIFIER, 
            projection_identifier = PROJECTION_IDENTIFIER, 
            projection_window = heightMapStatus.state.get_window_string_lowerleft_topright(), 
            heightfiles = ' '.join(heightMapStatus.current_files), 
            outpath = outpath
        )
        call_command(command, heightMapStatus, debug)
        heightMapStatus.add_next_file(outpath)
        heightMapStatus.next()
    
def translate_heightfiles(heightMapStatus, debug = False):
    for ind, cf in enumerate(heightMapStatus.current_files):
        outpath = path.join(FINALIZED_DIR, FINAL_HEIGHT_FILENAME_FORMAT.format(ind))
        metapath = path.join(FINALIZED_DIR, FINAL_HEIGHT_METADATA_FORMAT.format(ind))
        command = 'gdal_translate -of {} {} {}'.format(HEIGHT_OUTPUT_FORMAT, cf, outpath)
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

def insert_colors(osmstatus, debug = False):
    for data in osmstatus.osmdata:
        for way in data.ways.values():
            tag = OSMData.get_tag(way, OSMData.KEY_LANDUSE)
            if tag in osmstatus.state.area_colors:
                ET.SubElement(way, OSMData.TAG_TAG, attrib={
                    OSMData.ATTRIB_KEY: OSM_RGB_KEY,
                    OSMData.ATTRIB_VALUE: OSM_RGB_VALUE_FORMAT.format(osmstatus.state.area_colors[tag])
                })

def prepare_write(osmstatus, debug = False):
    map(lambda data: data.prepare_for_save(), osmstatus.osmdata)

# Combines several OSM-files and writes out only on OSM file
def write(osmstatus, debug = False):
    if len(osmstatus.osmdata) > 1:
        combined_osmdata = osm.merge(osmstatus.osmdata)
    elif len(osmstatus.osmdata) == 1:
        combined_osmdata = osmstatus.osmdata
    else: return
    
    outpath = path.join(FINALIZED_DIR, FINAL_OSM_FORMAT.format(0))
    combined_osmdata.save(outpath)
    osmstatus.add_result_file(outpath)

# Satellite image status and actions
class SatelliteStatus:
    def __init__(self, index, satellitefiles, state):
        self.output = StringIO()
        self.original_files = satellitefiles
        self.current_files = satellitefiles
        self.next_files = []
        
        self.files_in_window = []
        self.state = state
        self.intermediate_files = []
        self.result_files = []
    def next(self):
        self.current_files = self.next_files
        self.next_files = []
    def add_next_file(self, f):
        self.next_files.append(f)
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

# Outputs only one combined file
def process_satellite_with_gdal(satellitestatus, debug = False):
    if satellitestatus.current_files:
        outpath = path.join(FINALIZED_DIR, INTERMEDIATE_SATELLITE_FORMAT.format(0))
        command = 'gdalwarp {source_system_cmd}-tr {cellsize} {cellsize} -te_srs {latlon_datum_identifier} -t_srs {projection_identifier} -r bilinear -te {projection_window} {satfiles} {outpath}'.format(
            source_system_cmd='-s_srs {} '.format(satellitestatus.state.satellite_coordinatesystem) if satellitestatus.state.has_satellite_system() else '', 
            cellsize = satellitestatus.state.satellite_resolution, 
            latlon_datum_identifier = LATLON_DATUM_IDENTIFIER, 
            projection_identifier = PROJECTION_IDENTIFIER, 
            projection_window=satellitestatus.state.get_window_string_lowerleft_topright(), 
            satfiles=' '.join(satellitestatus.current_files), 
            outpath=outpath
        )
        call_command(command, satellitestatus, debug)
        satellitestatus.add_next_file(outpath)
        satellitestatus.next()

def translate_satellite_to_png(satellitestatus, debug = False):
    for ind, cf in enumerate(satellitestatus.current_files):
        outpath = path.join(FINALIZED_DIR, FINAL_SATELLITE_FORMAT.format(ind))
        command = 'gdal_translate -of {} {} {}'.format(SATELLITE_OUTPUT_FORMAT, cf, outpath)
        call_command(command, satellitestatus, debug)    
        satellitestatus.add_result_file(outpath)    

HEIGHTMAP_ACTIONS = (
    check_projection_window, process_heightfiles_with_gdal, translate_heightfiles
)

OSM_ACTIONS = (
    load_osm, add_filters, apply_filters, insert_colors, prepare_write, write
)

SATELLITE_ACTIONS = (
    check_projection_window, process_satellite_with_gdal, translate_satellite_to_png
)
