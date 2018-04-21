from os import path

# Makeshift enum, as enums were introduced only in 3.4 and are reasonably usable from 3.6 onwards
class FileAddResult:
    SUCCESS = 'SUCCESS'
    ALREADY_ADDED = 'ALREADY_ADDED'
    DOESNT_EXIST = 'DOESNT_EXIST'

class State:

    def __init__(self):
        self.height_files = []
        self.osm_files = []
        self.satellite_files = []
        self.area_colors = {}
        self.height_resolution = 10
        self.satellite_resolution = 10
    
    def has_height_files(self):
        return hasattr(self, 'height_files') and len(self.height_files) > 0
    
    def has_osm_files(self):
        return hasattr(self, 'osm_files') and len(self.osm_files) > 0

    def has_satellite_files(self):
        return hasattr(self, 'satellite_files') and len(self.satellite_files) > 0
    
    def add_height_file(self, fpath):
        return State.add_file(fpath, self.height_files)
    
    def add_osm_file(self, fpath):
        return State.add_file(fpath, self.osm_files)
    
    def add_satellite_file(self, fpath):
        return State.add_file(fpath, self.satellite_files)

    @classmethod
    def add_file(cls, fpath, flist):
        truepath = path.abspath(fpath)
        if not path.exists(truepath):
            return FileAddResult.DOESNT_EXIST
        if truepath in flist:
            return FileAddResult.ALREADY_ADDED
        else:
            flist.append(truepath)
            return FileAddResult.SUCCESS
    
    def has_area_colors(self):
        return hasattr(self, 'area_colors') and len(self.area_colors) > 0
    
    def add_area_color(self, tag, r, g, b):
        self.area_colors[tag] = (r, g, b)
    
    def clear_area_colors(self):
        self.area_colors = {}
    
    def has_window(self):
        return hasattr(self, 'window') and len(self.window) > 0

    def set_window(self, ulx, uly, lrx, lry):
        self.window = {
            'ulx': ulx,
            'uly': uly,
            'lrx': lrx,
            'lry': lry,
        }
    
    def get_window_upper_left(self):
        if not self.has_window(): return None
        return (self.window['ulx'], self.window['uly'])
    
    def get_window_lower_right(self):
        if not self.has_window(): return None
        return (self.window['lrx'], self.window['lry'])

    def get_window_string(self):
        if not self.has_window(): return ''
        return '{0[0]} {0[1]} {1[0]} {1[1]}'.format(self.get_window_upper_left(), self.get_window_lower_right())
    
    def get_window_string_lowerleft_topright(self):
        if not self.has_window(): return ''
        return '{0[0]} {1[1]} {1[0]} {0[1]}'.format(self.get_window_upper_left(), self.get_window_lower_right())

    def get_window_string_lowerleft_topright_cut(self, gdal_info):
        if not self.has_window(): return ''
        lowerleftX = max(self.get_window_upper_left()[0], gdal_info.minX)
        lowerleftY = max(self.get_window_lower_right()[1], gdal_info.minY)
        toprightX = min(self.get_window_lower_right()[0], gdal_info.maxX)
        toprightY = min(self.get_window_upper_left()[1], gdal_info.maxY)

        # If a projection window exists after trimming, return it. Otherwise return None.
        if (lowerleftX < toprightX) and (lowerleftY < toprightY):
            return '{} {} {} {}'.format(lowerleftX, lowerleftY, toprightX, toprightY)
        else:
            return None

    def set_height_system(self, height_coordinatesystem):
        self.height_coordinatesystem = height_coordinatesystem
    
    def has_height_system(self):
        return hasattr(self, 'height_coordinatesystem') and len(self.height_coordinatesystem) > 0
    
    def set_satellite_system(self, satellite_coordinatesystem):
        self.satellite_coordinatesystem = satellite_coordinatesystem
    
    def has_satellite_system(self):
        return hasattr(self, 'satellite_coordinatesystem') and len(self.satellite_coordinatesystem) > 0

    def set_height_resolution(self, height_resolution):
        self.height_resolution = height_resolution

    def set_satellite_resolution(self, satellite_resolution):
        self.satellite_resolution = satellite_resolution

    @classmethod
    def from_dict(cls, d):
        new_state = State()
        new_state.__dict__ = d
        return new_state
    
    def to_dict(self):
        return self.__dict__
    
    @classmethod
    def file_list_to_lines(cls, flist):
        lines = []
        for fpath in flist:
            lines.append('--{}'.format(fpath))
        return lines

    def __str__(self):
        lines = []
        if self.has_height_files():
            lines.append('-Height files:')
            lines.extend(State.file_list_to_lines(self.height_files))
        else:
            lines.append('-No height files added')
        if self.has_osm_files():
            lines.append('-Open street map files:')
            lines.extend(State.file_list_to_lines(self.osm_files))
        else:
            lines.append('-No open street map files added')
        if self.has_satellite_files():
            lines.append('-Satellite/aerial files:')
            lines.extend(State.file_list_to_lines(self.satellite_files))
        else:
            lines.append('-No satellite/aerial files added')
        if self.has_window():
            lines.append('-Window:')
            lines.append('--Upper left corner:  x={0[0]}, y={0[1]}'.format(self.get_window_upper_left()))
            lines.append('--Lower right corner: x={0[0]}, y={0[1]}'.format(self.get_window_lower_right()))
        else:
            lines.append('-No projection window set')
        lines.append('-Height file output resolution: {} m'.format(self.height_resolution))
        lines.append('-Satellite/aerial image output resolution: {} m'.format(self.satellite_resolution))
        if self.has_height_system():
            lines.append('-Forced source height file coordinate system: {}'.format(self.height_coordinatesystem))
        if self.has_satellite_system():
            lines.append('-Forced source satellite/aerial file coordinate system: {}'.format(self.satellite_coordinatesystem))        
        if self.has_area_colors():
            if len(self.area_colors) > 5:
                lines.append('-There are {} area colors set'.format(len(self.area_colors)))
            else:
                lines.append('-Area colors:')
                for tag in self.area_colors:
                    lines.append('--Color for {} is {}'.format(tag, self.area_colors[tag]))
        else:
            lines.append('-No area colors set')
        return '\n'.join(lines)
