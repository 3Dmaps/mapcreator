import os
import shutil
from mapcreator.osm import OSMData, areaFilter, WayCoordinateFilter, trailFilter, OSMMerger
from mapcreator.building import OSMStatus
from os import path, mkdir
from util import get_resource_path, assert_xml_equal

CLEAN_TEMP_DIR = False
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
    data.do_filter()
    data.prepare_for_save()
    data.save(result_path)
    assert_xml_equal(get_resource_path('test_osm_expected.xml'), result_path)

def test_osm_terrainfilter():
    data = OSMData.load(get_resource_path('test_osm_terrains_input.xml'))
    data.add_way_filter(areaFilter)
    
    result_path = path.join(TEMP_DIR, 'test_osm_terrains_result.xml')
    data.do_filter()
    data.prepare_for_save()
    data.save(result_path)
    assert_xml_equal(get_resource_path('test_osm_terrains_expected.xml'), result_path)

def test_way_coordinate_filter():
    wcf = WayCoordinateFilter(-112.060, -112.000, 36.050, 36.109)
    data = OSMData.load(get_resource_path('test_osm_input.xml'))
    data.add_way_filter(wcf.filter)
    result_path = path.join(TEMP_DIR, 'test_osm_result.xml')
    data.do_filter()
    data.prepare_for_save()
    data.save(result_path)
    assert_xml_equal(get_resource_path('test_osm_expected_way_coord_filter.xml'), result_path)

def test_osm_trailfilter():
    data = OSMData.load(get_resource_path('test_osm_trails_input.xml'))
    data.add_way_filter(trailFilter)
    
    result_path = path.join(TEMP_DIR, 'test_osm_trails_result.xml')
    data.do_filter()
    data.prepare_for_save()
    data.save(result_path)
    assert_xml_equal(get_resource_path('test_osm_trails_expected.xml'), result_path)

def test_osm_trailfilter_with_coordinates():
    wcf = WayCoordinateFilter(-113.0, -112.0, 36.0, 37.0)
    data = OSMData.load(get_resource_path('test_osm_trails_input.xml'))
    data.add_way_filter(trailFilter, wcf.filter)
    
    result_path = path.join(TEMP_DIR, 'test_osm_trails_and_coordinates_result.xml')
    data.do_filter()
    data.prepare_for_save()
    data.save(result_path)
    assert_xml_equal(get_resource_path('test_osm_trails_and_coordinates_expected.xml'), result_path)

def test_osm_merger():
    trails = OSMData.load(get_resource_path('test_osm_trails_input.xml'))
    terrains = OSMData.load(get_resource_path('test_osm_terrains_input.xml'))
    combined = OSMMerger().merge([trails, terrains])
    result_path = path.join(TEMP_DIR, 'test_osm_combined_result.xml')
    combined.tree.write(result_path, encoding='utf-8', xml_declaration=True)
    assert_xml_equal(get_resource_path('test_osm_combined_result.xml'), result_path)
    
def teardown_function(function):
    if CLEAN_TEMP_DIR and path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    

