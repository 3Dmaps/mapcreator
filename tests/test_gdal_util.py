from util import get_resource_path
from mapcreator import gdal_util
import mock
PRECISION = 0.0001

@mock.patch('subprocess.Popen')
def test_gdal_coordinates(mock_popen):
    f = open(get_resource_path('test_satelliteimg_gdalinfo.txt'), 'rb')
    mock_popen.return_value.__enter__.return_value.communicate.return_value = (f.read(), b'')
    gdal_info = gdal_util.Gdalinfo.for_file(get_resource_path('test_satelliteimage.tif'))
    assert abs(gdal_info.minX - (-112.5047533)) < PRECISION
    assert abs(gdal_info.maxY - (36.0036116)) < PRECISION

    assert abs(gdal_info.maxX - (-112.4328512)) < PRECISION
    assert abs(gdal_info.minY - (35.9338875)) < PRECISION