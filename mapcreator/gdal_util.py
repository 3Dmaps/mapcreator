import json
import subprocess

class Gdalinfo:
    @classmethod
    def for_file(cls, path):
        with subprocess.Popen(['gdalinfo', '-json', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            stdout, stderr = process.communicate()
            gdal_info_dict = json.loads(stdout.decode('utf-8'))
            gdal_info = Gdalinfo()
            gdal_info_coordinates = gdal_info_dict['wgs84Extent']['coordinates'][0]
            minX = gdal_info_coordinates[0][0]
            minY = gdal_info_coordinates[0][1]
            maxX = gdal_info_coordinates[0][0]
            maxY = gdal_info_coordinates[0][1]
            for coord in gdal_info_coordinates:
                minX = min(minX, coord[0])
                maxX = max(maxX, coord[0])
                minY = min(minY, coord[1])
                maxY = max(maxY, coord[1])
            
            gdal_info.minX = minX
            gdal_info.minY = minY
            gdal_info.maxX = maxX
            gdal_info.maxY = maxY

            return gdal_info
        

