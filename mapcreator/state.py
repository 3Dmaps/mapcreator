from os import path

# Makeshift enum, as enums were introduced only in 3.4 and are reasonably usable from 3.6 onwards
class FileAddResult:
    SUCCESS = 'SUCCESS'
    ALREADY_ADDED = 'ALREADY_ADDED'
    DOESNT_EXIST = 'DOESNT_EXIST'

class State:

    def __init__(self):
        self.height_files = []
    
    def add_height_file(self, fpath):
        truepath = path.abspath(fpath)
        if not path.exists(truepath):
            return FileAddResult.DOESNT_EXIST
        if truepath in self.height_files:
            return FileAddResult.ALREADY_ADDED
        else:
            self.height_files.append(truepath)
            return FileAddResult.SUCCESS
    
    def set_window(self, ulx, uly, lrx, lry):
        self.window = {
            'ulx': ulx,
            'uly': uly,
            'lrx': lrx,
            'lry': lry,
        }
    
    def get_window_upper_left(self):
        return (self.window['ulx'], self.window['uly'])
    
    def get_window_lower_right(self):
        return (self.window['lrx'], self.window['lry'])

    @staticmethod
    def from_dict(d):
        new_state = State()
        new_state.__dict__ = d
        return new_state
    
    def to_dict(self):
        return self.__dict__
    
    def __str__(self):
        lines = []
        if hasattr(self, 'height_files') and len(self.height_files) > 0:
            lines.append('-Height files:')
            for fpath in self.height_files:
                lines.append('--{}'.format(fpath))
        else:
            lines.append('-No height files added.')
        if hasattr(self, 'window'):
            lines.append('-Window:')
            lines.append('--Upper left corner:  x={0[0]}, y={0[1]}'.format(self.get_window_upper_left()))
            lines.append('--Lower right corner: x={0[0]}, y={0[1]}'.format(self.get_window_lower_right()))
        else:
            lines.append('-No projection window set.')
        return '\n'.join(lines)