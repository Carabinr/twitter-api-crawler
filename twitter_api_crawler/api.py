import json
import logging
import requests
import datetime
from requests_oauthlib import OAuth1  # type: ignore
from typing import Dict, List, Union
from requests_cache import CachedSession
from twitter_api_crawler.exceptions import (
    Twitter429Exception,
    Twitter404Exception,
    Twitter503Exception,
    TwitterAPIClientException,
)
from twitter_api_crawler.helper_utils import sanitize


logger = logging.getLogger(__name__)


class TwitterAPIv1(object):

    def __init__(
        self,
        api_key: str,
        api_key_secret: str,
        access_token: str,
        access_token_secret: str,
        cache_requests: bool = False,
    ):
        """
        Initialize the TwitterAPIv1 API client.

        You need credentials from the developer portal.

        Arguments:
            api_key: Twitter issued API_KEY
            api_key_secret: Twitter issued API_KEY_SECRET
            access_token: Twitter issued ACCESS_TOKEN
            access_token_secret: Twitter issued ACCESS_TOKEN_SECRET
            cache_requests: Cache object or None

        """
        self.auth = OAuth1(
            api_key,
            api_key_secret,
            access_token,
            access_token_secret,
        )
        self.sleep_until = None
        self.cache_requests = cache_requests

    def sleep(self, seconds: int = None) -> None:
        """
        Flag the API client as asleep by setting the `sleep_until` attribute.

        Arguments:
            seconds: How long to sleep in seconds

        Raises:
            TwitterAPIClientException
        """
        if not seconds:
            raise TwitterAPIClientException('You must declare seconds.')

        now = datetime.datetime.now(datetime.timezone.utc)
        delta = datetime.timedelta(seconds=seconds)
        self.sleep_until = now + delta  # type: ignore

    def wakeup(self) -> None:
        """
        Wakes up the API client and makes it active.

        Set the `sleep_until` property to None.

        """
        self.sleep_until = None

    def is_asleep(self):
        """

        Returns
        -------

        """
        now = datetime.datetime.now(datetime.timezone.utc)

        if self.sleep_until is None:
            return False

        if now > self.sleep_until:
            self.wakeup()
            return False

        return True

    def lookup_users(self, screen_name: str) -> Union[Dict, List[Dict]]:
        """Lookup a user in the Twitter API.

        Up to 100 usernames in CSV string may be submitted.

        Args:
            screen_name: CSV string of Twitter accounts (up to 100)

        Returns:
            A dict object API response

        """
        url = 'https://api.twitter.com/1.1/users/lookup.json'
        data = {'screen_name': screen_name}
        logger.debug(f'Looking up {screen_name} on {url}')
        return self._post(url, request_params={}, payload_data=data)

    def get_followers(self, screen_name: str, cursor: int = -1) -> Dict:

        url = 'https://api.twitter.com/1.1/followers/list.json'
        completed = False
        output = []

        request_params = {
            'count': 200,
            'cursor': cursor,
            'screen_name': screen_name,
        }
        results = self._post(url, request_params=request_params)

        if isinstance(results, dict):
            if 'users' in results:
                output.append(results['users'])
                cursor = results['next_cursor']
            else:
                completed = True

        return {
            'users': [item for sublist in output for item in sublist],
            'cursor': cursor,
            'completed': completed,
        }

    def get_following(self, screen_name: str, cursor: int = -1) -> Union[Dict, List[Dict]]:
        """Get the users that screen_name is following.

        Args:
            screen_name: Twitter account name
            cursor: The current position / offset of results

        Returns:
            Twitter API response body
        """
        url = 'https://api.twitter.com/1.1/friends/list.json'

        request_params = {
            'count': 200,
            'cursor': cursor,
            'screen_name': screen_name,
        }
        return self._get(url, request_params)

    def _call(
        self,
        method: str,
        url: str,
        request_params: Dict = None,
        payload_data: Dict = None,
    ) -> Union[Dict, List[Dict]]:
        """
        Dispatches HTTP requests into the Session() module.

        Parameters
        method (str):
        url (str): The Full URL of the destination
        request_params (Dict): an optional dictionary of parameters passed
        into the HTTP request URL
        payload_data (Dict): Optional dictionary of POST/PUT data send in body

        Returns
        A Dict of the Twitter API response body

        Raises
        Twitter429Exception: when API response with HTTP 429 (rate-limit)
        Twitter404Exception: when the API response returns a 404. Often
        because the screen_names are no longer accounts

        """
        session = CachedSession() if self.cache_requests else requests.session()

        response: requests.Response = getattr(session, method)(
            url=url,
            auth=self.auth,
            params=request_params,
            data=payload_data,
        )
        status_code = response.status_code

        logger.debug(f'Fetched: {response.url}')
        logger.debug(f'Got HTTP Response: {status_code}')

        if status_code == 400:
            logger.warning('Got HTTP code: 400')
            logger.warning(response.content)

        if status_code == 429:
            logger.warning('Got HTTP code: 429')
            raise Twitter429Exception()

        if status_code == 404:
            raise Twitter404Exception()

        if status_code == 503:
            payload = response.json()
            logger.warning('Got HTTP code: 503')
            logger.debug(payload)
            raise Twitter503Exception(payload)

        cleaned_str = sanitize(response.content.decode())

        return json.loads(cleaned_str)

    def _get(
        self,
        url: str,
        request_params: Dict = None,
    ) -> Union[Dict, List[Dict]]:
        """Send a GET with params."""
        return self._call('get', url, request_params)

    def _post(
        self,
        url: str,
        request_params: Dict = None,
        payload_data: Dict = None,
    ) -> Union[Dict, List[Dict]]:
        """Send a POST with params and data payloads."""
        return self._call('post', url, request_params, payload_data)
