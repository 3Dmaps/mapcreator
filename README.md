# mapcreator
Map creator tool for 3Dmaps application

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
mapcreator \[command] --help

## Sample command sequence
Place the altitude source files (e.g. n37w113.img) and Open Street Map XML files (e.g. Sampletrails.xml) in a folder.
In the folder, input:
```
mapcreator init
mapcreator add_height_files n37w113.img
mapcreator add_osm_files Sampletrails.xml
mapcreator set_window -- -112.224157 36.201466185186 -112.038971814814 36.016281
mapcreator build
```
The resulting map data is saved in the file 3dmapdata.zip:
* altitude file (heightfile0.bin)
* altitude metadata file (heightfile0.hdr)
* XML file containing trails and terrain types (heightfile0_osm.xml)
