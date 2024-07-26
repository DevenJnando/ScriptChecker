import os
import types

import yaml

consts = types.SimpleNamespace()
consts.SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
consts.MOCK_DATA_DIRECTORY = consts.SCRIPT_DIR + "\\MockData"
consts.BAD_XML_PPC = "bad_xml.ppc_processed"
consts.MOCK_PATIENT_XML = "mock_patient_xml.ppc_processed"
consts.MOCK_SCRIPT_XML = "mock_script_xml.txt"
consts.TEST_SETTINGS = consts.SCRIPT_DIR + "\\test_settings.yaml"
consts.PPC_SEPARATING_TAG = "OrderInfo"
consts.PRN_KEY = "prns_dict"
consts.LINKED_MEDS_KEY = "linked_meds_dict"
consts.MOCK_OBJECT_FILE = "mock_pickle_object.pk1"
consts.PERFECT_MATCH = "PERFECT_MATCH"
consts.IMPERFECT_MATCH = "IMPERFECT_MATCH"
consts.NO_MATCH = "NO_MATCH"


def populate_test_settings():
    location_json = {"pillpackDataLocation": consts.MOCK_DATA_DIRECTORY}
    with open(consts.TEST_SETTINGS, 'w') as file:
        yaml.dump(location_json, file, sort_keys=False)


def load_test_settings():
    with open(consts.TEST_SETTINGS, 'r') as file:
        settings = file.read()
    return yaml.safe_load(settings)

