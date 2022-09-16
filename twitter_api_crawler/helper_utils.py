from typing import Dict, List
import re


MAX_ENS_DOMAIN_LENGTH = 50  # arbitrary. I don't know the actual length


def extract_ens_domains(blob: str) -> List[str]:
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
    out: List = list()
    blob = blob.lower()

    if blob == '.eth':
        return out

    if '.eth' not in blob:
        return out

    blob = blob.replace('\n', '').replace('\r', '').replace('#', ' ').replace('$', ' ').replace('/', ' ')
    str_list: List[str] = re.split(' ', blob)

    str_list = [_ for _ in str_list if len(_) <= MAX_ENS_DOMAIN_LENGTH]
    str_list = [_ for _ in str_list if '.eth' in _]

    for test_str in str_list:
        test_str = test_str.replace('.eth.', '.eth')
        test_str = re.sub(r'\.{2,}|,|;|\)|\(|\s|^\.', '', test_str)

        if test_str.endswith('.eth'):
            out.append(test_str)

    return out


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


def get_mentions_from_text(text: str) -> List[str]:
    """
    Pull user mentions (@username) from a blob of text.

    Parameters
        text: The target piece of text

    Returns
        A list of mentions
    """
    matches = re.findall(r'(^|[^@\w])@(\w{1,15})', text)
    return [_[1] for _ in matches]


def get_hashtags_from_text(text: str) -> List[str]:
    """
    Return a list of hashtags found in a blob of text.

    Parameters
        text: The target blob of text

    Returns
        A list of strings of hashtags
    """
    rem_url = re.sub(r'https?:[^\s]+', '', text)
    rem_periods = rem_url.replace('.', ' ')
    pattern = r'(?:(?<=\s)|^)#(\w*[A-Za-z\d\-]{2,60}\w*)'
    return [hashtag_match.group(1) for hashtag_match in re.finditer(pattern, rem_periods)]


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


def get_urls(user: Dict) -> List[str]:
    """
    Extract urls from a Twitter API user Dict.

    Return the urls as a list of strings or empty list given a
    Twitter API Response Object

    @param user: API User response object
    @return: List of strings or empty list
    """
    url_list = user.get('entities', {}).get('url', {}).get('urls', [])

    urls = [name.get('expanded_url') for name in url_list if name.get('expanded_url')]

    if user.get('url'):
        urls.append(user.get('url'))

    return urls
