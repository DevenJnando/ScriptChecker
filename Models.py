import datetime
import types
import logging

consts = types.SimpleNamespace()
consts.READY_TO_PRODUCE_CODE = 1
consts.NOTHING_TO_COMPARE = 2
consts.MISSING_MEDICATIONS = 3
consts.DO_NOT_PRODUCE = 4
consts.MANUALLY_CHECKED = 5
consts.PRN_KEY = "prns_dict"
consts.LINKED_MEDS_KEY = "linked_meds_dict"
consts.COLLECTED_PATIENTS_FILE = 'Application/Patients.pk1'
consts.PRNS_AND_LINKED_MEDICATIONS_FILE = 'Application/PrnsAndLinkedMeds.pk1'


class Medication:
    def __init__(self, medication_name: str, dosage: float, start_date: datetime,
                 doctors_orders: str = None,
                 code: str = None,
                 disp_code: str = None,
                 med_type: str = None):
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

    def dosage_equals(self, comparator):
        if isinstance(comparator, Medication):
            dosage_hash = hash(self.dosage)
            comparator_dosage_hash = hash(comparator.dosage)
            if dosage_hash == comparator_dosage_hash:
                return True
            else:
                return False
        else:
            return False

    def __eq__(self, other):
        return ((self.medication_name, self.dosage)
                == (other.medication_name, other.dosage))

    def __hash__(self):
        return hash((self.medication_name, self.dosage))


class PillpackPatient:
    def __init__(self, first_name, last_name, date_of_birth,
                 title: str = None,
                 middle_name: str = None,
                 address: str = None,
                 healthcare_no: str = None,
                 postcode: str = None,
                 script_no: str = None,
                 surgery: str = None,
                 surgery_address: str = None,
                 surgery_postcode: str = None,
                 doctor_id_no: str = None,
                 doctor_name: str = None,
                 surgery_id_no: str = None,
                 script_id: str = None,
                 script_issuer: str = None,
                 script_date: str = None
                 ):
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
            elif len(self.matched_medications_dict) == len(self.production_medications_dict):
                self.ready_to_produce_code = consts.READY_TO_PRODUCE_CODE
            else:
                self.ready_to_produce_code = consts.NOTHING_TO_COMPARE
        else:
            self.ready_to_produce_code = consts.MANUALLY_CHECKED

    @staticmethod
    def __add_to_dict_of_medications(medication_to_add: Medication, dict_to_add_to: dict,
                                     name_of_dict: str):
        if isinstance(medication_to_add, Medication):
            if not dict_to_add_to.__contains__(medication_to_add.medication_name):
                dict_to_add_to[medication_to_add.medication_name] = medication_to_add
                logging.info("Added medication {0} to dictionary {1}"
                             .format(medication_to_add.medication_name, name_of_dict))

    @staticmethod
    def __remove_from_dict_of_medications(medication_to_remove: Medication, dict_to_remove_from: dict,
                                          name_of_dict: str):
        if isinstance(medication_to_remove, Medication):
            if dict_to_remove_from.__contains__(medication_to_remove.medication_name):
                dict_to_remove_from.pop(medication_to_remove.medication_name)
                logging.info("Removed medication {0} from dictionary {1}"
                             .format(medication_to_remove.medication_name, name_of_dict))

    def add_medication_to_production_dict(self, med_to_be_added: Medication):
        self.__add_to_dict_of_medications(med_to_be_added, self.production_medications_dict,
                                          "Production Medications")

    def remove_medication_from_production_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.production_medications_dict,
                                               "Production Medications")

    def add_medication_to_matched_dict(self, med_to_be_added):
        self.__add_to_dict_of_medications(med_to_be_added, self.matched_medications_dict,
                                          "Matched Medications")

    def remove_medication_from_matched_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.matched_medications_dict,
                                               "Matched Medications")

    def add_medication_to_missing_dict(self, med_to_be_added):
        self.__add_to_dict_of_medications(med_to_be_added, self.missing_medications_dict,
                                          "Missing Medications")

    def remove_medication_from_missing_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.missing_medications_dict,
                                               "Missing Medications")

    def add_medication_to_unknown_dict(self, med_to_be_added):
        self.__add_to_dict_of_medications(med_to_be_added, self.unknown_medications_dict,
                                          "Unknown Medications")

    def remove_medication_from_unknown_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.unknown_medications_dict,
                                               "Unknown Medications")

    def add_medication_to_incorrect_dosage_dict(self, med_to_be_added: Medication):
        self.__add_to_dict_of_medications(med_to_be_added, self.incorrect_dosages_dict,
                                          "Incorrect Dosage Medications")

    def remove_medication_from_incorrect_dosage_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.incorrect_dosages_dict,
                                               "Incorrect Dosage Medications")

    def add_medication_to_prn_dict(self, med_to_be_added: Medication):
        self.__add_to_dict_of_medications(med_to_be_added, self.prn_medications_dict,
                                          "PRN Medications")

    def remove_medication_from_prn_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.prn_medications_dict,
                                               "PRN Medications")

    def add_medication_to_prns_for_current_cycle(self, med_to_be_added: Medication):
        dupe: bool = False
        for med in self.prns_for_current_cycle:
            if isinstance(med, Medication):
                if med.__eq__(med_to_be_added):
                    dupe = True
        if not dupe and isinstance(med_to_be_added, Medication):
            self.prns_for_current_cycle.append(med_to_be_added)

    def remove_medication_from_prns_for_current_cycle(self, med_to_be_removed: Medication):
        try:
            self.prns_for_current_cycle.remove(med_to_be_removed)
        except ValueError as e:
            logging.error(e)

    def add_medication_link(self, linking_med: Medication, med_to_be_linked: Medication):
        if not self.linked_medications.__contains__(linking_med.medication_name):
            if linking_med.dosage == med_to_be_linked.dosage:
                self.remove_medication_from_unknown_dict(linking_med)
                self.remove_medication_from_missing_dict(med_to_be_linked)
                self.add_medication_to_matched_dict(linking_med)
                self.linked_medications[linking_med.medication_name] = med_to_be_linked

    def remove_medication_link(self, medication_to_unlink: Medication):
        if self.linked_medications.__contains__(medication_to_unlink.medication_name):
            linked_medication: Medication = self.linked_medications[medication_to_unlink.medication_name]
            self.add_medication_to_unknown_dict(medication_to_unlink)
            self.add_medication_to_missing_dict(linked_medication)
            self.remove_medication_from_matched_dict(medication_to_unlink)
            self.linked_medications.pop(medication_to_unlink.medication_name)

    def add_medication_to_ignore_dict(self, med_to_be_added: Medication):
        self.__add_to_dict_of_medications(med_to_be_added, self.medications_to_ignore,
                                          "Medications to Ignore")
        self.remove_medication_from_incorrect_dosage_dict(med_to_be_added)
        self.remove_medication_from_missing_dict(med_to_be_added)
        self.add_medication_to_matched_dict(med_to_be_added)

    def remove_medication_from_ignore_dict(self, med_to_be_removed: Medication, med_with_correct_dosage: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.medications_to_ignore,
                                               "Medications to Ignore")
        self.remove_medication_from_matched_dict(med_to_be_removed)
        self.add_medication_to_incorrect_dosage_dict(med_to_be_removed)
        self.add_medication_to_missing_dict(med_with_correct_dosage)

    def __hash__(self):
        return hash((self.first_name, self.last_name, self.date_of_birth))

    def __eq__(self, other):
        return ((self.first_name, self.last_name, self.date_of_birth)
                == (other.first_name, other.last_name, other.date_of_birth))

    def __ne__(self, other):
        return not (self == other)
