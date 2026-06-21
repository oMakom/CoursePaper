from unittest.mock import patch, mock_open

from src.views import read_datafile


@patch("builtins.open", side_effect=FileNotFoundError)
def test_read_exls_file_not_found(mock_open):
    """Тест обработки ошибки отсутствия файла."""
    result = read_datafile("nonexistent.exls")
    # вернула пустой список
    assert result == []
    # попытка открыть файл была
    assert mock_open.called


@patch("builtins.open", mock_open(read_data="некорректный exls {]"))
def test_exls_decode_error():
    """Тест обработки некорректного xlsx."""
    result = read_datafile("test_invalid.exls")
    assert result == []
