import logging
from typing import Dict, Union

from twitter_api_crawler.api import TwitterAPIv1
from twitter_api_crawler.exceptions import (
    Twitter429Exception,
    TwitterAPIClientException,
    TwitterNoAvailableAPIs,
)

logger = logging.getLogger(__name__)

SLEEP_PERIOD = 15 * 60


class TwitterAPIv1Crawler(object):

    def __init__(self):
        """Initialize the crawler object."""
        self.apis = {}
        self.current_key = ''
        self.cursors = {}

    def create_api(
        self,
        key: str,
        api_key: str,
        api_key_secret: str,
        access_token: str,
        access_token_secret: str,
    ):
        """
            Initialize a new TwitterAPI and add it to the list of APIs.

        @param key:
        @param api_key:
        @param api_key_secret:
        @param access_token:
        @param access_token_secret:
        @return:
        """
        if key in self.apis:
            raise TwitterAPIClientException(
                'Duplicate Key in your credentials',
            )

        if self.current_key == '':
            self.current_key = key

        self.apis[key] = TwitterAPIv1(
            api_key,
            api_key_secret,
            access_token,
            access_token_secret,
        )

    def get_api(self, key: str) -> Union[TwitterAPIv1, None]:
        """Fetch an API client by it lookup key."""
        return self.apis.get(key, None)

    def fetch_api(self) -> Union[TwitterAPIv1, None]:
        """Return the current active API client."""
        return self.apis.get(self.current_key, None)

    def next_api(self) -> TwitterAPIv1:
        """
        Grab the next available API client from our list that is not asleep.

        Returns
            A TwitterAPI client

        Raises
            TwitterNoAvailableAPIs
        """
        for key in list(self.apis.keys()):
            if not self.apis[key].is_asleep():
                self.current_key = key
                return self.apis[key]

        self.current_key = None
        raise TwitterNoAvailableAPIs()

    def pause_current_api(self, secs: int) -> None:
        """
        Set a sleep property on the TwitterAPI object.

        If it is set (and still valid), then it will not be included when
        rotating API clients.

        Args
            secs: the number of seconds this api client should sleep

        Returns
            None
        """
        if self.current_key:
            self.apis[self.current_key].sleep(secs)

    def set_cursor(self, username: str, cursor: str) -> None:
        """Set the cursor for the current API round."""
        self.cursors[username] = cursor

    def get_cursor(self, username: str) -> str:
        return self.cursors.get(username, -1)

    def get_following(self, username: str, cursor: int = -1) -> Dict:
        """
        Crawl as many followed accounts as possible with the Twitter Objects.

        Given a Username (eg Twitter screen_name) and optional Twitter
        "cursor", try to crawl as many followed accounts as possible with the
        assigned Twitter Objects.

        If API Rate limits are hit (HTTP 429), then it will mark that
        particular API client as asleep and rotate to another client in the
        list.

        Once it runs out of available API clients, it will exit the loop and
        return the users it has up to that point. It will also return the last
        known cursor so you can save your process.

        Args
            username (str): username (eg. screen_name) of a known Twitter user
            cursor (int): An integer that is used for pagination with the
            Twitter API

        Returns
            Python dict containing username(str), users(list of users crawled),
            cursor (int), and completed(boolean)

        """
        output = []
        try:
            following = self.next_api().get_following(username, cursor)
        except Twitter429Exception:
            logger.info('Got 429: API Client Key unavailable for 15 minutes')
            self.pause_current_api(SLEEP_PERIOD)
            raise Twitter429Exception()

        users = following.get('users', [])
        cursor = int(following.get('next_cursor', -1))

        if users:
            output.append(users)

        flat_users = [user for sublist in output for user in sublist]

        return {
            'username': username,
            'users': flat_users,
            'cursor': cursor,
            'completed': cursor == 0,
        }
