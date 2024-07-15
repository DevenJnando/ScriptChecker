import datetime
import types

import sys
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

consts = types.SimpleNamespace()
consts.READY_TO_PRODUCE_CODE = 1
consts.NOTHING_TO_COMPARE = 2
consts.MISSING_MEDICATIONS = 3
consts.DO_NOT_PRODUCE = 4
consts.MANUALLY_CHECKED = 5
consts.PRN_KEY = "prns_dict"
consts.LINKED_MEDS_KEY = "linked_meds_dict"
consts.COLLECTED_PATIENTS_FILE = 'Patients.pk1'
consts.PRNS_AND_IGNORED_MEDICATIONS_FILE = 'PrnsAndIgnoredMeds.pk1'


class Medication:
    def __init__(self, medication_name: str, dosage: float, start_date: datetime):
        self.medication_name: str = medication_name
        self.dosage: float = dosage
        self.start_date: datetime = start_date

    def equals(self, comparator):
        if isinstance(comparator, Medication):
            dosage_hash = hash(self.dosage)
            comparator_dosage_hash = hash(comparator.dosage)
            if dosage_hash == comparator_dosage_hash:
                return True
            else:
                return False
        else:
            return False


class PillpackPatient:
    def __init__(self, first_name, last_name, date_of_birth):
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.date_of_birth: datetime.date = date_of_birth
        self.start_date: datetime = datetime.date.today()
        self.manually_checked_flag: bool = False
        self.ready_to_produce_code: int = 0
        self.medication_dict: dict = {}
        self.matched_medications_dict: dict = {}
        self.missing_medications_dict: dict = {}
        self.unknown_medications_dict: dict = {}
        self.incorrect_dosages_dict: dict = {}
        self.prn_medications_dict: dict = {}
        self.medications_to_ignore: dict = {}
        self.linked_medications: dict = {}

    def manually_checked(self, manually_checked: bool):
        self.manually_checked_flag = manually_checked

    def set_start_date(self, start_date: datetime):
        self.start_date = start_date

    def determine_ready_to_produce_code(self):
        if not self.manually_checked_flag:
            if len(self.unknown_medications_dict) > 0:
                self.ready_to_produce_code = consts.DO_NOT_PRODUCE
            elif len(self.incorrect_dosages_dict) > 0:
                self.ready_to_produce_code = consts.DO_NOT_PRODUCE
            elif len(self.missing_medications_dict) > 0:
                self.ready_to_produce_code = consts.MISSING_MEDICATIONS
            elif len(self.matched_medications_dict) == len(self.medication_dict):
                self.ready_to_produce_code = consts.READY_TO_PRODUCE_CODE
            else:
                self.ready_to_produce_code = consts.NOTHING_TO_COMPARE
        else:
            self.ready_to_produce_code = consts.MANUALLY_CHECKED

    @staticmethod
    def __add_to_dict_of_medications(medication_to_add: Medication, dict_to_add_to: dict):
        if not dict_to_add_to.__contains__(medication_to_add.medication_name):
            dict_to_add_to[medication_to_add.medication_name] = medication_to_add
            logging.info("Added medication {0} to dictionary {1}"
                         .format(medication_to_add.medication_name, dict_to_add_to))

    @staticmethod
    def __remove_from_dict_of_medications(medication_to_remove: Medication, dict_to_remove_from: dict):
        if dict_to_remove_from.__contains__(medication_to_remove.medication_name):
            dict_to_remove_from.pop(medication_to_remove.medication_name)
            logging.info("Removed medication {0} from dictionary {1}"
                         .format(medication_to_remove.medication_name, dict_to_remove_from))

    def add_medication_to_dict(self, med_to_be_added: Medication):
        self.__add_to_dict_of_medications(med_to_be_added, self.medication_dict)

    def remove_medication_from_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.medication_dict)

    def add_matched_medication_to_dict(self, med_to_be_added):
        self.__add_to_dict_of_medications(med_to_be_added, self.matched_medications_dict)

    def remove_matched_medication_from_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.matched_medications_dict)

    def add_missing_medication_to_dict(self, med_to_be_added):
        self.__add_to_dict_of_medications(med_to_be_added, self.missing_medications_dict)

    def remove_missing_medication_from_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.missing_medications_dict)

    def add_unknown_medication_to_dict(self, med_to_be_added):
        self.__add_to_dict_of_medications(med_to_be_added, self.unknown_medications_dict)

    def remove_unknown_medication_from_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.unknown_medications_dict)

    def add_incorrect_dosage_medication_to_dict(self, med_to_be_added: Medication):
        self.__add_to_dict_of_medications(med_to_be_added, self.incorrect_dosages_dict)

    def remove_incorrect_dosage_medication_from_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.incorrect_dosages_dict)

    def add_prn_medication_to_dict(self, med_to_be_added: Medication):
        self.__add_to_dict_of_medications(med_to_be_added, self.prn_medications_dict)

    def remove_prn_medication_from_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.prn_medications_dict)

    def add_medication_link(self, linking_med: Medication, med_to_be_linked: Medication):
        if not self.linked_medications.__contains__(linking_med.medication_name):
            if linking_med.dosage == med_to_be_linked.dosage:
                self.remove_unknown_medication_from_dict(linking_med)
                self.remove_missing_medication_from_dict(med_to_be_linked)
                self.add_matched_medication_to_dict(linking_med)
                self.linked_medications[linking_med.medication_name] = med_to_be_linked

    def remove_medication_link(self, medication_to_unlink: Medication):
        if self.linked_medications.__contains__(medication_to_unlink.medication_name):
            linked_medication: Medication = self.linked_medications[medication_to_unlink.medication_name]
            self.add_unknown_medication_to_dict(medication_to_unlink)
            self.add_missing_medication_to_dict(linked_medication)
            self.remove_matched_medication_from_dict(medication_to_unlink)
            self.linked_medications.pop(medication_to_unlink.medication_name)

    def add_medication_to_ignore_dict(self, med_to_be_added: Medication):
        self.__add_to_dict_of_medications(med_to_be_added, self.medications_to_ignore)
        self.remove_incorrect_dosage_medication_from_dict(med_to_be_added)
        self.remove_missing_medication_from_dict(med_to_be_added)
        self.add_matched_medication_to_dict(med_to_be_added)

    def remove_medication_from_ignore_dict(self, med_to_be_removed: Medication, med_with_correct_dosage: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.medications_to_ignore)
        self.remove_matched_medication_from_dict(med_to_be_removed)
        self.add_incorrect_dosage_medication_to_dict(med_to_be_removed)
        self.add_missing_medication_to_dict(med_with_correct_dosage)

    def __hash__(self):
        return hash((self.first_name, self.last_name, self.date_of_birth))

    def __eq__(self, other):
        return ((self.first_name, self.last_name, self.date_of_birth)
                == (other.first_name, other.last_name, other.date_of_birth))

    def __ne__(self, other):
        return not (self == other)


class CollectedPatients:
    def __init__(self):
        self.ready_to_produce_code = 0
        self.pillpack_patient_dict = {}
        self.all_patients = {}
        self.matched_patients = {}
        self.minor_mismatch_patients = {}
        self.severe_mismatch_patients = {}

    @staticmethod
    def __add_to_dict_of_patients(patient_to_add: PillpackPatient, dict_to_add_to: dict):
        if dict_to_add_to.__contains__(patient_to_add.last_name.lower()):
            logging.info("{0} contains patients with last name {1}"
                         .format(dict_to_add_to, patient_to_add.last_name))
            patients_with_last_name: list = dict_to_add_to.get(patient_to_add.last_name.lower())
            patients_with_last_name.append(patient_to_add)
            dict_to_add_to[patient_to_add.last_name.lower()] = patients_with_last_name
            logging.info("Added patient {0} {1} to the dictionary {2}"
                         .format(patient_to_add.first_name, patient_to_add.last_name, dict_to_add_to))
        else:
            list_of_patients: list = [patient_to_add]
            dict_to_add_to[patient_to_add.last_name.lower()] = list_of_patients
            logging.info("{0} contains no patients with last name {1}. Created new list object with patient "
                         "{2} {1} as initial member"
                         .format(dict_to_add_to, patient_to_add.last_name, patient_to_add.first_name))

    @staticmethod
    def __remove_from_dict_of_patients(patient_to_remove: PillpackPatient, dict_to_remove_from: dict):
        if dict_to_remove_from.__contains__(patient_to_remove.last_name.lower()):
            logging.info("{0} contains patients with last name {1}"
                         .format(dict_to_remove_from, patient_to_remove.last_name))
            patients_with_last_name: list = dict_to_remove_from.get(patient_to_remove.last_name.lower())
            for i in range(len(patients_with_last_name)):
                patient = patients_with_last_name[i]
                if isinstance(patient, PillpackPatient):
                    if patient.__eq__(patient_to_remove):
                        patients_with_last_name.pop(i)
                        logging.info("Located patient {0} {1} in {2}. Patient has been removed from dictionary {2}"
                                     .format(patient_to_remove.first_name, patient_to_remove.last_name,
                                             dict_to_remove_from))
                        break
            if len(patients_with_last_name) == 0:
                dict_to_remove_from.pop(patient_to_remove.last_name.lower())
                logging.info("No more patients with last name {0} exist within {1}. Removing last name key."
                             .format(patient_to_remove.last_name, dict_to_remove_from))

    @staticmethod
    def __update_patient_dict(patient_dict: dict, patient_to_be_updated: PillpackPatient):
        patient_is_updated = False
        if patient_dict.__contains__(patient_to_be_updated.last_name.lower()):
            logging.info("{0} contains patients with last name {1}"
                         .format(patient_dict, patient_to_be_updated.last_name))
            patients_with_last_name: list = patient_dict.get(patient_to_be_updated.last_name.lower())
            for i in range(0, len(patients_with_last_name)):
                patient: PillpackPatient = patients_with_last_name[i]
                if patient.__eq__(patient_to_be_updated):
                    patients_with_last_name[i] = patient_to_be_updated
                    patient_dict[patient_to_be_updated.last_name.lower()] = patients_with_last_name
                    patient_is_updated = True
                    logging.info("Located patient {0} {1} in {2}. Patient information has been updated."
                                 .format(patient_to_be_updated.first_name, patient_to_be_updated.last_name, patient_dict))
        return patient_is_updated

    def set_pillpack_patient_dict(self, patient_dict: dict):
        self.pillpack_patient_dict = patient_dict
        logging.info("Set patient pillpack dictionary as {0}".format(patient_dict))

    def add_patient(self, patient_to_add: PillpackPatient, status: str):
        patient_wrapper: dict = {
            "PatientObject": patient_to_add,
            "Status": status
        }
        if self.all_patients.__contains__(patient_to_add.last_name.lower()):
            logging.info("{0} contains patients with last name {1}"
                         .format(self.all_patients, patient_to_add.last_name))
            patients_with_last_name: list = self.all_patients.get(patient_to_add.last_name.lower())
            patients_with_last_name.append(patient_wrapper)
            self.all_patients[patient_to_add.last_name.lower()] = patients_with_last_name
            logging.info("Added patient {0} {1} to the dictionary {2}"
                         .format(patient_to_add.first_name, patient_to_add.last_name, self.all_patients))
        else:
            list_of_wrappers: list = [patient_wrapper]
            self.all_patients[patient_to_add.last_name.lower()] = list_of_wrappers
            logging.info("{0} does not contain patients with last name {1}. Created a new list object with patient "
                         "{2} {1} as the initial member."
                         .format(self.all_patients, patient_to_add.last_name, patient_to_add.first_name))

    def add_matched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.matched_patients)

    def add_minor_mismatched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.minor_mismatch_patients)

    def add_severely_mismatched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.severe_mismatch_patients)

    def remove_patient(self, patient_to_remove: PillpackPatient):
        if self.all_patients.__contains__(patient_to_remove.last_name.lower()):
            logging.info("{0} contains patients with last name {1}"
                         .format(self.all_patients, patient_to_remove.last_name))
            patients_with_last_name: list = self.all_patients.get(patient_to_remove.last_name.lower())
            for i in range(len(patients_with_last_name)):
                patient = patients_with_last_name[i]["PatientObject"]
                if isinstance(patient, PillpackPatient):
                    print(patient.first_name, " ", patient_to_remove.first_name)
                    if patient.__eq__(patient_to_remove):
                        patients_with_last_name.pop(i)
                        logging.info("Located patient {0} {1} in dictionary {2}. Patient has been removed."
                                     .format(patient_to_remove.first_name, patient_to_remove.last_name,
                                             self.all_patients))
                        break
            if len(patients_with_last_name) == 0:
                self.all_patients.pop(patient_to_remove.last_name.lower())
                logging.info("No more patients with last name {0} exist within {1}. Removing last name key."
                             .format(patient_to_remove.last_name, self.all_patients))

    def remove_pillpack_patient(self, patient_to_remove: PillpackPatient):
        self.__remove_from_dict_of_patients(patient_to_remove, self.pillpack_patient_dict)

    def remove_matched_patient(self, patient_to_remove: PillpackPatient):
        self.__remove_from_dict_of_patients(patient_to_remove, self.matched_patients)

    def remove_minor_mismatched_patient(self, patient_to_remove: PillpackPatient):
        self.__remove_from_dict_of_patients(patient_to_remove, self.minor_mismatch_patients)

    def remove_severely_mismatched_patient(self, patient_to_remove: PillpackPatient):
        self.__remove_from_dict_of_patients(patient_to_remove, self.severe_mismatch_patients)

    def update_pillpack_patient_dict(self, patient_to_be_updated: PillpackPatient):
        return self.__update_patient_dict(self.pillpack_patient_dict, patient_to_be_updated)

    def update_matched_patients_dict(self, patient_to_be_updated: PillpackPatient):
        return self.__update_patient_dict(self.matched_patients, patient_to_be_updated)

    def update_minor_mismatched_patients_dict(self, patient_to_be_updated: PillpackPatient):
        return self.__update_patient_dict(self.minor_mismatch_patients, patient_to_be_updated)

    def update_severe_mismatched_patients_dict(self, patient_to_be_updated: PillpackPatient):
        return self.__update_patient_dict(self.severe_mismatch_patients, patient_to_be_updated)
