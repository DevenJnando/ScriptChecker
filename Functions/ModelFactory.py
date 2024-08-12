from functools import reduce
from Functions.XML import sanitise_and_encode_text_from_file, parse_xml
from Functions.DAOFunctions import scan_pillpack_folder, retrieve_prns_and_linked_medications
from Functions.ModelBuilder import create_patient_object_from_pillpack_data
from Models import PillpackPatient


def get_patient_medicine_data(prns_and_linked_medications: dict, separating_tag: str, config):
    if config is not None:
        ppc_processed_files = scan_pillpack_folder(config["pillpackDataLocation"])
        dict_of_patients: dict = {}
        for ppc_file in ppc_processed_files:
            list_of_orders_raw_text = sanitise_and_encode_text_from_file(ppc_file.name, separating_tag, config)
            list_of_orders: list = reduce(list.__add__, parse_xml(list_of_orders_raw_text))
            for order in list_of_orders:
                patient_object = create_patient_object_from_pillpack_data(order)
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
    list_of_orders_raw_text = sanitise_and_encode_text_from_file(specified_file_name, separating_tag)
    list_of_orders: list = reduce(list.__add__, parse_xml(list_of_orders_raw_text))
    list_of_patients: list = []
    for order in list_of_orders:
        patient_object = create_patient_object_from_pillpack_data(order)
        patient_object = retrieve_prns_and_linked_medications(patient_object, prns_and_linked_medications)
        if isinstance(patient_object, PillpackPatient):
            list_of_patients.append(patient_object)
    return list_of_patients
