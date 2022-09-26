import unittest
import csv
from twitter_api_crawler.helper_utils import (
    sanitize,
    extract_ens_domains,
    get_hashtags_from_text,
    get_mentions_from_text,
    get_urls,
    get_hashtags,
    get_mentions,
)
import responses


class TestSanitize(unittest.TestCase):

    def test_sanitize_with_null_characters(self):
        s = """
        [{'id': 787310777493364736, 'id_str': '787310777493364736', 'name': '\x00Hunter', 'screen_name': 'hunter_bdm', 'location': '\x00Houston', 'description': 'Welcome.\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\r\rDoing Absolutely Nothing', 'url': None, 'entities': {'description': {'urls': []}}, 'protected': False, 'followers_count': 16151, 'friends_count': 298, 'listed_count': 33, 'created_at': 'Sat Oct 15 15:14:51 +0000 2016', 'favourites_count': 6390, 'utc_offset': None, 'time_zone': None, 'geo_enabled': False, 'verified': False, 'statuses_count': 576, 'lang': None, 'status': {'created_at': 'Wed Sep 07 05:14:07 +0000 2022', 'id': 1567380673505202176, 'id_str': '1567380673505202176', 'text': '@xCodeh If it makes you feel any better I asked my friend I should buy $ETH at $12  and he said fuck no 😭', 'truncated': False, 'entities': {'hashtags': [], 'symbols': [{'text': 'ETH', 'indices': [71, 75]}], 'user_mentions': [{'screen_name': 'xCodeh', 'name': 'xCodeh', 'id': 1053411019, 'id_str': '1053411019', 'indices': [0, 7]}], 'urls': []}, 'source': '<a href="http://twitter.com/download/iphone" rel="nofollow">Twitter for iPhone</a>', 'in_reply_to_status_id': 1567375881609289729, 'in_reply_to_status_id_str': '1567375881609289729', 'in_reply_to_user_id': 1053411019, 'in_reply_to_user_id_str': '1053411019', 'in_reply_to_screen_name': 'xCodeh', 'geo': None, 'coordinates': None, 'place': None, 'contributors': None, 'is_quote_status': False, 'retweet_count': 0, 'favorite_count': 7, 'favorited': False, 'retweeted': False, 'lang': 'en'}, 'contributors_enabled': False, 'is_translator': False, 'is_translation_enabled': False, 'profile_background_color': '000000', 'profile_background_image_url': 'http://abs.twimg.com/images/themes/theme1/bg.png', 'profile_background_image_url_https': 'https://abs.twimg.com/images/themes/theme1/bg.png', 'profile_background_tile': False, 'profile_image_url': 'http://pbs.twimg.com/profile_images/1548808078203781120/YPyRKLdW_normal.png', 'profile_image_url_https': 'https://pbs.twimg.com/profile_images/1548808078203781120/YPyRKLdW_normal.png', 'profile_banner_url': 'https://pbs.twimg.com/profile_banners/787310777493364736/1658099545', 'profile_link_color': '1B95E0', 'profile_sidebar_border_color': '000000', 'profile_sidebar_fill_color': '000000', 'profile_text_color': '000000', 'profile_use_background_image': False, 'has_extended_profile': True, 'default_profile': False, 'default_profile_image': False, 'following': False, 'follow_request_sent': False, 'notifications': False, 'translator_type': 'none', 'withheld_in_countries': []}]
        """
        # s = '\x00abc123'
        self.assertIn('\x00', s)
        out = sanitize(s)
        self.assertNotIn('\x00', out)

        unicode_str = r'\u0000Hunter'
        out2 = sanitize(unicode_str)
        self.assertTrue('Hunter' == out2)


class TestGetEnsDomains(unittest.TestCase):

    def test_extract_ens_domains(self):
        out = extract_ens_domains('Houston, Texas')
        self.assertCountEqual([], out)

        out = extract_ens_domains('bob.eth')
        self.assertEqual('bob.eth', out[0])

        out = extract_ens_domains('bob.eth / bill.eth')
        self.assertEqual(['bob.eth', 'bill.eth'], out)

        out = extract_ens_domains('.eth')
        self.assertEqual([], out)

        out = extract_ens_domains('heysamtexas')
        self.assertCountEqual([], out)

        with open('descriptions.csv', 'r') as f:
            reader = csv.DictReader(f)
            a = list(reader)

        for _ in a:
            out = extract_ens_domains(_['fixed'])
            out = [''] if len(out) == 0 else out
            self.assertEqual(_['results'].lower().split(','), out)


class TestGetMentions(unittest.TestCase):

    def setUp(self) -> None:
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

    def test_get_mentions_empty(self):
        output = get_mentions(self.empty_obj)
        self.assertEqual(len(output), 0)

    def test_get_mentions_single(self):
        output = get_mentions(self.single_obj)
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

        output = get_mentions(self.single_obj)
        self.assertEqual(len(output), 2)

    def test_get_hashtags_empty(self):
        output = get_hashtags(self.empty_obj)
        self.assertEqual(len(output), 0)

    def test_get_hashtags_single(self):
        output = get_hashtags(self.single_obj)
        self.assertEqual(len(output), 1)

    def test_get_hashtags_multiple(self):
        self.single_obj['entities']['hashtags'].append({"text": "hashtag2", "indices": [23, 31]})
        output = get_hashtags(self.single_obj)
        self.assertEqual(len(output), 2)

    def test_get_urls_empty(self):
        output = get_urls(self.empty_obj)
        self.assertEqual(len(output), 0)

    def test_get_urls_single(self):
        output = get_urls(self.single_obj)
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
        output = get_urls(self.single_obj)
        self.assertEqual(len(output), 2)

    def test_get_mentions_from_text_one_result(self):
        description = "Hi, I'm bob. I work for @heysamtexas"
        out = get_mentions_from_text(description)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], 'heysamtexas')

    def test_get_mentions_from_text_multiple_results(self):
        description = "Hi, I'm bob. I work for @heysamtexas formerly @king"
        out = get_mentions_from_text(description)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], 'heysamtexas')

    def test_get_mentions_from_text_empty_string(self):
        description = ""
        out = get_mentions_from_text(description)
        self.assertEqual(len(out), 0)

    def test_get_mentions_from_text_no_mentions(self):
        description = "This is a description without a mention"
        out = get_mentions_from_text(description)
        self.assertEqual(len(out), 0)

    def test_get_mentions_from_text_with_email(self):
        description = "This is a description without a mention. bob@idiot.com"
        out = get_mentions_from_text(description)
        self.assertEqual(len(out), 0)

    def test_get_hashtags_from_text_empty(self):
        description = ''
        out = get_hashtags_from_text(description)
        self.assertEqual(len(out), 0)

    def test_get_hashtags_from_text_one_hashtag(self):
        description = 'This is my #hashtag'
        out = get_hashtags_from_text(description)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], 'hashtag')

    def test_get_hashtags_from_text_multiple_hashtags(self):
        description = 'This is my #hashtag. There is another one #here.'
        out = get_hashtags_from_text(description)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[1], 'here')

    def test_get_hashtags_from_text_multiple_hashtags_tricky(self):
        description = 'This is my #hashtag. There is another one #here.#here2'
        out = get_hashtags_from_text(description)
        self.assertEqual(len(out), 3)
        self.assertEqual(out[2], 'here2')

    def test_get_hashtags_from_text_with_tricky_url(self):
        description = 'This is my #hashtag. https://www.bob.com/#bob'
        out = get_hashtags_from_text(description)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], 'hashtag')


class TestGetUrls(unittest.TestCase):

    def setUp(self) -> None:
        self.user_obj_fragment = {
            'url': 'https://t.co/0ymMfMj6ht',
            'entities': {
                'url': {
                    'urls': [
                        {
                            'url': 'https://t.co/0ymMfMj6ht',
                            'expanded_url': 'https://www.curabase.com',
                            'display_url': 'curabase.com',
                            'indices': [0, 23],
                        },
                        {
                            'url': 'https://t.co/0ymMfMj6ht2',
                            'expanded_url': 'https://www.simplecto.com',
                            'display_url': 'curabase2.com',
                            'indices': [0, 23],
                        },
                    ],
                },
                'description': {
                    'urls': [
                        {
                            'display_url': 'techunity.dev',
                            'expanded_url': 'http://techunity.dev',
                            'indices': [0, 23],
                            'url': 'https://t.co/p1c9TRYlXO',
                        },
                        {
                            'display_url': 'techunity2.dev',
                            'expanded_url': 'http://techunity2.dev',
                            'indices': [0, 23],
                            'url': 'https://t.co/p1c9TRYlXO2',
                        },
                    ],
                },
            },
        }

    def test_extract_urls(self):
        actual = get_urls(self.user_obj_fragment)
        expected = sorted([
            'https://www.curabase.com',
            'https://www.simplecto.com',
            'http://techunity.dev',
            'http://techunity2.dev',
        ])
        self.assertEqual(expected, actual)

    @responses.activate
    def test_extract_urls_empty(self):
        rsp1 = responses.Response(
            method='HEAD',
            url='https://t.co/0ymMfMj6ht',
            status=301,
            headers={'Location': 'https://www.curabase.com/'},
        )
        rsp2 = responses.Response(
            method='HEAD',
            url='https://www.curabase.com/',
            status=200,
        )
        responses.add(rsp1)
        responses.add(rsp2)
        fragment = {
            'url': 'https://t.co/0ymMfMj6ht',
            'entities': {
                'url': {
                    'urls': [],
                },
                'description': {
                    'urls': [],
                },
            },
        }
        actual = get_urls(fragment)
        expected = ['https://www.curabase.com']
        self.assertEqual(expected, actual)


class TestGetHashTagsFromText(unittest.TestCase):

    def test_text_with_url(self):
        blob = 'Friends with @heysamtexas. Find me here: https://example.com/bob#uhoh\n\n#hashtagsforlife'
        expected = ['hashtagsforlife']
        actual = get_hashtags_from_text(blob)

        self.assertEqual(expected, actual)

    def test_text_with_hashtag_in_url(self):
        actual = get_hashtags_from_text(
            'https://test.com/hahah#boom ##bob' +
            ' https://search.brave.com/search?q=wtf+am|i+doing+' +
            'length&source=desktop'
        )
        self.assertEqual(['bob'], actual)

    def test_text_with_hashtag_no_spaces(self):
        blob = 'I am an #idiot#toomanytags stuck together'
        expected = ['idiot', 'toomanytags']
        actual = get_hashtags_from_text(blob)
        self.assertEqual(expected, actual)

    def test_text_full_retard(self):
        blob = '#I#am#an##idiot#toomanytags#stuck#together'
        expected = ['I', 'am', 'an', 'idiot', 'toomanytags', 'stuck', 'together']
        actual = get_hashtags_from_text(blob)
        self.assertEqual(expected, actual)

    def test_dash_and_underscores(self):
        blob = 'This blob tests #hash-hypens and #hash_underscores'
        expected = ['hash-hypens', 'hash_underscores']
        actual = get_hashtags_from_text(blob)
        self.assertEqual(expected, actual)
