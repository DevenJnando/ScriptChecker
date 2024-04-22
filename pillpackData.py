import datetime
import os
import re
import types
import xml.parsers.expat
from functools import reduce
from os import scandir
import xml.dom.minidom as minidom
import sys
from zipfile import ZipFile

import yaml

consts = types.SimpleNamespace()
consts.READY_TO_PRODUCE_CODE = 0
consts.NOTHING_TO_COMPARE = 1
consts.MISSING_MEDICATIONS = 2
consts.DO_NOT_PRODUCE = 3
consts.PRN_KEY = "prns_dict"
consts.LINKED_MEDS_KEY = "linked_meds_dict"
consts.COLLECTED_PATIENTS_FILE = 'Patients.pk1'
consts.PRNS_AND_IGNORED_MEDICATIONS_FILE = 'PrnsAndIgnoredMeds.pk1'


class Medication:
    def __init__(self, medication_name: str, dosage: float):
        self.medication_name: str = medication_name
        self.dosage: float = dosage

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
        self.do_not_produce_flag: bool = False
        self.ready_to_produce_code: int = 0
        self.medication_dict: dict = {}
        self.matched_medications_dict: dict = {}
        self.missing_medications_dict: dict = {}
        self.unknown_medications_dict: dict = {}
        self.incorrect_dosages_dict: dict = {}
        self.prn_medications_dict: dict = {}
        self.medications_to_ignore: dict = {}
        self.linked_medications: dict = {}

    def do_not_produce(self, do_not_produce: bool):
        self.do_not_produce_flag = do_not_produce

    def set_ready_to_produce_code(self, ready_to_produce_code: int):
        if 3 > ready_to_produce_code > 0:
            self.ready_to_produce_code = ready_to_produce_code

    def determine_ready_to_produce_code(self):
        if not self.do_not_produce_flag:
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
            self.ready_to_produce_code = consts.DO_NOT_PRODUCE

    @staticmethod
    def __add_to_dict_of_medications(medication_to_add: Medication, dict_to_add_to: dict):
        if not dict_to_add_to.__contains__(medication_to_add.medication_name):
            dict_to_add_to[medication_to_add.medication_name] = medication_to_add

    @staticmethod
    def __remove_from_dict_of_medications(medication_to_remove: Medication, dict_to_remove_from: dict):
        if dict_to_remove_from.__contains__(medication_to_remove.medication_name):
            dict_to_remove_from.pop(medication_to_remove.medication_name)

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

    def remove_medication_from_ignore_dict(self, med_to_be_removed: Medication):
        self.__remove_from_dict_of_medications(med_to_be_removed, self.medications_to_ignore)

    def __hash__(self):
        return hash((self.first_name, self.last_name, self.date_of_birth))

    def __eq__(self, other):
        return ((self.first_name, self.last_name, self.date_of_birth)
                == (other.first_name, other.last_name, other.date_of_birth))

    def __ne__(self, other):
        return not (self == other)


def __load_settings():
    return yaml.safe_load(open(sys.path[0] + "\\settings.yaml"))


config = __load_settings()
patient_order_list: list


def __scan_pillpack_folder(filepath: str):
    entities = scandir(filepath)
    return list(filter(lambda entity: entity.is_file() and entity.name.split(".")[1] == "ppc_processed", entities))


def __sanitise_and_encode_text_from_file(filename: str):
    if config is not None:
        raw_file = None
        list_of_strings = None
        try:
            raw_file = open(config["pillpackDataLocation"] + "\\" + filename, "rb")
            raw_binary = raw_file.read()
            raw_text = str(raw_binary)
            trimmed_text = "<" + raw_text.split("<", 1)[1].rsplit(">\\n", 1)[0] + ">"
            sanitised_text = re.sub("</OrderInfo>.*?<OrderInfo>", "</OrderInfo>\n<OrderInfo>", trimmed_text,
                                    flags=re.DOTALL)
            sanitised_text = re.sub(r'^.*?<\?xml', "<?xml", sanitised_text)
            encoded_text = sanitised_text.encode('utf8').decode('unicode-escape')
            list_of_strings = encoded_text.split("</OrderInfo>")
            for i in range(0, len(list_of_strings)):
                string = list_of_strings[i]
                if len(string) > 0:
                    if '<?xml version="1.0" encoding="utf-8"?>' not in string:
                        string = '<?xml version="1.0" encoding="utf-8"?>' + string
                    if '</OrderInfo>' not in string:
                        string = string + '</OrderInfo>'
                    list_of_strings[i] = string
                else:
                    list_of_strings.pop(i)
        except FileNotFoundError as e:
            print("FileNotFoundError: ", e)
        finally:
            try:
                raw_file.close()
            except AttributeError as e:
                print("AttributeError: ", e)
        return list_of_strings


def __remove_whitespace(node):
    if node.nodeType == minidom.Node.TEXT_NODE:
        if node.nodeValue.strip() == "":
            node.nodeValue = ""
    for child in node.childNodes:
        __remove_whitespace(child)


def __generate_medication_dict(medication_element):
    if isinstance(medication_element, minidom.Element):
        medications = medication_element.getElementsByTagName("MedNm")[0]
        medication_name = medications.firstChild.nodeValue if medications.hasChildNodes() else ""
        list_of_dosages = medication_element.getElementsByTagName("MedItemDose")
        number_of_days_to_take = list_of_dosages.length
        dosage_list = list_of_dosages[0].getElementsByTagName("DoseList")[0]
        dosage_list_value = dosage_list.firstChild.nodeValue if dosage_list.hasChildNodes() else ""
        trimmed_dosage_list = list(filter(lambda entity: entity != "", dosage_list_value.split(";")))
        final_dosage: float = -1
        try:
            final_dosage = sum([float(e.split(":")[1]) for e in trimmed_dosage_list])
        except ValueError as e:
            print("ValueError: ", e)
        total_dosage = number_of_days_to_take * final_dosage
        medication_object: Medication = Medication(medication_name, total_dosage)
        return medication_object
    else:
        print("The medication parameter: ", medication_element, " is not a valid XML element.")
        return


def __create_patient_object(order_element):
    if isinstance(order_element, minidom.Element):
        patient_name_element = order_element.getElementsByTagName("PtntNm")[0]
        patient_dob_element = order_element.getElementsByTagName("Birthday")[0]
        patient_full_name: list = patient_name_element.firstChild.nodeValue.split(
            ",") if patient_name_element.hasChildNodes() else []
        patient_first_name: str = patient_full_name[1].strip() if len(patient_full_name) > 0 else ""
        patient_last_name: str = patient_full_name[0].strip() if len(patient_full_name) > 0 else ""
        patient_dob_string: str = patient_dob_element.firstChild.nodeValue if patient_dob_element.hasChildNodes() else ""
        patient_dob_string = patient_dob_string[:4] + "-" + patient_dob_string[4:] if patient_dob_string != "" else ""
        patient_dob_string = patient_dob_string[:7] + "-" + patient_dob_string[7:] if patient_dob_string != "" else ""
        patient_dob = datetime.date.today()
        try:
            patient_dob = datetime.date.fromisoformat(patient_dob_string)
        except ValueError as e:
            print("Date of birth could not be read from given string: ", patient_dob_string, e)
        finally:
            patient_object = PillpackPatient(patient_first_name, patient_last_name, patient_dob)
        medication_items: list = order_element.getElementsByTagName("MedItem")
        for medication in medication_items:
            medication_object = __generate_medication_dict(medication)
            if isinstance(medication_object, Medication):
                patient_object.add_medication_to_dict(medication_object)
        return patient_object
    else:
        print("The order parameter: ", order_element, " is not a valid XML element.")
        print(order_element, " is of type: ", type(order_element))
        return


def __parse_xml(list_of_orders_raw_text: list):
    order_information: list = []
    for order_raw_text in list_of_orders_raw_text:
        try:
            document = minidom.parseString(order_raw_text)
            __remove_whitespace(document)
            document.normalize()
            order_information.append(document.getElementsByTagName("OrderInfo"))
        except xml.parsers.expat.ExpatError as e:
            print("ExpatError: ", e)
        except TypeError as e:
            print("TypeError: ", e)
    return order_information


def get_patient_medicine_data(prns_and_ignored_medications: dict):
    if config is not None:
        ppc_processed_files = __scan_pillpack_folder(config["pillpackDataLocation"])
        dict_of_patients: dict = {}
        for ppc_file in ppc_processed_files:
            list_of_orders_raw_text = __sanitise_and_encode_text_from_file(ppc_file.name)
            list_of_orders: list = reduce(list.__add__, __parse_xml(list_of_orders_raw_text))
            for order in list_of_orders:
                patient_object = __create_patient_object(order)
                patient_object = retrieve_prns_and_ignored_medications(patient_object, prns_and_ignored_medications)
                if isinstance(patient_object, PillpackPatient):
                    if dict_of_patients.__contains__(patient_object.last_name.lower()):
                        list_of_patients: list = dict_of_patients.get(patient_object.last_name.lower())
                        list_of_patients.append(patient_object)
                        list_of_patients = list(dict.fromkeys(list_of_patients))
                        dict_of_patients[patient_object.last_name.lower()] = list_of_patients
                    else:
                        list_of_patients: list = [patient_object]
                        dict_of_patients[patient_object.last_name.lower()] = list_of_patients
        return dict_of_patients


def retrieve_prns_and_ignored_medications(patient: PillpackPatient, prns_and_ignored_medications: dict):
    key = patient.first_name + " " + patient.last_name + " " + str(patient.date_of_birth)
    if prns_and_ignored_medications.__contains__(key.lower()):
        patient.prn_medications_dict = prns_and_ignored_medications[key.lower()][consts.PRN_KEY]
        patient.linked_medications = prns_and_ignored_medications[key.lower()][consts.LINKED_MEDS_KEY]
    return patient


def archive_pillpack_production(archive_file):
    if config is not None:
        ppc_processed_files = __scan_pillpack_folder(config["pillpackDataLocation"])
        pillpack_directory = config["pillpackDataLocation"] + "\\"
        with ZipFile(archive_file.name, 'w') as archived_production_data:
            for file in ppc_processed_files:
                archived_production_data.write(pillpack_directory + file.name)
                os.remove(pillpack_directory + file.name)
            os.remove(consts.COLLECTED_PATIENTS_FILE)
