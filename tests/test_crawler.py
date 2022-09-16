import time
import unittest
from twitter_api_crawler.api import TwitterAPIv1
from twitter_api_crawler.crawler import TwitterAPIv1_Crawler


class TestTwitterAPIv1_Crawler(unittest.TestCase):

    def setUp(self) -> None:
        self.crawler = TwitterAPIv1_Crawler()

    def tearDown(self) -> None:
        self.crawler = None

    def create_api(self, key:str):
        self.crawler.create_api(
            key=key,
            api_key=f"{key}_api_key",
            api_key_secret='b',
            access_token='c',
            access_token_secret='d',
        )

    def test_create_empty(self):
        self.assertEqual(len(self.crawler.apis), 0)

    def test_create_api(self):
        self.create_api('boom')
        self.assertEqual(len(self.crawler.apis), 1)
        self.assertEqual(self.crawler.current_key, 'boom')

    def test_create_api_duplicate_key(self):

        with self.assertRaises(Exception):
            self.create_api('boom')
            self.create_api('boom')

    def test_create_api_does_not_change_current_key(self):
        self.create_api('bob')
        self.create_api('bob2')

        self.assertEqual(self.crawler.current_key, 'bob')

    def test_get_api(self):
        self.create_api('boom')
        cred = self.crawler.get_api('boom')
        self.assertIsInstance(cred, TwitterAPIv1)

    def test_get_api_missing_key(self):
        self.create_api('boom')
        cred = self.crawler.get_api('boom2')
        self.assertIsNone(cred)

    def test_get_cursor_when_empty(self):
        cursor = self.crawler.get_cursor('bob')
        self.assertEqual(cursor, "-1")

    def test_get_cursor_when_present(self):
        self.crawler.set_cursor('bob', '9999')
        cursor = self.crawler.get_cursor('bob')
        self.assertEqual(cursor, "9999")

    def test_fetch_api_when_empty(self):
        self.assertIsNone(self.crawler.fetch_api())

    def test_next_api_advances_next_key(self):
        self.create_api('boom')
        first_key = self.crawler.current_key
        self.create_api('boom2')
        self.create_api('boom3')
        self.create_api('boom4')
        self.create_api('boom5')
        self.assertEqual(self.crawler.current_key, first_key)

        # gets current api without iterating to next
        cred1 = self.crawler.fetch_api()
        api_key = cred1.auth.client.client_key
        self.assertEqual(api_key, 'boom_api_key')

        self.crawler.pause_current_api(60)
        cred2 = self.crawler.next_api()
        api_key = cred2.auth.client.client_key
        self.assertNotEqual(self.crawler.current_key, first_key)

    def test_next_api_loops_around(self):
        self.create_api('boom')
        self.create_api('boom2')
        self.create_api('boom3')

        # test that it loops around
        looped = self.crawler.next_api()
        looped = self.crawler.next_api()
        looped = self.crawler.next_api()
        api_key = looped.auth.client.client_key
        self.assertEqual(api_key, 'boom_api_key')
        self.assertEqual(self.crawler.current_key, 'boom')

    def test_next_api_is_none_when_empty(self):
        cred1 = self.crawler.next_api()
        self.assertIsNone(cred1)

    def test_pause_current_api(self):
        self.create_api('boom')
        self.crawler.pause_current_api(15*60)

        self.assertTrue(self.crawler.fetch_api().is_asleep())

    def test_pause_current_api_short_time(self):
        self.create_api('boom')
        self.crawler.pause_current_api(2)
        self.assertTrue(self.crawler.fetch_api().is_asleep())

        time.sleep(3)

        self.assertFalse(self.crawler.fetch_api().is_asleep())

    def test_next_api__all_apis_paused_is_none(self):
        self.create_api('boom')
        self.create_api('boom2')
        self.create_api('boom3')

        self.crawler.pause_current_api(600)
        out1 = self.crawler.next_api()

        self.crawler.pause_current_api(600)
        out2 = self.crawler.next_api()

        self.crawler.pause_current_api(600)
        out3 = self.crawler.next_api()

        self.assertIsNone(self.crawler.next_api())

    def test_next_api__no_apis_created(self):
        self.create_api('boom')
        self.crawler.pause_current_api(600)
        self.crawler.next_api()
        self.assertIsNone(self.crawler.next_api())

    def test_get_all_following_no_api(self):
        self.create_api('boom')
        self.crawler.pause_current_api(60)

        payload = self.crawler.get_all_following('heysamtexas')

        self.assertEqual(len(payload['users']), 0)
        self.assertFalse(payload['completed'])
        self.assertEqual(payload['cursor'], -1)
