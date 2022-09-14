import json
import logging
import requests
from requests_oauthlib import OAuth1
from typing import Dict, List, Union
import datetime
import re
from requests_cache import CachedSession
from .exceptions import Twitter429Exception, Twitter404Exception

logger = logging.getLogger(__name__)


class TwitterAPIv1(object):

    auth = None
    sleep_until = None
    cache_requests = False

    def __init__(self,
                 api_key: str,
                 api_key_secret: str,
                 access_token: str,
                 access_token_secret: str,
                 cache_requests: bool = False):
        self.auth = OAuth1(api_key, api_key_secret, access_token, access_token_secret)
        self.sleep_until = None
        self.cache_requests = cache_requests

    def sleep(self, secs):
        self.sleep_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=secs)

    def wakeup(self):
        self.sleep_until = None

    def is_asleep(self):
        now = datetime.datetime.now(datetime.timezone.utc)

        if self.sleep_until is None:
            return False

        if now > self.sleep_until:
            self.wakeup()
            return False

        return True

    def _call(self, method:str, url:str, params: Dict = None, data: Dict = None) -> Union[Dict, List[Dict]]:
        """
        Secret method that dispatches get, post, put, and delete requests into the Session() module
        Args:
            method (str): get, post, put, or delete all lower case. The HTTP method
            url (str): The Full URL of the destination
            params (dict): an optional dictionary of parameters passed into the HTTP request

        Returns:
            A dict of the Twitter API response body

        Raises:
            Twitter429Exception: when API response with HTTP 429 (rate-limit)
            Twitter404Exception: when the API response returns a 404. Often because the screen_names are no
                                 longer accounts

        """
        session = CachedSession() if self.cache_requests else requests.session()

        r = getattr(session, method)(url=url, auth=self.auth, params=params, data=data)

        logger.debug(f'Fetched: {r.url}')
        logger.debug(f'Got HTTP Response: {r.status_code}')

        if r.status_code == 400:
            logger.warning("Got error 400:")
            logger.warning(r.content)

        if r.status_code == 429:
            raise Twitter429Exception()

        if r.status_code == 404:
            raise Twitter404Exception()

        content = self.sanitize(r.content.decode())

        return json.loads(content)

    def _get(self, url:str, params: Dict = None) -> Union[Dict, List[Dict]]:
        return self._call("get", url, params)

    def _post(self, url:str, params: Dict = None, data: Dict = None) -> Union[Dict, List[Dict]]:
        return self._call("post", url, params, data)

    def lookup_users(self, screen_name: str) -> List[Dict]:
        """
        Lookup a user in the Twitter API. Up to 100 usernames in CSV string may be submitted

        Args:
            screen_name: CSV string of Twitter accounts (up to 100)

        Returns:
            A dict object API response

        """
        url = 'https://api.twitter.com/1.1/users/lookup.json'
        data = {'screen_name': screen_name}
        logger.debug(f"Looking up {screen_name} on {url}")
        return self._post(url, params={}, data=data)

    def get_followers(self, screen_name:str, cursor:int = -1) -> Dict:

        url = 'https://api.twitter.com/1.1/followers/list.json'
        completed = False
        output = []

        results = self._post(url, params={'count': 200, 'cursor': cursor, 'screen_name': screen_name})

        if len(results['users']) > 0:
            output.append(results['users'])
            cursor = results['next_cursor']
        else:
            completed = True

        return {
            'users': [item for sublist in output for item in sublist],
            'cursor': cursor,
            'completed': completed
        }

    def get_following(self, screen_name: str, cursor: int = -1) -> Dict:
        """
        Get the users that screen_name is following.

        Args:
            screen_name: Twitter account name
            cursor: The current position / offset of results

        Returns:
            Twitter API response body
        """
        url = 'https://api.twitter.com/1.1/friends/list.json'

        params = {
            'count': 200,
            'cursor': cursor,
            'screen_name': screen_name
        }
        return self._get(url, params)

    @staticmethod
    def get_mentions(response:Dict) -> List[str]:
        """
        Given an API response status object, return the mentions as a list of strings or empty list

        Args:
            response: API User response object

        Returns:
            List of strings or empty list
        """
        mentions = response.get('entities',{}).get('user_mentions',[])
        usernames = [name.get('screen_name') for name in mentions]
        return usernames

    @staticmethod
    def get_mentions_from_text(text:str) -> List[str]:
        result = re.findall("(^|[^@\w])@(\w{1,15})", text)
        return [_[1] for _ in result]

    @staticmethod
    def get_hashtags_from_text(text:str) -> List[str]:
        rem_url = re.sub(r"https?:[^\s]+",'', text)
        rem_periods = rem_url.replace('.',' ')
        pattern = '(?:(?<=\s)|^)#(\w*[A-Za-z\d\-]{2,60}\w*)'
        return [hashtag_match.group(1) for hashtag_match in re.finditer(pattern, rem_periods)]

    @staticmethod
    def get_hashtags(u:Dict) -> List[str]:
        """
        Given an API response user object, return the hashtags as a list of strings or empty list

        @param u: API User response object
        @return: List of strings or empty list
        """
        mentions = u.get('entities',{}).get('hashtags',[])
        hashtags = [name.get('text') for name in mentions]
        return hashtags

    @staticmethod
    def get_urls(u:Dict) -> List[str]:
        """
        Given an API response user object, return the urls as a list of strings or empty list

        @param u: API User response object
        @return: List of strings or empty list
        """
        url_objs = u.get('entities',{}).get('url',{}).get('urls',[])

        urls = [name.get('expanded_url') for name in url_objs if name.get('expanded_url')]

        if u.get('url'):
            urls.append(u.get('url'))

        return urls

    @staticmethod
    def sanitize(s: str) -> str:
        """
        Remove illegal characters from strings
        """
        output = s.replace('\x00','').replace(r'\u0000','')
        return output
