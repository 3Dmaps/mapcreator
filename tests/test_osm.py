import os
import shutil
from mapcreator.osm import OSMData
from os import path, mkdir
from util import get_resource_path, assert_xml_equal

TEMP_DIR = '.test_osm'

def setup_function(function):
    if not path.exists(TEMP_DIR):
        mkdir(TEMP_DIR)

def test_osmdata():
    def node_filter_a(element, data):
        return element.get('user') == 'zmeu'
    def node_filter_b(element, data):
        for tag in element:
            if tag.get('k') == 'zmeuicon':
                return True
        return False
    def way_filter_a(element, data):
        for tag in element.iter('tag'):
            if tag.get('k') == 'zmeucolor' and tag.get('v') == 'yellow':
                return True
        return False
    def way_filter_b(element, data):
        for tag in element.iter('tag'):
            if tag.get('k') == 'highway' and tag.get('v') == 'footway':
                return True
        return False
    def way_filter_c(element, data):
        for tag in element.iter('tag'):
            if tag.get('k') == 'EXPORT_ROUTE' and tag.get('v') == 'true':
                return True
        return False
    data = OSMData.load(get_resource_path('test_osm_input.xml'))
    data.add_node_filter(node_filter_a) #Node filter a
    data.add_node_filter(node_filter_b) #Or node filter b
    data.add_way_filter(way_filter_a, way_filter_b) #Way filter a and way filter b
    data.add_way_filter(way_filter_c) #Or way filter c
    result_path = path.join(TEMP_DIR, 'test_osm_result.xml')
    data.save(result_path)
    assert_xml_equal(get_resource_path('test_osm_expected.xml'), result_path)

def teardown_function(function):
    if path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)