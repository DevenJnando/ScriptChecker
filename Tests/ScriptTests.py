import unittest
from xml.dom import minidom

from TestConsts import consts, load_test_settings, populate_test_settings
from Functions.XML import scan_script


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        populate_test_settings()
        cls.config = load_test_settings()
        with open(consts.MOCK_DATA_DIRECTORY + "\\" + consts.MOCK_SCRIPT_XML) as script_file:
            cls.mock_script = script_file.read()

    def test_get_patient_details_from_script(self):
        script_as_xml = scan_script(self.mock_script)
        self.assertIsNotNone(script_as_xml)
        if isinstance(script_as_xml, minidom.Document):
            patient_details = script_as_xml.getElementsByTagName("pa")[0]
            first_name = patient_details.getAttribute("f")
            middle_name = patient_details.getAttribute("m")
            last_name = patient_details.getAttribute("l")
            dob = patient_details.getAttribute("b")
            self.assertEqual("John", first_name)
            self.assertEqual("Paul", middle_name)
            self.assertEqual("Johnson", last_name)
            self.assertEqual("1955-11-05", dob)
        else:
            self.fail("Script type incorrect. Expected type: {0}, Actual type: {1}".format(minidom.Document,
                                                                                           type(script_as_xml)))

    def test_get_medicine_details_from_script(self):
        script_as_xml = scan_script(self.mock_script)
        self.assertIsNotNone(script_as_xml)
        if isinstance(script_as_xml, minidom.Document):
            medicines_on_script = script_as_xml.getElementsByTagName("dd")
            for i in range(len(medicines_on_script)):
                medicine = medicines_on_script[i]
                match i:
                    case 0:
                        self.assertEqual("Frisium 10mg tablets (Sanofi)", medicine.getAttribute("d"))
                        self.assertEqual(str(10), medicine.getAttribute("q"))
                    case 1:
                        self.assertEqual("Frisium 10mg tablets (Sanofi)", medicine.getAttribute("d"))
                        self.assertEqual(str(15), medicine.getAttribute("q"))
                    case 2:
                        self.assertEqual("Lamictal 200mg tablets (GlaxoSmithKline UK Ltd)", medicine.getAttribute("d"))
                        self.assertEqual(str(56), medicine.getAttribute("q"))
                    case 3:
                        self.assertEqual("Lamictal 50mg tablets (GlaxoSmithKline UK Ltd)", medicine.getAttribute("d"))
                        self.assertEqual(str(56), medicine.getAttribute("q"))
        else:
            self.fail("Script type incorrect. Expected type: {0}, Actual type: {1}".format(minidom.Document,
                                                                                           type(script_as_xml)))


if __name__ == '__main__':
    unittest.main()
