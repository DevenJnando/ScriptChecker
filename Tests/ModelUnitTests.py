import datetime
import unittest

import Functions
import Models
from TestConsts import consts, load_test_settings, populate_test_settings


class ModelUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        populate_test_settings()
        Functions.config = load_test_settings()
        cls.mock_patient = Models.PillpackPatient("Real", "Patient", datetime.date.today())
        cls.mock_patient2 = Models.PillpackPatient("Totally", "Real", datetime.date.today())
        cls.mock_patient3 = Models.PillpackPatient("Trustme", "Bro", datetime.date.today())
        cls.mock_patient4 = Models.PillpackPatient("Don't", "Worry", datetime.date.today())
        cls.mock_patient5 = Models.PillpackPatient("Actually", "Real", datetime.date.today())
        cls.mock_medicine1 = Models.Medication("First medication", 28, datetime.date.today())
        cls.mock_medicine2 = Models.Medication("Second medication", 28, datetime.date.today())
        cls.mock_medicine3 = Models.Medication("Third medication", 56, datetime.date.today())
        cls.mock_collected_patients = Models.CollectedPatients()
        cls.mock_collected_patients.add_pillpack_patient(cls.mock_patient)
        cls.mock_collected_patients.add_pillpack_patient(cls.mock_patient2)
        cls.mock_collected_patients.add_pillpack_patient(cls.mock_patient3)
        cls.mock_collected_patients.add_pillpack_patient(cls.mock_patient4)
        cls.mock_collected_patients.add_pillpack_patient(cls.mock_patient5)

    def test_dosage_equality_check(self):
        self.assertTrue(self.mock_medicine1.dosage_equals(self.mock_medicine2))
        self.assertFalse(self.mock_medicine1.dosage_equals(self.mock_medicine3))

    def test_add_and_remove_production_medication(self):
        self.mock_patient.add_medication_to_production_dict(self.mock_medicine1)
        self.assertEqual(self.mock_medicine1, self.mock_patient.production_medications_dict.get("First medication"))
        self.assertEqual(1, len(self.mock_patient.production_medications_dict))
        self.mock_patient.remove_medication_from_production_dict(self.mock_medicine1)
        self.assertEqual(0, len(self.mock_patient.production_medications_dict))

    def test_add_and_remove_matched_medication(self):
        self.mock_patient.add_medication_to_matched_dict(self.mock_medicine1)
        self.assertEqual(self.mock_medicine1, self.mock_patient.matched_medications_dict.get("First medication"))
        self.assertEqual(1, len(self.mock_patient.matched_medications_dict))
        self.mock_patient.remove_medication_from_matched_dict(self.mock_medicine1)
        self.assertEqual(0, len(self.mock_patient.matched_medications_dict))

    def test_add_and_remove_missing_medication(self):
        self.mock_patient.add_medication_to_missing_dict(self.mock_medicine2)
        self.assertEqual(self.mock_medicine2, self.mock_patient.missing_medications_dict.get("Second medication"))
        self.assertEqual(1, len(self.mock_patient.missing_medications_dict))
        self.mock_patient.remove_medication_from_missing_dict(self.mock_medicine2)
        self.assertEqual(0, len(self.mock_patient.missing_medications_dict))

    def test_add_and_remove_unknown_medication(self):
        self.mock_patient.add_medication_to_unknown_dict(self.mock_medicine3)
        self.assertEqual(self.mock_medicine3, self.mock_patient.unknown_medications_dict.get("Third medication"))
        self.assertEqual(1, len(self.mock_patient.unknown_medications_dict))
        self.mock_patient.remove_medication_from_unknown_dict(self.mock_medicine3)
        self.assertEqual(0, len(self.mock_patient.unknown_medications_dict))

    def test_add_and_remove_prn_medication(self):
        self.mock_patient.add_medication_to_prn_dict(self.mock_medicine1)
        self.assertEqual(self.mock_medicine1, self.mock_patient.prn_medications_dict.get("First medication"))
        self.assertEqual(1, len(self.mock_patient.prn_medications_dict))
        self.mock_patient.remove_medication_from_prn_dict(self.mock_medicine1)
        self.assertEqual(0, len(self.mock_patient.prn_medications_dict))

    def test_add_and_remove_incorrect_dosage_medication(self):
        self.mock_patient.add_medication_to_incorrect_dosage_dict(self.mock_medicine1)
        self.assertEqual(self.mock_medicine1, self.mock_patient.incorrect_dosages_dict.get("First medication"))
        self.assertEqual(1, len(self.mock_patient.incorrect_dosages_dict))
        self.mock_patient.remove_medication_from_incorrect_dosage_dict(self.mock_medicine1)
        self.assertEqual(0, len(self.mock_patient.incorrect_dosages_dict))

    def test_create_link(self):
        self.mock_patient.add_medication_to_production_dict(self.mock_medicine1)
        self.mock_patient.add_medication_to_missing_dict(self.mock_medicine2)
        self.mock_patient.add_medication_to_unknown_dict(self.mock_medicine1)
        self.mock_patient.add_medication_link(self.mock_medicine1, self.mock_medicine2)
        self.assertEqual(self.mock_medicine2, self.mock_patient.linked_medications.get("First medication"))
        self.assertEqual(1, len(self.mock_patient.linked_medications))
        self.assertEqual(0, len(self.mock_patient.missing_medications_dict))
        self.assertEqual(0, len(self.mock_patient.unknown_medications_dict))

    def test_set_production_patient_dict(self):
        self.assertEqual(4, len(self.mock_collected_patients.pillpack_patient_dict))
        self.assertEqual(1, len(self.mock_collected_patients.pillpack_patient_dict.get("Patient".lower())))
        self.assertEqual(2, len(self.mock_collected_patients.pillpack_patient_dict.get("Real".lower())))
        self.assertEqual(1, len(self.mock_collected_patients.pillpack_patient_dict.get("Bro".lower())))
        self.assertEqual(1, len(self.mock_collected_patients.pillpack_patient_dict.get("Worry".lower())))

    def test_add_patients_to_wrapped_dict(self):
        for patient_list in self.mock_collected_patients.pillpack_patient_dict.values():
            if isinstance(patient_list, list):
                for patient in patient_list:
                    self.mock_collected_patients.add_patient(patient, consts.PERFECT_MATCH)
        self.assertEqual(1, len(self.mock_collected_patients.all_patients.get("Patient".lower())))
        self.assertEqual(2, len(self.mock_collected_patients.all_patients.get("Real".lower())))
        self.assertEqual(1, len(self.mock_collected_patients.all_patients.get("Bro".lower())))
        self.assertEqual(1, len(self.mock_collected_patients.all_patients.get("Worry".lower())))

    def test_add_update_and_remove_pillpack_production_patient(self):
        patient_to_add: Models.PillpackPatient = Models.PillpackPatient("New", "Guy",
                                                                        datetime.date.fromisoformat("1988-08-10"))
        medication_to_add: Models.Medication = Models.Medication("It's a medication!", 28, datetime.date.today())
        self.assertEqual(None, self.mock_collected_patients.pillpack_patient_dict.get("Guy".lower()))
        self.mock_collected_patients.add_pillpack_patient(patient_to_add)
        self.assertEqual(1, len(self.mock_collected_patients.pillpack_patient_dict.get("Guy".lower())))
        patient_to_add.add_medication_to_production_dict(medication_to_add)
        patient_to_add.first_name = "Not so new"
        self.mock_collected_patients.update_pillpack_patient_dict(patient_to_add)
        updated_patient: Models.PillpackPatient = self.mock_collected_patients.pillpack_patient_dict.get("Guy".lower())[0]
        self.assertEqual("Not so new", updated_patient.first_name)
        self.assertEqual(1, len(updated_patient.production_medications_dict))
        self.mock_collected_patients.remove_pillpack_patient(patient_to_add)
        self.assertEqual(None, self.mock_collected_patients.pillpack_patient_dict.get("Guy".lower()))

    def test_add_and_remove_matched_patient(self):
        patient_to_add: Models.PillpackPatient = Models.PillpackPatient("New", "Guy",
                                                                        datetime.date.fromisoformat("1988-08-10"))
        self.assertEqual(None, self.mock_collected_patients.matched_patients.get("Guy".lower()))
        self.mock_collected_patients.add_matched_patient(patient_to_add)
        self.assertEqual(1, len(self.mock_collected_patients.matched_patients.get("Guy".lower())))
        self.mock_collected_patients.remove_matched_patient(patient_to_add)
        self.assertEqual(None, self.mock_collected_patients.matched_patients.get("Guy".lower()))

    def test_add_and_remove_minor_mismatched_patient(self):
        patient_to_add: Models.PillpackPatient = Models.PillpackPatient("New", "Guy",
                                                                        datetime.date.fromisoformat("1988-08-10"))
        self.assertEqual(None, self.mock_collected_patients.minor_mismatch_patients.get("Guy".lower()))
        self.mock_collected_patients.add_minor_mismatched_patient(patient_to_add)
        self.assertEqual(1, len(self.mock_collected_patients.minor_mismatch_patients.get("Guy".lower())))
        self.mock_collected_patients.remove_minor_mismatched_patient(patient_to_add)
        self.assertEqual(None, self.mock_collected_patients.minor_mismatch_patients.get("Guy".lower()))

    def test_add_and_remove_severe_mismatched_patient(self):
        patient_to_add: Models.PillpackPatient = Models.PillpackPatient("New", "Guy",
                                                                        datetime.date.fromisoformat("1988-08-10"))
        self.assertEqual(None, self.mock_collected_patients.severe_mismatch_patients.get("Guy".lower()))
        self.mock_collected_patients.add_severely_mismatched_patient(patient_to_add)
        self.assertEqual(1, len(self.mock_collected_patients.severe_mismatch_patients.get("Guy".lower())))
        self.mock_collected_patients.remove_severely_mismatched_patient(patient_to_add)
        self.assertEqual(None, self.mock_collected_patients.severe_mismatch_patients.get("Guy".lower()))


if __name__ == '__main__':
    unittest.main()
