import os
import unittest
from twitter_api_crawler.api import TwitterAPIv1
from twitter_api_crawler.exceptions import Twitter404Exception



class TestTwitterAPIv1(unittest.TestCase):

    def setUp(self) -> None:
        self.api = TwitterAPIv1(
            api_key=f"test_api_key",
            api_key_secret='b',
            access_token='c',
            access_token_secret='d'
        )
        self.real_api = TwitterAPIv1(
            api_key=os.getenv('API_KEY'),
            api_key_secret=os.getenv('API_KEY_SECRET'),
            access_token=os.getenv('ACCESS_TOKEN'),
            access_token_secret=os.getenv('ACCESS_TOKEN_SECRET'),
            cache_requests=False
        )
        self.empty_obj = {
            "id": 1234,
            "entities": {
            }
        }
        self.single_obj= {
            "id": 1234,
            "entities": {
                "user_mentions": [
                    {
                        "screen_name": "twitterapi",
                        "name": "Twitter API",
                        "id": 6253282,
                        "id_str": "6253282",
                        "indices": [11,22]
                    }
                ],
                "hashtags": [
                    {
                        "text": "hashtag",
                        "indices": [
                            23,
                            31
                        ]
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
                            "indices": [32,54]
                        }
                    ]
                }
            }
        }


    def test_lookup_group_of_missing_users_with_404(self):
        # screen_name='Bowtiedspiderc1,camperkenny,GardenOfMyopia,petr_bz,Wealth_Theory,wvaeu'
        screen_name='Bowtiedspiderc1,camperkenny'

        with self.assertRaises(Twitter404Exception):
            self.real_api.lookup_users(screen_name)

    def test_get_mentions_empty(self):
        output = self.api.get_mentions(self.empty_obj)
        self.assertEqual(len(output), 0)

    def test_get_mentions_single(self):
        output = self.api.get_mentions(self.single_obj)
        self.assertEqual(len(output), 1)

    def test_get_mentions_multiple(self):
        self.single_obj['entities']['user_mentions'].append(
            {
                "screen_name": "twitterapi2",
                "name": "Twitter API2",
                "id": 62532822,
                "id_str": "62532822",
                "indices": [112, 122]
            }
        )

        output = self.api.get_mentions(self.single_obj)
        self.assertEqual(len(output), 2)

    def test_get_hashtags_empty(self):
        output = self.api.get_hashtags(self.empty_obj)
        self.assertEqual(len(output), 0)

    def test_get_hashtags_single(self):
        output = self.api.get_hashtags(self.single_obj)
        self.assertEqual(len(output), 1)

    def test_get_hashtags_multiple(self):
        self.single_obj['entities']['hashtags'].append({"text": "hashtag2","indices": [23,31]})
        output = self.api.get_hashtags(self.single_obj)
        self.assertEqual(len(output), 2)

    def test_get_urls_empty(self):
        output = self.api.get_urls(self.empty_obj)
        self.assertEqual(len(output), 0)

    def test_get_urls_single(self):
        output = self.api.get_urls(self.single_obj)
        self.assertEqual(len(output), 1)

    def test_get_urls_multiple(self):
        urlobj = {
            "url": "http:\/\/t.co\/p5dOtmnZyu2",
            "expanded_url": "http:\/\/dev.twitter.com2",
            "display_url": "dev.twitter.com2",
            "indices": [
                132,
                154
            ]
        }

        self.single_obj['entities']['url']['urls'].append(urlobj)
        output = self.api.get_urls(self.single_obj)
        self.assertEqual(len(output), 2)


    def test_get_mentions_from_text_one_result(self):
        description = "Hi, I'm bob. I work for @heysamtexas"
        out = self.api.get_mentions_from_text(description)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], 'heysamtexas')

    def test_get_mentions_from_text_multiple_results(self):
        description = "Hi, I'm bob. I work for @heysamtexas formerly @king"
        out = self.api.get_mentions_from_text(description)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], 'heysamtexas')

    def test_get_mentions_from_text_empty_string(self):
        description = ""
        out = self.api.get_mentions_from_text(description)
        self.assertEqual(len(out), 0)

    def test_get_mentions_from_text_no_mentions(self):
        description = "This is a description without a mention"
        out = self.api.get_mentions_from_text(description)
        self.assertEqual(len(out), 0)

    def test_get_mentions_from_text_with_email(self):
        description = "This is a description without a mention. bob@idiot.com"
        out = self.api.get_mentions_from_text(description)
        self.assertEqual(len(out), 0)

    def test_get_hashtags_from_text_empty(self):
        description = ''
        out = self.api.get_hashtags_from_text(description)
        self.assertEqual(len(out), 0)

    def test_get_hashtags_from_text_one_hashtag(self):
        description = 'This is my #hashtag'
        out = self.api.get_hashtags_from_text(description)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], 'hashtag')

    def test_get_hashtags_from_text_multiple_hashtags(self):
        description = 'This is my #hashtag. There is another one #here.'
        out = self.api.get_hashtags_from_text(description)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[1], 'here')

    def test_get_hashtags_from_text_multiple_hashtags_tricky(self):
        description = 'This is my #hashtag. There is another one #here.#here2'
        out = self.api.get_hashtags_from_text(description)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[2], 'here2')

    def test_get_hashtags_from_text_with_tricky_url(self):
        description = 'This is my #hashtag. https://www.bob.com/#bob'
        out = self.api.get_hashtags_from_text(description)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], 'hashtag')
