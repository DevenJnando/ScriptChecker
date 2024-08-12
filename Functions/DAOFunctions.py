import os
import pickle
import sys
from os import scandir
from zipfile import ZipFile
from Functions.ConfigSingleton import consts
from Models import PillpackPatient
from Repositories import CollectedPatients

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


def scan_pillpack_folder(filepath: str):
    entities = scandir(filepath)
    return list(filter(lambda entity: entity.is_file() and entity.name.split(".")[1] == "ppc_processed", entities))


def archive_pillpack_production(archive_file, config):
    if config is not None:
        ppc_processed_files = scan_pillpack_folder(config["pillpackDataLocation"])
        pillpack_directory = config["pillpackDataLocation"] + "\\"
        with ZipFile(archive_file.name, 'w') as archived_production_data:
            for file in ppc_processed_files:
                archived_production_data.write(pillpack_directory + file.name)
                logging.info("Wrote file {0} to this production's archive".format(file.name))
                os.remove(pillpack_directory + file.name)
                logging.info("Removed file {0} from the pillpack directory {1}".format(file.name, pillpack_directory))
            os.remove(consts.COLLECTED_PATIENTS_FILE)
            logging.info("Removed the pickle file of this production")


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
    collected_patients: CollectedPatients = load_object(consts.COLLECTED_PATIENTS_FILE)
    if collected_patients is None:
        collected_patients = CollectedPatients()
    return collected_patients


def load_prns_and_linked_medications_from_object():
    prns_and_linked_medications: dict = load_object(consts.PRNS_AND_LINKED_MEDICATIONS_FILE)
    if prns_and_linked_medications is None:
        prns_and_linked_medications = {}
    return prns_and_linked_medications


def save_collected_patients(collected_patients: CollectedPatients):
    save_to_file(collected_patients, consts.COLLECTED_PATIENTS_FILE)


def save_prns_and_linked_medications(patient_prns_and_linked_medications_dict: dict):
    save_to_file(patient_prns_and_linked_medications_dict, consts.PRNS_AND_LINKED_MEDICATIONS_FILE)


def update_current_prns_and_linked_medications(patient: PillpackPatient,
                                               collected_patients: CollectedPatients,
                                               prns_and_linked_medications: dict):
    if collected_patients.pillpack_patient_dict.__contains__(patient.last_name.lower()):
        key: str = patient.first_name.lower() + " " + patient.last_name.lower() + " " + str(patient.date_of_birth)
        prns_ignored_medications_sub_dict: dict = {
            consts.PRN_KEY: patient.prn_medications_dict,
            consts.LINKED_MEDS_KEY: patient.linked_medications
        }
        prns_and_linked_medications[key] = prns_ignored_medications_sub_dict
        save_prns_and_linked_medications(prns_and_linked_medications)
        logging.info("Updated patient {0} {1}'s PRNs and linked medications."
                     .format(patient.first_name, patient.last_name))


def retrieve_prns_and_linked_medications(patient: PillpackPatient, prns_and_linked_medications: dict):
    key = patient.first_name + " " + patient.last_name + " " + str(patient.date_of_birth)
    if prns_and_linked_medications.__contains__(key.lower()):
        patient.prn_medications_dict = prns_and_linked_medications[key.lower()][consts.PRN_KEY]
        patient.linked_medications = prns_and_linked_medications[key.lower()][consts.LINKED_MEDS_KEY]
    return patient


def save_to_file(object_to_save, filename):
    with open(filename, 'wb') as output:
        pickle.dump(object_to_save, output, consts.PROTOCOL)
        logging.info("Saved object {0} to pickle file {1} successfully.".format(object_to_save, filename))
