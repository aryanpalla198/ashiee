"""
String Helpers Utility Module
Provides production-grade string transformation utilities: slugify, title_case, and truncate_words.
"""
import re
from typing import List

def slugify(text: str) -> str:
    """Converts a string into a clean, URL-friendly slug."""
    text = text.strip().lower()
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Remove leading and trailing hyphens
    text = re.sub(r'^-+|-+$', '', text)
    return text

def title_case(text: str) -> str:
    """Capitalizes the first letter of each word in a string, preserving minor words where appropriate."""
    minor_words = {'and', 'or', 'the', 'in', 'on', 'at', 'to', 'for', 'a', 'an', 'of'}
    words = text.strip().split()
    if not words:
        return ""
    result = []
    for i, word in enumerate(words):
        w_lower = word.lower()
        if i == 0 or i == len(words) - 1 or w_lower not in minor_words:
            result.append(word.capitalize())
        else:
            result.append(w_lower)
    return " ".join(result)

def truncate_words(text: str, num_words: int, suffix: str = "...") -> str:
    """Truncates text after a given number of words and appends a suffix."""
    words = text.strip().split()
    if len(words) <= num_words:
        return text.strip()
    return " ".join(words[:num_words]) + suffix

if __name__ == "__main__":
    print("=== String Helpers Demonstration ===")
    sample_text = "Hello World! This is an Advanced Antigravity 2026 Tutorial"
    print(f"Original:        '{sample_text}'")
    print(f"Slugified:       '{slugify(sample_text)}'")
    print(f"Title Cased:     '{title_case('the quick brown fox jumps over the lazy dog')}'")
    print(f"Truncated (4w):  '{truncate_words(sample_text, 4)}'")
    print("All string helper functions executed cleanly!")
