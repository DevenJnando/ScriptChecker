import re
import xml.parsers.expat
import xml.dom.minidom as minidom
import datetime
from functools import reduce

from pillpackData import Medication, PillpackPatient
import pillpackData
import types
import pickle

consts = types.SimpleNamespace()
consts.PERFECT_MATCH = "PERFECT_MATCH"
consts.IMPERFECT_MATCH = "IMPERFECT_MATCH"
consts.NO_MATCH = "NO_MATCH"
consts.PROTOCOL = pickle.HIGHEST_PROTOCOL


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
            patients_with_last_name: list = dict_to_add_to.get(patient_to_add.last_name.lower())
            patients_with_last_name.append(patient_to_add)
            dict_to_add_to[patient_to_add.last_name.lower()] = patients_with_last_name
        else:
            list_of_patients: list = [patient_to_add]
            dict_to_add_to[patient_to_add.last_name.lower()] = list_of_patients

    def set_pillpack_patient_dict(self, patient_dict: dict):
        self.pillpack_patient_dict = patient_dict

    def add_patient(self, patient_to_add: PillpackPatient, status: str):
        patient_wrapper: dict = {
            "PatientObject": patient_to_add,
            "Status": status
        }
        if self.all_patients.__contains__(patient_to_add.last_name.lower()):
            patients_with_last_name: list = self.all_patients.get(patient_to_add.last_name.lower())
            patients_with_last_name.append(patient_wrapper)
            self.all_patients[patient_to_add.last_name.lower()] = patients_with_last_name
        else:
            list_of_wrappers: list = [patient_wrapper]
            self.all_patients[patient_to_add.last_name.lower()] = list_of_wrappers

    def add_matched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.matched_patients)

    def add_minor_mismatched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.minor_mismatch_patients)

    def add_severely_mismatched_patient(self, patient_to_add: PillpackPatient):
        self.__add_to_dict_of_patients(patient_to_add, self.severe_mismatch_patients)

    def update_pillpack_patient_dict(self, patient_to_be_updated: PillpackPatient):
        if self.pillpack_patient_dict.__contains__(patient_to_be_updated.last_name):
            patients_with_last_name = self.pillpack_patient_dict.get(patient_to_be_updated.last_name)
            for i in range(0, len(patients_with_last_name)):
                patient: PillpackPatient = patients_with_last_name[i]
                if patient.__eq__(patient_to_be_updated):
                    patients_with_last_name[i] = patient_to_be_updated
                    self.pillpack_patient_dict[patient_to_be_updated.last_name] = patients_with_last_name


def scan_script(raw_xml_text: str):
    try:
        sanitised_xml_text = raw_xml_text.replace('@', '"').replace('£', "#")
        sanitised_xml_text.encode("iso-8859-1")
        document = minidom.parseString(sanitised_xml_text)
        return document
    except xml.parsers.expat.ExpatError as e:
        print("ExpatError: ", e)
        return
    except TypeError as e:
        print("TypeError: ", e)
        return


def load_pillpack_data(prns_and_ignored_medications: dict):
    patient_data_from_pillpack: dict = pillpackData.get_patient_medicine_data(prns_and_ignored_medications)
    return patient_data_from_pillpack


def extract_medicine_data(medicine_element: minidom.Element):
    medicine_name_on_script = medicine_element.getAttribute("d")
    medicine_dosage_on_script = medicine_element.getAttribute("q")
    medication: Medication = Medication(medicine_name_on_script, float(medicine_dosage_on_script))
    return medication


def extract_patient_data(script_xml):
    if isinstance(script_xml, minidom.Document) and script_xml.hasChildNodes():
        patient_details = script_xml.getElementsByTagName("pa")[0]
        patient_last_name = patient_details.getAttribute("l")
        patient_first_name = patient_details.getAttribute("f")
        patient_dob = datetime.date.fromisoformat(patient_details.getAttribute("b"))
        medicines_on_script = script_xml.getElementsByTagName("dd")
        patient_object = PillpackPatient(patient_first_name, patient_last_name, patient_dob)
        for medicine in medicines_on_script:
            medication_object: Medication = extract_medicine_data(medicine)
            patient_object.add_medication_to_dict(medication_object)
        return patient_object
    else:
        return None


def check_script_medications_against_pillpack(patient_from_production: PillpackPatient,
                                              patient_from_script: PillpackPatient,
                                              collected_patients: CollectedPatients):
    full_medication_dict: dict = patient_from_production.medication_dict
    script_medication_dict: dict = patient_from_script.medication_dict
    for medication in full_medication_dict.keys():
        substring_results = [key for key in script_medication_dict.keys() if medication in key]
        if (len(substring_results) > 0
                and not patient_from_production.matched_medications_dict.__contains__(medication)):
            pillpack_medication: Medication = full_medication_dict[medication]
            script_medication: Medication = script_medication_dict[substring_results[0]]
            if pillpack_medication.equals(script_medication):
                patient_from_production.add_matched_medication_to_dict(pillpack_medication)
                clear_medication_warning_dicts(patient_from_production, pillpack_medication)
            else:
                patient_from_production.add_incorrect_dosage_medication_to_dict(script_medication)
        elif not patient_from_script.medication_dict.__contains__(medication):
            if not patient_from_production.matched_medications_dict.__contains__(medication):
                if (not patient_from_production.prn_medications_dict.__contains__(medication)
                        and not patient_from_production.medications_to_ignore.__contains__(medication)):
                    patient_from_production.add_missing_medication_to_dict(full_medication_dict[medication])
    for medication in script_medication_dict.keys():
        substring_results = [key for key in full_medication_dict.keys() if key in medication]
        if len(substring_results) > 0:
            pillpack_medication: Medication = full_medication_dict[substring_results[0]]
            if patient_from_production.matched_medications_dict.__contains__(pillpack_medication):
                clear_medication_warning_dicts(patient_from_production, pillpack_medication)
        else:
            if not full_medication_dict.__contains__(medication):
                patient_from_production.add_unknown_medication_to_dict(script_medication_dict[medication])
    collected_patients.update_pillpack_patient_dict(patient_from_production)


def clear_medication_warning_dicts(patient: PillpackPatient, medication: Medication):
    patient.remove_missing_medication_from_dict(medication)
    patient.remove_incorrect_dosage_medication_from_dict(medication)
    patient.remove_unknown_medication_from_dict(medication)


def extend_existing_patient_medication_dict(patient_object: PillpackPatient, collected_patients: CollectedPatients):
    exists: bool = False
    if collected_patients.all_patients.__contains__(patient_object.last_name.lower()):
        list_of_wrappers: list = collected_patients.all_patients.get(patient_object.last_name.lower())
        for patient_wrapper in list_of_wrappers:
            if isinstance(patient_wrapper["PatientObject"], PillpackPatient):
                unwrapped_patient: PillpackPatient = patient_wrapper["PatientObject"]
                match patient_wrapper["Status"]:
                    case consts.PERFECT_MATCH:
                        if (unwrapped_patient.date_of_birth == patient_object.date_of_birth
                                and unwrapped_patient.last_name == patient_object.last_name
                                and unwrapped_patient.first_name == patient_object.first_name):
                            check_script_medications_against_pillpack(unwrapped_patient, patient_object, collected_patients)
                            exists = True
                            break
                    case consts.IMPERFECT_MATCH:
                        if (unwrapped_patient.last_name == patient_object.last_name
                                and unwrapped_patient.first_name == patient_object.first_name):
                            check_script_medications_against_pillpack(unwrapped_patient, patient_object, collected_patients)
                            exists = True
                            break
                    case consts.NO_MATCH:
                        return exists
    return exists


def compare_patient_details(pillpack_patient: PillpackPatient, script_patient: PillpackPatient):
    matches: dict = {
        "Patient": PillpackPatient("", "", datetime.date.today()),
        "PerfectMatch": False
    }
    match_patient_first_name = re.match(pillpack_patient.first_name.lower(), script_patient.first_name.lower())
    if match_patient_first_name is not None:
        matches["Patient"] = pillpack_patient
        if pillpack_patient.date_of_birth == script_patient.date_of_birth:
            matches["PerfectMatch"] = True
    return matches


def query_pillpack_patient_list(pillpack_patient_dict, script_patient: PillpackPatient):
    patient_matches_list: list = []
    if pillpack_patient_dict.__contains__(script_patient.last_name.lower()):
        patients_with_last_name = pillpack_patient_dict.get(script_patient.last_name.lower())
        for patient in patients_with_last_name:
            if isinstance(patient, PillpackPatient):
                pillpack_patient_matches: dict = compare_patient_details(patient, script_patient)
                if pillpack_patient_matches["Patient"] == patient and pillpack_patient_matches["PerfectMatch"] is True:
                    return patient
                elif pillpack_patient_matches["Patient"] == patient:
                    patient_matches_list.append(patient)
        return patient_matches_list
    else:
        return patient_matches_list


def check_if_patient_is_in_pillpack_production(pillpack_patient_dict: dict,
                                               script_patient: PillpackPatient,
                                               collected_patients: CollectedPatients):
    if isinstance(pillpack_patient_dict, dict) and isinstance(script_patient, PillpackPatient):
        matched_patient = query_pillpack_patient_list(pillpack_patient_dict, script_patient)
        if isinstance(matched_patient, PillpackPatient):
            check_script_medications_against_pillpack(matched_patient, script_patient, collected_patients)
            collected_patients.add_patient(matched_patient, consts.PERFECT_MATCH)
            collected_patients.add_matched_patient(matched_patient)
        elif isinstance(matched_patient, list) and len(matched_patient) > 0:
            for patient in matched_patient:
                check_script_medications_against_pillpack(patient, script_patient, collected_patients)
                collected_patients.add_patient(patient, consts.IMPERFECT_MATCH)
                collected_patients.add_minor_mismatched_patient(patient)
        elif isinstance(matched_patient, list) and len(matched_patient) == 0:
            collected_patients.add_patient(script_patient, consts.NO_MATCH)
            script_patient.do_not_produce(True)
            script_patient.ready_to_produce_code = 3
            for medication in list(script_patient.medication_dict.values()):
                script_patient.add_unknown_medication_to_dict(medication)
            script_patient.medication_dict.clear()
            collected_patients.add_severely_mismatched_patient(script_patient)
        else:
            print("You should not see this. Something has broken...tell James to fix his awful code!")
    else:
        print("The scanned barcode did not correspond to a valid script. Please check your barcode and try again.")


def scan_script_and_check_medications(collected_patients: CollectedPatients, scanned_input: str):
    script_as_xml = scan_script(scanned_input)
    script_patient_object: PillpackPatient = extract_patient_data(script_as_xml)
    if isinstance(script_patient_object, PillpackPatient):
        if not extend_existing_patient_medication_dict(script_patient_object, collected_patients):
            check_if_patient_is_in_pillpack_production(collected_patients.pillpack_patient_dict, script_patient_object, collected_patients)
        save_collected_patients(collected_patients)
    else:
        print("Failed to read patient data from script...")


def update_current_prns_and_ignored_medications(patient: pillpackData.PillpackPatient,
                                                collected_patients: CollectedPatients,
                                                prns_and_ignored_medications: dict):
    if collected_patients.pillpack_patient_dict.__contains__(patient.last_name.lower()):
        key: str = patient.first_name.lower() + " " + patient.last_name.lower() + " " + str(patient.date_of_birth)
        prns_ignored_medications_sub_dict: dict = {
            pillpackData.consts.PRN_KEY: patient.prn_medications_dict,
            pillpackData.consts.IGNORE_KEY: patient.medications_to_ignore
        }
        prns_and_ignored_medications[key] = prns_ignored_medications_sub_dict
        save_prns_and_ignored_medications(prns_and_ignored_medications)


def save_collected_patients(collected_patients: CollectedPatients):
    save_to_file(collected_patients, pillpackData.consts.COLLECTED_PATIENTS_FILE)


def save_prns_and_ignored_medications(patient_prns_and_ignored_medications_dict: dict):
    save_to_file(patient_prns_and_ignored_medications_dict, pillpackData.consts.PRNS_AND_IGNORED_MEDICATIONS_FILE)


def save_to_file(object_to_save, filename):
    with open(filename, 'wb') as output:
        pickle.dump(object_to_save, output, consts.PROTOCOL)
        print("Saved!")


def load_object(object_file_name: str):
    o = None
    try:
        with open(object_file_name, 'rb') as inpt:
            o = pickle.load(inpt)
    except FileNotFoundError:
        o = None
    finally:
        return o


def load_collected_patients_from_object():
    collected_patients: CollectedPatients = load_object(pillpackData.consts.COLLECTED_PATIENTS_FILE)
    if collected_patients is None:
        collected_patients = CollectedPatients()
    return collected_patients


def load_prns_and_ignored_medications_from_object():
    prns_and_ignored_medications: dict = load_object(pillpackData.consts.PRNS_AND_IGNORED_MEDICATIONS_FILE)
    if prns_and_ignored_medications is None:
        prns_and_ignored_medications = {}
    return prns_and_ignored_medications
