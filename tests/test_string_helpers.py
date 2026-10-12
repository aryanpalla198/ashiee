import pytest
from string_helpers import slugify, title_case, truncate_words

def test_slugify():
    assert slugify("Hello World!") == "hello-world"
    assert slugify("  Antigravity & Ashiee -- AI  ") == "antigravity-ashiee-ai"
    assert slugify("Test 1234") == "test-1234"
    assert slugify("") == ""

def test_title_case():
    assert title_case("the lord of the rings") == "The Lord of the Rings"
    assert title_case("war and peace") == "War and Peace"
    assert title_case("antigravity AI") == "Antigravity Ai"

def test_truncate_words():
    assert truncate_words("one two three four five", 3) == "one two three..."
    assert truncate_words("short text", 5) == "short text"
    assert truncate_words("one two three", 2, suffix=" [more]") == "one two [more]"
