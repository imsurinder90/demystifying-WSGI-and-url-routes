"""
utils.py: Utility functions
References: https://werkzeug.palletsprojects.com/en/1.0.x/
"""
from urllib import parse

def is_valid_url(url):
    parts = parse.urlparse(url)
    return parts.scheme in ('http', 'https')

def base36_encode(number):
    assert number >= 0, 'positive integer required'
    if number == 0:
        return '0'
    base36 = []
    while number != 0:
        number, i = divmod(number, 36)
        base36.append('0123456789abcdefghijklmnopqrstuvwxyz'[i])
    return ''.join(reversed(base36))