import datetime
from functools import reduce
from Functions.XML import sanitise_and_encode_text_from_file, parse_xml_ppc, parse_xml_fd
from Functions.DAOFunctions import scan_pillpack_folder, retrieve_prns_and_linked_medications
from Functions.ModelBuilder import create_patient_object_from_pillpack_data
from DataStructures.Models import PillpackPatient


def add_patient_to_dict(patient_object: PillpackPatient, dict_of_patients: dict):
    if isinstance(patient_object, PillpackPatient):
        if dict_of_patients.__contains__(patient_object.last_name.lower()):
            list_of_patients: list = dict_of_patients.get(patient_object.last_name.lower())
            list_of_patients.append(patient_object)
            list_of_patients = list(dict.fromkeys(list_of_patients))
            dict_of_patients[patient_object.last_name.lower()] = list_of_patients
        else:
            list_of_patients: list = [patient_object]
            dict_of_patients[patient_object.last_name.lower()] = list_of_patients


def get_patient_medicine_data_ppc(prns_and_linked_medications: dict, separating_tag: str, config,
                                  earliest_start_date: datetime.date = None):
    if config is not None:
        ppc_processed_files = scan_pillpack_folder(config["pillpackDataLocation"])
        dict_of_patients: dict = {}
        for ppc_file in ppc_processed_files:
            list_of_orders_raw_text = sanitise_and_encode_text_from_file(ppc_file.name, separating_tag, config)
            list_of_orders: list = reduce(list.__add__, parse_xml_ppc(list_of_orders_raw_text))
            for order in list_of_orders:
                patient_object = create_patient_object_from_pillpack_data(order)
                patient_object = retrieve_prns_and_linked_medications(patient_object, prns_and_linked_medications)
                match earliest_start_date:
                    case None:
                        add_patient_to_dict(patient_object, dict_of_patients)
                    case _:
                        if patient_object.start_date >= earliest_start_date:
                            add_patient_to_dict(patient_object, dict_of_patients)
        return dict_of_patients


def get_patient_medicine_data_xml(prns_and_linked_medications: dict, raw_xml):
    list_of_patients: list = []
    list_of_orders: list = reduce(list.__add__, parse_xml_fd(raw_xml))
    for order in list_of_orders:
        patient_object = create_patient_object_from_pillpack_data(order)
        patient_object = retrieve_prns_and_linked_medications(patient_object, prns_and_linked_medications)
        if isinstance(patient_object, PillpackPatient):
            list_of_patients.append(patient_object)
    return list_of_patients


def get_patient_data_from_specific_file(prns_and_linked_medications: dict, specified_file_name: str,
                                        separating_tag: str, config):
    list_of_orders_raw_text = sanitise_and_encode_text_from_file(specified_file_name, separating_tag, config)
    list_of_orders: list = reduce(list.__add__, parse_xml_ppc(list_of_orders_raw_text))
    list_of_patients: list = []
    for order in list_of_orders:
        patient_object = create_patient_object_from_pillpack_data(order)
        patient_object = retrieve_prns_and_linked_medications(patient_object, prns_and_linked_medications)
        if isinstance(patient_object, PillpackPatient):
            list_of_patients.append(patient_object)
    return list_of_patients
