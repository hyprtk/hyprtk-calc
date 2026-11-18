import json
import os
import tempfile
import unittest

from hyprtk_calc.history import History
from hyprtk_calc.settings import DEFAULTS, Settings


class Temp(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="hyprtk-calc-test-")
        self.path = os.path.join(self.dir, "history.jsonl")

    def tearDown(self):
        for name in os.listdir(self.dir):
            os.remove(os.path.join(self.dir, name))
        os.rmdir(self.dir)


class HistoryTest(Temp):
    def test_add_and_persist(self):
        history = History(self.path)
        history.add("1+1", "2")
        history.add("2+2", "4")
        self.assertEqual(len(history), 2)

        reopened = History(self.path)
        self.assertEqual([entry.expression for entry in reopened.entries()], ["1+1", "2+2"])
        self.assertEqual(reopened.entries()[0].result, "2")

    def test_newest_first(self):
        history = History(self.path)
        history.add("1+1", "2")
        history.add("2+2", "4")
        self.assertEqual(history.newest_first()[0].expression, "2+2")
        self.assertEqual(history.newest_first(1)[0].expression, "2+2")

    def test_repeat_replaces(self):
        history = History(self.path)
        history.add("1+1", "2")
        history.add("1+1", "2")
        self.assertEqual(len(history), 1)

    def test_blank_expression_is_ignored(self):
        history = History(self.path)
        history.add("   ", "0")
        self.assertEqual(len(history), 0)
        self.assertFalse(os.path.exists(self.path))

    def test_find(self):
        history = History(self.path)
        history.add("12*12", "144")
        history.add("sqrt(9)", "3")
        self.assertEqual(len(history.find("12")), 1)
        self.assertEqual(history.find("3")[0].result, "3")
        self.assertEqual(len(history.find("")), 2)

    def test_limit_trims_oldest(self):
        history = History(self.path, limit=3)
        for index in range(5):
            history.add("1+{0}".format(index), str(index + 1))
        self.assertEqual(len(history), 3)
        self.assertEqual(history.entries()[0].expression, "1+2")
        self.assertEqual(len(History(self.path).entries()), 3)

    def test_corrupt_line_is_skipped(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write('{"expression": "1+1", "result": "2", "at": ""}\n')
            handle.write("{not json}\n")
            handle.write('{"expression": "2+2", "result": "4", "at": ""}\n')
        self.assertEqual(len(History(self.path)), 2)

    def test_clear(self):
        history = History(self.path)
        history.add("1+1", "2")
        history.clear()
        self.assertEqual(len(history), 0)
        self.assertFalse(os.path.exists(self.path))


class SettingsTest(Temp):
    def test_defaults(self):
        settings = Settings(os.path.join(self.dir, "config.json"))
        self.assertEqual(settings.get("precision"), DEFAULTS["precision"])
        self.assertEqual(settings.get("angle"), "deg")

    def test_round_trip(self):
        path = os.path.join(self.dir, "config.json")
        settings = Settings(path)
        self.assertTrue(settings.set("precision", 18))
        self.assertTrue(settings.set("angle", "rad"))
        self.assertTrue(settings.set("grouping", "comma"))
        settings.save()

        reopened = Settings(path)
        self.assertEqual(reopened.get("precision"), 18)
        self.assertEqual(reopened.get("angle"), "rad")
        self.assertEqual(reopened.get("grouping"), "comma")

    def test_set_reports_change(self):
        settings = Settings(os.path.join(self.dir, "config.json"))
        self.assertTrue(settings.set("angle", "grad"))
        self.assertFalse(settings.set("angle", "grad"))
        self.assertFalse(settings.set("nonsense", 1))

    def test_invalid_values_fall_back(self):
        settings = Settings(os.path.join(self.dir, "config.json"))
        settings.set("precision", "banana")
        self.assertEqual(settings.get("precision"), DEFAULTS["precision"])
        settings.set("angle", "turns")
        self.assertEqual(settings.get("angle"), "deg")
        settings.set("grouping", ";")
        self.assertEqual(settings.get("grouping"), "none")
        settings.set("keypad", "graphing")
        self.assertEqual(settings.get("keypad"), "basic")

    def test_ranges(self):
        settings = Settings(os.path.join(self.dir, "config.json"))
        settings.set("precision", 1000)
        self.assertEqual(settings.get("precision"), 60)
        settings.set("precision", 1)
        self.assertEqual(settings.get("precision"), 3)
        settings.set("width", 10)
        self.assertEqual(settings.get("width"), 320)
        settings.set("width", 1927)   # a tiled launch must not become the default
        self.assertEqual(settings.get("width"), 1200)
        settings.set("height", 5000)
        self.assertEqual(settings.get("height"), 1400)

    def test_booleans(self):
        settings = Settings(os.path.join(self.dir, "config.json"))
        settings.set("live", 0)
        self.assertFalse(settings.get("live"))
        settings.set("always_on_top", "yes")
        self.assertTrue(settings.get("always_on_top"))

    def test_unknown_keys_are_not_written(self):
        path = os.path.join(self.dir, "config.json")
        settings = Settings(path)
        settings.set("evil", 1)
        settings.save()
        with open(path, encoding="utf-8") as handle:
            self.assertNotIn("evil", json.load(handle))

    def test_broken_file_is_ignored(self):
        path = os.path.join(self.dir, "config.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{oops")
        self.assertEqual(Settings(path).get("precision"), DEFAULTS["precision"])


if __name__ == "__main__":
    unittest.main()
