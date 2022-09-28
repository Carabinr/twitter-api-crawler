import re
from typing import Dict, List

import logging
import requests

logger = logging.getLogger(__name__)

MAX_ENS_DOMAIN_LENGTH = 50  # arbitrary. I don't know the actual length


def get_ens_domains_from_text(text: str) -> List[str]:
    """
    Extract a list of ENS domains from a blob of text.

    Hey, don't look at me like that. This was built using PURE TDD (just go
    look at the test and the attached CSV used as input). Twitter is a
    cesspool of emojis and profile abuse. Everyone is an ascii artist
    these days, and this masterpiece cuts through it like a hot knife
    through butter.

    I tried to make this as explicit as possible, without any regex magic.

    Parameters
        blob: String of text

    Returns
        List of ENS domains
    """
    out: List = []
    text = text.lower()

    if text == '.eth':
        return out

    if '.eth' not in text:
        return out

    text = re.sub('[\n\r]', '', text)
    text = re.sub('[#$/]', ' ', text)

    str_list: List[str] = re.split(' ', text)

    str_list = [_ for _ in str_list if len(_) <= MAX_ENS_DOMAIN_LENGTH]
    str_list = [_ for _ in str_list if '.eth' in _]

    for test_str in str_list:
        test_str = test_str.replace('.eth.', '.eth')
        test_str = re.sub(r'\.{2,}|,|;|\)|\(|\s|^\.', '', test_str)

        if test_str.endswith('.eth'):
            out.append(test_str)

    return list(set(out))


def get_mentions_from_text(text: str) -> List[str]:
    """
    Pull user mentions (@username) from a blob of text.

    Parameters
        text: The target piece of text

    Returns
        A list of mentions
    """
    text = text.lower()
    matches = re.findall(r'(^|[^@\w])@(\w{1,15})', text)
    extracted = [_[1] for _ in matches]
    return list(set(extracted))


def get_hashtags_from_text(text: str) -> List[str]:
    """
    Return a list of hashtags found in a blob of text.

    Parameters
        text: The target blob of text

    Returns
        A list of strings of hashtags
    """
    text = text.lower()

    text = re.sub(r'https?:\S+', '', text)  # remove urls

    # remove punctuation and other non-word type chars
    text = re.sub(r'[^\w\s#_-]', ' ', text)

    # remove newlines
    text = text.replace('\n', ' ')

    text = text.split(' ')

    hashtags = [word.split('#') for word in text if word.startswith('#')]

    flat_list = []
    for sublist in hashtags:
        for _ in sublist:
            if _:  # will remote null and empty vals
                flat_list.append(_)

    return list(set(flat_list))


def sanitize(string: str) -> str:
    """
    Remove illegal characters from strings.

    Parameters
        string: A string that possibly has NULL 0x00 chars

    Returns
        A string stripped of nulls
    """
    return string.replace('\x00', '').replace(r'\u0000', '')


def get_mentions(response: Dict) -> List[str]:
    """
    Given an API response status object.

    Return the mentions as a list of strings or empty list

    Parameters
        response: API User response object

    Returns
        A list of strings or empty list
    """
    mentions = response.get('entities', {}).get('user_mentions', [])
    return [name.get('screen_name') for name in mentions]


def get_hashtags(user: Dict) -> List[str]:
    """
    Extract hashtags from a blob of text.

    Return the hashtags as a list of strings or empty list given a
    Twitter API Response Object

    @param user: API User response object
    @return: List of strings or empty list
    """
    mentions = user.get('entities', {}).get('hashtags', [])
    return [name.get('text') for name in mentions]


def unroll_url(url: str) -> str:
    """
    Follow shortened links to their final endpoint.

    Params:
    url: URL to unroll

    Returns
    unrolled url string

    """
    if url.startswith('http://'):
        url = url.replace('http://', 'https://')

    if not url.startswith('https://t.co/'):
        return url.rstrip('/')

    session = requests.Session()
    try:
        resp = session.head(url, allow_redirects=False)
    except UnicodeDecodeError:
        return url.strip('/')

    if resp.status_code in [301, 302]:
        return resp.next.url.rstrip('/')

    return url.rstrip('/')

def get_urls(user: Dict) -> List[str]:
    """
    Extract urls from a Twitter API user Dict.

    Return the urls as a list of strings or empty list given a
    Twitter API Response Object

    @param user: API User response object
    @param verify_ssl: Verify SSL when making HTTP requests
    @return: List of strings or empty list
    """
    urls = []

    entities = user.get('entities', {})
    url_list = entities.get('url', {}).get('urls', [])
    description_url_list = entities.get('description', {}).get('urls', [])

    for _ in url_list:
        urls.append(_.get('expanded_url', ''))

    for _ in description_url_list:
        urls.append(_.get('expanded_url', ''))

    urls.append(user.get('url', ''))

    unrolled_urls = [unroll_url(url) for url in urls if url]

    # This will remove nulls and empty strings
    cleaned_urls = [url for url in unrolled_urls if url]

    return sorted(set(cleaned_urls))
