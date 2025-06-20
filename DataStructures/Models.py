import datetime
import types
import logging

"""

Module which contains the models/structures which will hold relevant application data. Mutation functions and basic
read/write functions are present within each Model class, as well as some hash functions and comparison operations.

"""

consts = types.SimpleNamespace()
consts.READY_TO_PRODUCE_CODE = 1
consts.NOTHING_TO_COMPARE = 2
consts.MISSING_MEDICATIONS = 3
consts.DO_NOT_PRODUCE = 4
consts.MANUALLY_CHECKED = 5
consts.PRN_KEY = "prns_dict"
consts.LINKED_MEDS_KEY = "linked_meds_dict"
consts.COLLECTED_PATIENTS_FILE = '../Application/Patients.pk1'
consts.PRNS_AND_LINKED_MEDICATIONS_FILE = '../Application/PrnsAndLinkedMeds.pk1'


class Medication:
    """
    Class which defines the fields, attributes and operations for the Medication data structure. A Medication object
    requires a name, a dosage and a start date at bare minimum in order to be instantiated.

    If using the kardex generation or dispensation list generation features, doctor's orders, the script code,
    dispensation code and the medication type (tablet/capsule) also need to be provided.
    """

    def __init__(self, medication_name: str, dosage: float, start_date: datetime,
                 doctors_orders: str = None,
                 code: str = None,
                 disp_code: str = None,
                 med_type: str = None):
        """
        The constructor for the Medication Class. Medication name, dosage and start date are all mandatory fields.
        Everything else is optional.

        :param medication_name: Name of the medication
        :param dosage: The dosage to be taken for the current cycle
        :param start_date: Start date of the current cycle
        :param doctors_orders: Any additional information provided by the doctor on the RX
        :param code: The script code the medication is from
        :param disp_code: The dispensation code of the medication
        :param med_type: The type of medication being taken (tablet/capsule)
        """
        self.medication_name: str = medication_name
        self.doctors_orders: str = doctors_orders
        self.code: str = code
        self.disp_code: str = disp_code
        self.med_type: str = med_type
        self.dosage: float = dosage
        self.start_date: datetime = start_date
        self.morning_dosage = None
        self.afternoon_dosage = None
        self.evening_dosage = None
        self.night_dosage = None

    def __hash__(self):
        return hash((self.medication_name, self.dosage))

    def __eq__(self, other):
        if isinstance(other, Medication):
            if self.__hash__() == other.__hash__():
                return True
            else:
                return False
        else:
            return False

    def dosage_equals(self, comparator):
        """
        Function to check that this instance of a Medication object's dosage is equal to another Medication object's
        dosage.

        :param comparator: The Medication object to have its dosage checked against this Medication object
        :return: Returns a boolean, True if it matches and False if it doesn't
        """
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
    """

    Class which defines the fields, attributes and operations of the PillpackPatient data structure. A PillpackPatient
    object requires a first name, last name and a date of birth at bare minimum to be instantiated.

    If using the kardex/dispensation list generation features, various other details will be obtained from any
    scanned in scripts. If there are no scripts scanned in, then these details will have to be entered by the user
    manually.
    """

    def __init__(self, first_name, last_name, date_of_birth,
                 title: str = None,
                 middle_name: str = None,
                 address: str = None,
                 healthcare_no: str = None,
                 postcode: str = None,
                 script_no: str = "0",
                 surgery: str = None,
                 surgery_address: str = None,
                 surgery_postcode: str = None,
                 doctor_id_no: str = "000000",
                 doctor_name: str = None,
                 surgery_id_no: str = "Z00000",
                 script_id: str = "0000000000000000000",
                 script_issuer: str = None,
                 script_date: str = datetime.date.today()
                 ):
        """
        The constructor for the PillpackPatient class. The mandatory fields for instantiation are the first name,
        last name and date of birth. Every other piece of information will be taken from a doctor prescribed script
        which is scanned in at another place in the application. The information can also be entered manually.

        The constructor also defines a set of dictionaries which contain production medications, correctly matched
        medications, missing medications, unknown medications, incorrectly dosed medications, all known PRN medications,
        PRN medications for this current cycle only, ignored problem medications and equivalent medications
        respectively.

        :param first_name: First name of the patient
        :param last_name: Last name of the patient
        :param date_of_birth: Date of birth of the patient
        :param title: Optional title of the Patient (e.g. Mr. Mrs. Ms. Miss, Master, etc.)
        :param middle_name: Optional middle name of the patient
        :param address: Optional address of the patient
        :param healthcare_no: Optional healthcare number of the patient
        :param postcode: Optional Postcode of the patient
        :param script_no: Optional script number taken from a scanned script (e.g. Script 1 of 4)
        :param surgery: Optional surgery of the patient
        :param surgery_address: Optional address of the patient's surgery
        :param surgery_postcode: Optional postcode of the patient's surgery
        :param doctor_id_no: Optional ID number of the prescribing doctor taken from a scanned script
        :param doctor_name: Optional name of the prescribing doctor
        :param surgery_id_no: Optional ID number of the surgery taken from a scanned script
        :param script_id: Optional ID number of the scanned script
        :param script_issuer: Optional script issuer taken from a scanned script
        :param script_date: Optional date a scanned script has been issued
        """
        self.title: str = title
        self.first_name: str = first_name
        self.middle_name: str = middle_name
        self.last_name: str = last_name
        self.healthcare_no: str = healthcare_no
        self.date_of_birth: datetime.date = date_of_birth
        self.start_date: datetime = datetime.date.today()
        self.surgery: str = surgery
        self.address: str = address
        self.postcode: str = postcode
        self.script_no: str = script_no
        self.surgery_address: str = surgery_address
        self.surgery_postcode: str = surgery_postcode
        self.doctor_id_no: str = doctor_id_no
        self.doctor_name: str = doctor_name
        self.surgery_id_no: str = surgery_id_no
        self.script_id: str = script_id
        self.script_issuer: str = script_issuer
        self.script_date: str = script_date
        self.manually_checked_flag: bool = False
        self.ready_to_produce_code: int = 0
        self.production_medications_dict: dict = {}
        self.matched_medications_dict: dict = {}
        self.missing_medications_dict: dict = {}
        self.unknown_medications_dict: dict = {}
        self.incorrect_dosages_dict: dict = {}
        self.prn_medications_dict: dict = {}
        self.prns_for_current_cycle: list = []
        self.medications_to_ignore: dict = {}
        self.linked_medications: dict = {}

    def manually_checked(self, manually_checked: bool):
        """
        Function which sets the manually checked flag to True or False. If the flag is True, this overrides all other
        behaviours and the instantiated PillpackPatient with a True manually checked flag will always be considered
        ready to produce.

        :param manually_checked: True or False boolean argument
        :return: None
        """
        self.manually_checked_flag = manually_checked

    def set_start_date(self, start_date: datetime):
        """
        Setter which defines the PillpackPatient's start date for their full medication cycle.

        :param start_date: The datetime object which defines their start date
        :return: None
        """
        self.start_date = start_date

    def determine_ready_to_produce_code(self):
        """
        Function which determines the PillpackPatient's production code.

        :return: None
        """
        if not self.manually_checked_flag:
            if len(self.unknown_medications_dict) > 0:
                self.ready_to_produce_code = consts.DO_NOT_PRODUCE
            elif len(self.incorrect_dosages_dict) > 0:
                self.ready_to_produce_code = consts.DO_NOT_PRODUCE
            elif len(self.missing_medications_dict) > 0:
                self.ready_to_produce_code = consts.MISSING_MEDICATIONS
            elif len(self.matched_medications_dict) == len(self.production_medications_dict):
                self.ready_to_produce_code = consts.READY_TO_PRODUCE_CODE
            else:
                self.ready_to_produce_code = consts.NOTHING_TO_COMPARE
        else:
            self.ready_to_produce_code = consts.MANUALLY_CHECKED

    @staticmethod
    def __add_to_dict_of_medications(medication_to_add: Medication, dict_to_add_to: dict,
                                     name_of_dict: str):
        """
        Static function which provides generic logic to add a Medication object to an arbitrary dictionary. This
        function will be implemented elsewhere and the dictionary to add a Medication object to will be defined there.

        :param medication_to_add: The Medication to add to the arbitrary dictionary
        :param dict_to_add_to: The dictionary for the Medication object to be added to
        :param name_of_dict: The name of the dictionary (only used for logging purposes to improve readability)
        :return: None
        """
        if isinstance(medication_to_add, Medication):
            if not dict_to_add_to.__contains__(medication_to_add.medication_name):
                dict_to_add_to[medication_to_add.medication_name] = medication_to_add
                logging.info("Added medication {0} to dictionary {1}"
                             .format(medication_to_add.medication_name, name_of_dict))

    @staticmethod
    def __remove_from_dict_of_medications(medication_to_remove: Medication, dict_to_remove_from: dict,
                                          name_of_dict: str):
        """
        Static function which provides generic logic to remove a Medication object from an arbitrary dictionary. This
        function will be implemented elsewhere and the dictionary to remove a Medication object from will be defined
        there.

        :param medication_to_remove: The Medication to remove from the arbitrary dictionary
        :param dict_to_remove_from: The dictionary for the Medication object to be removed from
        :param name_of_dict: The name of the dictionary (only used for logging purposes to improve readability)
        :return: None
        """
        if isinstance(medication_to_remove, Medication):
            if dict_to_remove_from.__contains__(medication_to_remove.medication_name):
                dict_to_remove_from.pop(medication_to_remove.medication_name)
                logging.info("Removed medication {0} from dictionary {1}"
                             .format(medication_to_remove.medication_name, name_of_dict))

    def add_all_missing_medications(self):
        """
        Iterates through the production medications dictionary and adds any medications which are not accounted for
        either through being already matched, having incorrect dosages ignored, or being attributed to another
        medication to the missing medications dictionary.
        :return: None
        """
        for medication in self.production_medications_dict.keys():
            substring_results = [key for key in self.matched_medications_dict.keys() if medication in key]
            if (not self.matched_medications_dict.__contains__(medication)
                    and not self.medications_to_ignore.__contains__(medication)):
                medication_object: Medication = self.production_medications_dict[medication]
                if (not self.check_for_medication_linkage(medication_object)
                        and not self.missing_medications_dict.__contains__(medication)
                        and not len(substring_results) > 0):
                    self.add_medication_to_missing_dict(medication_object)

    def check_for_medication_linkage(self, medication: Medication):
        """
        Checks for an existing medication linkage in the linked medications dictionary. If the specified medication
        provided as an argument is in the linked medications dictionary, then a linkage exists and a True boolean is
        returned. Otherwise, a False boolean is returned.
        :param medication: Medication object which is looked for in the linked medications dictionary's values
        :return: True if linkage exists, otherwise False
        """
        linkage_exists: bool = False
        for value in self.linked_medications.values():
            if isinstance(value, Medication):
                if medication.__eq__(value):
                    linkage_exists = True
                    break
        return linkage_exists

    def add_medication_to_production_dict(self, med_to_be_added: Medication):
        """
        Implementation of the __add_to_dict_of_medications function. Adds a Medication object to the dictionary of
        production medications

        :param med_to_be_added: The Medication object to be added to the production medications dictionary
        :return: None
        """
        self.__add_to_dict_of_medications(med_to_be_added, self.production_medications_dict,
                                          "Production Medications")

    def remove_medication_from_production_dict(self, med_to_be_removed: Medication):
        """
        Implementation of the __remove_from_dict_of_medications function. Removes a Medication object from the
        dictionary of production medications

        :param med_to_be_removed: The Medication object to be removed from the production medications dictionary
        :return: None
        """
        self.__remove_from_dict_of_medications(med_to_be_removed, self.production_medications_dict,
                                               "Production Medications")

    def add_medication_to_matched_dict(self, med_to_be_added):
        """
        Implementation of the __add_to_dict_of_medications function. Adds a Medication object to the dictionary of
        matched medications

        :param med_to_be_added: The Medication object to be added to the matched medications dictionary
        :return: None
        """
        self.__add_to_dict_of_medications(med_to_be_added, self.matched_medications_dict,
                                          "Matched Medications")

    def remove_medication_from_matched_dict(self, med_to_be_removed: Medication):
        """
        Implementation of the __remove_from_dict_of_medications function. Removes a Medication object from the
        dictionary of matched medications

        :param med_to_be_removed: The Medication object to be removed from the matched medications dictionary
        :return: None
        """
        self.__remove_from_dict_of_medications(med_to_be_removed, self.matched_medications_dict,
                                               "Matched Medications")

    def add_medication_to_missing_dict(self, med_to_be_added):
        """
        Implementation of the __add_to_dict_of_medications function. Adds a Medication object to the dictionary of
        missing medications

        :param med_to_be_added: The Medication object to be added to the missing medications dictionary
        :return: None
        """
        self.__add_to_dict_of_medications(med_to_be_added, self.missing_medications_dict,
                                          "Missing Medications")

    def remove_medication_from_missing_dict(self, med_to_be_removed: Medication):
        """
        Implementation of the __remove_from_dict_of_medications function. Removes a Medication object from the
        dictionary of missing medications

        :param med_to_be_removed: The Medication object to be removed from the missing medications dictionary
        :return: None
        """
        self.__remove_from_dict_of_medications(med_to_be_removed, self.missing_medications_dict,
                                               "Missing Medications")

    def add_medication_to_unknown_dict(self, med_to_be_added):
        """
        Implementation of the __add_to_dict_of_medications function. Adds a Medication object to the dictionary of
        unknown medications

        :param med_to_be_added: The Medication object to be added to the unknown medications dictionary
        :return: None
        """
        self.__add_to_dict_of_medications(med_to_be_added, self.unknown_medications_dict,
                                          "Unknown Medications")

    def remove_medication_from_unknown_dict(self, med_to_be_removed: Medication):
        """
        Implementation of the __remove_from_dict_of_medications function. Removes a Medication object from the
        dictionary of unknown medications

        :param med_to_be_removed: The Medication object to be removed from the unknown medications dictionary
        :return: None
        """
        self.__remove_from_dict_of_medications(med_to_be_removed, self.unknown_medications_dict,
                                               "Unknown Medications")

    def add_medication_to_incorrect_dosage_dict(self, med_to_be_added: Medication):
        """
        Implementation of the __add_to_dict_of_medications function. Adds a Medication object to the dictionary of
        incorrect dosage medications

        :param med_to_be_added: The Medication object to be added to the incorrect dosage medications dictionary
        :return: None
        """
        self.__add_to_dict_of_medications(med_to_be_added, self.incorrect_dosages_dict,
                                          "Incorrect Dosage Medications")

    def remove_medication_from_incorrect_dosage_dict(self, med_to_be_removed: Medication):
        """
        Implementation of the __remove_from_dict_of_medications function. Removes a Medication object from the
        dictionary of incorrect dosage medications

        :param med_to_be_removed: The Medication object to be removed from the incorrect dosage medications dictionary
        :return: None
        """
        self.__remove_from_dict_of_medications(med_to_be_removed, self.incorrect_dosages_dict,
                                               "Incorrect Dosage Medications")

    def add_medication_to_prn_dict(self, med_to_be_added: Medication):
        """
        Implementation of the __add_to_dict_of_medications function. Adds a Medication object to the dictionary of
        all PRN medications

        :param med_to_be_added: The Medication object to be added to the dictionary of all PRN medications
        :return: None
        """
        self.__add_to_dict_of_medications(med_to_be_added, self.prn_medications_dict,
                                          "PRN Medications")

    def remove_medication_from_prn_dict(self, med_to_be_removed: Medication):
        """
        Implementation of the __remove_from_dict_of_medications function. Removes a Medication object from the
        dictionary of all PRN medications

        :param med_to_be_removed: The Medication object to be removed from the dictionary of all PRN medications
        :return: None
        """
        self.__remove_from_dict_of_medications(med_to_be_removed, self.prn_medications_dict,
                                               "PRN Medications")

    def add_medication_to_prns_for_current_cycle(self, med_to_be_added: Medication):
        """
        Implementation of the __add_to_dict_of_medications function. Adds a Medication object to the dictionary of
        current cycle PRN medications

        :param med_to_be_added: The Medication object to be added to the current cycle PRN medications dictionary
        :return: None
        """
        dupe: bool = False
        for med in self.prns_for_current_cycle:
            if isinstance(med, Medication):
                print("PRN MED: " + med.medication_name)
                if med.__eq__(med_to_be_added):
                    print(
                        "med being iterated: " + med.medication_name + " med to be added: " + med_to_be_added.medication_name)
                    dupe = True
        if not dupe and isinstance(med_to_be_added, Medication):
            print("added " + med_to_be_added.medication_name)
            self.prns_for_current_cycle.append(med_to_be_added)

    def remove_medication_from_prns_for_current_cycle(self, med_to_be_removed: Medication):
        """
        Implementation of the __remove_from_dict_of_medications function. Removes a Medication object from the
        dictionary of current cycle PRN medications

        :param med_to_be_removed: The Medication object to be removed from the current cycle PRN medications dictionary
        :return: None
        """
        try:
            self.prns_for_current_cycle.remove(med_to_be_removed)
        except ValueError as e:
            logging.error(e)

    def add_medication_link(self, linking_med: Medication, med_to_be_linked: Medication):
        """
        Function which creates a linkage between two equivalent medications and adds the name of the medication to be
        linked to the linked medications dictionary as a key. The equivalent medication is then added as the value.
        Any instances of the linked medication in the unknown, or missing medications dictionaries are then removed.

        :param linking_med: The medication which needs linked to an equivalent medication
        :param med_to_be_linked: The equivalent medication to be used as a value in the linked medications dictionary
        :return: None
        """
        if not self.linked_medications.__contains__(linking_med.medication_name):
            if linking_med.dosage == med_to_be_linked.dosage:
                self.remove_medication_from_unknown_dict(linking_med)
                self.remove_medication_from_missing_dict(med_to_be_linked)
                self.add_medication_to_matched_dict(linking_med)
                self.linked_medications[linking_med.medication_name] = med_to_be_linked

    def remove_medication_link(self, medication_to_unlink: Medication):
        """
        Function which severs an existing link between one medication and another and removes the Medication object
        from the linked medication dictionary. The unlinked medication is then added to the unknown medications
        dictionary and its value is added to the missing medications list.

        :param medication_to_unlink: The Medication object which is to have its equivalent medication removed
        from the linked medication dictionary
        :return: None
        """
        if self.linked_medications.__contains__(medication_to_unlink.medication_name):
            linked_medication: Medication = self.linked_medications[medication_to_unlink.medication_name]
            self.add_medication_to_unknown_dict(medication_to_unlink)
            self.add_medication_to_missing_dict(linked_medication)
            self.remove_medication_from_matched_dict(medication_to_unlink)
            self.linked_medications.pop(medication_to_unlink.medication_name)

    def add_medication_to_ignore_dict(self, med_to_be_added: Medication):
        """
        Function which is used to add an incorrectly dosed medication to the ignored problem medications dictionary.
        This function should only be used at the discretion of a responsible pharmacist.

        :param med_to_be_added: Medication object to be added to the ignored problem medications dictionary
        :return: None
        """
        self.__add_to_dict_of_medications(med_to_be_added, self.medications_to_ignore,
                                          "Medications to Ignore")
        self.remove_medication_from_incorrect_dosage_dict(med_to_be_added)
        self.remove_medication_from_missing_dict(med_to_be_added)
        self.add_medication_to_matched_dict(med_to_be_added)

    def remove_medication_from_ignore_dict(self, med_to_be_removed: Medication, med_with_correct_dosage: Medication):
        """
        Function which removes a previously ignored problem medication from the ignored problem medications dictionary
        and re-adds it to the incorrect dosage dictionary.

        :param med_to_be_removed: Medication object to be removed from the ignored problem medications dictionary
        :param med_with_correct_dosage: Medication object which has the expected dosage
        :return: None
        """
        self.__remove_from_dict_of_medications(med_to_be_removed, self.medications_to_ignore,
                                               "Medications to Ignore")
        self.remove_medication_from_matched_dict(med_to_be_removed)
        self.add_medication_to_incorrect_dosage_dict(med_to_be_removed)
        self.add_medication_to_missing_dict(med_with_correct_dosage)

    def __hash__(self):
        """
        Overrides the default hash function
        :return: True if the hash matches, otherwise False
        """
        return hash((self.first_name, self.last_name, self.date_of_birth))

    def __eq__(self, other):
        """
        Overrides the default eq function
        :param other: The other instance being compared with this instance
        :return: True if the hash matches, otherwise False
        """
        return self.__hash__() == other.__hash__()

    def update_fields(self, other):
        """
        Function which updates this instance's fields updated with the other instance's fields.

        :param other: The other instance being compared to this current instance
        :return: None
        """
        self.script_id = other.script_id
        self.script_issuer = other.script_issuer
        self.script_date = other.script_date
        self.middle_name = other.middle_name
        self.healthcare_no = other.healthcare_no
        self.title = other.title
        self.script_no = other.script_no
        self.address = other.address
        self.postcode = other.postcode
        self.doctor_id_no = other.doctor_id_no
        self.doctor_name = other.doctor_name
        self.surgery_id_no = other.surgery_id_no
        self.surgery = other.surgery
        self.surgery_address = other.surgery_address
        self.surgery_postcode = other.surgery_postcode

    def __ne__(self, other):
        """
        Overrides the default ne function

        :param other: The other instance being compared with this instance
        :return: True if the hash matches, otherwise false
        """
        return not (self.__hash__() == other.__hash__())
