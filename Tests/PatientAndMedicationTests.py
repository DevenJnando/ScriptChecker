import unittest
from functools import reduce
from TestConsts import consts, populate_test_settings, load_test_settings
import Models
import Functions
import datetime


class PatientAndMedicationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        populate_test_settings()
        Functions.config = load_test_settings()
        mock_prn_1: Models.Medication = Models.Medication("Not real",
                                                          28,
                                                          datetime.date.fromisoformat("2024-08-22")
                                                          )
        mock_prn_2: Models.Medication = Models.Medication("Not real either",
                                                          56,
                                                          datetime.date.fromisoformat("2024-07-23")
                                                          )
        mock_linked_medication: Models.Medication = Models.Medication("Fake link medication",
                                                                      42,
                                                                      datetime.date.fromisoformat("2024-07-16")
                                                                      )
        cls.mock_prns_and_ignored_meds = {
            "hogarth hughes 1985-11-09": {
                consts.PRN_KEY: {
                    "Not real": mock_prn_1,
                    "Not real either": mock_prn_2
                },
                consts.LINKED_MEDS_KEY: {
                    "Aciclovir 400mg tablets": mock_linked_medication
                }
            }
        }
        cls.list_of_orders: list = reduce(list.__add__, Functions._parse_xml(
            Functions._sanitise_and_encode_text_from_file(consts.MOCK_PATIENT_XML,
                                                          consts.PPC_SEPARATING_TAG)
        ))

    def test_retrieve_prns_and_linked_medications(self):
        for order in self.list_of_orders:
            patient_object = Functions._create_patient_object(order)
            patient_object = Functions.retrieve_prns_and_linked_medications(patient_object,
                                                                            self.mock_prns_and_ignored_meds)
            for i in range(len(patient_object.prn_medications_dict)):
                prn_medication = list(patient_object.prn_medications_dict.values())[i]
                if isinstance(prn_medication, Models.Medication):
                    match i:
                        case 0:
                            self.assertEqual("Not real", prn_medication.medication_name)
                            self.assertEqual(28, prn_medication.dosage)
                            self.assertEqual(datetime.date.fromisoformat("2024-08-22"), prn_medication.start_date)
                        case 1:
                            self.assertEqual("Not real either", prn_medication.medication_name)
                            self.assertEqual(56, prn_medication.dosage)
                            self.assertEqual(datetime.date.fromisoformat("2024-07-23"), prn_medication.start_date)
                        case _:
                            self.fail("Reading PRN medications has failed. Should have a dictionary of size {0}, "
                                      "but there were {1} elements in total".format(2, i+1))
                else:
                    self.fail("Reading PRN medications has failed. The element {0} should be of type {1}, "
                              "but was of type {2}".format(prn_medication, type(Models.Medication),
                                                           type(prn_medication)))
            for i in range(len(patient_object.linked_medications)):
                linked_medication = list(patient_object.linked_medications.values())[i]
                if isinstance(linked_medication, Models.Medication):
                    match i:
                        case 0:
                            self.assertEqual("Fake link medication", linked_medication.medication_name)
                            self.assertEqual(42, linked_medication.dosage)
                            self.assertEqual(datetime.date.fromisoformat("2024-07-16"), linked_medication.start_date)
                        case _:
                            self.fail("Reading Linked medications has failed. Should have a dictionary of size {0}, "
                                      "but there were {1} elements in total".format(2, i+1))
                else:
                    self.fail("Reading Linked medications has failed. The element {0} should be of type {1}, "
                              "but was of type {2}".format(linked_medication, type(Models.Medication),
                                                           type(linked_medication)))


if __name__ == '__main__':
    unittest.main()
