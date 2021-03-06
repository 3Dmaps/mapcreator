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

### List of commands

| Command                      | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `add_area_color`   |  Adds one area color for OSM data.                                                                                                                                                                                                                                                                                                                               |
| `add_area_colors`        | Adds multiple area colors for OSM data.                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `add_height_files`        | Adds given height data files to the project                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `add_osm_files`        | Adds open street map files to the project                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `add_satellite_files`        | Adds given satellite image files to the...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `build`        | Builds the project.                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `clean_temp_files`        | Cleans up temporary build files                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `clear_area_colors`        | Clears are colors.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `clear_height_files`        | Clears height files.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `clear_height_system`        | Clears the set forced coordinate system for...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `clear_osm_files`        | Clears open street map files                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `clear_satellite_files`        | Clears satellite/aerial image files                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `clear_satellite_system`        | Clears the set forced coordinate system for...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `hello`        | Says 'Hello world!', very successfully!                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `init`        | Initializes the project.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `set_height_resolution`        | Specifies the height data output resolution...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `set_height_system`        | Specifies a forced coordinate system for...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `set_satellite_resolution`        | Specifies the satellite/aerial data output...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `set_satellite_system`        |  Specifies a forced coordinate system for...                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `set_window`        | Specifies projection subwindow.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `show_area_colors`        | Lists area colors.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `status`        | Shows the status of the current project                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

## Supported source data formats
Supported altitude model and satellite/aerial image source file formats are the same as those supported by GDAL (http://www.gdal.org/formats_list.html). Mapcreator uses GDAL for processing the input data. Examples of altitude source data formats are ASCII Grid (.asc) and GeoTIFF (.tif). Examples of satellite and aerial image source data formats are JPEG2000 (.jp2) and GeoTIFF (.tif). 

Route, point of interest and landuse data must be in Open Street Map XML-format (usually .xml or .osm). OSM source data can be exported from https://www.openstreetmap.org/.

## Running the tests
To locally run the automated tests, enter `pytest` in the project's root folder.

## Continuous integration
The project uses Travis as its continous integration platform. Travis automatically builds and tests the master branch.

## Built With
* [Python 3](https://www.python.org/)
* [Click](http://click.pocoo.org/5/)

## Source data licensing
Repository contains source geographic data from the following sources:
- Finnish regions: the [National Land Survey of Finland Topographic Database](https://tiedostopalvelu.maanmittauslaitos.fi/tp/kartta) 1-4/2018 (source data licenced under CC BY 4.0)
- US regions: the U.S. Geological Survey, National Geospatial Program, the [National Map](https://nationalmap.gov/) (source data in the public domain)

## Versioning
Version 1.0: Released May 2nd 2018.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
