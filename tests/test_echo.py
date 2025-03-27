from src.bot.echo import concat_new


def test_concat_new_with_simple_text():
    """Tests adding ' new' to a simple text."""
    message = "Hello"
    result = concat_new(message)
    assert result == "Hello new"


def test_concat_new_with_empty_string():
    """Tests adding ' new' to an empty string."""
    message = ""
    result = concat_new(message)
    assert result == " new"


def test_concat_new_with_whitespace():
    """Tests adding ' new' to a string with whitespace."""
    message = "Hello world"
    result = concat_new(message)
    assert result == "Hello world new"


def test_concat_new_with_special_chars():
    """Tests adding ' new' to a string with special characters."""
    message = "Hello! @#$%^&*()"
    result = concat_new(message)
    assert result == "Hello! @#$%^&*() new"
