from xml.etree import ElementTree

class OSMData:

    TAG_ROOT = 'osm'
    TAG_NODE = 'node'
    TAG_WAY = 'way'
    TAG_WAY_NODE = 'nd'
    TAG_TAG = 'tag'
    ATTRIB_ID = 'id'
    ATTRIB_REF = 'ref'
    ATTRIB_KEY = 'k'
    ATTRIB_VALUE = 'v'
    ATTRIB_LAT = 'lat'
    ATTRIB_LON = 'lon'
    KEY_LANDUSE = 'landuse'
    ACCEPTED_LANDUSES = ['meadow']

    def __init__(self):
        self.node_filters = []
        self.way_filters = []

    @classmethod
    def load(cls, path):
        data = OSMData()
        data.tree = ElementTree.parse(path)
        data.preprocess()
        return data

    @classmethod
    def get_elem_id(cls, elem):
        return int(elem.get(OSMData.ATTRIB_ID))

    def preprocess(self):
        self.nodes = {}
        self.included_nodes = set()
        self.ways = {}
        self.included_ways = set()
        root = self.tree.getroot()
        if root.tag != OSMData.TAG_ROOT:
            raise ValueError('Invalid OSM XML Data - the root node\'s tag was not "osm"!')
        for child in root:
            if child.tag == OSMData.TAG_NODE:
                nodeid = OSMData.get_elem_id(child)
                self.nodes[nodeid] = child
                self.included_nodes.add(nodeid)
            elif child.tag == OSMData.TAG_WAY:
                wayid = OSMData.get_elem_id(child)
                self.ways[wayid] = child
                self.included_ways.add(wayid)

    def add_node_filter(self, *filters):
        """
        Adds filters. 
        Filters are functions that take a ElementTree element and this OSMData instance
        as arguments and returns a truthful value if said element should be
        kept.
        Filters given in the same method call are joined with "and",
        while filters given in subsequent calls are joined with "or".
        For example

        data = OSMData()
        data.add_node_filter(f1, f2, f3)
        data.add_node_filter(f4)

        will result in elements for which
        
        (f1(element) and f2(element) and f3(element)) or f4(element)

        is False getting filtered out and elements for which that is True being kept
        """
        OSMData.add_filter(self.node_filters, *filters)
    
    def add_way_filter(self, *filters):
        """
        Adds filters.
        Filters are functions that take a ElementTree element and this OSMData instance
        as arguments and returns a truthful value if said element should be
        kept.
        Filters given in the same method call are joined with "and",
        while filters given in subsequent calls are joined with "or".
        For example

        data = OSMData()
        data.add_way_filter(f1, f2, f3)
        data.add_way_filter(f4)

        will result in elements for which
        
        (f1(element) and f2(element) and f3(element)) or f4(element)

        is False getting filtered out and elements for which that is True being kept
        """
        OSMData.add_filter(self.way_filters, *filters)
    
    @classmethod
    def add_filter(cls, filterlist, *filters):
        filterlist.append(filters)

    def do_filter(self):
        self.filter(self.included_nodes, self.nodes, self.node_filters)
        self.filter(self.included_ways, self.ways, self.way_filters)

    def filter(self, idset, elemdict, filterlist):
        filterset = set()
        for elemid in idset:
            elem = elemdict[elemid]
            ok = False
            for filt in filterlist:
                current_ok = True
                for f in filt:
                    if not f(elem, self):
                        current_ok = False
                        break
                if current_ok:
                    ok = True
                    break
            if not ok:
                filterset.add(elemid)
        idset -= filterset


    def prepare_for_save(self):
        root = self.tree.getroot()
        for way in self.ways.values():
            wayid = OSMData.get_elem_id(way)
            # Remove dropped ways
            if wayid not in self.included_ways:
                root.remove(way)
            else:
                for child in way:
                    # Add nodes that belong to the way even if they were dropped by some other filter
                    if child.tag == OSMData.TAG_WAY_NODE:
                        self.included_nodes.add(int(child.get(OSMData.ATTRIB_REF)))
        for node in self.nodes.values():
            nodeid = OSMData.get_elem_id(node)
            # Remove dropped nodes
            if nodeid not in self.included_nodes:
                root.remove(node)

    def save(self, path):
        self.do_filter()
        self.prepare_for_save()
        self.tree.write(path, encoding='utf-8', xml_declaration=True)
    
def areaFilter(elem, osmdata):
    """
    Currently filters in only areas with "landuse" in the accepted landuses list.
    """
    for tagElement in elem.findall(OSMData.TAG_TAG):
        # Check landuses
        if tagElement.get(OSMData.ATTRIB_KEY) == OSMData.KEY_LANDUSE and tagElement.get(OSMData.ATTRIB_VALUE) in OSMData.ACCEPTED_LANDUSES:
            return True
    return False

class WayCoordinateFilter:
    def __init__(self, minx, maxx, miny, maxy):
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
    def filter(self, elem, osmdata):
        for ref in elem.iter(OSMData.TAG_WAY_NODE):
            try:
                node = osmdata.nodes[int(ref.get(OSMData.ATTRIB_REF))]
                x = float(node.get(OSMData.ATTRIB_LON))
                y = float(node.get(OSMData.ATTRIB_LAT))
            except ValueError:
                continue # Just skip any dirty data
            if self.minx <= x and x <= self.maxx and self.miny <= y and y <= self.maxy:
                return True
        return False
