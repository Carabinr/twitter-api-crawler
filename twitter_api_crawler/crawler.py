from typing import Union, Dict
import logging
from .exceptions import TwitterNoAvailableAPIs, Twitter429Exception
from .api import TwitterAPIv1
from requests_oauthlib import OAuth1

logger = logging.getLogger(__name__)


class TwitterAPIv1_Crawler(object):
    apis = {}
    current_key = ''
    cursors = {}

    def __init__(self):
        self.apis = {}
        self.current_key = ''
        self.cursors = {}

    def create_api(self, key:str, api_key:str, api_key_secret:str, access_token:str, access_token_secret:str):
        """

        @param key:
        @param api_key:
        @param api_key_secret:
        @param access_token:
        @param access_token_secret:
        @return:
        """
        if key in self.apis:
            raise Exception('Duplicate Key in your credentials')

        if self.current_key == '':
            self.current_key = key

        self.apis[key] = TwitterAPIv1(api_key, api_key_secret, access_token, access_token_secret)


    def get_api(self, key:str):
        return self.apis.get(key, None)

    def delete_api(self, key:str) -> None:
        if key in self.apis:
            del self.apis[key]


    def update_api(self, key:str, api_key:str, api_key_secret:str, access_token:str, access_token_secret:str):
        if key not in self.apis:
            raise Exception('That key does not exist')

        self.apis[key] = OAuth1(api_key, api_key_secret, access_token, access_token_secret)

    def fetch_api(self) -> Union[TwitterAPIv1, None]:
        if len(self.apis) == 0:
            return None

        return self.apis[self.current_key]


    def next_api(self) -> Union[TwitterAPIv1, None]:
        """
        Grab the next available API client from our list that is not asleep.

        Returns:
            None (if none are available) or a TwitterAPI client
        """
        for k in list(self.apis.keys()):
            if not self.apis[k].is_asleep():
                self.current_key = k
                return self.apis[k]

        self.current_key = None
        return None

    def pause_current_api(self, secs:int) -> None:
        """
        Calling this method will set a sleep property on the TwitterAPI object. If it is set (and still valid), then
        it will not be included when rotating API clients.

        Args:
            secs: the number of seconds this api client should sleep

        Returns:
            None
        """
        if self.current_key:
            self.apis[self.current_key].sleep(secs)

    def set_cursor(self, username:str, cursor:str) -> None:
        self.cursors[username] = cursor

    def get_cursor(self, username:str) -> str:
        return self.cursors.get(username, '-1')

    def get_all_following(self, username: str, cursor: str = "-1") -> Dict:
        """
        Given a Username (eg Twitter screen_name) and optional Twitter "cursor", try to crawl as many followed
        accounts as possible with the assigned Twitter Objects.

        If API Rate limits are hit (HTTP 429), then it will mark that particular API client as asleep and rotate
        to another client in the list.

        Once it runs out of available API clients, it will exit the loop and return the users it has up to that point.
        It will also return the last known cursor so you can save your process.

        Args:
            username (str): username (eg. screen_name) of a known Twitter user
            cursor (int): An integer that is used for pagination with the Twitter API

        Returns:
            Python dict containing username(str), users(list of users crawled), cursor (int), and completed(boolean)
        """
        has_more = True
        output = []
        completed = False

        while has_more:
            api = self.next_api()

            if api is None:
                has_more = False
                break

            try:
                results = api.get_following(username, cursor)
            except Twitter429Exception:
                logger.info('Got 429: Marking API Client Key as unavailable')
                self.pause_current_api(15*60)
                continue

            users = results.get('users', [])
            cursor = results.get('next_cursor')

            if len(users) > 0:
                output.append(users)
            else:
                completed = True
                has_more = False

        flat_users = [item for sublist in output for item in sublist]

        payload = {
            'username': username,
            'users': flat_users,
            'cursor': cursor,
            'completed': completed
        }

        return payload

    def get_following(self, username: str, cursor: int = -1) -> Dict:
        """
        Given a Username (eg Twitter screen_name) and optional Twitter "cursor", try to crawl as many followed
        accounts as possible with the assigned Twitter Objects.

        If API Rate limits are hit (HTTP 429), then it will mark that particular API client as asleep and rotate
        to another client in the list.

        Once it runs out of available API clients, it will exit the loop and return the users it has up to that point.
        It will also return the last known cursor so you can save your process.

        Args:
            username (str): username (eg. screen_name) of a known Twitter user
            cursor (int): An integer that is used for pagination with the Twitter API

        Returns:
            Python dict containing username(str), users(list of users crawled), cursor (int), and completed(boolean)

        Raises:
            Twitter429Exception
        """
        output = []
        completed = False

        api = self.next_api()

        if api is None:
            raise TwitterNoAvailableAPIs()

        try:
            results = api.get_following(username, cursor)
        except Twitter429Exception:
            logger.info('Got 429: Marking API Client Key as unavailable for 15 minutes')
            self.pause_current_api(15 * 60)
            raise Twitter429Exception()

        users = results.get('users', [])
        cursor = results.get('next_cursor')

        if len(users) > 0:
            output.append(users)

        flat_users = [item for sublist in output for item in sublist]

        payload = {
            'username': username,
            'users': flat_users,
            'cursor': cursor,
            'completed': cursor == 0
        }

        return payload
