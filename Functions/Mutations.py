import datetime
import logging
import re

from DataStructures.Models import PillpackPatient, Medication
from DataStructures.Repositories import CollectedPatients
from Functions.ConfigSingleton import consts
from Functions.XML import scan_script
from Functions.ModelBuilder import create_patient_object_from_script
from Functions.DAOFunctions import save_collected_patients


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
            matched_patient.surgery = script_patient.surgery
            check_script_medications_against_pillpack(matched_patient, script_patient, collected_patients)
            collected_patients.add_patient(matched_patient, consts.PERFECT_MATCH)
            collected_patients.add_matched_patient(matched_patient)
        elif isinstance(matched_patient, list) and len(matched_patient) > 0:
            for patient in matched_patient:
                patient.surgery = script_patient.surgery
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
                patient_from_production.add_medication_to_matched_dict(script_medication)
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
                substring_results = [key for key in patient_from_production.matched_medications_dict.keys()
                                     if medication in key]
                if len(substring_results) == 0:
                    if (not patient_from_production.prn_medications_dict.__contains__(medication)
                            and not patient_from_production.medications_to_ignore.__contains__(medication)
                            and not check_for_medication_linkage(patient_from_production.linked_medications, medication)):
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
                if patient_from_production.prn_medications_dict.__contains__(medication):
                    prn_medication: Medication = patient_from_production.prn_medications_dict[medication]
                    patient_from_production.add_medication_to_prns_for_current_cycle(prn_medication)
                linked_medication: Medication = check_for_linked_medications(script_medication_dict[medication],
                                                                             patient_from_production.linked_medications)
                if linked_medication is not None:
                    clear_medication_warning_dicts(patient_from_production, linked_medication)
                    clear_medication_warning_dicts(patient_from_production, medication)
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


def check_for_medication_linkage(linked_dict: dict, medication: Medication):
    linkage_exists: bool = False
    for value in linked_dict.values():
        if isinstance(value, Medication):
            if medication.__eq__(value):
                linkage_exists = True
                break
    return linkage_exists


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


def populate_script_patient_and_surgery_data(script_patient: PillpackPatient, production_patient: PillpackPatient):
    print(production_patient)
    if production_patient.script_id is None:
        production_patient.script_id = script_patient.script_id
        production_patient.script_issuer = script_patient.script_issuer
        production_patient.script_date = script_patient.script_date
        production_patient.middle_name = script_patient.middle_name
        production_patient.healthcare_no = script_patient.healthcare_no
        production_patient.title = script_patient.title
        production_patient.script_no = script_patient.script_no
        production_patient.address = script_patient.address
        production_patient.postcode = script_patient.postcode
        production_patient.doctor_id_no = script_patient.doctor_id_no
        production_patient.doctor_name = script_patient.doctor_name
        production_patient.surgery_id_no = script_patient.surgery_id_no
        production_patient.surgery = script_patient.surgery
        production_patient.surgery_address = script_patient.surgery_address
        production_patient.surgery_postcode = script_patient.surgery_postcode


def extend_existing_patient_medication_dict(patient_object: PillpackPatient, collected_patients: CollectedPatients):
    exists: bool = False
    if collected_patients.all_patients.__contains__(patient_object.last_name.lower()):
        list_of_wrappers: list = collected_patients.all_patients.get(patient_object.last_name.lower())
        for patient_wrapper in list_of_wrappers:
            if isinstance(patient_wrapper["PatientObject"], PillpackPatient):
                unwrapped_patient: PillpackPatient = patient_wrapper["PatientObject"]
                populate_script_patient_and_surgery_data(patient_object, unwrapped_patient)
                match patient_wrapper["Status"]:
                    case consts.PERFECT_MATCH:
                        if unwrapped_patient.__eq__(patient_object):
                            unwrapped_patient.surgery = patient_object.surgery
                            check_script_medications_against_pillpack(unwrapped_patient, patient_object,
                                                                      collected_patients)
                            exists = True
                            logging.info("Patient {0} {1} found in full patient dictionary. Patient is a perfect match."
                                         "Patient's medication dictionary has been updated."
                                         .format(patient_object.first_name, patient_object.last_name))
                            break
                        elif (unwrapped_patient.last_name == patient_object.last_name
                                and unwrapped_patient.first_name == patient_object.first_name):
                            unwrapped_patient.surgery = patient_object.surgery
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
                            unwrapped_patient.surgery = patient_object.surgery
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


def scan_script_and_check_medications(collected_patients: CollectedPatients, scanned_input: str):
    script_as_xml = scan_script(scanned_input)
    script_patient_object: PillpackPatient = create_patient_object_from_script(script_as_xml)
    if isinstance(script_patient_object, PillpackPatient):
        if not extend_existing_patient_medication_dict(script_patient_object, collected_patients):
            check_if_patient_is_in_pillpack_production(collected_patients.pillpack_patient_dict, script_patient_object, collected_patients)
        save_collected_patients(collected_patients)
        return True
    else:
        return False
