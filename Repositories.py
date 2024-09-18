import logging
import sys

from Models import PillpackPatient

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)


class CollectedPatients:
    def __init__(self):
        self.ready_to_produce_code = 0
        self.production_group_name = ""
        self.pillpack_patient_dict = {}
        self.all_patients = {}
        self.matched_patients = {}
        self.minor_mismatch_patients = {}
        self.severe_mismatch_patients = {}

    @staticmethod
    def __add_to_dict_of_patients(patient_to_add: PillpackPatient, dict_to_add_to: dict, name_of_dict: str):
        if dict_to_add_to.__contains__(patient_to_add.last_name.lower()):
            logging.info("{0} contains patients with last name {1}"
                         .format(name_of_dict, patient_to_add.last_name))
            patients_with_last_name: list = dict_to_add_to.get(patient_to_add.last_name.lower())
            patients_with_last_name.append(patient_to_add)
            dict_to_add_to[patient_to_add.last_name.lower()] = patients_with_last_name
            logging.info("Added patient {0} {1} to the dictionary {2}"
                         .format(patient_to_add.first_name, patient_to_add.last_name, name_of_dict))
        else:
            list_of_patients: list = [patient_to_add]
            dict_to_add_to[patient_to_add.last_name.lower()] = list_of_patients
            logging.info("{0} contains no patients with last name {1}. Created new list object with patient "
                         "{2} {1} as initial member"
                         .format(name_of_dict, patient_to_add.last_name, patient_to_add.first_name))

    @staticmethod
    def __remove_from_dict_of_patients(patient_to_remove: PillpackPatient, dict_to_remove_from: dict,
                                       name_of_dict: str):
        if dict_to_remove_from.__contains__(patient_to_remove.last_name.lower()):
            logging.info("{0} contains patients with last name {1}"
                         .format(name_of_dict, patient_to_remove.last_name))
            patients_with_last_name: list = dict_to_remove_from.get(patient_to_remove.last_name.lower())
            for i in range(len(patients_with_last_name)):
                patient = patients_with_last_name[i]
                if isinstance(patient, PillpackPatient):
                    if patient.__eq__(patient_to_remove):
                        patients_with_last_name.pop(i)
                        logging.info("Located patient {0} {1} in {2}. Patient has been removed from dictionary {2}"
                                     .format(patient_to_remove.first_name, patient_to_remove.last_name,
                                             name_of_dict))
                        break
            if len(patients_with_last_name) == 0:
                dict_to_remove_from.pop(patient_to_remove.last_name.lower())
                logging.info("No more patients with last name {0} exist within {1}. Removing last name key."
                             .format(patient_to_remove.last_name, name_of_dict))

    @staticmethod
    def __update_patient_dict(patient_dict: dict, patient_to_be_updated: PillpackPatient, name_of_dict: str):
        patient_is_updated = False
        if patient_dict.__contains__(patient_to_be_updated.last_name.lower()):
            logging.info("{0} contains patients with last name {1}"
                         .format(name_of_dict, patient_to_be_updated.last_name))
            patients_with_last_name: list = patient_dict.get(patient_to_be_updated.last_name.lower())
            for i in range(0, len(patients_with_last_name)):
                patient: PillpackPatient = patients_with_last_name[i]
                if patient.__eq__(patient_to_be_updated):
                    patients_with_last_name[i] = patient_to_be_updated
                    patient_dict[patient_to_be_updated.last_name.lower()] = patients_with_last_name
                    patient_is_updated = True
                    logging.info("Located patient {0} {1} in {2}. Patient information has been updated."
                                 .format(patient_to_be_updated.first_name, patient_to_be_updated.last_name,
                                         name_of_dict))
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
                         .format("All Patients", patient_to_add.last_name))
            patients_with_last_name: list = self.all_patients.get(patient_to_add.last_name.lower())
            patients_with_last_name.append(patient_wrapper)
            self.all_patients[patient_to_add.last_name.lower()] = patients_with_last_name
            logging.info("Added patient {0} {1} to the dictionary {2}"
                         .format(patient_to_add.first_name, patient_to_add.last_name, "All Patients"))
        else:
            list_of_wrappers: list = [patient_wrapper]
            self.all_patients[patient_to_add.last_name.lower()] = list_of_wrappers
            logging.info("{0} does not contain patients with last name {1}. Created a new list object with patient "
                         "{2} {1} as the initial member."
                         .format("All Patients", patient_to_add.last_name, patient_to_add.first_name))

    def add_pillpack_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.pillpack_patient_dict, "Pillpack Patients")

    def add_matched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.matched_patients, "Matched Patients")

    def add_minor_mismatched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.minor_mismatch_patients, "Minor Mismatch Patients")

    def add_severely_mismatched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.severe_mismatch_patients, "Severe Mismatch Patients")

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
                                             "All Patients"))
                        break
            if len(patients_with_last_name) == 0:
                self.all_patients.pop(patient_to_remove.last_name.lower())
                logging.info("No more patients with last name {0} exist within {1}. Removing last name key."
                             .format(patient_to_remove.last_name, "All Patients"))

    def remove_pillpack_patient(self, patient_to_remove: PillpackPatient):
        self.__remove_from_dict_of_patients(patient_to_remove, self.pillpack_patient_dict,
                                            "Pillpack Patients")

    def remove_matched_patient(self, patient_to_remove: PillpackPatient):
        self.__remove_from_dict_of_patients(patient_to_remove, self.matched_patients,
                                            "Matched Patients")

    def remove_minor_mismatched_patient(self, patient_to_remove: PillpackPatient):
        self.__remove_from_dict_of_patients(patient_to_remove, self.minor_mismatch_patients,
                                            "Minor Mismatched Patients")

    def remove_severely_mismatched_patient(self, patient_to_remove: PillpackPatient):
        self.__remove_from_dict_of_patients(patient_to_remove, self.severe_mismatch_patients,
                                            "Severe Mismatched Patients")

    def update_pillpack_patient_dict(self, patient_to_be_updated: PillpackPatient):
        return self.__update_patient_dict(self.pillpack_patient_dict, patient_to_be_updated,
                                          "Pillpack Patients")