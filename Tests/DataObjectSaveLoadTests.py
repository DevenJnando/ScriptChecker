import unittest

from Functions.DAOFunctions import save_to_file, load_object
from TestConsts import consts, populate_test_settings


class DataObjectSaveLoadTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        populate_test_settings()
        cls.mock_object = {
            "Truly, we do live": "In the strangest of ages",
            "Are we cursed": "Or blessed?"
        }

    def test_save_and_load_object(self):
        save_to_file(self.mock_object, consts.MOCK_DATA_DIRECTORY + "\\" + consts.MOCK_OBJECT_FILE)
        loaded_object: dict = load_object(consts.MOCK_DATA_DIRECTORY + "\\" + consts.MOCK_OBJECT_FILE)
        self.assertIsNotNone(loaded_object)
        self.assertEqual("In the strangest of ages", loaded_object.get("Truly, we do live"))
        self.assertEqual("Or blessed?", loaded_object.get("Are we cursed"))

    def test_load_bad_object(self):
        loaded_object: dict = load_object("Total rubbish.txt")
        self.assertEqual(loaded_object, None)


if __name__ == '__main__':
    unittest.main()
