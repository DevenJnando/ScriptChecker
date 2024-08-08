import unittest
import Functions.ConfigSingleton
from functools import reduce
from Functions import DocxGeneration
from TestConsts import populate_test_settings, load_test_settings, consts
from Functions.XML import sanitise_and_encode_text_from_file, parse_xml
from Functions.ModelBuilder import create_patient_object_from_pillpack_data


class KardexDocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        populate_test_settings()
        Functions.ConfigSingleton.config = load_test_settings()
        list_of_orders: list = reduce(list.__add__, parse_xml(
            sanitise_and_encode_text_from_file(consts.MOCK_PATIENT_XML_2,
                                               consts.PPC_SEPARATING_TAG)
        ))
        for order in list_of_orders:
            cls.mock_patient = create_patient_object_from_pillpack_data(order)

    def test_populate_kardex_table(self):
        DocxGeneration.generate_kardex_doc_file(self.mock_patient,
                                                "Test Production",
                                                "Test Kardex File.docx")
        kardex = open("Test Kardex File.docx")
        self.assertIsNotNone(kardex)
        kardex.close()


if __name__ == '__main__':
    unittest.main()
