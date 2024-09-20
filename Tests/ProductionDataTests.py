import datetime
from functools import reduce
from xml.dom import minidom
from Functions.XML import parse_xml_ppc, sanitise_and_encode_text_from_file
from Functions.DAOFunctions import scan_pillpack_folder
from Functions.ModelBuilder import create_patient_object_from_pillpack_data

import Models
from TestConsts import consts, populate_test_settings, load_test_settings
import unittest


class ProductionDataXMLTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        populate_test_settings()
        cls.config = load_test_settings()

    def test_xml_location(self):
        self.assertEqual(self.config["pillpackDataLocation"], consts.MOCK_DATA_DIRECTORY)

    def test_file_scanning(self):
        list_of_ppc_processed_files: list = scan_pillpack_folder(consts.MOCK_DATA_DIRECTORY)
        self.assertEqual(3, len(list_of_ppc_processed_files))

    def test_xml_sanitization(self):
        strings: list = sanitise_and_encode_text_from_file(consts.BAD_XML_PPC, consts.PPC_SEPARATING_TAG, self.config)
        self.assertEqual(3, len(strings))
        for string in strings:
            self.assertEqual("<?xml version=\"1.0\" encoding=\"utf-8\"?>", string.partition('\n')[0].strip())

    def test_parse_xml(self):
        xml_data: list = reduce(list.__add__,
                                parse_xml_ppc(sanitise_and_encode_text_from_file(consts.BAD_XML_PPC,
                                                                                 consts.PPC_SEPARATING_TAG, self.config)))
        self.assertEqual(3, len(xml_data))
        for i in range(len(xml_data)):
            if isinstance(xml_data[i], minidom.Element):
                node_children = xml_data[i].childNodes
                child_node = node_children[0]
                if isinstance(child_node, minidom.Element):
                    match i:
                        case 0:
                            self.assertEqual("This is an xml tag", child_node.firstChild.nodeValue.strip())
                        case 1:
                            self.assertEqual("This is another xml tag", child_node.firstChild.nodeValue.strip())
                        case 2:
                            self.assertEqual("This is the final xml tag", child_node.firstChild.nodeValue.strip())
                        case _:
                            self.fail("Expected total tags ({0}) did not equal the actual total tags ({1})."
                                      .format(3, i+1))
                else:
                    self.fail("XML parsing has failed: inner tags cannot be interpreted")
            else:
                self.fail("XML parsing has failed: outer tags cannot be interpreted")

    def test_create_patient_from_xml(self):
        list_of_orders: list = reduce(list.__add__, parse_xml_ppc(
            sanitise_and_encode_text_from_file(consts.MOCK_PATIENT_XML,
                                               consts.PPC_SEPARATING_TAG, self.config)
        ))
        for order in list_of_orders:
            patient_object = create_patient_object_from_pillpack_data(order)
            if isinstance(patient_object, Models.PillpackPatient):
                self.assertEqual("Hogarth", patient_object.first_name)
                self.assertEqual("Hughes", patient_object.last_name)
                self.assertEqual(datetime.date.fromisoformat("1985-11-09"), patient_object.date_of_birth)
                self.assertEqual(2, len(patient_object.production_medications_dict))
            else:
                self.fail("Expected object of type {0}, but recieved {1}"
                          .format(type(Models.PillpackPatient),
                                  type(patient_object)))

    def test_create_medications_for_patient_from_xml(self):
        list_of_orders: list = reduce(list.__add__, parse_xml_ppc(
            sanitise_and_encode_text_from_file(consts.MOCK_PATIENT_XML,
                                               consts.PPC_SEPARATING_TAG, self.config)
        ))
        for order in list_of_orders:
            patient_object = create_patient_object_from_pillpack_data(order)
            patient_medications: dict = patient_object.production_medications_dict
            for medication_name in patient_medications.keys():
                medication: Models.Medication = patient_medications.get(medication_name)
                match medication.medication_name:
                    case "Aciclovir 400mg tablets":
                        self.assertEqual(42.0, medication.dosage)
                        self.assertEqual(datetime.date.fromisoformat("2024-07-16"), medication.start_date)
                    case "Co-trimoxazole 80mg/400mg tablets":
                        self.assertEqual(18.0, medication.dosage)
                        self.assertEqual(datetime.date.fromisoformat("2024-07-22"), medication.start_date)
                    case _:
                        self.fail("Medicine {0} did not match the given test medications. The incorrect information "
                                  "has been parsed from the XML")
            self.assertEqual(datetime.date.fromisoformat("2024-07-16"), patient_object.start_date)


if __name__ == '__main__':
    unittest.main()
