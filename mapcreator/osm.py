from xml.etree import ElementTree


class OSMData:

    TAG_ROOT = 'osm'
    TAG_NODE = 'node'
    TAG_WAY = 'way'
    TAG_WAY_NODE = 'nd'
    ATTRIB_ID = 'id'
    ATTRIB_REF = 'ref'

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

    def and_filter_ways(self, *filters):
        OSMData.and_filter(self.included_ways, self.ways, *filters)

    def or_filter_ways(self, *filters):
        OSMData.or_filter(self.included_ways, self.ways, *filters)

    def and_filter_nodes(self, *filters):
        OSMData.and_filter(self.included_nodes, self.nodes, *filters)

    def or_filter_nodes(self, *filters):
        OSMData.or_filter(self.included_nodes, self.nodes, *filters)

    @classmethod
    def and_filter(cls, idset, elemdict, *filters):
        for elemid in idset:
            elem = elemdict[elemid]
            for f in filters:
                if not f(elem):
                    idset.remove(elemid)
                    break

    @classmethod
    def or_filter(cls, idset, elemdict, *filters):
        for elemid in idset:
            elem = elemdict[elemid]
            ok = False
            for f in filters:
                if f(elem):
                    ok = True
                    break
            if not ok:
                idset.remove(elemid)

    def prepare_for_save(self):
        for way in self.ways.values():
            wayid = OSMData.get_elem_id(way)
            if wayid not in self.included_ways:
                way.remove()
            else:
                for child in way:
                    if child.tag == OSMData.TAG_WAY_NODE:
                        self.included_nodes.add(int(child.get(OSMData.ATTRIB_REF)))
        for node in self.nodes.values():
            nodeid = OSMData.get_elem_id(node)
            if nodeid not in self.included_nodes:
                node.remove()

    def save(self, path):
        self.prepare_for_save()
        self.tree.write(path)