import unittest
from twitter_api_crawler.api import TwitterAPIv1
from twitter_api_crawler.exceptions import (
    Twitter404Exception,
    Twitter503Exception,
    Twitter429Exception
)
import responses
import csv


class TestTwitterAPIv1(unittest.TestCase):

    def setUp(self) -> None:
        self.api = TwitterAPIv1(
            api_key="test_api_key",
            api_key_secret='b',
            access_token='c',
            access_token_secret='d'
        )
        self.empty_obj = {
            "id": 1234,
            "entities": {
            }
        }
        self.single_obj = {
            "id": 1234,
            "entities": {
                "user_mentions": [
                    {
                        "screen_name": "twitterapi",
                        "name": "Twitter API",
                        "id": 6253282,
                        "id_str": "6253282",
                        "indices": [11, 22]
                    }
                ],
                "hashtags": [
                    {
                        "text": "hashtag",
                        "indices": [23, 31]
                    }
                ],
                "symbols": [
                    {
                        "text": "TWTR",
                        "indices": [
                            5,
                            10
                        ]
                    }
                ],
                "url": {
                    "urls": [
                        {
                            "url": "http:\/\/t.co\/p5dOtmnZyu",
                            "expanded_url": "http:\/\/dev.twitter.com",
                            "display_url": "dev.twitter.com",
                            "indices": [32, 54]
                        }
                    ]
                }
            }
        }

    @responses.activate
    def test_lookup_group_of_missing_users_with_404(self):
        rsp1 = responses.Response(
            method='POST',
            url='https://api.twitter.com/1.1/users/lookup.json',
            status=404
        )

        responses.add(rsp1)
        screen_name = 'idontexist123,ialsodontexist123'

        with self.assertRaises(Twitter404Exception):
            self.api.lookup_users(screen_name)

    @responses.activate
    def test_call_gets_503_error(self):
        rsp1 = responses.Response(
            method='POST',
            url='https://api.twitter.com/1.1/users/lookup.json',
            status=503,
            json={
                'code': 130,
                'message': 'Over capacity'
            }
        )

        responses.add(rsp1)
        screen_name = 'heysamtexas'

        with self.assertRaises(Twitter503Exception):
            self.api.lookup_users(screen_name)

    @responses.activate
    def test_call_gets_429_error(self):
        rsp1 = responses.Response(
            method='POST',
            url='https://api.twitter.com/1.1/users/lookup.json',
            status=429,
            json={}
        )

        responses.add(rsp1)
        screen_name='heysamtexas'

        with self.assertRaises(Twitter429Exception):
            self.api.lookup_users(screen_name)

