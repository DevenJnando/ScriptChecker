import logging

from DataStructures.Models import PillpackPatient


"""

Module which contains the data objects which hold and persist model data in memory. The data structures are comprised 
of dictionaries which contain various patient and related medication information. There are static add and removal 
functions which are invoked later in the class.

"""


class CollectedPatients:
    """

    Class which contains all retrieved patient model data. Patients which match a scanned script completely are placed
    in the matched_patients dict, patients with slight inconsistencies are placed in minor_mismatch_patients and
    completely mismatched patients are placed in severe_mismatch_patients.
    """
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

        """
        Static method for adding a PillpackPatient object to any given directory. The name of the dictionary and the
        dictionary itself are provided as function arguments.

        PillpackPatient objects are stored in the dictionary
        in a list wrapper.

        If a patient with any given last name already exists in the specified dictionary then the
        PillpackPatient object would be appended to that list. Otherwise, a new list wrapper is created and the patient
        to be added is made the first element of that list.

        :param patient_to_add: The PillpackPatient object to be added to the dictionary
        :param dict_to_add_to: Dictionary where the PillpackPatient object shall be added to
        :param name_of_dict: Name of the dictionary. Used for logging purposes.
        :return: None
        """
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

        """
        Static method for removing a PillpackPatient object to any given directory. The name of the dictionary and the
        dictionary itself are provided as function arguments.

        PillpackPatient objects are stored in the dictionary
        in a list wrapper.

        If the length of the list wrapper is greater than zero, and the specified patient exists within the list, then
        it is removed. If the length of the list wrapper is exactly zero, this means there is only a single patient
        in the list. The entire list wrapper can therefore be removed in this case.

        :param patient_to_remove: The PillpackPatient object to be added to the dictionary
        :param dict_to_remove_from: Dictionary where the PillpackPatient object shall be added to
        :param name_of_dict: Name of the dictionary. Used for logging purposes.
        :return: None
        """
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

        """
        Static function which updates an already existing PillpackPatient object stored within a given dictionary.
        If the specified PillpackPatient object exists within the specified dictionary, then the old patient object
        is replaced with the new one, and reinserted in the same place in the list wrapper. A True statement is then
        returned.

        Otherwise, no action occurs and a False statement is returned.

        :param patient_dict: The dictionary to be updated
        :param patient_to_be_updated: The new PillpackPatient object which is to replace the old one if found
        :param name_of_dict: The name of the dictionary to be updated, used for logging purposes.
        :return: True statement if patient exists and is updated, False statement if no update occurs.
        """
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

        """
        Setter for the initial pillpack patient dictionary.
        :param patient_dict: the dictionary to be assigned to the class's pillpack_patient_dict field.
        :return: None
        """
        self.pillpack_patient_dict = patient_dict
        logging.info("Set patient pillpack dictionary as {0}".format(patient_dict))

    def add_patient(self, patient_to_add: PillpackPatient, status: str):

        """
        Function to wrap a newly added patient with their status. The status being whether they are matched, slightly
        mismatched or unknown.

        The wrapper is another dictionary object. This function is used exclusively to add to the complete dictionary of
        every single PillpackPatient object. This dictionary is used as a frame of reference for all other dictionaries
        to check the status of a patient and whether they have previously been added to any other dictionary.
        :param patient_to_add: PillpackPatient object to be added
        :param status: The status of the patient, being Unscanned, matched, minor mismatched, and unknown.
        :return: None
        """
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

        """
        Implementation of the static add_to_dict_of_patients function. Adds a patient to the dictionary of all
        production patients

        :param patient_to_add: PillpackPatient to be added to the dictionary
        :return: None
        """
        self.__add_to_dict_of_patients(patient_to_add, self.pillpack_patient_dict, "Pillpack Patients")

    def add_matched_patient(self, patient_to_add: PillpackPatient):

        """
        Implementation of the static add_to_dict_of_patients function. Adds a patient to the dictionary of matched
        patients

        :param patient_to_add: PillpackPatient to be added to the dictionary
        :return: None
        """
        self.__add_to_dict_of_patients(patient_to_add, self.matched_patients, "Matched Patients")

    def add_minor_mismatched_patient(self, patient_to_add: PillpackPatient):

        """
        Implementation of the static add_to_dict_of_patients function. Adds a patient to the dictionary of
        minor mismatched patients

        :param patient_to_add: PillpackPatient to be added to the dictionary
        :return: None
        """
        self.__add_to_dict_of_patients(patient_to_add, self.minor_mismatch_patients, "Minor Mismatch Patients")

    def add_severely_mismatched_patient(self, patient_to_add: PillpackPatient):

        """
        Implementation of the static add_to_dict_of_patients function. Adds a patient to the dictionary of severely
        mismatched patients

        :param patient_to_add: PillpackPatient to be added to the dictionary
        :return: None
        """
        self.__add_to_dict_of_patients(patient_to_add, self.severe_mismatch_patients, "Severe Mismatch Patients")

    def remove_patient(self, patient_to_remove: PillpackPatient):

        """
        Function to remove a patient wrapped with their status from the dictionary of all patients

        The patient is unwrapped and checked. If it matches the patient argument to be removed, then it is.

        If the length of the list wrapper is exactly zero, then no patients are still present within that wrapper and
        the key is removed. This is to prevent any phantom keys persisting in the dictionary which no longer point to
        any value.
        :return: None
        """
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

        """
        Implementation of the static remove_from_dict_of_patients function. Removes a patient from the pillpack
        production dictionary.

        :param patient_to_remove: PillpackPatient object to remove
        :return: None
        """
        self.__remove_from_dict_of_patients(patient_to_remove, self.pillpack_patient_dict,
                                            "Pillpack Patients")

    def remove_matched_patient(self, patient_to_remove: PillpackPatient):

        """
        Implementation of the static remove_from_dict_of_patients function. Removes a patient from the matched
        patients dictionary.

        :param patient_to_remove: PillpackPatient object to remove
        :return: None
        """
        self.__remove_from_dict_of_patients(patient_to_remove, self.matched_patients,
                                            "Matched Patients")

    def remove_minor_mismatched_patient(self, patient_to_remove: PillpackPatient):

        """
        Implementation of the static remove_from_dict_of_patients function. Removes a patient from the minor mismatched
        dictionary.

        :param patient_to_remove: PillpackPatient object to remove
        :return: None
        """
        self.__remove_from_dict_of_patients(patient_to_remove, self.minor_mismatch_patients,
                                            "Minor Mismatched Patients")

    def remove_severely_mismatched_patient(self, patient_to_remove: PillpackPatient):

        """
        Implementation of the static remove_from_dict_of_patients function. Removes a patient from the severe
        mismatched dictionary.

        :param patient_to_remove: PillpackPatient object to remove
        :return: None
        """
        self.__remove_from_dict_of_patients(patient_to_remove, self.severe_mismatch_patients,
                                            "Severe Mismatched Patients")

    def update_pillpack_patient_dict(self, patient_to_be_updated: PillpackPatient):

        """
        Implementation of the static update_patient_dict function. Updates a patient within the pillpack production
        dictionary.
        There are no update functions for the other dictionaries since all script information will need to be
        rescanned if any update to patient medical data occurs. Rather, the patient is removed entirely from all other
        dictionaries in another function.
        :param patient_to_be_updated: PillpackPatient object to update the old version
        :return: True statement if an update occurred successfully, False if no update occurred.
        """
        return self.__update_patient_dict(self.pillpack_patient_dict, patient_to_be_updated,
                                          "Pillpack Patients")
