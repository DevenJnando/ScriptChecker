import unittest
from functools import reduce
from Functions import DocxGeneration
from TestConsts import populate_test_settings, load_test_settings, consts
from Functions.XML import sanitise_and_encode_text_from_file, parse_xml_ppc
from Functions.ModelBuilder import create_patient_object_from_pillpack_data


class KardexDocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        populate_test_settings()
        config = load_test_settings()
        list_of_orders: list = reduce(list.__add__, parse_xml_ppc(
            sanitise_and_encode_text_from_file(consts.MOCK_PATIENT_XML_2,
                                               consts.PPC_SEPARATING_TAG, config)
        ))
        for order in list_of_orders:
            cls.mock_patient = create_patient_object_from_pillpack_data(order)

    def test_populate_kardex_table(self):
        DocxGeneration.generate_kardex_doc_file(self.mock_patient,
                                                "Test Production",
                                                "C:\\Users\\Farmadosis\\Test Kardex File.docx")
        kardex = open("C:\\Users\\Farmadosis\\Test Kardex File.docx")
        self.assertIsNotNone(kardex)
        kardex.close()

    def test_populate_prn_list(self):
        DocxGeneration.generate_dispensation_list_doc_file(self.mock_patient,
                                                  "Test Production",
                                                  "C:\\Users\\Farmadosis\\Test PRN List.docx")
        prn_list = open("C:\\Users\\Farmadosis\\Test PRN List.docx")
        self.assertIsNotNone(prn_list)
        prn_list.close()


if __name__ == '__main__':
    unittest.main()
