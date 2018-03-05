from mapcreator import echoes

def test_format_echo_with_identifier():
    identifier = 'TEST'
    message = 'Success?'
    result = echoes.format_echo(identifier, message)
    assert result == (echoes.IDENTIFIER_SIZE - len(identifier)) * ' ' + identifier + ': ' + message

def test_format_echo_without_identifier():
    message = 'Success?'
    result = echoes.format_echo('', message)
    assert result == (echoes.IDENTIFIER_SIZE + 1) * ' ' + ' ' + message
