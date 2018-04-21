import mapcreator
from mock import patch
from imp import reload
from mapcreator import cli_util
from mapcreator.state import State, FileAddResult

@patch('mapcreator.cli_util.echoes')
class TestCliUtil:

    def x_or_error_shows_error(self, function, mock_persistence_func, mock_echoes, call_contents):
        assert not function()
        mock_persistence_func.assert_called_once()
        mock_error = mock_echoes.error
        mock_error.assert_called()
        total_output = ''
        for call in mock_error.call_args_list:
            args, kwargs = call
            assert 0 == len(kwargs)
            assert 1 == len(args)
            total_output += ' ' + args[0] 
        for piece in call_contents:
            assert piece in total_output
    
    def x_or_error_no_error(self, function, mock_persistence_func, mock_echoes, return_value):
        assert function() == return_value
        mock_persistence_func.assert_called_once()
        mock_error = mock_echoes.error
        mock_error.assert_not_called()

    @patch('mapcreator.persistence.init_state', side_effect=OSError('Whoops!'))
    def test_init_or_error_shows_error_when_unsuccessful(self, mock_init, mock_echoes):
        self.x_or_error_shows_error(
            cli_util.init_or_error, 
            mock_init, 
            mock_echoes,
            ['Unable to initialize project', str(OSError('Whoops!'))]
            )
    
    @patch('mapcreator.persistence.init_state', return_value = 'Success :-)')
    def test_init_or_error_doesnt_show_error_when_successful(self, mock_init, mock_echoes):
        self.x_or_error_no_error(cli_util.init_or_error, mock_init, mock_echoes, 'Success :-)')

    @patch('mapcreator.persistence.load_state', side_effect=OSError('Whoops!'))
    def test_load_or_error_shows_error_when_unsuccessful(self, mock_load, mock_echoes):
        self.x_or_error_shows_error(
            cli_util.load_or_error, 
            mock_load, 
            mock_echoes,
            ['Unable to load or initialize the project', str(OSError('Whoops!'))]
            )
    
    @patch('mapcreator.persistence.load_state', return_value = 'Success :-)')
    def test_load_or_error_doesnt_show_error_when_successful(self, mock_load, mock_echoes):
        self.x_or_error_no_error(cli_util.load_or_error, mock_load, mock_echoes, 'Success :-)')
    
    @patch('mapcreator.persistence.save_state', side_effect=OSError('Whoops!'))
    def test_save_or_error_shows_error_when_unsuccessful(self, mock_save, mock_echoes):
        self.x_or_error_shows_error(
            lambda: cli_util.save_or_error('asd'), 
            mock_save, 
            mock_echoes,
            ['Unable to save changes', 'No changes done', 'What went wrong', str(OSError('Whoops!'))]
            )
    
    @patch('mapcreator.persistence.save_state', return_value = True)
    def test_save_or_error_doesnt_show_error_when_successful(self, mock_save, mock_echoes):
        self.x_or_error_no_error(lambda: cli_util.save_or_error('Success :-)'), mock_save, mock_echoes, 'Success :-)')

    @patch('mapcreator.persistence.clear_state', side_effect=OSError('Whoops!'))
    def test_clear_or_error_shows_error_when_unsuccessful(self, mock_clear, mock_echoes):
        self.x_or_error_shows_error(
            cli_util.clear_or_error, 
            mock_clear, 
            mock_echoes,
            ['Unable to reset project', str(OSError('Whoops!'))]
            )
    
    @patch('mapcreator.persistence.clear_state', return_value = True)
    def test_clear_or_error_doesnt_show_error_when_successful(self, mock_clear, mock_echoes):
        self.x_or_error_no_error(cli_util.clear_or_error, mock_clear, mock_echoes, True)
    
    @patch('mapcreator.building.init_build', side_effect=OSError('Whoops!'))
    def test_build_init_or_error_shows_error_when_unsuccessful(self, mock_init, mock_echoes):
        self.x_or_error_shows_error(
            cli_util.build_init_or_error,
            mock_init,
            mock_echoes,
            ['Unable to initialize build', str(OSError('Whoops!'))]
        )
    
    @patch('mapcreator.building.init_build')
    def test_build_init_or_error_doesnt_show_error_when_successful(self, mock_init, mock_echoes):
        self.x_or_error_no_error(cli_util.build_init_or_error, mock_init, mock_echoes, True)

    @patch('mapcreator.building.cleanup', side_effect=OSError('Whoops!'))
    def test_build_clean_or_error_shows_error_when_unsuccessful(self, mock_clean, mock_echoes):
        self.x_or_error_shows_error(
            cli_util.build_clean_or_error,
            mock_clean,
            mock_echoes,
            ['Unable to clean', str(OSError('Whoops!'))]
        )
    
    @patch('mapcreator.building.cleanup')
    def test_build_clean_or_error_doesnt_show_error_when_successful(self, mock_clean, mock_echoes):
        self.x_or_error_no_error(cli_util.build_clean_or_error, mock_clean, mock_echoes, True)

    @patch('mapcreator.persistence.load_state', lambda: State())
    @patch.object(mapcreator.state.State, 'add_height_file')
    @patch('mapcreator.persistence.save_state', side_effect = lambda state: state) #Returns state, so save was successful
    def test_add_files(self, mock_save, mock_state, mock_echoes):
        mock_state.return_value = FileAddResult.SUCCESS
        cli_util.add_files(('test1.txt', 'test2.txt'), 'add_height_file')
        mock_state.assert_any_call('test1.txt')
        mock_state.assert_any_call('test2.txt')
        assert mock_state.call_count == 2
        assert mock_save.call_count == 1
        mock_echoes.success.assert_called()

    @patch('mapcreator.persistence.load_state', lambda: State())
    @patch.object(mapcreator.state.State, 'add_osm_file')
    @patch('mapcreator.persistence.save_state')
    def test_add_files_no_files_exist(self, mock_save, mock_state, mock_echoes):
        mock_state.return_value = FileAddResult.DOESNT_EXIST
        cli_util.add_files(('test1.txt','test2.txt','test3.txt'), 'add_osm_file')
        mock_state.assert_any_call('test1.txt')
        mock_state.assert_any_call('test2.txt')
        mock_state.assert_any_call('test3.txt')
        assert mock_state.call_count == 3
        assert mock_save.call_count == 0 # Don't save if there's no changes
        for i in range(1,3):
            mock_echoes.error.assert_any_call('File "test{}.txt" doesn\'t exist!'.format(i))

    @patch('mapcreator.persistence.load_state', lambda: State())
    @patch.object(mapcreator.state.State, 'add_height_file')
    @patch('mapcreator.persistence.save_state')
    def test_add_files_all_already_added(self, mock_save, mock_state, mock_echoes):
        mock_state.return_value = FileAddResult.ALREADY_ADDED
        cli_util.add_files(('test3.txt',), 'add_height_file')
        mock_state.assert_called_once_with('test3.txt')
        assert mock_save.call_count == 0
        mock_echoes.warn.assert_any_call('test3.txt has already been added to this project')

    @patch('mapcreator.persistence.load_state', lambda: State())
    @patch.object(mapcreator.state.State, 'add_osm_file')
    @patch('mapcreator.persistence.save_state')
    def test_add_files_some_files_ok(self, mock_save, mock_state, mock_echoes):
        def add_side_effect(filename):
            if filename in ('1', '11', '21'):
                return FileAddResult.SUCCESS
            else:
                return (FileAddResult.ALREADY_ADDED, FileAddResult.DOESNT_EXIST)[int(filename) % 2]
        mock_state.side_effect = add_side_effect
        files = [str(i) for i in range(25)]
        cli_util.add_files(files, 'add_osm_file')
        assert mock_state.call_count == len(files)
        assert mock_save.call_count == 1
        mock_echoes.warn.assert_called_with('3 files (out of 25) added to the project successfully')
    
    def test_parse_color_wrong_number_of_args(self, mock_echoes):
        mock_error = mock_echoes.error
        assert not cli_util.parse_color("tag 123 221 9 77")
        mock_error.assert_called()
    
    def test_parse_color_invalid_number_format(self, mock_echoes):
        mock_error = mock_echoes.error
        assert not cli_util.parse_color("terrain 7 8 cheese")
        mock_error.assert_called()
    
    def test_parse_color(self, mock_echoes):
        mock_error = mock_echoes.error
        assert ["hello", 7, 88, 3] == cli_util.parse_color("hello 7 88 3")
        mock_error.assert_not_called()
    
    def test_validate_color_inivalid_color(self, mock_echoes):
        mock_error = mock_echoes.error
        assert not cli_util.validate_color(-11, 255, 13)
        mock_error.assert_called()
        mock_error.reset_mock()
        assert not cli_util.validate_color(0, 256, 13)
        mock_error.assert_called()
        mock_error.reset_mock()
        assert not cli_util.validate_color(6, 7, 999)
        mock_error.assert_called()
    
    def test_validate_color_valid_color(self, mock_echoes):
        mock_error = mock_echoes.error
        assert cli_util.validate_color(0, 255, 127)
        assert cli_util.validate_color(255, 44, 0)
        assert cli_util.validate_color(31, 0, 255)
        assert cli_util.validate_color(123, 221, 99)
        mock_error.assert_not_called()
    
    def test_validate_resolution_valid_reso(self, mock_echoes):
        mock_error = mock_echoes.error
        assert cli_util.validate_resolution(1, 0.5, 1000)
        assert cli_util.validate_resolution(0.05, 0.01, 0.05)
        assert cli_util.validate_resolution(700, 300, 800)
        mock_error.assert_not_called()
    
    def test_validate_resolution_invalid_reso(self, mock_echoes):
        mock_error = mock_echoes.error
        assert not cli_util.validate_resolution(1, 2, 1000)
        mock_error.assert_called()
        mock_error.reset_mock()
        assert not cli_util.validate_resolution(1000, 50, 999)
        mock_error.assert_called()
        mock_error.reset_mock()
        assert not cli_util.validate_resolution(0.05, 0.1, 0.5)
        mock_error.assert_called()
        
        
    