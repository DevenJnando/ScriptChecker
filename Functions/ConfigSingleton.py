import os
import pickle
import sys
import types

import yaml

consts = types.SimpleNamespace()
consts.PERFECT_MATCH = "PERFECT_MATCH"
consts.IMPERFECT_MATCH = "IMPERFECT_MATCH"
consts.NO_MATCH = "NO_MATCH"
consts.PROTOCOL = pickle.HIGHEST_PROTOCOL
consts.UNSET_LOCATION = "Location not set"
consts.HOME_SCREEN = "HomeScreen"
consts.VIEW_PATIENT_SCREEN = "ViewPatientScreen"
consts.VIEW_PILLPACK_FOLDER_LOCATION = "ViewPillpackProductionFolder"
consts.SHOW_ALL_RESULTS_STRING = "All Patients"
consts.SHOW_ALL_RESULTS_CODE = 0
consts.READY_TO_PRODUCE_STRING = "Ready to produce"
consts.READY_TO_PRODUCE_CODE = 1
consts.NOTHING_TO_COMPARE_STRING = "Nothing to compare"
consts.NOTHING_TO_COMPARE_CODE = 2
consts.MISSING_MEDICATIONS_STRING = "Missing Medications"
consts.MISSING_MEDICATIONS_CODE = 3
consts.DO_NOT_PRODUCE_STRING = "Do not produce"
consts.DO_NOT_PRODUCE_CODE = 4
consts.MANUALLY_CHECKED_STRING = "Manually Checked"
consts.MANUALLY_CHECKED_CODE = 5
consts.PPC_SEPARATING_TAG = "OrderInfo"
consts.READY_TO_PRODUCE_CODE = 1
consts.NOTHING_TO_COMPARE = 2
consts.MISSING_MEDICATIONS = 3
consts.DO_NOT_PRODUCE = 4
consts.MANUALLY_CHECKED = 5
consts.PRN_KEY = "prns_dict"
consts.LINKED_MEDS_KEY = "linked_meds_dict"
consts.COLLECTED_PATIENTS_FILE = 'Patients.pk1'
consts.PRNS_AND_LINKED_MEDICATIONS_FILE = 'PrnsAndLinkedMeds.pk1'
warning_constants = types.SimpleNamespace()
warning_constants.PILLPACK_DATA_OVERWRITE_WARNING = "WARNING: You already have a pillpack production dataset open! " \
                                                    "If you reload the downloaded pillpack data, " \
                                                    "you will lose all data from any scanned in scripts. " \
                                                    "Are you sure you wish to continue?"
warning_constants.NO_LOADED_PILLPACK_DATA_WARNING = "You have not loaded any pillpack production data! " \
                                                    "It is highly recommended that you do this before " \
                                                    "scanning in scripts."

bookmark_constants = types.SimpleNamespace()
bookmark_constants.PRODUCTION_VIEW = 0
bookmark_constants.PERFECTLY_MATCHED_PATIENTS_VIEW = 1
bookmark_constants.MINOR_MISMATCH_PATIENTS_VIEW = 2
bookmark_constants.SEVERE_MISMATCH_PATIENTS_VIEW = 3


def load_settings():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__))))
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


config = load_settings()


def set_config(settings):
    global config
    config = settings
