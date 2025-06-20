from datetime import datetime
import os
import pickle
from os import scandir
from zipfile import ZipFile
from Functions.ConfigSingleton import consts
from DataStructures.Models import PillpackPatient
from DataStructures.Repositories import CollectedPatients

import logging


def scan_pillpack_folder(filepath: str):
    entities = None
    try:
        entities = scandir(filepath)
    except FileNotFoundError:
        entities = list()
    finally:
        return list(filter(lambda entity: entity.is_file() and entity.name.split(".")[1] == "ppc_processed", entities))


def archive_pillpack_production(archive_file, config, collected_patients: CollectedPatients):
    if config is not None:
        archive_file_name = consts.OBJECTS_PATH + "archived_production_{0}.pk1".format(datetime.today().date())
        ppc_processed_files = scan_pillpack_folder(config["pillpackDataLocation"])
        pillpack_directory = config["pillpackDataLocation"] + "\\"
        with ZipFile(archive_file.name, 'a') as archived_production_data:
            for file in ppc_processed_files:
                try:
                    os.remove(pillpack_directory + file.name)
                    logging.info("Removed file {0} from the pillpack directory {1}".format(file.name, pillpack_directory))
                except FileNotFoundError as e:
                    logging.exception("{0}\n Failed to located file...".format(e))
            try:
                save_to_file(collected_patients, archive_file_name)
                archived_production_data.write(archive_file_name)
                logging.info("Archived patient pickle file successfully.")
            except Exception as e:
                logging.error("Failed to write to production archive... {0}".format(e))
            try:
                os.remove(archive_file_name)
                os.remove(consts.COLLECTED_PATIENTS_FILE)
                logging.info("Removed the pickle file of this production")
            except Exception as e:
                logging.error("Failed to remove archive file and collected patients pickle file... {0}".format(e))


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


def load_collected_patients_from_zip_file(archived_production: ZipFile):
    o = None
    try:
        for info in archived_production.infolist():
            if info.filename.endswith('.pk1'):
                with archived_production.open(info.filename) as binary_file:
                    o = pickle.loads(binary_file.read())
                    logging.info("Loaded file {0} from archive {1} into memory".format(binary_file.name,
                                                                                       archived_production.filename))
                    break
    except Exception as e:
        o = None
        logging.error("{0} \nCould not load file from archive {1} into memory".format(e, archived_production.filename))
    finally:
        return o


def load_collected_patients_from_object():
    collected_patients: CollectedPatients = load_object(consts.COLLECTED_PATIENTS_FILE)
    if collected_patients is None:
        collected_patients = CollectedPatients()
    return collected_patients


def load_prns_and_linked_medications_from_object():
    print(consts.PRNS_AND_LINKED_MEDICATIONS_FILE)
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
    key = patient.first_name.lower() + " " + patient.last_name.lower() + " " + str(patient.date_of_birth)
    if prns_and_linked_medications.__contains__(key):
        patient.prn_medications_dict = prns_and_linked_medications[key][consts.PRN_KEY]
        patient.linked_medications = prns_and_linked_medications[key][consts.LINKED_MEDS_KEY]
    return patient


def save_to_file(object_to_save, filename):
    with open(filename, 'wb') as output:
        try:
            pickle.dump(object_to_save, output, pickle.HIGHEST_PROTOCOL)
            logging.info("Saved object {0} to pickle file {1} successfully.".format(object_to_save, filename))
        except Exception as e:
            logging.error("Failed to save object {0} to pickle file {1} due to exception {2}"
                          .format(object_to_save, filename, e))
