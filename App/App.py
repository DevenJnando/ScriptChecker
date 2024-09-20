import os
import shutil
import tkinter
import logging
import sys
import typing
from zipfile import ZipFile

try:
    from multiprocessing import Queue
    from tkinter import font, filedialog
    from tkinter.ttk import Treeview
    from Functions.ModelFactory import get_patient_data_from_specific_file, get_patient_medicine_data_xml
    from Models import PillpackPatient, Medication
    from Repositories import CollectedPatients
    from AppObserver import Observer
    import HomeScreen
    import PatientDetails
    from WatchdogEventHandler import WatchdogEventHandler
    import ProductionDirectorySettings
    from Functions.ConfigSingleton import load_settings, consts, modify_pillpack_location
    from Functions.DAOFunctions import (load_collected_patients_from_object,
                                        load_prns_and_linked_medications_from_object,
                                        save_collected_patients)
    from watchdog.observers import Observer as WatchdogObserver
    from watchdog.events import FileCreatedEvent, FileMovedEvent
except Exception as e:
    logging.error("{0}".format(e))

if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
    logging.info("Script is running as a frozen executable at the following location: {0}"
                 .format(os.path.dirname(sys.executable)))
else:
    script_dir = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
    logging.info("Script is running on the python interpreter at the following location: {0}"
                 .format(os.path.dirname(os.path.abspath(__file__))))


logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler(script_dir + '\\logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)


logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

resources_dir = script_dir + "\\Resources"
icons_dir = resources_dir + "\\icons"
themes_dir = resources_dir + "\\themes"
collected_patients: CollectedPatients = CollectedPatients()


class App(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.config = load_settings()
        self.filesystem_observer = WatchdogObserver()
        self.current_directory_to_watch = None
        self.queue = Queue()
        self.style = tkinter.ttk.Style(self)
        self.tk.call("source", themes_dir + "\\" + "forest-dark.tcl")
        self.style.theme_use("forest-dark")
        self.geometry("1280x820")
        self.title("Pillpack Script Checker")
        self.minsize(1080, 720)
        self.maxsize(1280, 820)
        self.collected_patients = load_collected_patients_from_object()
        self.loaded_prns_and_linked_medications: dict = load_prns_and_linked_medications_from_object()
        self.app_observer: Observer = Observer()
        self.total_medications = 0
        self.title_font = font.Font(family='Verdana', size=28, weight="bold")
        self.container = tkinter.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.bind("<<WatchdogEvent>>", self.on_watchdog_event)
        if self.config["pillpackDataLocation"] == consts.UNSET_LOCATION:
            self.show_frame(consts.VIEW_PILLPACK_FOLDER_LOCATION)
        else:
            self.show_frame(consts.HOME_SCREEN)
            self.handler = WatchdogEventHandler(self)
            self.current_directory_to_watch = (
                self.filesystem_observer.schedule(self.handler, self.config["pillpackDataLocation"], recursive=False))
            self.filesystem_observer.start()
            logging.info("File system observer started in directory {0} successfully."
                         .format(self.config["pillpackDataLocation"]))

    def show_frame(self, view_name: str, patient_to_view: PillpackPatient = None):
        match view_name:
            case consts.HOME_SCREEN:
                for patient_view_name in list(self.app_observer.connected_views):
                    patient_view = self.app_observer.connected_views[patient_view_name]
                    if isinstance(patient_view, PatientDetails.PatientMedicationDetails):
                        self.app_observer.connected_views[patient_view_name].grid_remove()
                        self.app_observer.disconnect(patient_view_name)
                        patient_view.display_canvas.unbind_all("<MouseWheel>")
                        logging.info("Unbound mouse wheel from patient view {0}".format(patient_view_name))
                        patient_view.grid_remove()
                        logging.info("Disconnected patient view {0} from the application grid"
                                     .format(patient_view_name))
                        patient_view.destroy()
                        logging.info("Destroyed patient view {0}".format(patient_view_name))
                    else:
                        logging.warning("The view {0} was not of type PatientMedicationDetails"
                                        .format(patient_view_name))
                if self.app_observer.connected_views.__contains__(view_name):
                    frame: HomeScreen = self.app_observer.connected_views[view_name]
                    logging.info("Accessed home screen view {0} from application observer.".format(view_name))
                else:
                    frame: HomeScreen.HomeScreen = HomeScreen.HomeScreen(parent=self.container, master=self)
                    logging.info("No home screen view connected to application observer. "
                                 "A new home screen frame has been created.")
                    self.app_observer.connect(view_name, frame)
                    frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                frame.tkraise()
                logging.info("Home screen view is now the current view.")
            case consts.VIEW_PATIENT_SCREEN:
                if isinstance(patient_to_view, PillpackPatient):
                    key = view_name + patient_to_view.first_name + patient_to_view.last_name
                    if self.app_observer.connected_views.__contains__(key):
                        frame: PatientDetails.PatientMedicationDetails = self.app_observer.connected_views[key]
                        logging.info("Accessed patient view {0} from application observer.".format(key))
                    else:
                        frame: PatientDetails.PatientMedicationDetails = (PatientDetails.PatientMedicationDetails
                                                                          (parent=self.container, master=self,
                                                                           patient=patient_to_view)
                                                                          )
                        logging.info("No patient view connected to application observer. "
                                     "A new patient view has been created.")
                        self.app_observer.connect(key, frame)
                        frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                    frame.tkraise()
                    logging.info("Patient view {0} is now the current view.".format(key))
                else:
                    logging.warning("The object {0} was not of type PillpackPatient".format(patient_to_view))
            case consts.VIEW_PILLPACK_FOLDER_LOCATION:
                if self.app_observer.connected_views.__contains__(consts.VIEW_PILLPACK_FOLDER_LOCATION):
                    frame: ProductionDirectorySettings.ViewPillpackProductionFolder = self.app_observer.connected_views[
                        consts.VIEW_PILLPACK_FOLDER_LOCATION]
                    logging.info("Accessed pillpack location view from application observer")
                else:
                    frame: ProductionDirectorySettings.ViewPillpackProductionFolder = (
                        ProductionDirectorySettings.ViewPillpackProductionFolder(parent=self.container,
                                                                                 master=self))
                    logging.info("No pillpack location view connected to application observer. "
                                 "A new pillpack location view has been created")
                    self.app_observer.connect(consts.VIEW_PILLPACK_FOLDER_LOCATION, frame)
                    frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                frame.tkraise()
                logging.info("The pillpack location view is now the current view.")

    def set_pillpack_production_directory(self):
        directory = filedialog.askdirectory()
        directory = directory.replace("/", "\\")
        modify_pillpack_location(directory)
        self.config = load_settings()

    def on_watchdog_event(self, event):
        watchdog_event = self.queue.get()
        full_path = ""
        if isinstance(watchdog_event, FileCreatedEvent):
            full_path = str(watchdog_event.src_path)
        if isinstance(watchdog_event, FileMovedEvent):
            full_path = str(watchdog_event.dest_path)
        logging.info("Full path of file monitored by watchdog observer: {0}".format(full_path))
        split_file_name = full_path.rsplit('\\')
        file_name = split_file_name[len(split_file_name) - 1]
        file_extension = full_path.rsplit('.')[1]
        if file_extension == "ppc_processed":
            logging.info("The modified file has a ppc_processed file extension. Executing patient(s) update...")
            self.handler.extract_patient_data_from_ppc_xml(file_name)
            save_collected_patients(self.collected_patients)
            self.app_observer.update_all()
        elif file_extension == "fd":
            copied_zip_file_name = self.config["pillpackDataLocation"] + "\\farma_copy.zip"
            shutil.copyfile(watchdog_event.dest_path, copied_zip_file_name)
            with ZipFile(copied_zip_file_name, 'r') as farmadosis_zip:
                for info in farmadosis_zip.infolist():
                    if info.filename.endswith('.xml'):
                        with farmadosis_zip.open(info.filename) as binary_file:
                            self.handler.extract_patient_data_from_fd_xml(binary_file)
            os.remove(copied_zip_file_name)
            save_collected_patients(self.collected_patients)
            self.app_observer.update_all()

    def notify(self, event):
        self.queue.put(event)
        self.event_generate("<<WatchdogEvent>>", when="tail")
        logging.info("Watchdog event {0} has been added to the queue.".format(event))

    @staticmethod
    def match_patient_to_pillpack_patient(patient_to_be_matched: PillpackPatient, pillpack_patient_dict: dict):
        pillpack_patients: list = pillpack_patient_dict.get(
            patient_to_be_matched.last_name.lower())
        if pillpack_patients is None:
            pillpack_patients = []
        pillpack_patients = list(
            filter
            (lambda entity:
             typing.cast(PillpackPatient, entity).first_name.lower() == patient_to_be_matched.first_name.lower(),
             pillpack_patients)
        )
        matching_pillpack_patient: PillpackPatient = pillpack_patients[0] if (
                len(pillpack_patients) > 0) else patient_to_be_matched
        return matching_pillpack_patient


if __name__ == '__main__':
    try:
        app = App()
        app.mainloop()
        app.filesystem_observer.stop()
        if app.config["pillpackDataLocation"] != consts.UNSET_LOCATION:
            app.filesystem_observer.join()
    except Exception:
        raise
