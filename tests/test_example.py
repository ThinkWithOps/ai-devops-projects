"""
Simple test file for demo purposes.
This will be discovered by pytest (if it's installed).
"""


def test_example():
    """Simple passing test."""
    assert True


def test_addition():
    """Test basic math."""
    assert 1 + 1 == 2


def test_string():
    """Test string operations."""
    assert "hello".upper() == "HELLO"
