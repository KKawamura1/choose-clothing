import unittest
from unittest.mock import patch

from clothing_app import choose_outfit, send_ntfy_notification


class ChooseOutfitTests(unittest.TestCase):
    def test_hot_day(self) -> None:
        outfit = choose_outfit(31, 23)
        self.assertEqual(outfit["items"], ["1", "6"])

    def test_warm_day(self) -> None:
        outfit = choose_outfit(25, 17)
        self.assertEqual(outfit["items"], ["1", "2"])

    def test_mild_day(self) -> None:
        outfit = choose_outfit(19, 11)
        self.assertEqual(outfit["items"], ["1", "2", "3"])

    def test_cool_day(self) -> None:
        outfit = choose_outfit(14, 6)
        self.assertEqual(outfit["items"], ["1", "2", "3", "4"])

    def test_cold_day(self) -> None:
        outfit = choose_outfit(8, 1)
        self.assertEqual(outfit["items"], ["1", "2", "3", "5"])


class NtfyNotificationTests(unittest.TestCase):
    @patch("clothing_app.urllib.request.urlopen")
    def test_send_ntfy_notification_posts_to_topic(self, mock_urlopen) -> None:
        send_ntfy_notification(
            server="https://ntfy.sh",
            topic="secret-topic",
            title="今日の服装",
            message="おすすめ: 肌着 / 綿の長袖",
        )

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://ntfy.sh/secret-topic")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.headers["Title"], "今日の服装")
        self.assertEqual(request.data, "おすすめ: 肌着 / 綿の長袖".encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
