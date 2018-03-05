from mock import patch
from imp import reload
from mapcreator import cli_util

@patch('mapcreator.echoes.error')
class TestCliUtil:

    def x_or_error_shows_error(self, function, mock_persistence_func, mock_error, call_contents):
        assert not function()
        mock_persistence_func.assert_called_once()
        mock_error.assert_called()
        total_output = ''
        for call in mock_error.call_args_list:
            args, kwargs = call
            assert 0 == len(kwargs)
            assert 1 == len(args)
            total_output += ' ' + args[0] 
        for piece in call_contents:
            assert piece in total_output
    
    def x_or_error_no_error(self, function, mock_persistence_func, mock_error, return_value):
        assert function() == return_value
        mock_persistence_func.assert_called_once()
        mock_error.assert_not_called()

    @patch('mapcreator.persistence.init_state', side_effect=OSError('Whoops!'))
    def test_init_or_error_shows_error_when_unsuccessful(self, mock_init, mock_error):
        self.x_or_error_shows_error(
            cli_util.init_or_error, 
            mock_init, 
            mock_error,
            ['Unable to initialize project', str(OSError('Whoops!'))]
            )
    
    @patch('mapcreator.persistence.init_state', return_value = 'Success :-)')
    def test_init_or_error_doesnt_show_error_when_successful(self, mock_init, mock_error):
        self.x_or_error_no_error(cli_util.init_or_error, mock_init, mock_error, 'Success :-)')

    @patch('mapcreator.persistence.load_state', side_effect=OSError('Whoops!'))
    def test_load_or_error_shows_error_when_unsuccessful(self, mock_load, mock_error):
        self.x_or_error_shows_error(
            cli_util.load_or_error, 
            mock_load, 
            mock_error,
            ['Unable to load or initialize the project', str(OSError('Whoops!'))]
            )
    
    @patch('mapcreator.persistence.load_state', return_value = 'Success :-)')
    def test_load_or_error_doesnt_show_error_when_successful(self, mock_load, mock_error):
        self.x_or_error_no_error(cli_util.load_or_error, mock_load, mock_error, 'Success :-)')
    
    @patch('mapcreator.persistence.save_state', side_effect=OSError('Whoops!'))
    def test_save_or_error_shows_error_when_unsuccessful(self, mock_save, mock_error):
        self.x_or_error_shows_error(
            lambda: cli_util.save_or_error('asd'), 
            mock_save, 
            mock_error,
            ['Unable to save changes', 'No changes done', 'What went wrong', str(OSError('Whoops!'))]
            )
    
    @patch('mapcreator.persistence.save_state', return_value = True)
    def test_save_or_error_doesnt_show_error_when_successful(self, mock_save, mock_error):
        self.x_or_error_no_error(lambda: cli_util.save_or_error('Success :-)'), mock_save, mock_error, 'Success :-)')

    @patch('mapcreator.persistence.clear_state', side_effect=OSError('Whoops!'))
    def test_clear_or_error_shows_error_when_unsuccessful(self, mock_clear, mock_error):
        self.x_or_error_shows_error(
            cli_util.clear_or_error, 
            mock_clear, 
            mock_error,
            ['Unable to reset project', str(OSError('Whoops!'))]
            )
    
    @patch('mapcreator.persistence.clear_state', return_value = True)
    def test_clear_or_error_doesnt_show_error_when_successful(self, mock_clear, mock_error):
        self.x_or_error_no_error(cli_util.clear_or_error, mock_clear, mock_error, True)


    
    