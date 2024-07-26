import xml.parsers.expat
import xml.parsers.expat
from functools import reduce
from os import scandir
import xml.dom.minidom as minidom
from zipfile import ZipFile

import yaml
import datetime
import os
import re

from Models import Medication, PillpackPatient, CollectedPatients
import Models
import types
import pickle

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
consts.PERFECT_MATCH = "PERFECT_MATCH"
consts.IMPERFECT_MATCH = "IMPERFECT_MATCH"
consts.NO_MATCH = "NO_MATCH"
consts.PROTOCOL = pickle.HIGHEST_PROTOCOL


def scan_script(raw_xml_text: str):
    try:
        sanitised_xml_text = ""
        for character in raw_xml_text:
            match character:
                case '"':
                    character = '@'
                case '@':
                    character = '"'
                case '£':
                    character = '#'
                case '#':
                    character = '£'
            sanitised_xml_text += character
        sanitised_xml_text = sanitised_xml_text.encode("iso-8859-1")
        document = minidom.parseString(sanitised_xml_text)
        logging.info("Successfully scanned and encoded XML from script.")
        return document
    except xml.parsers.expat.ExpatError as e:
        logging.error("Failed to read XML from script; an expat error has occurred: {0}".format(e))
        return
    except TypeError as e:
        logging.error("Failed to read XML from script; a type error has occurred: {0}".format(e))
        return


def load_pillpack_data(prns_and_linked_medications: dict, separating_tag: str):
    patient_data_from_pillpack: dict = get_patient_medicine_data(prns_and_linked_medications, separating_tag)
    return patient_data_from_pillpack


def extract_medicine_data(medicine_element: minidom.Element):
    medicine_name_on_script = medicine_element.getAttribute("d")
    medicine_dosage_on_script = medicine_element.getAttribute("q")
    medication: Medication = Medication(medicine_name_on_script, float(medicine_dosage_on_script),
                                        datetime.date.today())
    logging.info("Extracted Medicine information ({0} x{1}) from the script's XML"
                 .format(medicine_name_on_script, medicine_dosage_on_script))
    return medication


def extract_patient_data(script_xml):
    if isinstance(script_xml, minidom.Document) and script_xml.hasChildNodes():
        patient_details = script_xml.getElementsByTagName("pa")[0]
        patient_last_name = patient_details.getAttribute("l")
        patient_first_name = patient_details.getAttribute("f")
        patient_dob = datetime.date.fromisoformat(patient_details.getAttribute("b"))
        medicines_on_script = script_xml.getElementsByTagName("dd")
        patient_object = PillpackPatient(patient_first_name, patient_last_name, patient_dob)
        logging.info("Extracted Patient information ({0} {1} {2}) from script's XML"
                     .format(patient_first_name, patient_last_name, patient_dob))
        for medicine in medicines_on_script:
            medication_object: Medication = extract_medicine_data(medicine)
            patient_object.add_medication_to_production_dict(medication_object)
        return patient_object
    else:
        return None


def check_script_medications_against_pillpack(patient_from_production: PillpackPatient,
                                              patient_from_script: PillpackPatient,
                                              collected_patients: CollectedPatients):
    full_medication_dict: dict = patient_from_production.production_medications_dict
    script_medication_dict: dict = patient_from_script.production_medications_dict
    for medication in full_medication_dict.keys():
        substring_results = [key for key in script_medication_dict.keys() if medication in key]
        if (len(substring_results) > 0
                and not patient_from_production.matched_medications_dict.__contains__(medication)):
            pillpack_medication: Medication = full_medication_dict[medication]
            script_medication: Medication = script_medication_dict[substring_results[0]]
            logging.info("Comparing pillpack medication ({0}) with matched medication on scanned script ({1})"
                         .format(pillpack_medication.medication_name, script_medication.medication_name))
            if pillpack_medication.dosage_equals(script_medication):
                patient_from_production.add_medication_to_matched_dict(pillpack_medication)
                clear_medication_warning_dicts(patient_from_production, pillpack_medication)
                logging.info("Medications and dosages match. Adding medication {0} to matched medications dictionary"
                             .format(script_medication.medication_name))
            else:
                script_medication.medication_name = pillpack_medication.medication_name
                patient_from_production.add_medication_to_incorrect_dosage_dict(script_medication)
                logging.info("Medications match, but dosages are inconsistent. Adding medication {0} to "
                             "incorrect dosages dictionary.".format(script_medication.medication_name))
        elif not patient_from_script.production_medications_dict.__contains__(medication):
            if not patient_from_production.matched_medications_dict.__contains__(medication):
                if (not patient_from_production.prn_medications_dict.__contains__(medication)
                        and not patient_from_production.medications_to_ignore.__contains__(medication)
                        and not patient_from_production.linked_medications.__contains__(medication)):
                    patient_from_production.add_medication_to_missing_dict(full_medication_dict[medication])
                    logging.info("Medication {0} is not present on the scanned script. "
                                 "No exceptions for this medication exist. "
                                 "Adding to the missing medication dictionary."
                                 .format(medication))
    for medication in script_medication_dict.keys():
        substring_results = [key for key in full_medication_dict.keys() if key in medication]
        if len(substring_results) > 0:
            pillpack_medication: Medication = full_medication_dict[substring_results[0]]
            if patient_from_production.matched_medications_dict.__contains__(pillpack_medication):
                clear_medication_warning_dicts(patient_from_production, pillpack_medication)
                logging.info("Medication {0} is in matched dictionary. Clearing all other dictionaries."
                             .format(pillpack_medication.medication_name))
        else:
            if not full_medication_dict.__contains__(medication):
                linked_medication: Medication = check_for_linked_medications(script_medication_dict[medication],
                                                                             patient_from_production.linked_medications)
                if linked_medication is not None:
                    clear_medication_warning_dicts(patient_from_production, linked_medication)
                    patient_from_production.add_medication_to_matched_dict(script_medication_dict[medication])
                    logging.info("Medication {0} is linked to {1}. Adding medication to matched dictionary."
                                 .format(script_medication_dict[medication], linked_medication))
                elif (not patient_from_production.prn_medications_dict.__contains__(medication)
                      and not patient_from_production.medications_to_ignore.__contains__(medication)):
                    patient_from_production.add_medication_to_unknown_dict(script_medication_dict[medication])
                    logging.info("Medication {0} from script is not present in {1} {2}'s list of pillpack medications. "
                                 "Adding medication to unknown medications dictionary."
                                 .format(medication,
                                         patient_from_production.first_name, patient_from_production.last_name))
    collected_patients.update_pillpack_patient_dict(patient_from_production)


def clear_medication_warning_dicts(patient: PillpackPatient, medication: Medication):
    patient.remove_medication_from_missing_dict(medication)
    patient.remove_medication_from_incorrect_dosage_dict(medication)
    patient.remove_medication_from_unknown_dict(medication)
    logging.info("Removed medication {0} from missing medications, incorrect dosages and unknown medications "
                 "dictionaries.".format(medication.medication_name))


def check_for_linked_medications(medication_to_check: Medication, linked_medication_dict: dict):
    if linked_medication_dict.__contains__(medication_to_check.medication_name):
        if isinstance(linked_medication_dict[medication_to_check.medication_name], Medication):
            logging.info("Medication {0} was found in linked medications dictionary. Returning linked medication."
                         .format(medication_to_check.medication_name))
            return linked_medication_dict[medication_to_check.medication_name]
        else:
            logging.warning("Object retrieved from linked medications dictionary was not a Medication object.")
            return None
    else:
        logging.info("Medication {0} was not present in linked medications dictionary."
                     .format(medication_to_check.medication_name))
        return None


def extend_existing_patient_medication_dict(patient_object: PillpackPatient, collected_patients: CollectedPatients):
    exists: bool = False
    if collected_patients.all_patients.__contains__(patient_object.last_name.lower()):
        list_of_wrappers: list = collected_patients.all_patients.get(patient_object.last_name.lower())
        for patient_wrapper in list_of_wrappers:
            if isinstance(patient_wrapper["PatientObject"], PillpackPatient):
                unwrapped_patient: PillpackPatient = patient_wrapper["PatientObject"]
                match patient_wrapper["Status"]:
                    case consts.PERFECT_MATCH:
                        if unwrapped_patient.__eq__(patient_object):
                            check_script_medications_against_pillpack(unwrapped_patient, patient_object,
                                                                      collected_patients)
                            exists = True
                            logging.info("Patient {0} {1} found in full patient dictionary. Patient is a perfect match."
                                         "Patient's medication dictionary has been updated."
                                         .format(patient_object.first_name, patient_object.last_name))
                            break
                        elif (unwrapped_patient.last_name == patient_object.last_name
                                and unwrapped_patient.first_name == patient_object.first_name):
                            check_script_medications_against_pillpack(unwrapped_patient, patient_object,
                                                                      collected_patients)
                            exists = True
                            logging.info("Patient {0} {1} found in full patient dictionary. "
                                         "Patient's medication dictionary has been updated."
                                         .format(patient_object.first_name, patient_object.last_name))
                            logging.warning("Patient is marked as a perfect match, but the given DoB {0} "
                                            "does not match the DoB stored in the full dictionary: {1}"
                                            .format(patient_object.date_of_birth, unwrapped_patient.date_of_birth))
                            break
                    case consts.IMPERFECT_MATCH:
                        if (unwrapped_patient.last_name == patient_object.last_name
                                and unwrapped_patient.first_name == patient_object.first_name):
                            check_script_medications_against_pillpack(unwrapped_patient, patient_object,
                                                                      collected_patients)
                            exists = True
                            logging.info("Patient {0} {1} found in full patient dictionary. "
                                         "Patient's medication dictionary has been updated."
                                         .format(patient_object.first_name, patient_object.last_name))
                            logging.warning("Given DoB {0} does not match the DoB stored in the full dictionary: {1}"
                                            .format(patient_object.date_of_birth, unwrapped_patient.date_of_birth))
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
        logging.info("Patient {0} {1} in production matches patient {2} {3} on the script."
                     .format(pillpack_patient.first_name, pillpack_patient.last_name,
                             script_patient.first_name, script_patient.last_name))
        if pillpack_patient.date_of_birth == script_patient.date_of_birth:
            matches["PerfectMatch"] = True
            logging.info("Patient's DoB in production ({0}) matches patient's DoB on the script ({1})"
                         .format(pillpack_patient.date_of_birth, script_patient.date_of_birth))
        else:
            logging.warning("Patients DoB in production ({0}) does not match patient's DoB on the script ({1})"
                            .format(pillpack_patient.date_of_birth, script_patient.date_of_birth))
    else:
        logging.warning("Patient {0} {1} in production does not match patient {2} {3} on the script."
                        .format(pillpack_patient.first_name, pillpack_patient.last_name,
                                script_patient.first_name, script_patient.last_name))
    return matches


def query_pillpack_patient_list(pillpack_patient_dict, script_patient: PillpackPatient):
    patient_matches_list: list = []
    if pillpack_patient_dict.__contains__(script_patient.last_name.lower()):
        patients_with_last_name = pillpack_patient_dict.get(script_patient.last_name.lower())
        for patient in patients_with_last_name:
            if isinstance(patient, PillpackPatient):
                pillpack_patient_matches: dict = compare_patient_details(patient, script_patient)
                if pillpack_patient_matches["Patient"] == patient and pillpack_patient_matches["PerfectMatch"] is True:
                    logging.info("Patient on script ({0} {1}) perfectly matches a patient in current pillpack "
                                 "production".format(script_patient.first_name, script_patient.last_name))
                    return patient
                elif pillpack_patient_matches["Patient"] == patient:
                    patient_matches_list.append(patient)
                    logging.warning("Patient on script ({0} {1}) matches a patient in current pillpack production, "
                                    "but the DoB is inconsistent. It is likely the DoB in pillpack care is incorrect."
                                    .format(script_patient.first_name, script_patient.last_name))
        return patient_matches_list
    else:
        logging.warning("No patient in pillpack production matches the given patient {0} {1}"
                        .format(script_patient.first_name, script_patient.last_name))
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
            script_patient.ready_to_produce_code = 3
            for medication in list(script_patient.production_medications_dict.values()):
                script_patient.add_medication_to_unknown_dict(medication)
            script_patient.production_medications_dict.clear()
            collected_patients.add_severely_mismatched_patient(script_patient)


def scan_script_and_check_medications(collected_patients: CollectedPatients, scanned_input: str):
    script_as_xml = scan_script(scanned_input)
    script_patient_object: PillpackPatient = extract_patient_data(script_as_xml)
    if isinstance(script_patient_object, PillpackPatient):
        if not extend_existing_patient_medication_dict(script_patient_object, collected_patients):
            check_if_patient_is_in_pillpack_production(collected_patients.pillpack_patient_dict, script_patient_object, collected_patients)
        save_collected_patients(collected_patients)
        return True
    else:
        return False


def update_current_prns_and_linked_medications(patient: Models.PillpackPatient,
                                               collected_patients: CollectedPatients,
                                               prns_and_linked_medications: dict):
    if collected_patients.pillpack_patient_dict.__contains__(patient.last_name.lower()):
        key: str = patient.first_name.lower() + " " + patient.last_name.lower() + " " + str(patient.date_of_birth)
        prns_ignored_medications_sub_dict: dict = {
            Models.consts.PRN_KEY: patient.prn_medications_dict,
            Models.consts.LINKED_MEDS_KEY: patient.linked_medications
        }
        prns_and_linked_medications[key] = prns_ignored_medications_sub_dict
        save_prns_and_linked_medications(prns_and_linked_medications)
        logging.info("Updated patient {0} {1}'s PRNs and linked medications."
                     .format(patient.first_name, patient.last_name))


def save_collected_patients(collected_patients: CollectedPatients):
    save_to_file(collected_patients, Models.consts.COLLECTED_PATIENTS_FILE)


def save_prns_and_linked_medications(patient_prns_and_linked_medications_dict: dict):
    save_to_file(patient_prns_and_linked_medications_dict, Models.consts.PRNS_AND_LINKED_MEDICATIONS_FILE)


def save_to_file(object_to_save, filename):
    with open(filename, 'wb') as output:
        pickle.dump(object_to_save, output, consts.PROTOCOL)
        logging.info("Saved object {0} to pickle file {1} successfully.".format(object_to_save, filename))


def load_object(object_file_name: str):
    o = None
    try:
        with open(object_file_name, 'rb') as inpt:
            o = pickle.load(inpt)
            logging.info("Loaded file {0} into memory".format(object_file_name))
    except FileNotFoundError:
        o = None
        logging.error("No such file {0} detected. Could not load into memory".format(object_file_name))
    finally:
        return o


def load_collected_patients_from_object():
    collected_patients: CollectedPatients = load_object(Models.consts.COLLECTED_PATIENTS_FILE)
    if collected_patients is None:
        collected_patients = CollectedPatients()
    return collected_patients


def load_prns_and_linked_medications_from_object():
    prns_and_linked_medications: dict = load_object(Models.consts.PRNS_AND_LINKED_MEDICATIONS_FILE)
    if prns_and_linked_medications is None:
        prns_and_linked_medications = {}
    return prns_and_linked_medications


def load_settings():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    with open(application_path + "\\settings.yaml", 'r') as file:
        settings = file.read()
    return yaml.safe_load(settings)


def modify_pillpack_location(new_location: str):
    location_json = {"pillpackDataLocation": new_location}
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    with open(application_path + "\\settings.yaml", 'w') as file:
        yaml.dump(location_json, file, sort_keys=False)


def _scan_pillpack_folder(filepath: str):
    entities = scandir(filepath)
    return list(filter(lambda entity: entity.is_file() and entity.name.split(".")[1] == "ppc_processed", entities))


def _sanitise_and_encode_text_from_file(filename: str, separating_tag: str):
    if config is not None:
        raw_file = None
        list_of_strings = None
        try:
            raw_file = open(config["pillpackDataLocation"] + "\\" + filename, "rb")
            raw_binary = raw_file.read()
            raw_text = str(raw_binary)

            # This is a really horrible hack...wraps the xml in tags
            trimmed_text = "<" + raw_text.split("<", 1)[1].rsplit(">\\n", 1)[0] + ">"

            # Makes the content within the OrderInfo tags a bit more readable.
            sanitised_text = re.sub("</" + separating_tag + ">.*?<" + separating_tag + ">",
                                    "</" + separating_tag + ">\n<" + separating_tag + ">",
                                    trimmed_text,
                                    flags=re.DOTALL)

            # For some reason, pillpack adds a bunch of garbage text before the start of the XML tag.
            # This line removes all that crap so the XML can be interpreted correctly.
            sanitised_text = re.sub(r'^.*?<\?xml', "<?xml", sanitised_text)
            encoded_text = sanitised_text.encode('utf8').decode('unicode-escape')

            # Splits each OrderInfo tag and sets each of them as an element in a list.
            list_of_strings = encoded_text.split("</" + separating_tag + ">")
            for i in range(0, len(list_of_strings)):
                string = list_of_strings[i]
                if len(string) > 0:

                    # Utterly awful, primitive way of adding the xml version + encoding if it doesn't exist in the
                    # pillpack production file for some reason
                    if '<?xml version="1.0" encoding="utf-8"?>' not in string:
                        string = '<?xml version="1.0" encoding="utf-8"?>' + string

                    # Ditto for the OrderInfo closing tags
                    if '</' + separating_tag + '>' not in string:
                        string = string + '</' + separating_tag + '>'
                    if '<' + separating_tag + '>' in string:
                        list_of_strings[i] = string
                    else:
                        list_of_strings.pop(i)
                else:
                    list_of_strings.pop(i)
        except FileNotFoundError as e:
            logging.error("File not found: {0}".format(e))
        finally:
            try:
                raw_file.close()
            except AttributeError as e:
                logging.error("Attribute Error: {0}".format(e))
        return list_of_strings


def _remove_whitespace(node):
    if node.nodeType == minidom.Node.TEXT_NODE:
        if node.nodeValue.strip() == "":
            node.nodeValue = ""
    for child in node.childNodes:
        _remove_whitespace(child)


def _generate_medication_dict(medication_element):
    if isinstance(medication_element, minidom.Element):
        # Only requires the first instance of a medicine name tag
        medications = medication_element.getElementsByTagName("MedNm")[0]
        medication_name = medications.firstChild.nodeValue if medications.hasChildNodes() else ""

        # Since pillpack states each individual day that a medicine is to be taken, it is enough to just count the total
        # number of MedItemDose tags and obtain the number of days this way
        list_of_dosages = medication_element.getElementsByTagName("MedItemDose")
        number_of_days_to_take = list_of_dosages.length

        # Only require the first instance of a medication start date
        start_date = list_of_dosages[0].getElementsByTagName("TakeDt")[0]
        start_date_value = start_date.firstChild.nodeValue if start_date.hasChildNodes() else ""
        start_date_final = _create_datetime(start_date_value)

        # DoseList represents each moment in the day a medicine has to be taken; this is represented in the following
        # format: Time_of_day:Dose - if there are multiple times in the day a medicine needs to be taken, then these
        # will be separated by a semicolon, like this: ToD:Dose;AnotherToD:AnotherDose
        dosage_list = list_of_dosages[0].getElementsByTagName("DoseList")[0]
        dosage_list_value = dosage_list.firstChild.nodeValue if dosage_list.hasChildNodes() else ""

        # Because of this, we need to split each dosage entry by semicolons
        trimmed_dosage_list = list(filter(lambda entity: entity != "", dosage_list_value.split(";")))
        final_dosage: float = -1
        try:
            final_dosage = sum([float(e.split(":")[1]) for e in trimmed_dosage_list])
        except ValueError as e:
            logging.error("ValueError: {0}".format(e))
        total_dosage = number_of_days_to_take * final_dosage
        medication_object: Medication = Medication(medication_name, total_dosage, start_date_final)
        return medication_object
    else:
        logging.error("The medication parameter: {0} is not a valid XML element.".format(medication_element))
        return


def _create_datetime(date_string: str):
    date = datetime.date.today()
    try:
        date = datetime.date.fromisoformat(date_string)
    except ValueError as e:
        logging.error("Datetime could not be obtained from the given string: {0}".format(e))
    finally:
        return date


def _create_patient_object(order_element):
    if isinstance(order_element, minidom.Element):
        patient_name_element = order_element.getElementsByTagName("PtntNm")[0]
        patient_dob_element = order_element.getElementsByTagName("Birthday")[0]
        patient_full_name: list = patient_name_element.firstChild.nodeValue.split(
            ",") if patient_name_element.hasChildNodes() else []
        patient_first_name: str = patient_full_name[1].strip() if len(patient_full_name) > 0 else ""
        patient_last_name: str = patient_full_name[0].strip() if len(patient_full_name) > 0 else ""
        patient_dob_string: str = patient_dob_element.firstChild.nodeValue if patient_dob_element.hasChildNodes() else ""

        # There are no separators for day, month and year in the pillpack XML file, so these need to be added in
        # manually
        patient_dob_string = patient_dob_string[:4] + "-" + patient_dob_string[4:] if patient_dob_string != "" else ""
        patient_dob_string = patient_dob_string[:7] + "-" + patient_dob_string[7:] if patient_dob_string != "" else ""
        patient_dob = _create_datetime(patient_dob_string)

        patient_object = PillpackPatient(patient_first_name, patient_last_name, patient_dob)
        medication_items: list = order_element.getElementsByTagName("MedItem")
        start_date_list: list = []
        for medication in medication_items:
            medication_object = _generate_medication_dict(medication)
            start_date_list.append(medication_object.start_date)
            if isinstance(medication_object, Medication):
                _update_medication_dosage(patient_object, medication_object)
                patient_object.add_medication_to_production_dict(medication_object)

        # Sets the start date for the patient's medication cycle as the earliest date relative to now.
        patient_object.set_start_date(min(start_date_list))
        return patient_object
    else:
        logging.error("The order parameter: {0} is not a valid XML element. Actual type is {1}"
                      .format(order_element, type(order_element)))
        return None


def _parse_xml(list_of_orders_raw_text: list):
    order_information: list = []
    if list_of_orders_raw_text is not None:
        for order_raw_text in list_of_orders_raw_text:
            try:
                document = minidom.parseString(order_raw_text)
                _remove_whitespace(document)
                document.normalize()
                order_information.append(document.getElementsByTagName("OrderInfo"))
                logging.info("Parsed order from XML file")
            except xml.parsers.expat.ExpatError as e:
                logging.error("Could not parse order from XML file: {0}".format(e))
            except TypeError as e:
                logging.error("Could not parse order from XML file: {0}".format(e))
    return order_information


def _update_medication_dosage(patient_object: PillpackPatient, medication_object: Medication):
    if patient_object.production_medications_dict.__contains__(medication_object.medication_name):
        medication_to_update: Medication = patient_object.production_medications_dict[medication_object.medication_name]
        medication_to_update.dosage = medication_to_update.dosage + medication_object.dosage
        patient_object.production_medications_dict[medication_object.medication_name] = medication_to_update
        logging.info("Updated medication {0} dosage to {1}"
                     .format(medication_to_update.medication_name, medication_to_update.dosage))


def get_patient_medicine_data(prns_and_linked_medications: dict, separating_tag: str):
    if config is not None:
        ppc_processed_files = _scan_pillpack_folder(config["pillpackDataLocation"])
        dict_of_patients: dict = {}
        for ppc_file in ppc_processed_files:
            list_of_orders_raw_text = _sanitise_and_encode_text_from_file(ppc_file.name, separating_tag)
            list_of_orders: list = reduce(list.__add__, _parse_xml(list_of_orders_raw_text))
            for order in list_of_orders:
                patient_object = _create_patient_object(order)
                patient_object = retrieve_prns_and_linked_medications(patient_object, prns_and_linked_medications)
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


def get_patient_data_from_specific_file(prns_and_linked_medications: dict, specified_file_name: str,
                                        separating_tag: str):
    list_of_orders_raw_text = _sanitise_and_encode_text_from_file(specified_file_name, separating_tag)
    list_of_orders: list = reduce(list.__add__, _parse_xml(list_of_orders_raw_text))
    list_of_patients: list = []
    for order in list_of_orders:
        patient_object = _create_patient_object(order)
        patient_object = retrieve_prns_and_linked_medications(patient_object, prns_and_linked_medications)
        if isinstance(patient_object, PillpackPatient):
            list_of_patients.append(patient_object)
    return list_of_patients


def retrieve_prns_and_linked_medications(patient: PillpackPatient, prns_and_linked_medications: dict):
    key = patient.first_name + " " + patient.last_name + " " + str(patient.date_of_birth)
    if prns_and_linked_medications.__contains__(key.lower()):
        patient.prn_medications_dict = prns_and_linked_medications[key.lower()][Models.consts.PRN_KEY]
        patient.linked_medications = prns_and_linked_medications[key.lower()][Models.consts.LINKED_MEDS_KEY]
    return patient


def archive_pillpack_production(archive_file):
    if config is not None:
        ppc_processed_files = _scan_pillpack_folder(config["pillpackDataLocation"])
        pillpack_directory = config["pillpackDataLocation"] + "\\"
        with ZipFile(archive_file.name, 'w') as archived_production_data:
            for file in ppc_processed_files:
                archived_production_data.write(pillpack_directory + file.name)
                logging.info("Wrote file {0} to this production's archive".format(file.name))
                os.remove(pillpack_directory + file.name)
                logging.info("Removed file {0} from the pillpack directory {1}".format(file.name, pillpack_directory))
            os.remove(consts.COLLECTED_PATIENTS_FILE)
            logging.info("Removed the pickle file of this production")


config = load_settings()
patient_order_list: list
