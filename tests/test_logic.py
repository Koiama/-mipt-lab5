"""Тесты логики, не требующей запуска графического интерфейса."""

from pathlib import Path
import tempfile
import unittest

from advanced03_clicker import ClickerGame
from advanced10_local_chat import ChatMessage, decode_message, encode_message
from task08_file_dialog import read_text_file


class ClickerGameTests(unittest.TestCase):
    def test_game_counts_clicks_and_stops_on_zero(self) -> None:
        game = ClickerGame(duration=2)
        game.start()

        game.click()
        game.click()
        self.assertEqual(game.score, 2)
        self.assertEqual(game.tick(), 1)
        self.assertEqual(game.tick(), 0)
        self.assertFalse(game.active)
        self.assertEqual(game.click(), 2)

    def test_best_score_is_kept_between_rounds(self) -> None:
        game = ClickerGame(duration=1)
        game.start()
        for _ in range(4):
            game.click()
        game.tick()

        game.start()
        game.click()
        self.assertEqual(game.best_score, 4)

    def test_invalid_duration_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ClickerGame(duration=0)


class FileReaderTests(unittest.TestCase):
    def test_reads_utf8_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_text("Привет, файл!", encoding="utf-8")
            self.assertEqual(read_text_file(path), "Привет, файл!")

    def test_rejects_file_above_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.txt"
            path.write_text("12345", encoding="utf-8")
            with self.assertRaises(ValueError):
                read_text_file(path, max_size=4)

    def test_invalid_utf8_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.txt"
            path.write_bytes(b"\xff\xfe\xfa")
            with self.assertRaises(UnicodeDecodeError):
                read_text_file(path)


class ChatProtocolTests(unittest.TestCase):
    def test_round_trip_keeps_unicode(self) -> None:
        message = ChatMessage(nickname="Ксения", text="Привет, локальная сеть!")
        encoded = encode_message(message)
        self.assertEqual(decode_message(encoded), message)

    def test_empty_message_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ChatMessage(nickname="Ксения", text="   ")

    def test_unknown_kind_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ChatMessage(nickname="server", text="test", kind="unknown")


if __name__ == "__main__":
    unittest.main()
