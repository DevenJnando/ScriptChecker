import datetime
import unittest
from xml.dom import minidom

from PIL.Image import Image

from DataStructures.Models import PillpackPatient, Medication
from TestConsts import consts, load_test_settings, populate_test_settings
from Functions.XML import scan_script, encode_to_datamatrix, encode_medications_to_xml


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        populate_test_settings()
        cls.config = load_test_settings()
        cls.mock_patient = PillpackPatient("John", "Thomas", "1999-04-04",
                                           title="Mr",
                                           middle_name="John",
                                           address="42 Poopypants lane",
                                           healthcare_no="69420",
                                           postcode="BT69 420",
                                           script_no="00001",
                                           surgery="Deez Nuts Medical Practice",
                                           surgery_address="311 Wobblybollocks Drive",
                                           surgery_postcode="BT9 KMA",
                                           doctor_id_no="696969",
                                           doctor_name="Dr. Hu",
                                           surgery_id_no="5urg3ry",
                                           script_id="5cr1pt",
                                           script_issuer="Me",
                                           script_date=str(datetime.date.today()))
        cls.mock_medication_1 = Medication("Medication", 28.0, datetime.date.today(),
                                           doctors_orders="Orders",
                                           code="11111111",
                                           disp_code="0o00000101010101",
                                           med_type="Capsule"
                                           )
        cls.mock_medication_2 = Medication("Medication2", 28.0, datetime.date.today(),
                                           doctors_orders="Orders2",
                                           code="111111112222",
                                           disp_code="222222",
                                           med_type="Tablet"
                                           )
        cls.mock_medication_3 = Medication("Medication3", 28.0, datetime.date.today(),
                                           doctors_orders="Orders3",
                                           code="23234234",
                                           disp_code="25456456",
                                           med_type="Tablussy"
                                           )
        cls.mock_medication_4 = Medication("Medication4", 28.0, datetime.date.today(),
                                           doctors_orders="Orders",
                                           code="11111111",
                                           disp_code="0o00000101010101",
                                           med_type="Capsule"
                                           )
        cls.mock_medication_5 = Medication("Medication5", 28.0, datetime.date.today(),
                                           doctors_orders="Orders2",
                                           code="111111112222",
                                           disp_code="222222",
                                           med_type="Tablet"
                                           )
        cls.mock_medication_6 = Medication("Medication6", 28.0, datetime.date.today(),
                                           doctors_orders="Orders3",
                                           code="23234234",
                                           disp_code="25456456",
                                           med_type="Tablussy"
                                           )
        cls.mock_medication_7 = Medication("Medication7", 28.0, datetime.date.today(),
                                           doctors_orders="Orders",
                                           code="11111111",
                                           disp_code="0o00000101010101",
                                           med_type="Capsule"
                                           )
        cls.mock_medication_8 = Medication("Medication8", 28.0, datetime.date.today(),
                                           doctors_orders="Orders2",
                                           code="111111112222",
                                           disp_code="222222",
                                           med_type="Tablet"
                                           )
        cls.mock_medication_9 = Medication("Medication9", 28.0, datetime.date.today(),
                                           doctors_orders="Orders3",
                                           code="23234234",
                                           disp_code="25456456",
                                           med_type="Tablussy"
                                           )
        cls.mock_medication_10 = Medication("Medication10", 28.0, datetime.date.today(),
                                            doctors_orders="Orders",
                                            code="11111111",
                                            disp_code="0o00000101010101",
                                            med_type="Capsule"
                                            )
        cls.mock_medication_11 = Medication("Medication11", 28.0, datetime.date.today(),
                                            doctors_orders="Orders2",
                                            code="111111112222",
                                            disp_code="222222",
                                            med_type="Tablet"
                                            )
        cls.mock_medication_12 = Medication("Medication12", 28.0, datetime.date.today(),
                                            doctors_orders="Orders3",
                                            code="23234234",
                                            disp_code="25456456",
                                            med_type="Tablussy"
                                            )
        cls.mock_medication_13 = Medication("Medication13", 28.0, datetime.date.today(),
                                            doctors_orders="Orders",
                                            code="11111111",
                                            disp_code="0o00000101010101",
                                            med_type="Capsule"
                                            )
        cls.mock_medication_14 = Medication("Medication14", 28.0, datetime.date.today(),
                                            doctors_orders="Orders2",
                                            code="111111112222",
                                            disp_code="222222",
                                            med_type="Tablet"
                                            )
        cls.mock_medication_15 = Medication("Medication15", 28.0, datetime.date.today(),
                                            doctors_orders="Orders3",
                                            code="23234234",
                                            disp_code="25456456",
                                            med_type="Tablussy"
                                            )
        cls.mock_medication_16 = Medication("Medication16", 28.0, datetime.date.today(),
                                            doctors_orders="Orders",
                                            code="11111111",
                                            disp_code="0o00000101010101",
                                            med_type="Capsule"
                                            )
        cls.mock_medication_17 = Medication("Medication17", 28.0, datetime.date.today(),
                                            doctors_orders="Orders2",
                                            code="111111112222",
                                            disp_code="222222",
                                            med_type="Tablet"
                                            )
        cls.mock_medication_18 = Medication("Medication18", 28.0, datetime.date.today(),
                                            doctors_orders="Orders3",
                                            code="23234234",
                                            disp_code="25456456",
                                            med_type="Tablussy"
                                            )
        cls.mock_medication_19 = Medication("Medication19", 28.0, datetime.date.today(),
                                            doctors_orders="Orders",
                                            code="11111111",
                                            disp_code="0o00000101010101",
                                            med_type="Capsule"
                                            )
        cls.mock_medication_20 = Medication("Medication20", 28.0, datetime.date.today(),
                                            doctors_orders="Orders2",
                                            code="111111112222",
                                            disp_code="222222",
                                            med_type="Tablet"
                                            )
        cls.mock_medication_21 = Medication("Medication21", 28.0, datetime.date.today(),
                                            doctors_orders="Orders3",
                                            code="23234234",
                                            disp_code="25456456",
                                            med_type="Tablussy"
                                            )
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

    def test_encode_prn_medications(self):
        self.mock_patient.add_medication_to_prns_for_current_cycle(self.mock_medication_1)
        self.mock_patient.add_medication_to_prns_for_current_cycle(self.mock_medication_2)
        self.mock_patient.add_medication_to_prns_for_current_cycle(self.mock_medication_3)
        encoded_scripts: list = encode_medications_to_xml(self.mock_patient,
                                                          self.mock_patient.prns_for_current_cycle,
                                                          "(PRN)")
        for script in encoded_scripts:
            print(script)
        self.assertIsNotNone(encoded_scripts)

    def test_encode_matched_medications(self):
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_1)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_2)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_3)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_4)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_5)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_6)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_7)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_8)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_9)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_10)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_11)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_12)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_13)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_14)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_15)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_16)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_17)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_18)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_19)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_20)
        self.mock_patient.add_medication_to_matched_dict(self.mock_medication_21)
        encoded_scripts: list = encode_medications_to_xml(self.mock_patient,
                                                          list(self.mock_patient.matched_medications_dict.values()),
                                                          "(Pillpack)")
        for script in encoded_scripts:
            print(script)
        self.assertIsNotNone(encoded_scripts)

    def test_encode_prns_to_datamatrix(self):
        self.mock_patient.add_medication_to_prns_for_current_cycle(self.mock_medication_1)
        self.mock_patient.add_medication_to_prns_for_current_cycle(self.mock_medication_2)
        self.mock_patient.add_medication_to_prns_for_current_cycle(self.mock_medication_3)
        encoded_scripts: list = encode_medications_to_xml(self.mock_patient,
                                                          self.mock_patient.prns_for_current_cycle,
                                                          "(PRN)")
        for script in encoded_scripts:
            encoded_image: Image = encode_to_datamatrix(script)
            self.assertIsNotNone(encoded_image)


if __name__ == '__main__':
    unittest.main()
