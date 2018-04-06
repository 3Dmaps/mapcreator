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
    
    def has_window(self):
        return hasattr(self, 'window')

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
            lines.append('-No height files added.')
        if self.has_osm_files():
            lines.append('-Open street map files:')
            lines.extend(State.file_list_to_lines(self.osm_files))
        else:
            lines.append('-No open street map files added.')
        if self.has_satellite_files():
            lines.append('-Satellite files:')
            lines.extend(State.file_list_to_lines(self.satellite_files))
        else:
            lines.append('-No satellite files added.')
        if self.has_window():
            lines.append('-Window:')
            lines.append('--Upper left corner:  x={0[0]}, y={0[1]}'.format(self.get_window_upper_left()))
            lines.append('--Lower right corner: x={0[0]}, y={0[1]}'.format(self.get_window_lower_right()))
        else:
            lines.append('-No projection window set.')
        return '\n'.join(lines)
