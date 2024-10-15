import logging
import App
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from Functions.DAOFunctions import save_collected_patients
from Functions.ModelFactory import get_patient_data_from_specific_file, get_patient_medicine_data_xml
from DataStructures.Models import PillpackPatient


class WatchdogEventHandler(FileSystemEventHandler):
    def __init__(self, application: App.App):
        FileSystemEventHandler.__init__(self)
        self.app: App.App = application

    def extract_patient_data_from_ppc_xml(self, file_name: str):
        list_of_patients = (get_patient_data_from_specific_file
                            (self.app.loaded_prns_and_linked_medications, file_name,
                             "OrderInfo",
                             self.app.config))
        self.update_existing_patient_dicts(list_of_patients)
        save_collected_patients(self.app.collected_patients)
        self.app.app_observer.update_all()

    def extract_patient_data_from_fd_xml(self, binary_file):
        list_of_patients: list = get_patient_medicine_data_xml(
            self.app.loaded_prns_and_linked_medications,
            binary_file.read()
        )
        self.update_existing_patient_dicts(list_of_patients)
        save_collected_patients(self.app.collected_patients)
        self.app.app_observer.update_all()

    def update_existing_patient_dicts(self, list_of_patients: list):
        for patient in list_of_patients:
            if isinstance(patient, PillpackPatient):
                patient_exists: bool = self.app.collected_patients.update_pillpack_patient_dict(patient)
                if not patient_exists:
                    logging.info("Patient {0} {1} does not exist in current production. "
                                 "Adding to production list...".format(patient.first_name, patient.last_name))
                    if self.app.collected_patients.pillpack_patient_dict.__contains__(patient.last_name.lower()):
                        logging.info("Patients with last name {0} already exists in dictionary. "
                                     "Adding new patient to this list.".format(patient.last_name))
                        list_of_patients: list = (self.app.collected_patients
                                                  .pillpack_patient_dict.get(patient.last_name.lower()))
                        list_of_patients.append(patient)
                        list_of_patients = list(dict.fromkeys(list_of_patients))
                        self.app.collected_patients.pillpack_patient_dict[patient.last_name.lower()] = list_of_patients
                        logging.info("Added new patient {0} {1} to the production list."
                                     .format(patient.first_name, patient.last_name))
                    else:
                        logging.info("No patient with last name {0} exists in dictionary. "
                                     "Creating new list of patients with this last name.".format(patient.last_name))
                        list_of_patients: list = [patient]
                        self.app.collected_patients.pillpack_patient_dict[patient.last_name.lower()] = list_of_patients
                        logging.info("Added new patient {0} {1} to the production list."
                                     .format(patient.first_name, patient.last_name))
                else:
                    logging.info("Patient {0} {1} exists in current production. Removing old script data..."
                                 .format(patient.first_name, patient.last_name))
                    self.app.collected_patients.remove_patient(patient)
                    self.app.collected_patients.remove_matched_patient(patient)
                    self.app.collected_patients.remove_minor_mismatched_patient(patient)
                    self.app.collected_patients.remove_severely_mismatched_patient(patient)
            else:
                logging.warning("Object {0} is not of type PillpackPatient".format(patient))

    def on_created(self, event: FileSystemEvent) -> None:
        self.app.notify(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self.app.notify(event)
