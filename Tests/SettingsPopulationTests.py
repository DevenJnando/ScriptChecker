import os

from TestConsts import consts, populate_test_settings, load_test_settings
import unittest
import Functions.ConfigSingleton


class SettingsPopulationTests(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        populate_test_settings()
        Functions.ConfigSingleton.config = load_test_settings()

    def test_settings_population(self):
        self.assertEqual(consts.TEST_SETTINGS, os.path.dirname(os.path.abspath(__file__)) + "\\test_settings.yaml")


if __name__ == '__main__':
    unittest.main()
