# mapcreator
Map creator tool for 3Dmaps application. A subproject of the [*3DMaps in augmented reality*](https://github.com/3Dmaps/3Dmaps). Built on the Software production project course / Univ. of Helsinki, spring 2018. Additional information: see main project repository.

## Installation
This project requires [Python 3](https://www.python.org/downloads/) to run.
To install, first ensure that pip (included in Python 3.4+) is installed. Navigate to project root. First, run
```
pip install -r requirements.txt
```
from your command line. Then, run
```
pip install --editable .
```
to install. After that, try
```
mapcreator hello
```
If you wan't to build files, you need to install GDAL.

## Help
```
mapcreator --help
```
## Help on a command
```
mapcreator \[command] --help
```
## Commands 
| Command | Description |
| --- | | --- |
|'add_area_color' | Adds one area color for OSM data. |
| 'add_area_color --help' | Usage: mapcreator add_area_color [OPTIONS] TAG RED GREEN BLUE

  Adds one area color for OSM data.
| 'add_area_colors' | Adds multiple area colors for OSM data. |
| 'add_area_colors --help' | Usage: mapcreator add_area_colors [OPTIONS]

  Adds multiple area colors for OSM data.

  The colors should be inputted one color per line in the following format:

  TAG RED GREEN BLUE

  where TAG is OSM landuse value and RED, GREEN and BLUE are the color's RGB
  value (each of them an integer between 0 and 255). For example

  meadow 10 200 10

  forest 20 100 20

  The command reads lines until a blank line or an EOF is encountered. You
  can either input the lines straight into the terminal, or use piping:

  cat colors | mapcreator add_area_colors

Options:
  -d, --debug  Causes additional information to be printed on error
  --help       Show this message and exit.
| 'add_height_files' | Adds given height data files to the project |
| 'add_height_files --help' | Usage: mapcreator add_height_files [OPTIONS] [FILES]...

  Adds given height data files to the project

Options:
  --help  Show this message and exit.
| 'add_osm_files' | Adds open street map files to the project |
| 'add_osm_files --help' | Usage: mapcreator add_osm_files [OPTIONS] [FILES]...

  Adds open street map files to the project

Options:
  --help  Show this message and exit.
| 'add_satellite_files' | Adds given satellite image files to the... |
| 'add_satellite_files --help' | Usage: mapcreator add_satellite_files [OPTIONS] [FILES]...

  Adds given satellite image files to the project

Options:
  --help  Show this message and exit.
| 'build' | Builds the project. |
| 'build --help' | Usage: mapcreator build [OPTIONS]

  Builds the project. Transforms and translates all output files to format
  used by the 3DMaps-application and packages them for easy transportation.

Options:
  -o, --output TEXT     Output file name. Default: 3dmapdata.zip
  -f, --force           Build even if output file already exists
  -d, --debug           Causes debug information to be printed during the
                        build
  --clean / --no-clean  Specifies whether to clean temporary build files after
                        building
  --help                Show this message and exit.
| 'clean_temp_files' | Cleans up temporary build files |
| 'clean_temp_files --help' | C:\Program Files\GDAL>mapcreator clean_temp_files --help
Usage: mapcreator clean_temp_files [OPTIONS]

  Cleans up temporary build files

Options:
  --help  Show this message and exit.
| 'clear_area_colors' | Clears area colors |
| 'clear_area_colors --help' | Usage: mapcreator clear_area_colors [OPTIONS]

  Clears area colors.

Options:
  --help  Show this message and exit.
| 'clear_height_files' | Clears height files |
| 'clear_height_files --help' | Usage: mapcreator clear_height_files [OPTIONS]

  Clears height files

Options:
  --help  Show this message and exit.
| 'clear_height_system' | Clears the set forced coordinate system for... |
| 'clear_height_system --help' | Usage: mapcreator clear_height_system [OPTIONS]

  Clears the set forced coordinate system for source height data. After
  clearing, mapcreator automatically uses the coordinate system read from
  the source file metadata.

Options:
  --help  Show this message and exit.

C:\Program Files\GDAL>mapcreator clear_osm_files --help
Usage: mapcreator clear_osm_files [OPTIONS]

  Clears open street map files

Options:
  --help  Show this message and exit.
| 'hello' | Says 'Hello world!', very successfully! |
| 'hello --help' | Usage: mapcreator hello [OPTIONS]

  Says 'Hello world!', very successfully!

Options:
  --help  Show this message and exit.
| 'init' | Initializes the project. |
| 'init --help' | Usage: mapcreator init [OPTIONS]

  Initializes the project.  A project is also automatically initialized by
  any command that needs persistence, so calling init is just a more verbose
  way to do it.

Options:
  -f, --force  Force initialization, even if project already exists
  --help       Show this message and exit.
| 'reset' | Clears the current project. |
| 'reset --help' | Usage: mapcreator reset [OPTIONS]

  Clears the current project.

Options:
  --help  Show this message and exit.
| 'set_height_resolution' | Specifies the height data output resolution... |
| 'set_height_resolution --help' | Usage: mapcreator set_height_resolution [OPTIONS] RESOLUTION

  Specifies the height data output resolution in meters as a float value.
  Default value is 10.0 m. Values in the range 1-1000 are valid.

  Usage example: mapcreator set_height_resolution 2

Options:
  --help  Show this message and exit.
| 'set_height_system' | Specifies a forced coordinate system for... |
| 'set_height_system --help' | Usage: mapcreator set_height_system [OPTIONS] EPSG_CODE

  Specifies a forced coordinate system for source height data as an EPSG
  code. The EPSG-code must be inserted as an integer.

  Usage example: mapcreator set_height_system 4269

Options:
  --help  Show this message and exit.
| 'set_satellite_resolution' | Specifies the satellite/aerial data output... |
| 'set_satelliet_resolution --help' | Usage: mapcreator set_satellite_resolution [OPTIONS] RESOLUTION

  Specifies the satellite/aerial data output resolution in meters as a float
  value. Default value is 10.0 m. Values in the range 0.1-1000 are valid.

  Usage example: mapcreator set_satellite_resolution 1

Options:
  --help  Show this message and exit.
| 'set_satellite_system' | Specifies a forced coordinate system for... |
| 'set_satellite_system --help' | Usage: mapcreator set_satellite_system [OPTIONS] EPSG_CODE

  Specifies a forced coordinate system for source satellite or aerial image
  data as an EPSG code. The EPSG-code must be inserted as an integer.

  Usage example: mapcreator set_satellite_system 26912

Options:
  --help  Show this message and exit.
| 'set_window' | Specifies projection subwindow. |
| 'set_window --help' | Usage: mapcreator set_window [OPTIONS] ULX ULY LRX LRY

  Specifies projection subwindow.  Uses upper left (ulx, uly) and lower
  right (lrx, lry) corners.

  If any of the coordinates is negative, you'll need to separate the
  arguments from the command with a double dash; for example

  mapcreator set_window -- 110.3 -12.1 110.5 -13.2

Options:
  --help  Show this message and exit.
| 'show_area_colors' | Lists area colors. |
| 'show_area_colors --help' | Usage: mapcreator show_area_colors [OPTIONS]

  Lists area colors.

Options:
  -t, --technical  Outputs colors in less readable format that can be used to
                   input colors
  --help           Show this message and exit.
| 'status' | Shows the status of the current project |
| 'status --help' | Usage: mapcreator status [OPTIONS]

  Shows the status of the current project

Options:
  --help  Show this message and exit.
|



## Sample command sequence
Place the altitude source files (e.g. n37w113.img), Open Street Map XML files (e.g. Sampletrails.xml) and satellite/aerial images (e.g. m_3611264_se_12_1_20150603.tif) in a folder.
In the folder, input:
```
mapcreator init
mapcreator add_height_files n37w113.img
mapcreator add_osm_files Sampletrails.xml
mapcreator add_satellite_files m_3611264_se_12_1_20150603.tif
mapcreator set_window -- -112.224157 36.201466185186 -112.038971814814 36.016281
mapcreator build
```
The resulting map data is saved in the file 3dmapdata.zip:
* altitude file (heightfile0.bin)
* altitude metadata file (heightfile0.hdr)
* XML file containing trails and terrain types (heightfile0_trails.xml)
* satellite/aerial image file (heightfile0_satellite.png)

## Running the tests
To locally run the automated tests, enter `pytest` in the project's root folder.

## Continuous integration
The project uses Travis as its continous integration platform. Travis automatically builds and tests the master branch.

## Built With
* [Python 3](https://www.python.org/)

## Versioning
Versioning. *Not defined yet.*

## Supported source data formats
Supported altitude model and satellite/aerial image source file formats are the same as those supported by GDAL (http://www.gdal.org/formats_list.html). Mapcreator uses GDAL for processing the input data. Examples of altitude source data formats are ASCII Grid (.asc) and GeoTIFF (.tif). Examples of satellite and aerial image source data formats are JPEG2000 (.jp2) and GeoTIFF (.tif). 

Route, point of interest and landuse data must be in Open Street Map XML-format (usually .xml or .osm). OSM source data can be exported from https://www.openstreetmap.org/.

## Source data licensing
Repository contains source geographic data from the following sources:
- Finnish regions: the [National Land Survey of Finland Topographic Database](https://tiedostopalvelu.maanmittauslaitos.fi/tp/kartta) 1-4/2018 (source data licenced under CC BY 4.0)
- US regions: the U.S. Geological Survey, National Geospatial Program, the [National Map](https://nationalmap.gov/) (source data in the public domain)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
