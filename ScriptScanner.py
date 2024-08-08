import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)


logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

try:
    import datetime
    import os
    import threading
    import tkinter
    import types
    import typing
    from functools import reduce
    from tkinter.ttk import Treeview
    from tkinter import *
    from tkinter import font
    from tkinter import filedialog
    from multiprocessing import Queue
    from Functions.DAOFunctions import (load_collected_patients_from_object,
                                        load_prns_and_linked_medications_from_object,
                                        save_collected_patients,
                                        update_current_prns_and_linked_medications,
                                        archive_pillpack_production)
    from Functions.ConfigSingleton import config, modify_pillpack_location, load_settings, set_config
    from Functions.ModelFactory import get_patient_data_from_specific_file, get_patient_medicine_data
    from Functions.Mutations import scan_script_and_check_medications

    from watchdog.observers import Observer as WatchdogObserver
    from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileCreatedEvent, FileMovedEvent

    from Models import PillpackPatient, Medication, CollectedPatients
except:
    logger.exception(ImportError("Failed to import one or more libraries..."))
    exit(1)

consts = types.SimpleNamespace()
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

if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
    logging.info("Script is running as a frozen executable at the following location: {0}"
                 .format(os.path.dirname(sys.executable)))
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.info("Script is running on the python interpreter at the following location: {0}"
                 .format(os.path.dirname(os.path.abspath(__file__))))

resources_dir = script_dir + "\\Resources"
icons_dir = resources_dir + "\\icons"
themes_dir = resources_dir + "\\themes"
collected_patients: CollectedPatients = CollectedPatients()


class Observer:
    def __init__(self):
        self.connected_views: dict = {}

    def connect(self, view_name: str, view_to_connect: Frame):
        if not self.connected_views.__contains__(view_name):
            self.connected_views[view_name] = view_to_connect
            logging.info("Connected view: {0} to the application observer.".format(view_name))

    def disconnect(self, view_name: str):
        if self.connected_views.__contains__(view_name):
            self.connected_views.pop(view_name)
            logging.info("Disconnected view: {0} from the application observer.".format(view_name))

    def clear(self):
        self.connected_views.clear()
        logging.info("Cleared all views from application observer.")

    def update(self, key_of_view_to_update):
        if self.connected_views.__contains__(key_of_view_to_update):
            view_object = self.connected_views[key_of_view_to_update]
            update_method = getattr(view_object, "update", None)
            if callable(update_method):
                view_object.update()
                logging.info("The update method in the specified view ({0}) "
                             "was called successfully.".format(view_object))
            else:
                logging.error("The update method in the specified view ({0}) "
                              "could not be called because the update method is not callable."
                              .format(view_object))
        else:
            logging.warning("No view with the key: {0} is currently connected to the application observer."
                            .format(key_of_view_to_update))

    def update_all(self):
        for view_key in self.connected_views.keys():
            self.update(view_key)


class App(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.filesystem_observer = WatchdogObserver()
        self.queue = Queue()
        self.style = tkinter.ttk.Style(self)
        self.tk.call("source", themes_dir + "\\" + "forest-dark.tcl")
        self.style.theme_use("forest-dark")
        self.geometry("1080x720")
        self.title("Pillpack Script Checker")
        self.minsize(1080, 720)
        self.maxsize(1080, 720)
        self.collected_patients = load_collected_patients_from_object()
        self.loaded_prns_and_linked_medications: dict = load_prns_and_linked_medications_from_object()
        self.app_observer: Observer = Observer()
        self.total_medications = 0
        self.title_font = font.Font(family='Verdana', size=28, weight="bold")
        self.container = Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.bind("<<WatchdogEvent>>", self.on_watchdog_event)
        if config["pillpackDataLocation"] == consts.UNSET_LOCATION:
            self.show_frame(consts.VIEW_PILLPACK_FOLDER_LOCATION)
        else:
            self.show_frame(consts.HOME_SCREEN)
            handler = WatchdogEventHandler(self)
            self.filesystem_observer.schedule(handler, config["pillpackDataLocation"], recursive=False)
            self.filesystem_observer.start()
            logging.info("File system observer started in directory {0} successfully."
                         .format(config["pillpackDataLocation"]))

    def show_frame(self, view_name: str, patient_to_view: PillpackPatient = None):
        match view_name:
            case consts.HOME_SCREEN:
                for patient_view_name in list(self.app_observer.connected_views):
                    patient_view = self.app_observer.connected_views[patient_view_name]
                    if isinstance(patient_view, PatientMedicationDetails):
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
                    frame: HomeScreen = HomeScreen(parent=self.container, master=self)
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
                        frame: PatientMedicationDetails = self.app_observer.connected_views[key]
                        logging.info("Accessed patient view {0} from application observer.".format(key))
                    else:
                        frame: PatientMedicationDetails = PatientMedicationDetails(parent=self.container, master=self,
                                                                                   patient=patient_to_view)
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
                    frame: ViewPillpackProductionFolder = self.app_observer.connected_views[
                        consts.VIEW_PILLPACK_FOLDER_LOCATION]
                    logging.info("Accessed pillpack location view from application observer")
                else:
                    frame: ViewPillpackProductionFolder = ViewPillpackProductionFolder(parent=self.container,
                                                                                       master=self)
                    logging.info("No pillpack location view connected to application observer. "
                                 "A new pillpack location view has been created")
                    self.app_observer.connect(consts.VIEW_PILLPACK_FOLDER_LOCATION, frame)
                    frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                frame.tkraise()
                logging.info("The pillpack location view is now the current view.")

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
            list_of_patients = (get_patient_data_from_specific_file
                                (self.loaded_prns_and_linked_medications, file_name, "OrderInfo"))
            for patient in list_of_patients:
                if isinstance(patient, PillpackPatient):
                    patient_exists: bool = self.collected_patients.update_pillpack_patient_dict(patient)
                    if not patient_exists:
                        logging.info("Patient {0} {1} does not exist in current production. "
                                     "Adding to production list...".format(patient.first_name, patient.last_name))
                        if self.collected_patients.pillpack_patient_dict.__contains__(patient.last_name.lower()):
                            logging.info("Patients with last name {0} already exists in dictionary. "
                                         "Adding new patient to this list.".format(patient.last_name))
                            list_of_patients: list = (self.collected_patients
                                                      .pillpack_patient_dict.get(patient.last_name.lower()))
                            list_of_patients.append(patient)
                            list_of_patients = list(dict.fromkeys(list_of_patients))
                            self.collected_patients.pillpack_patient_dict[patient.last_name.lower()] = list_of_patients
                            logging.info("Added new patient {0} {1} to the production list."
                                         .format(patient.first_name, patient.last_name))
                        else:
                            logging.info("No patient with last name {0} exists in dictionary. "
                                         "Creating new list of patients with this last name.".format(patient.last_name))
                            list_of_patients: list = [patient]
                            self.collected_patients.pillpack_patient_dict[patient.last_name.lower()] = list_of_patients
                            logging.info("Added new patient {0} {1} to the production list."
                                         .format(patient.first_name, patient.last_name))
                    else:
                        logging.info("Patient {0} {1} exists in current production. Removing old script data..."
                                     .format(patient.first_name, patient.last_name))
                        self.collected_patients.remove_patient(patient)
                        self.collected_patients.remove_matched_patient(patient)
                        self.collected_patients.remove_minor_mismatched_patient(patient)
                        self.collected_patients.remove_severely_mismatched_patient(patient)
                else:
                    logging.warning("Object {0} is not of type PillpackPatient".format(patient))
            save_collected_patients(self.collected_patients)
            self.app_observer.update_all()

    def notify(self, event):
        self.queue.put(event)
        self.event_generate("<<WatchdogEvent>>", when="tail")
        logging.info("Watchdog event {0} has been added to the queue.".format(event))


class WatchdogEventHandler(FileSystemEventHandler):
    def __init__(self, application: App):
        FileSystemEventHandler.__init__(self)
        self.app = application

    def on_created(self, event: FileSystemEvent) -> None:
        self.app.notify(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self.app.notify(event)


class SideBar(Frame):
    def __init__(self, parent, master: App):
        Frame.__init__(self, parent)
        self.configure(width=50, height=master.winfo_height())
        self.master: App = master
        self.script_window = None
        self.view_patients_button = Button(self, text="Home Screen",
                                           command=lambda: self.master.show_frame(consts.HOME_SCREEN))
        self.view_patients_button.grid(row=0, column=0, pady=10)
        self.scan_scripts_button = Button(self, text="Scan Scripts",
                                          command=lambda: display_warning_if_pillpack_data_is_empty
                                          (self.master,
                                           self.open_scan_scripts_window,
                                           warning_constants.NO_LOADED_PILLPACK_DATA_WARNING))
        self.scan_scripts_button.grid(row=1, column=0, pady=50)
        self.archive_production_data_button = Button(self, text="Archive Production Data",
                                                     command=lambda: confirm_production_archival(self.master))
        self.archive_production_data_button.grid(row=2, column=0, pady=50)
        self.view_pillpack_folder_location_button = Button(self, text="View Pillpack Folder location",
                                                           command=lambda: self.master.show_frame
                                                           (consts.VIEW_PILLPACK_FOLDER_LOCATION))
        self.view_pillpack_folder_location_button.grid(row=3, column=0, pady=50)

    def open_scan_scripts_window(self):
        if self.script_window is None or not self.script_window.winfo_exists():
            self.script_window = ScanScripts(self, self.master)  # create window if its None or destroyed
            self.script_window.grab_set()
        else:
            self.script_window.focus()  # if window exists focus it


class HomeScreen(Frame):
    def __init__(self, parent, master: App):
        Frame.__init__(self, parent)
        self.tab_variable = tkinter.DoubleVar(value=75.0)
        self.font = font.Font(family='Verdana', size=14, weight="normal")
        self.master: App = master
        warning_image_path = icons_dir + "\\warning.png"
        warning_image = PhotoImage(file=warning_image_path)
        self.loading_message_thread: threading.Thread = threading.Thread(target=self.execute_loading_message)
        self.get_production_thread = threading.Thread(target=self.threaded_get_production_data)
        self.delete_loading_message_thread = threading.Thread(target=self.delete_loading_message)
        self.update_thread = threading.Thread(target=self.threaded_update)
        self.warning_image = warning_image.subsample(30, 30)
        ready_to_produce_path = icons_dir + "\\check.png"
        ready_to_produce = PhotoImage(file=ready_to_produce_path)
        self.ready_to_produce_image = ready_to_produce.subsample(30, 30)
        no_scripts_scanned_path = icons_dir + "\\question.png"
        no_scripts_scanned_image = PhotoImage(file=no_scripts_scanned_path)
        self.no_scripts_scanned_image = no_scripts_scanned_image.subsample(30, 30)
        do_not_produce_path = icons_dir + "\\remove.png"
        do_not_produce_image = PhotoImage(file=do_not_produce_path)
        self.do_not_produce_image = do_not_produce_image.subsample(30, 30)
        self.list_of_trees = []

        side_bar = SideBar(self, self.master)
        side_bar.pack(side="left", fill="both")

        container_frame = tkinter.ttk.Frame(self)
        container_frame.pack(side="top", fill="both")

        options_frame = tkinter.ttk.Frame(container_frame)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(2, weight=1)
        options_frame.grid(row=0, column=1, pady=(25, 5), sticky="ew")
        load_pillpack_image = icons_dir + "\\pillpack-data.png"
        load_pillpack_label = Label(options_frame, text="Load Pillpack Production Data", font=self.font, wraplength=150,
                                    justify="center")
        load_pillpack_button_image = PhotoImage(file=load_pillpack_image)
        self.pillpack_button_image = load_pillpack_button_image.subsample(5, 5)
        load_pillpack_button = Button(options_frame, image=self.pillpack_button_image,
                                      command=lambda: display_warning_if_pillpack_data_is_not_empty
                                      (self.master,
                                       self.threaded_production_data_retrieval,
                                       warning_constants.PILLPACK_DATA_OVERWRITE_WARNING)
                                      )
        load_pillpack_label.grid(row=1, column=0, sticky="nsew")
        load_pillpack_button.grid(row=2, column=0, sticky="nsew")

        scan_scripts_image = icons_dir + "\\scan_scripts.png"
        scan_scripts_label = Label(options_frame, text="Scan scripts", font=self.font, wraplength=100, justify="center")
        scan_scripts_button_image = PhotoImage(file=scan_scripts_image)
        self.scripts_button_image = scan_scripts_button_image.subsample(5, 5)
        scan_scripts_button = Button(options_frame, image=self.scripts_button_image,
                                     command=lambda: display_warning_if_pillpack_data_is_empty
                                     (self.master,
                                      self.open_scan_scripts_window,
                                      warning_constants.NO_LOADED_PILLPACK_DATA_WARNING)
                                     )
        scan_scripts_label.grid(row=1, column=1, sticky="nsew")
        scan_scripts_button.grid(row=2, column=1, sticky="nsew")

        archive_production_label = Label(options_frame, text="Archive production data", font=self.font, wraplength=120,
                                         justify="center")
        archive_production_image = icons_dir + "\\archive.png"
        archive_production_button_image = PhotoImage(file=archive_production_image)
        self.archive_button_production_image = archive_production_button_image.subsample(5, 5)
        archive_production_button = Button(options_frame, image=self.archive_button_production_image,
                                           command=lambda: confirm_production_archival(self.master, self))
        archive_production_label.grid(row=1, column=2, sticky="nsew")
        archive_production_button.grid(row=2, column=2, sticky="nsew")

        paned_window = tkinter.ttk.PanedWindow(container_frame)
        paned_window.grid(row=3, column=1, pady=(25, 5), sticky="nsew", rowspan=4)

        paned_frame = tkinter.ttk.Frame(paned_window)
        paned_window.add(paned_frame, weight=1)

        results_notebook = tkinter.ttk.Notebook(paned_frame)

        self.production_patients_results = tkinter.ttk.Frame(results_notebook)
        self.production_patients_results.columnconfigure(index=0, weight=1)
        self.production_patients_results.columnconfigure(index=1, weight=1)
        self.production_patients_results.rowconfigure(index=0, weight=1)
        self.production_patients_results.rowconfigure(index=1, weight=1)
        results_notebook.add(self.production_patients_results, text="Patients in Pillpack Production")

        self.columns = ('First Name',
                        'Last Name',
                        'Date of Birth',
                        'Start Date',
                        'No. of Medications',
                        'Condition')

        self.production_patients_tree = Treeview(self.production_patients_results,
                                                 columns=self.columns,
                                                 height=10)
        calibrate_width(self.production_patients_tree, self.columns, 125)
        self.production_patients_tree["displaycolumns"] = (
        'Date of Birth', 'Start Date', 'No. of Medications', 'Condition')
        self.detached_production_patient_nodes: list = []
        self.list_of_trees.append([self.production_patients_tree,
                                   self.production_patients_results,
                                   self.master.collected_patients.pillpack_patient_dict,
                                   self.detached_production_patient_nodes,
                                   consts.SHOW_ALL_RESULTS_STRING,
                                   consts.SHOW_ALL_RESULTS_CODE])

        self.perfect_match_patients = tkinter.ttk.Frame(results_notebook)
        results_notebook.add(self.perfect_match_patients, text="Perfectly Matched Patients")

        self.perfect_patients_tree = Treeview(self.perfect_match_patients,
                                              columns=self.columns,
                                              height=10)
        calibrate_width(self.perfect_patients_tree, self.columns, 125)
        self.perfect_patients_tree["displaycolumns"] = (
        'Date of Birth', 'Start Date', 'No. of Medications', 'Condition')
        self.detached_perfect_patient_nodes: list = []
        self.list_of_trees.append([self.perfect_patients_tree,
                                   self.perfect_match_patients,
                                   self.master.collected_patients.matched_patients,
                                   self.detached_perfect_patient_nodes,
                                   consts.SHOW_ALL_RESULTS_STRING,
                                   consts.SHOW_ALL_RESULTS_CODE])

        self.minor_mismatch_patients = tkinter.ttk.Frame(results_notebook)
        results_notebook.add(self.minor_mismatch_patients, text="Minor Mismatched Patients")

        self.imperfect_patients_tree = Treeview(self.minor_mismatch_patients,
                                                columns=self.columns,
                                                height=10)
        calibrate_width(self.imperfect_patients_tree, self.columns, 125)
        self.imperfect_patients_tree["displaycolumns"] = (
        'Date of Birth', 'Start Date', 'No. of Medications', 'Condition')
        self.detached_imperfect_patient_nodes: list = []
        self.list_of_trees.append([self.imperfect_patients_tree,
                                   self.minor_mismatch_patients,
                                   self.master.collected_patients.minor_mismatch_patients,
                                   self.detached_imperfect_patient_nodes,
                                   consts.SHOW_ALL_RESULTS_STRING,
                                   consts.SHOW_ALL_RESULTS_CODE])

        self.severe_mismatch_patients = tkinter.ttk.Frame(results_notebook)
        results_notebook.add(self.severe_mismatch_patients, text="Severely Mismatched Patients")

        self.mismatched_patients_tree = Treeview(self.severe_mismatch_patients,
                                                 columns=self.columns,
                                                 height=10)
        calibrate_width(self.mismatched_patients_tree, self.columns, 125)
        self.mismatched_patients_tree["displaycolumns"] = \
            ('Date of Birth', 'Start Date', 'No. of Medications', 'Condition')
        self.detatched_mismatched_patient_nodes = []
        self.list_of_trees.append([self.mismatched_patients_tree,
                                   self.severe_mismatch_patients,
                                   self.master.collected_patients.severe_mismatch_patients,
                                   self.detatched_mismatched_patient_nodes,
                                   consts.SHOW_ALL_RESULTS_STRING,
                                   consts.SHOW_ALL_RESULTS_CODE])

        self.set_tree_widgets()
        results_notebook.pack(expand=True, fill="both", padx=5, pady=5)

        self.update()
        self.script_window = None

    def threaded_production_data_retrieval(self):
        self.loading_message_thread: threading.Thread = threading.Thread(target=self.execute_loading_message)
        self.get_production_thread = threading.Thread(target=self.threaded_get_production_data)
        self.delete_loading_message_thread = threading.Thread(target=self.delete_loading_message)
        self.update_thread = threading.Thread(target=self.threaded_update)
        for thread in [self.loading_message_thread, self.get_production_thread,
                       self.delete_loading_message_thread, self.update_thread]:
            thread.daemon = True
            thread.start()

    def threaded_get_production_data(self):
        self.loading_message_thread.join()
        logging.info("Loading message thread finished.")
        self.master.collected_patients = CollectedPatients()
        populate_pillpack_production_data(self.master)
        return

    def execute_loading_message(self):
        for trees_results_and_dicts in self.list_of_trees:
            tree: Treeview = trees_results_and_dicts[0]
            key = "loading"
            tree.delete(*tree.get_children())
            tree.insert('', 'end', key, text=key)
            tree.set(key, 'First Name', "Loading...")
            tree.set(key, 'Last Name', "Loading...")
            tree.set(key, 'Date of Birth', "Loading...")
            tree.set(key, 'Start Date', "Loading...")
            tree.set(key, 'No. of Medications', "Loading...")
            tree.set(key, 'Condition', "Loading...")

    def delete_loading_message(self):
        self.get_production_thread.join()
        logging.info("Production data re-population finished.")
        for trees_results_and_dicts in self.list_of_trees:
            tree: Treeview = trees_results_and_dicts[0]
            key = "loading"
            tree.delete(key)
        return

    def threaded_update(self):
        self.delete_loading_message_thread.join()
        logging.info("Loading message removed from tree.")
        self.update()
        return

    def _update_list_of_trees(self):
        self.list_of_trees[0] = ([self.production_patients_tree,
                                  self.production_patients_results,
                                  self.master.collected_patients.pillpack_patient_dict,
                                  self.detached_production_patient_nodes,
                                  self.list_of_trees[0][4],
                                  self.list_of_trees[0][5]])
        self.list_of_trees[1] = ([self.perfect_patients_tree,
                                  self.perfect_match_patients,
                                  self.master.collected_patients.matched_patients,
                                  self.detached_perfect_patient_nodes,
                                  self.list_of_trees[1][4],
                                  self.list_of_trees[1][5]])
        self.list_of_trees[2] = ([self.imperfect_patients_tree,
                                  self.minor_mismatch_patients,
                                  self.master.collected_patients.minor_mismatch_patients,
                                  self.detached_imperfect_patient_nodes,
                                  self.list_of_trees[2][4],
                                  self.list_of_trees[2][5]])
        self.list_of_trees[3] = ([self.mismatched_patients_tree,
                                  self.severe_mismatch_patients,
                                  self.master.collected_patients.severe_mismatch_patients,
                                  self.detatched_mismatched_patient_nodes,
                                  self.list_of_trees[3][4],
                                  self.list_of_trees[3][5]])
        logging.info("Updated list of patient trees.")

    def set_tree_widgets(self):
        for i in range(len(self.list_of_trees)):
            tree: Treeview = self.list_of_trees[i][0]
            results_location = self.list_of_trees[i][1]
            associated_dict: dict = self.list_of_trees[i][2]
            detached_nodes: list = self.list_of_trees[i][3]

            tree.heading('#0', text="Patient Name")
            for col in self.columns:
                tree.heading(col, text=col)
            tree.bind('<Double-1>', lambda event, e=tree: self.on_treeview_double_click(e))
            filter_label = Label(results_location, font=self.font, text="Filter results: ")
            filter_combobox = tkinter.ttk.Combobox(results_location,
                                                   state="readonly",
                                                   font=self.font,
                                                   values=[consts.SHOW_ALL_RESULTS_STRING,
                                                           consts.READY_TO_PRODUCE_STRING,
                                                           consts.NOTHING_TO_COMPARE_STRING,
                                                           consts.MISSING_MEDICATIONS_STRING,
                                                           consts.DO_NOT_PRODUCE_STRING,
                                                           consts.MANUALLY_CHECKED_STRING
                                                           ]
                                                   )
            filter_combobox.current(self.list_of_trees[i][5])
            filter_combobox.bind("<<ComboboxSelected>>",
                                 lambda event, e=(filter_combobox, tree, associated_dict, i):
                                 self._on_filter_selected(e[0].get(), e[1], e[2], e[3]))
            search_variable: StringVar = StringVar()
            search_variable.trace("w",
                                  lambda name, index, mode, args=(tree, detached_nodes, search_variable):
                                  search_treeview(args[0], args[1], args[2])
                                  )
            search_bar_label = Label(results_location, font=self.font, text="Search: ")
            search_bar = Entry(results_location, width=50, textvariable=search_variable)
            scrollbar = tkinter.ttk.Scrollbar(results_location, orient='vertical', command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            filter_label.grid(row=0, column=0)
            filter_combobox.grid(row=1, column=0)
            search_bar_label.grid(row=2, column=0)
            search_bar.grid(row=3, column=0)
            tree.grid(row=4, column=0, sticky="ew")
            scrollbar.grid(row=4, column=1, sticky="ns")
            logging.info("Set all widgets for tree {0} using results from {1} and associated dictionary {2}. "
                         "Nodes currently detatched from tree {0}: {3}"
                         .format(tree, results_location, associated_dict, detached_nodes))

    def _refresh_patient_status(self):
        for patient_list in self.master.collected_patients.pillpack_patient_dict.values():
            if isinstance(patient_list, list):
                for patient in patient_list:
                    if isinstance(patient, PillpackPatient):
                        patient.determine_ready_to_produce_code()
                        logging.info("Patient {0} {1}'s status is {2}"
                                     .format(patient.first_name, patient.last_name, patient.ready_to_produce_code))

    def _refresh_treeview(self, tree_to_refresh: tkinter.ttk.Treeview, dictionary: dict):
        iterator = dictionary.values()
        for patient_list in iterator:
            if isinstance(patient_list, list):
                for patient in patient_list:
                    if isinstance(patient, PillpackPatient):
                        matching_pillpack_patient: PillpackPatient = (
                            match_patient_to_pillpack_patient
                            (patient, self.master.collected_patients.pillpack_patient_dict)
                        )
                        key = patient.first_name + " " + patient.last_name
                        if not tree_to_refresh.exists(key):
                            tree_to_refresh.insert('', 'end', key, text=key)
                            tree_to_refresh.set(key, 'First Name', patient.first_name)
                            tree_to_refresh.set(key, 'Last Name', patient.last_name)
                            logging.info("New Patient {0} {1} added to tree {2}"
                                         .format(patient.first_name, patient.last_name, tree_to_refresh))
                        if matching_pillpack_patient.date_of_birth == datetime.date.today():
                            tree_to_refresh.set(key, 'Date of Birth', "Not provided...")
                        else:
                            tree_to_refresh.set(key, 'Date of Birth', matching_pillpack_patient.date_of_birth)
                        if matching_pillpack_patient.start_date == datetime.date.today():
                            tree_to_refresh.set(key, 'Start Date',
                                                str(matching_pillpack_patient.start_date) + " URGENT")
                        else:
                            tree_to_refresh.set(key, 'Start Date', matching_pillpack_patient.start_date)
                        tree_to_refresh.set(key, 'No. of Medications', len(matching_pillpack_patient.production_medications_dict))
                        if matching_pillpack_patient.manually_checked_flag:
                            tree_to_refresh.set(key, 'Condition', "Manually Checked")
                            tree_to_refresh.item(key, image=self.ready_to_produce_image)
                        else:
                            if len(matching_pillpack_patient.incorrect_dosages_dict) > 0:
                                tree_to_refresh.set(key, 'Condition', "Incorrect dosages")
                                tree_to_refresh.item(key, image=self.do_not_produce_image)
                            elif len(matching_pillpack_patient.unknown_medications_dict) > 0:
                                tree_to_refresh.set(key, 'Condition', "Unknown medications")
                                tree_to_refresh.item(key, image=self.do_not_produce_image)
                            elif len(matching_pillpack_patient.missing_medications_dict) > 0:
                                tree_to_refresh.set(key, 'Condition', "Missing medications")
                                tree_to_refresh.item(key, image=self.warning_image)
                            elif (len(matching_pillpack_patient.matched_medications_dict)
                                  == len(matching_pillpack_patient.production_medications_dict)):
                                tree_to_refresh.set(key, 'Condition', "Ready to produce")
                                tree_to_refresh.item(key, image=self.ready_to_produce_image)
                            else:
                                tree_to_refresh.set(key, 'Condition', "No scripts yet scanned")
                                tree_to_refresh.item(key, image=self.no_scripts_scanned_image)
                    else:
                        logging.error("Item in patient list: {0} is not of type PillpackPatient".format(patient))
        sort_treeview(tree_to_refresh, "Last Name", False)

    def _filter_treeview(self, tree_to_filter: Treeview, dictionary_to_reference: dict, search_code: int = None):
        if search_code is not None:
            iterator = dictionary_to_reference.values()
            for patient_list in iterator:
                if isinstance(patient_list, list):
                    for patient in patient_list:
                        if isinstance(patient, PillpackPatient):
                            matching_pillpack_patient: PillpackPatient = (
                                match_patient_to_pillpack_patient
                                (patient, self.master.collected_patients.pillpack_patient_dict)
                            )
                            key = patient.first_name + " " + patient.last_name
                            if (tree_to_filter.exists(key)
                                    and matching_pillpack_patient.ready_to_produce_code != search_code):
                                tree_to_filter.delete(key)
                                logging.info("Removed patient {0} {1} from tree. The search code of the filter ({2}) "
                                             "did not match the patient's production status code ({3})."
                                             .format(patient.first_name, patient.last_name,
                                                     search_code, patient.ready_to_produce_code))
                        else:
                            logging.error("Item in patient list: {0} is not of type PillpackPatient".format(patient))
        else:
            self._refresh_treeview(tree_to_filter, dictionary_to_reference)

    def update(self):
        logging.info("HomeScreen update function called.")
        self._update_list_of_trees()
        self._refresh_patient_status()
        self.set_tree_widgets()
        for i in range(len(self.list_of_trees)):
            tree: Treeview = self.list_of_trees[i][0]
            associated_dict: dict = self.list_of_trees[i][2]
            self._refresh_treeview(tree, associated_dict)
            self._on_filter_selected(self.list_of_trees[i][4], tree, associated_dict, i)
        logging.info("HomeScreen update function call complete")

    def open_scan_scripts_window(self):
        if self.script_window is None or not self.script_window.winfo_exists():
            logging.info("No Scan Scripts view has been instantiated. Creating new Scan Scripts view...")
            self.script_window = ScanScripts(self, self.master)
            self.script_window.grab_set()
            self.script_window.attributes('-topmost', 'true')
        else:
            logging.info("Scan Scripts view is now in focus.")
            self.script_window.focus()

    def _on_filter_selected(self, selected_filter: str, treeview_to_filter: Treeview, dictionary_to_reference: dict,
                            tree_index: int):
        match selected_filter:
            case consts.SHOW_ALL_RESULTS_STRING:
                self.list_of_trees[tree_index][4] = consts.SHOW_ALL_RESULTS_STRING
                self.list_of_trees[tree_index][5] = consts.SHOW_ALL_RESULTS_CODE
                self._refresh_treeview(treeview_to_filter, dictionary_to_reference)
                logging.info("'All Results' patient filter has been applied.")
            case consts.NOTHING_TO_COMPARE_STRING:
                self.list_of_trees[tree_index][4] = consts.NOTHING_TO_COMPARE_STRING
                self.list_of_trees[tree_index][5] = consts.NOTHING_TO_COMPARE_CODE
                self._refresh_treeview(treeview_to_filter, dictionary_to_reference)
                self._filter_treeview(treeview_to_filter, dictionary_to_reference, consts.NOTHING_TO_COMPARE_CODE)
                logging.info("'Nothing Yet Scanned' patient filter has been applied.")
            case consts.MISSING_MEDICATIONS_STRING:
                self.list_of_trees[tree_index][4] = consts.MISSING_MEDICATIONS_STRING
                self.list_of_trees[tree_index][5] = consts.MISSING_MEDICATIONS_CODE
                self._refresh_treeview(treeview_to_filter, dictionary_to_reference)
                self._filter_treeview(treeview_to_filter, dictionary_to_reference, consts.MISSING_MEDICATIONS_CODE)
                logging.info("'Missing Medications' patient filter has been applied.")
            case consts.DO_NOT_PRODUCE_STRING:
                self.list_of_trees[tree_index][4] = consts.DO_NOT_PRODUCE_STRING
                self.list_of_trees[tree_index][5] = consts.DO_NOT_PRODUCE_CODE
                self._refresh_treeview(treeview_to_filter, dictionary_to_reference)
                self._filter_treeview(treeview_to_filter, dictionary_to_reference, consts.DO_NOT_PRODUCE_CODE)
                logging.info("'Do Not Produce' patient filter has been applied.")
            case consts.READY_TO_PRODUCE_STRING:
                self.list_of_trees[tree_index][4] = consts.READY_TO_PRODUCE_STRING
                self.list_of_trees[tree_index][5] = consts.READY_TO_PRODUCE_CODE
                self._refresh_treeview(treeview_to_filter, dictionary_to_reference)
                self._filter_treeview(treeview_to_filter, dictionary_to_reference, consts.READY_TO_PRODUCE_CODE)
                logging.info("'Ready to Produce' patient filter has been applied.")
            case consts.MANUALLY_CHECKED_STRING:
                self.list_of_trees[tree_index][4] = consts.MANUALLY_CHECKED_STRING
                self.list_of_trees[tree_index][5] = consts.MANUALLY_CHECKED_CODE
                self._refresh_treeview(treeview_to_filter, dictionary_to_reference)
                self._filter_treeview(treeview_to_filter, dictionary_to_reference, consts.MANUALLY_CHECKED_CODE)
                logging.info("'Manually Checked' patient filter has been applied.")

    def on_treeview_double_click(self, tree_to_select_from: Treeview):
        if isinstance(tree_to_select_from, Treeview):
            try:
                item = tree_to_select_from.focus()
                column_values = tree_to_select_from.item(item).get("values")
                first_name = column_values[0]
                last_name = column_values[1]
                patient_list = self.master.collected_patients.pillpack_patient_dict.get(last_name.lower())
                if isinstance(patient_list, list):
                    filtered_patients = (list
                                         (filter
                                          (lambda patient: patient.first_name.lower() == first_name.lower(),
                                           patient_list)
                                          )
                                         )
                    selected_patient = filtered_patients[0]
                    if isinstance(selected_patient, PillpackPatient):
                        self.master.show_frame(consts.VIEW_PATIENT_SCREEN, selected_patient)
                        logging.info("Patient {0} {1} selected through user double click. Patient view for this "
                                     "patient has been opened."
                                     .format(selected_patient.first_name, selected_patient.last_name))
                    else:
                        logging.error("Object {0} in filtered patient list is not of type PillpackPatient."
                                      .format(selected_patient))
            except IndexError as e:
                logging.error("Thrown IndexError: {0}".format(e))


class ViewPillpackProductionFolder(Frame):
    def __init__(self, parent, master: App):
        Frame.__init__(self, parent)
        self.master: App = master
        self.descriptor_font = font.Font(family='Verdana', size=20, weight="bold")
        self.folder_location_font = font.Font(family='Verdana', size=14, weight="normal")
        self.folder_location = config["pillpackDataLocation"]
        side_bar = SideBar(self, self.master)
        side_bar.pack(side="left", fill="both")
        container_frame = tkinter.ttk.Frame(self)
        container_frame.pack(side="top", fill="both")
        self.folder_descriptor_label = Label(container_frame, font=self.descriptor_font,
                                             text="Pillpack Production Folder Location:")
        self.folder_descriptor_label.grid(row=0, column=0)
        self.folder_location_string_var: StringVar = StringVar()
        self.folder_location_string_var.set(self.folder_location)
        self.folder_location_label = Label(container_frame, font=self.folder_location_font,
                                           textvariable=self.folder_location_string_var)
        self.folder_location_label.grid(row=1, column=0)
        self.change_pillpack_directory_button = Button(container_frame, text="Select pillpack directory",
                                                       command=lambda: [set_pillpack_production_directory(),
                                                                        self.update()])
        self.change_pillpack_directory_button.grid(row=2, column=0, pady=50)
        if config["pillpackDataLocation"] == consts.UNSET_LOCATION:
            warning_message: NoPillpackFolderLocationSetWarning = NoPillpackFolderLocationSetWarning(self)
            warning_message.grab_set()
            logging.warning("No directory for pillpack data has been set by the user.")

    def update(self):
        logging.info("ViewPillpackProductionFolder update function called.")
        self.folder_location = config["pillpackDataLocation"]
        self.folder_location_string_var.set(self.folder_location)
        handler = WatchdogEventHandler(self.master)
        self.master.filesystem_observer.schedule(handler, config["pillpackDataLocation"], recursive=False)
        self.master.filesystem_observer.start()
        logging.info("File system observer started in directory {0} successfully."
                     .format(config["pillpackDataLocation"]))
        logging.info("ViewPillpackProductionFolder update function call complete.")


class NoPillpackFolderLocationSetWarning(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("400x200")
        self.attributes('-topmost', 'true')
        self.parent = parent
        self.warning_label = Label(self, text="It looks like this is your first time using Script Checker!"
                                              " Please select where your pillpack production files are located"
                                              " by clicking 'Select pillpack directory' and navigating to the "
                                              " correct folder.",
                                   wraplength=300)
        self.ok_button = Button(self, text="OK", command=self.destroy)
        self.warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
        self.ok_button.grid(row=1, column=0, padx=50, sticky="ew")


class PatientMedicationDetails(Frame):
    def __init__(self, parent, master: App, patient: PillpackPatient):
        Frame.__init__(self, parent)
        self.link_medication_window = None
        self.unlink_medication_window = None
        self.change_toggle_button_image = None
        link_icon_path = icons_dir + "\\link.png"
        link_icon_image = PhotoImage(file=link_icon_path)
        self.linked_medication_image = link_icon_image.subsample(20, 20)
        self.do_not_produce_image = None
        self.missing_scripts_image = None
        self.no_scripts_scanned_image = None
        self.ready_to_produce_image = None
        self.font = font.Font(family='Verdana', size=14, weight="normal")
        self.home_screen: HomeScreen = parent
        self.master: App = master
        side_bar = SideBar(self, self.master)
        side_bar.pack(side="left", fill="both")
        self.patient_object: PillpackPatient = patient
        self.patient_tree_key = self.patient_object.first_name + " " + self.patient_object.last_name

        container_frame = tkinter.ttk.Frame(self)
        container_frame.pack(side="top", fill="both", expand=1)

        self.display_canvas = tkinter.Canvas(container_frame, width=2000)
        self.display_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.display_canvas.pack(side="left", fill="both", expand=1)

        my_scrollbar = tkinter.ttk.Scrollbar(self.display_canvas, orient=VERTICAL, command=self.display_canvas.yview)
        my_scrollbar.pack(side="right", fill=Y)

        self.display_canvas.configure(yscrollcommand=my_scrollbar.set)
        self.display_canvas.bind(
            '<Configure>', lambda e: self.display_canvas.configure(scrollregion=self.display_canvas.bbox("all"))
        )

        self.display_frame = tkinter.ttk.Frame(self.display_canvas, width=2000)

        patient_name_label = Label(self.display_frame, font=self.font,
                                   text=self.patient_tree_key + " (Start Date: " +
                                        str(self.patient_object.start_date) + ")")
        patient_name_label.grid(row=0, column=0)
        manually_checked_toggle_label = Label(self.display_frame, font=self.font,
                                              text="Scripts Checked Manually", wraplength=300)
        self.changes_toggle_button = Button(self.display_frame, command=self._on_manually_checked_button_click)
        manually_checked_toggle_label.grid(row=1, column=1)
        self.changes_toggle_button.grid(row=1, column=2)

        self.production_medication_frame = LabelFrame(self.display_frame)
        self.production_medication_frame.columnconfigure(0, weight=1)
        self.production_medication_frame.columnconfigure(1, weight=2)

        self.matched_medication_frame = LabelFrame(self.display_frame)
        self.matched_medication_frame.columnconfigure(0, weight=1)
        self.matched_medication_frame.columnconfigure(1, weight=2)

        self.prn_medications_frame = LabelFrame(self.display_frame)
        self.prn_medications_frame.columnconfigure(0, weight=1)
        self.prn_medications_frame.columnconfigure(1, weight=2)

        self.missing_medication_frame = LabelFrame(self.display_frame)
        self.missing_medication_frame.columnconfigure(0, weight=1)
        self.missing_medication_frame.columnconfigure(1, weight=2)

        self.unknown_medication_frame = LabelFrame(self.display_frame)
        self.unknown_medication_frame.columnconfigure(0, weight=1)
        self.unknown_medication_frame.columnconfigure(1, weight=2)

        self.incorrect_medication_dosage_frame = LabelFrame(self.display_frame)
        self.incorrect_medication_dosage_frame.columnconfigure(0, weight=1)
        self.incorrect_medication_dosage_frame.columnconfigure(1, weight=2)

        self.ignore_medications_frame = LabelFrame(self.display_frame)
        self.ignore_medications_frame.columnconfigure(0, weight=1)
        self.ignore_medications_frame.columnconfigure(1, weight=2)

        self.display_canvas.create_window((0, 0), window=self.display_frame, anchor="nw")

        self.update()

    def _on_mousewheel(self, event):
        self.display_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_manually_checked_button_click(self):
        self.patient_object.manually_checked(not self.patient_object.manually_checked_flag)
        logging.info("Patient Manually checked flag set to: {0}". format(self.patient_object.manually_checked_flag))
        save_collected_patients(self.master.collected_patients)
        self.master.app_observer.update_all()

    def _refresh_patient_status(self):
        self.patient_object.determine_ready_to_produce_code()

    def check_if_patient_is_ready_for_production(self):
        if self.patient_object.manually_checked_flag:
            on_button_path = icons_dir + "\\on-button.png"
            on_button_image = PhotoImage(file=on_button_path)
            self.change_toggle_button_image = on_button_image.subsample(10, 10)
            self.changes_toggle_button.config(image=self.change_toggle_button_image)
        else:
            off_button_path = icons_dir + "\\off-button.png"
            off_button_image = PhotoImage(file=off_button_path)
            self.change_toggle_button_image = off_button_image.subsample(10, 10)
            self.changes_toggle_button.config(image=self.change_toggle_button_image)

        match self.patient_object.ready_to_produce_code:
            case consts.READY_TO_PRODUCE_CODE:
                ready_to_produce_path = icons_dir + "\\check.png"
                ready_to_produce_image = PhotoImage(file=ready_to_produce_path)
                self.ready_to_produce_image = ready_to_produce_image.subsample(5, 5)
                ready_to_produce_label = Label(self.display_frame, font=self.font,
                                               image=self.ready_to_produce_image)
                ready_to_produce_label.grid(row=0, column=1)
            case consts.NOTHING_TO_COMPARE_CODE:
                no_scripts_scanned_path = icons_dir + "\\question.png"
                no_scripts_scanned_image = PhotoImage(file=no_scripts_scanned_path)
                self.no_scripts_scanned_image = no_scripts_scanned_image.subsample(5, 5)
                no_scripts_scanned_label = Label(self.display_frame, font=self.font,
                                                 image=self.no_scripts_scanned_image)
                no_scripts_scanned_label.grid(row=0, column=1)
            case consts.MISSING_MEDICATIONS_CODE:
                missing_scripts_path = icons_dir + "\\warning.png"
                missing_scripts_image = PhotoImage(file=missing_scripts_path)
                self.missing_scripts_image = missing_scripts_image.subsample(5, 5)
                missing_scripts_label = Label(self.display_frame, font=self.font,
                                              image=self.missing_scripts_image)
                missing_scripts_label.grid(row=0, column=1)
            case consts.DO_NOT_PRODUCE_CODE:
                do_not_produce_path = icons_dir + "\\remove.png"
                do_not_produce_image = PhotoImage(file=do_not_produce_path)
                self.do_not_produce_image = do_not_produce_image.subsample(5, 5)
                do_not_produce_label = Label(self.display_frame, font=self.font,
                                             image=self.do_not_produce_image)
                do_not_produce_label.grid(row=0, column=1)
            case consts.MANUALLY_CHECKED_CODE:
                ready_to_produce_path = icons_dir + "\\check.png"
                ready_to_produce_image = PhotoImage(file=ready_to_produce_path)
                self.ready_to_produce_image = ready_to_produce_image.subsample(5, 5)
                ready_to_produce_label = Label(self.display_frame, font=self.font,
                                               image=self.ready_to_produce_image, text="Proceed with caution")
                ready_to_produce_label.grid(row=0, column=1)

    def populate_label_frame(self, label_frame_to_populate: LabelFrame, frame_title: str,
                             row_number: int, dictionary_to_iterate: dict,
                             include_prn_medications_button: bool = False,
                             include_delete_prn_medications_button: bool = False,
                             create_medication_link_button: bool = False,
                             remove_from_ignored_medications_button=False
                             ):
        dictionary_values: list = list(dictionary_to_iterate.values())
        if len(dictionary_values) > 0:
            production_medication_label = Label(self.display_frame, text=frame_title)
            production_medication_label.grid(row=row_number, column=0, pady=20)
            label_frame_to_populate.grid(row=row_number + 1, column=0, padx=20, pady=20, sticky="ew")
            medication_name_label = Label(label_frame_to_populate, text="Medication Name")
            medication_name_label.grid(row=0, column=0)
            medication_dosage_label = Label(label_frame_to_populate, text="Dosage")
            medication_dosage_label.grid(row=0, column=1)
        for i in range(0, len(dictionary_values)):
            medication = dictionary_values[i]
            if isinstance(medication, Medication):
                logging.info("Displaying medication {0}".format(medication.medication_name))
                medication_name_label = Label(label_frame_to_populate, text=medication.medication_name,
                                              wraplength=200)
                medication_dosage_label = Label(label_frame_to_populate, text=medication.dosage)
                medication_name_label.grid(row=i + 1, column=0)
                medication_dosage_label.grid(row=i + 1, column=1)
                if self.patient_object.linked_medications.__contains__(medication.medication_name):
                    linked_medication: Medication = self.patient_object.linked_medications[medication.medication_name]
                    link_icon_label = Label(label_frame_to_populate, image=self.linked_medication_image)
                    link_icon_label.grid(row=i + 1, column=2)
                    unlink_button = Button(label_frame_to_populate, text="Unlink",
                                           command=lambda e=medication: self.open_unlink_medication_view(
                                               e.medication_name))
                    unlink_button.grid(row=i + 1, column=3)
                    create_tool_tip(link_icon_label, text=linked_medication.medication_name)
                    logging.info("Medication {0} is linked to medication {1}."
                                 .format(medication.medication_name, linked_medication.medication_name))
                if include_prn_medications_button:
                    make_prn_medication_button = Button(label_frame_to_populate, text="Set as PRN",
                                                        command=lambda e=medication:
                                                        self.set_medication_as_prn(e,
                                                                                   dictionary_to_iterate
                                                                                   )
                                                        )
                    make_prn_medication_button.grid(row=i + 1, column=3)
                    logging.info("Medication is not currently listed as a PRN.")
                if include_delete_prn_medications_button:
                    delete_prn_medication_button = Button(label_frame_to_populate, text="Remove from PRN list",
                                                          command=lambda e=medication: self.remove_prn_medication(e))
                    delete_prn_medication_button.grid(row=i + 1, column=5)
                    logging.info("Medication is currently listed as a PRN.")
                if create_medication_link_button:
                    ignore_medication_button = Button(label_frame_to_populate, text="Link Medication",
                                                      command=lambda e=medication:
                                                      self.open_link_medication_view(e)
                                                      )
                    ignore_medication_button.grid(row=i + 1, column=7)
                    logging.info("Medication can be linked to another medication brand.")
                if remove_from_ignored_medications_button:
                    remove_from_ignored_medications_button = Button(label_frame_to_populate, text="Dosage is incorrect",
                                                                    command=lambda e=medication:
                                                                    self.remove_medication_from_ignore_dict(e)
                                                                    )
                    remove_from_ignored_medications_button.grid(row=i + 1, column=9)
                    logging.info("Medication dosage {0} has been disregarded.".format(medication.dosage))

    def populate_incorrect_dosages_label_frame(self,
                                               incorrect_medication_dosage_frame,
                                               row_number: int
                                               ):
        incorrect_dosages_values = list(self.patient_object.incorrect_dosages_dict.values())
        if len(incorrect_dosages_values) > 0:
            incorrect_medication_dosage_label = Label(self.display_frame,
                                                      text="Incorrect Dosage Medications")
            incorrect_medication_dosage_label.grid(row=row_number, column=0, pady=20)
            self.incorrect_medication_dosage_frame.grid(row=row_number + 1, column=0, padx=20, pady=20, sticky="ew",
                                                        columnspan=2)
            incorrect_medication_dosage_name_label = Label(self.incorrect_medication_dosage_frame,
                                                           text="Medication Name")
            incorrect_medication_dosage_name_label.grid(row=0, column=0)
            incorrect_medication_dosage_in_production_label = Label(self.incorrect_medication_dosage_frame,
                                                                    text="Dosage in Production")
            incorrect_medication_dosage_in_production_label.grid(row=0, column=1)
            incorrect_medication_dosage_on_script_label = Label(self.incorrect_medication_dosage_frame,
                                                                text="Dosage on Script")
            incorrect_medication_dosage_on_script_label.grid(row=0, column=2)
        for i in range(0, len(incorrect_dosages_values)):
            medication = incorrect_dosages_values[i]
            if isinstance(medication, Medication):
                logging.warning("Medication {0} has a dosage on script inconsistent with the dosage in production."
                                .format(medication.medication_name))
                substring_results = [key for key in self.patient_object.production_medications_dict.keys() if
                                     key in medication.medication_name]
                if len(substring_results) > 0:
                    matching_key = substring_results[0]
                    if self.patient_object.production_medications_dict.__contains__(matching_key):
                        medication_in_production: Medication = self.patient_object.production_medications_dict.get(
                            matching_key
                        )
                        medication_name_label = Label(incorrect_medication_dosage_frame,
                                                      text=medication.medication_name)
                        medication_dosage_in_production_label = Label(incorrect_medication_dosage_frame,
                                                                      text=medication_in_production.dosage)
                        medication_dosage_on_script_label = Label(incorrect_medication_dosage_frame,
                                                                  text=medication.dosage)
                        add_to_ignore_list_button = Button(incorrect_medication_dosage_frame,
                                                           text="Ignore dosage inaccuracy",
                                                           command=lambda e=medication:
                                                           self.add_medication_to_ignore_dict(e))
                        medication_name_label.grid(row=i + 1, column=0)
                        medication_dosage_in_production_label.grid(row=i + 1, column=1)
                        medication_dosage_on_script_label.grid(row=i + 1, column=2)
                        add_to_ignore_list_button.grid(row=i + 1, column=3)
                        logging.warning("Dosage in production: {0} Dosage on script: {1}"
                                        .format(medication.dosage, medication_in_production.dosage))

    @staticmethod
    def clear_label_frame(frame_to_clear: LabelFrame):
        for widget in frame_to_clear.winfo_children():
            widget.destroy()
            logging.info("Destroyed widget {0} in frame {1}".format(widget, frame_to_clear))

    def open_link_medication_view(self, selected_medication: Medication):
        if self.link_medication_window is None or not self.link_medication_window.winfo_exists():
            logging.info("No Link Medication view has been instantiated. Creating new Scan Scripts view...")
            self.link_medication_window = LinkMedication(self, self.patient_object, selected_medication, self.master)
            self.link_medication_window.grab_set()
        else:
            self.link_medication_window.focus()
            logging.info("Link Medication view is now in focus.")

    def open_unlink_medication_view(self, medication_key: str):
        if self.unlink_medication_window is None or not self.link_medication_window.winfo_exists():
            logging.info("No Unlink Medication view has been instantiated. Creating new Unlink Medication view...")
            self.unlink_medication_window = UnlinkMedication(self, self.patient_object, medication_key, self.master)
            self.unlink_medication_window.grab_set()
        else:
            self.unlink_medication_window.focus()
            logging.info("Unlink Medication is now in focus.")

    def set_medication_as_prn(self, selected_medication: Medication, medication_dict: dict):
        if medication_dict.__contains__(selected_medication.medication_name):
            medication_dict.pop(selected_medication.medication_name)
        self.patient_object.add_medication_to_prn_dict(selected_medication)
        save_collected_patients(self.master.collected_patients)
        update_current_prns_and_linked_medications(self.patient_object,
                                                   self.master.collected_patients,
                                                   self.master.loaded_prns_and_linked_medications)
        self.master.app_observer.update_all()

    def remove_prn_medication(self, selected_medication: Medication):
        if self.patient_object.prn_medications_dict.__contains__(selected_medication.medication_name):
            self.patient_object.remove_medication_from_prn_dict(selected_medication)
            if self.patient_object.production_medications_dict.__contains__(selected_medication.medication_name):
                self.patient_object.add_medication_to_missing_dict(selected_medication)
            else:
                self.patient_object.add_medication_to_unknown_dict(selected_medication)
            save_collected_patients(self.master.collected_patients)
            update_current_prns_and_linked_medications(self.patient_object,
                                                       self.master.collected_patients,
                                                       self.master.loaded_prns_and_linked_medications)
            self.master.app_observer.update_all()

    def add_medication_to_ignore_dict(self, selected_medication: Medication):
        self.patient_object.add_medication_to_ignore_dict(selected_medication)
        save_collected_patients(self.master.collected_patients)
        update_current_prns_and_linked_medications(self.patient_object,
                                                   self.master.collected_patients,
                                                   self.master.loaded_prns_and_linked_medications)
        self.master.app_observer.update_all()

    def remove_medication_from_ignore_dict(self, selected_medication: Medication):
        if self.patient_object.medications_to_ignore.__contains__(selected_medication.medication_name):
            correct_dosage_medication: Medication = self.patient_object.production_medications_dict[
                selected_medication.medication_name]
            self.patient_object.remove_medication_from_ignore_dict(selected_medication, correct_dosage_medication)
            save_collected_patients(self.master.collected_patients)
            update_current_prns_and_linked_medications(self.patient_object,
                                                       self.master.collected_patients,
                                                       self.master.loaded_prns_and_linked_medications)
            self.master.app_observer.update_all()

    def update(self):
        logging.info("PatientMedicationDetails update function called.")
        self._refresh_patient_status()
        self.check_if_patient_is_ready_for_production()
        self.clear_label_frame(self.production_medication_frame)
        self.clear_label_frame(self.matched_medication_frame)
        self.clear_label_frame(self.missing_medication_frame)
        self.clear_label_frame(self.prn_medications_frame)
        self.clear_label_frame(self.unknown_medication_frame)
        self.clear_label_frame(self.incorrect_medication_dosage_frame)
        self.clear_label_frame(self.ignore_medications_frame)
        self.populate_label_frame(self.production_medication_frame,
                                  "Repeat Pillpack Medications",
                                  1,
                                  self.patient_object.production_medications_dict
                                  )
        self.populate_label_frame(self.matched_medication_frame,
                                  "Matched Medications",
                                  3,
                                  self.patient_object.matched_medications_dict
                                  )
        self.populate_label_frame(self.prn_medications_frame,
                                  "PRN Medications Outside Pillpack",
                                  5,
                                  self.patient_object.prn_medications_dict,
                                  False, True
                                  )
        self.populate_label_frame(self.missing_medication_frame,
                                  "Missing Medications",
                                  7,
                                  self.patient_object.missing_medications_dict,
                                  True, False,
                                  )
        self.populate_label_frame(self.unknown_medication_frame,
                                  "Unknown Medications",
                                  9,
                                  self.patient_object.unknown_medications_dict,
                                  True, False,
                                  True
                                  )
        self.populate_label_frame(self.ignore_medications_frame,
                                  "Ignored Incorrect Dosages",
                                  11,
                                  self.patient_object.medications_to_ignore,
                                  False, False,
                                  False, True
                                  )
        self.populate_incorrect_dosages_label_frame(self.incorrect_medication_dosage_frame,
                                                    13)
        self.display_canvas.update_idletasks()
        self.display_canvas.config(scrollregion=self.display_frame.bbox())
        logging.info("PatientMedicationDetails update function call complete.")


class LinkMedication(Toplevel):
    def __init__(self, parent, patient: PillpackPatient,
                 medication: Medication, master: App):
        super().__init__(parent)
        self.attributes('-topmost', 'true')
        self.missing_medications_tree = Treeview(self,
                                                 columns='Dosage',
                                                 height=10)
        self.missing_medications_tree.heading('#0', text="Medication Name")
        self.missing_medications_tree.heading('Dosage', text="Dosage")
        self.geometry("1000x500")
        self.selectable_medications: list = []
        self.selected_patient: PillpackPatient = patient
        self.linking_medication: Medication = medication
        self.application: App = master
        self.parent = parent
        self.linkage_label = Label(self,
                                   text="Select which medication you wish to link to " +
                                        self.linking_medication.medication_name,
                                   wraplength=200)
        self.determine_selectable_medications()
        self.create_selectable_medications_tree()
        self.missing_medications_tree.bind('<Double-1>',
                                           lambda e: self.confirm_linkage(self.missing_medications_tree.focus())
                                           )
        self.linkage_label.pack(side="top", fill="both", pady=20, padx=20)
        self.missing_medications_tree.pack(side="top", fill="both", pady=20, padx=20)

    def determine_selectable_medications(self):
        for medication in self.selected_patient.missing_medications_dict.keys():
            medication_object: Medication = self.selected_patient.missing_medications_dict[medication]
            if medication_object.dosage == self.linking_medication.dosage:
                self.selectable_medications.append(medication_object)
                logging.info("Medication {0} can be linked with {1}. Dosages match."
                             .format(medication_object.medication_name, self.linking_medication.medication_name))

    def create_selectable_medications_tree(self):
        for medication in self.selectable_medications:
            self.missing_medications_tree.insert('', 'end', medication.medication_name,
                                                 text=medication.medication_name)
            self.missing_medications_tree.set(medication.medication_name, "Dosage", medication.dosage)

    def confirm_linkage(self, selected_medication: str):
        for medication in self.selectable_medications:
            if medication.medication_name == selected_medication:
                selected_medication_object: Medication = medication
                confirmation_box = Toplevel(self)
                confirmation_box.attributes('-topmost', 'true')
                confirmation_box.geometry("600x400")
                confirmation_label = Label(confirmation_box, text="You are about to link "
                                                                  + self.linking_medication.medication_name
                                                                  + " to "
                                                                  + selected_medication
                                                                  + ". \n"
                                                                  + "This means that for this patient, "
                                                                  + self.linking_medication.medication_name
                                                                  + " will be considered the same medication as "
                                                                  + selected_medication
                                                                  + ". \n"
                                                                  + "Do you wish to continue?",
                                           wraplength=300)
                confirmation_button = Button(confirmation_box, text="OK",
                                             command=lambda: [self.link_medication(selected_medication_object),
                                                              self.parent.update(),
                                                              confirmation_box.destroy(),
                                                              self.destroy()]
                                             )
                cancel_button = Button(confirmation_box, text="Cancel",
                                       command=lambda: [confirmation_box.destroy(),
                                                        self.destroy()])
                confirmation_label.grid(row=0, column=0, pady=25, sticky="ew")
                confirmation_button.grid(row=1, column=0, padx=50, sticky="ew")
                cancel_button.grid(row=1, column=1, padx=50, sticky="ew")
                break

    def link_medication(self, selected_medication: Medication):
        self.selected_patient.add_medication_link(self.linking_medication, selected_medication)
        save_collected_patients(self.application.collected_patients)
        update_current_prns_and_linked_medications(self.selected_patient,
                                                   self.application.collected_patients,
                                                   self.application.loaded_prns_and_linked_medications)
        self.application.app_observer.update_all()


class UnlinkMedication(Toplevel):
    def __init__(self, parent, patient: PillpackPatient,
                 medication_key: str, master: App):
        super().__init__(parent)
        self.attributes('-topmost', 'true')
        self.selected_patient: PillpackPatient = patient
        self.medication_key_to_be_unlinked: str = medication_key
        if self.selected_patient.linked_medications[medication_key] is not None:
            self.medication_to_be_unlinked: Medication = self.selected_patient.linked_medications[medication_key]
        else:
            self.medication_to_be_unlinked: Medication = Medication("Invalid Medication", 0,
                                                                    self.medication_to_be_unlinked.start_date)
        self.application: App = master
        self.parent = parent
        self.geometry("600x400")
        self.confirmation_label = Label(self,
                                        text="Are you sure you wish to unlink "
                                             + self.medication_key_to_be_unlinked + " from "
                                             + self.medication_to_be_unlinked.medication_name + " ?",
                                        wraplength=200)
        self.confirmation_button = Button(self, text="OK", command=lambda: [self.unlink_medication(),
                                                                            self.parent.update(),
                                                                            self.destroy()])
        self.cancel_button = Button(self, text="Cancel", command=self.destroy)
        self.confirmation_label.grid(row=0, column=0, sticky="ew")
        self.confirmation_button.grid(row=1, column=0, sticky="ew")
        self.cancel_button.grid(row=1, column=1, sticky="ew")

    def unlink_medication(self):
        if self.selected_patient.matched_medications_dict.__contains__(self.medication_key_to_be_unlinked):
            medication_in_key: Medication = self.selected_patient.matched_medications_dict[
                self.medication_key_to_be_unlinked]
            self.selected_patient.remove_medication_link(medication_in_key)
            save_collected_patients(self.application.collected_patients)
            update_current_prns_and_linked_medications(self.selected_patient,
                                                       self.application.collected_patients,
                                                       self.application.loaded_prns_and_linked_medications)
            self.application.app_observer.update_all()


class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.text = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        self.text = text
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tip_window = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(tw, text=self.text, justify=LEFT,
                      background="#ffffe0", foreground="#000000", relief=SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class ScanScripts(Toplevel):
    def __init__(self, parent, master: App):
        super().__init__(parent)
        self.attributes('-topmost', 'true')
        warning_image_path = icons_dir + "\\warning.png"
        warning_image = PhotoImage(file=warning_image_path)
        self.warning_image = warning_image.subsample(40, 40)
        ready_to_produce_path = icons_dir + "\\check.png"
        ready_to_produce = PhotoImage(file=ready_to_produce_path)
        self.ready_to_produce = ready_to_produce.subsample(40, 40)
        self.patient_tree = None
        self.matched_patients = None
        self.minor_mismatched_patients = None
        self.severe_mismatched_patients = None
        self.main_application: App = master
        self.parent = parent
        self.reduced_patients = []
        self.geometry("400x300")
        self.label = Label(self, text="Scan scripts below: ")
        self.label.pack(padx=20, pady=20)
        self.entry = Entry(self, width=400)
        self.entry.bind("<Return>", lambda func: [self.scan_scripts(self.main_application, self.entry.get()),
                                                  self.main_application.app_observer.update_all()])
        self.entry.pack(padx=20, pady=20)

        all_patients: list = list(self.main_application.collected_patients.pillpack_patient_dict.values())
        if len(all_patients) > 0:
            self.reduced_patients: list = reduce(list.__add__, all_patients)
        else:
            self.reduced_patients: list = []

        self.patient_tree = Treeview(self, columns=('No. of Patients',), height=3)
        self.patient_tree.heading('No. of Patients', text="No. of Patients")
        self.patient_tree.insert('', 'end', 'perfect_matches', text="Perfect Matches", tags=('perfect',))
        self.__iterate_patients(self.main_application.collected_patients.matched_patients.values(),
                                'perfect_matches')
        self.patient_tree.insert('', 'end', 'minor_mismatches', text="Minor Mismatches", tags=('minor',))
        self.__iterate_patients(self.main_application.collected_patients.minor_mismatch_patients.values(),
                                'minor_mismatches')
        self.patient_tree.insert('', 'end', 'severe_mismatches', text="Severe Mismatches", tags=('severe',))
        self.__iterate_patients(self.main_application.collected_patients.severe_mismatch_patients.values(),
                                'severe_mismatches')
        self.patient_tree.tag_configure('perfect', background='#2f8000')
        self.patient_tree.tag_configure('minor', background='#a8a82c')
        self.patient_tree.tag_configure('severe', background='#a30202')
        self.patient_tree.set('perfect_matches', 'No. of Patients',
                              str(len(self.main_application.collected_patients.matched_patients)) + "/"
                              + str(len(self.reduced_patients)))
        self.patient_tree.set('minor_mismatches', 'No. of Patients',
                              str(len(self.main_application.collected_patients.minor_mismatch_patients)) + "/"
                              + str(len(self.reduced_patients)))
        self.patient_tree.set('severe_mismatches', 'No. of Patients',
                              len(self.main_application.collected_patients.severe_mismatch_patients))
        self.patient_tree.bind('<Double-1>', self.on_treeview_double_click)
        self.patient_tree.pack(padx=20)

    def scan_scripts(self, application: App, script_input: str):
        logging.info("Scanning script...")
        if scan_script_and_check_medications(application.collected_patients, script_input):
            logging.info("Patient information retrieved from scanned script successfully.")
            self.patient_tree.set('perfect_matches', 'No. of Patients',
                                  str(len(self.main_application.collected_patients.matched_patients)) + "/"
                                  + str(len(self.reduced_patients)))
            self.__iterate_patients(application.collected_patients.matched_patients.values(), 'perfect_matches')
            self.patient_tree.set('minor_mismatches', 'No. of Patients',
                                  str(len(self.main_application.collected_patients.minor_mismatch_patients)) + "/"
                                  + str(len(self.reduced_patients)))
            self.__iterate_patients(application.collected_patients.minor_mismatch_patients, 'minor_mismatches')
            self.patient_tree.set('severe_mismatches', 'No. of Patients',
                                  len(application.collected_patients.severe_mismatch_patients))
            self.__iterate_patients(application.collected_patients.severe_mismatch_patients, 'severe_mismatches')
        else:
            logging.warning("Could not retrieve patient information from scanned script.")
            warning = Toplevel(master=self.master)
            warning.attributes('-topmost', 'true')
            warning.geometry("400x200")
            warning_label = Label(warning, text="Failed to interpret script XML...",
                                  wraplength=300)
            warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
            ok_button = Button(warning, text="OK", command=warning.destroy)
            ok_button.grid(row=1, column=0, padx=50, sticky="ew", columnspan=2)
            warning.grab_set()
        self.entry.delete(0, tkinter.END)
        self.entry.focus()

    def __iterate_patients(self, iterator, tree_parent_id):
        for patient_list in iterator:
            if isinstance(patient_list, list):
                for patient in patient_list:
                    if isinstance(patient, PillpackPatient):
                        matching_pillpack_patient: PillpackPatient = (
                            match_patient_to_pillpack_patient
                            (patient, self.main_application.collected_patients.pillpack_patient_dict)
                        )
                        if self.patient_tree.exists(patient.first_name + " " + patient.last_name):
                            logging.info("Patient {0} {1} exists within {2}."
                                         .format(patient.first_name, patient.last_name, iterator))
                            if len(patient.matched_medications_dict) == len(matching_pillpack_patient.production_medications_dict):
                                self.patient_tree.item(patient.first_name + " " + patient.last_name,
                                                       text=patient.first_name + " " + patient.last_name,
                                                       image=self.ready_to_produce)
                                logging.info("Patient {0} {1} is ready to produce."
                                             .format(patient.first_name, patient.last_name))
                            else:
                                self.patient_tree.item(patient.first_name + " " + patient.last_name,
                                                       text=patient.first_name + " " + patient.last_name,
                                                       image=self.warning_image)
                                logging.info("Patient {0} {1} is awaiting medications."
                                             .format(patient.first_name, patient.last_name))
                        else:
                            if len(patient.matched_medications_dict) == len(matching_pillpack_patient.production_medications_dict):
                                logging.info("Patient {0} {1} does not exist within {2}. Creating new tree entry."
                                             .format(patient.first_name, patient.last_name, iterator))
                                self.patient_tree.insert(tree_parent_id, 'end',
                                                         patient.first_name + " " + patient.last_name,
                                                         text=patient.first_name + " " + patient.last_name,
                                                         image=self.ready_to_produce)
                                logging.info("Patient {0} {1} is ready to produce."
                                             .format(patient.first_name, patient.last_name))
                            else:
                                self.patient_tree.insert(tree_parent_id, 'end',
                                                         patient.first_name + " " + patient.last_name,
                                                         text=patient.first_name + " " + patient.last_name,
                                                         image=self.warning_image)
                                logging.info("Patient {0} {1} is awaiting medications."
                                             .format(patient.first_name, patient.last_name))

    def on_treeview_double_click(self, event):
        tree = self.patient_tree
        if isinstance(tree, Treeview):
            try:
                item = tree.selection()[0]
                first_name = item.split(" ")[0]
                last_name = item.split(" ")[1]
                if self.main_application.collected_patients.pillpack_patient_dict.__contains__(last_name.lower()):
                    list_of_patients: list = self.main_application.collected_patients.pillpack_patient_dict.get(
                        last_name.lower())
                    for patient in list_of_patients:
                        if isinstance(patient, PillpackPatient):
                            if patient.first_name.lower() == first_name.lower():
                                self.main_application.show_frame(consts.VIEW_PATIENT_SCREEN, patient)
                                self.parent.focus()
                            logging.info("Patient {0} {1} selected through user double click. Patient view for this "
                                         "patient has been opened."
                                         .format(patient.first_name, patient.last_name))
                        else:
                            logging.error("Object {0} in filtered patient list is not of type PillpackPatient."
                                          .format(patient))
            except IndexError as e:
                logging.error("Thrown IndexError: {0}".format(e))


def display_warning_if_pillpack_data_is_empty(application: App, function, warning_text: str):
    if len(application.collected_patients.pillpack_patient_dict) == 0:
        display_warning(application, function, warning_text)
    else:
        function()


def display_warning_if_pillpack_data_is_not_empty(application: App, function, warning_text: str):
    if len(application.collected_patients.pillpack_patient_dict) > 0:
        display_warning(application, function, warning_text)
    else:
        function()


def display_warning(application: App, function, warning_text: str):
    warning = Toplevel(master=application)
    warning.attributes('-topmost', 'true')
    warning.geometry("300x240")
    warning_label = Label(warning, text=warning_text,
                          wraplength=200)
    warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
    continue_button = Button(warning, text="Continue",
                             command=lambda: [warning.destroy(),
                                              function()
                                              ])
    continue_button.grid(row=1, column=0, padx=50, sticky="ew")
    go_back_button = Button(warning, text="Go back", command=warning.destroy)
    go_back_button.grid(row=1, column=1, padx=50, sticky="ew")


def confirm_production_archival(application: App, home_screen: HomeScreen = None):
    warning = Toplevel(master=application)
    warning.attributes('-topmost', 'true')
    warning.geometry("400x200")
    warning_label = Label(warning, text="Warning: Archiving this production will PERMENANTLY archive "
                                        "all working data. This means you will not be able to make any more "
                                        "modifications on the current production after archival. "
                                        "Are you sure you wish to archive the current production? ",
                          wraplength=300)
    warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
    archive_button = Button(warning, text="OK",
                            command=lambda: [warning.destroy(), archive_pillpack_production_dialog(home_screen)])
    archive_button.grid(row=1, column=0, padx=50, sticky="ew")
    cancel_button = Button(warning, text="Cancel", command=warning.destroy)
    cancel_button.grid(row=1, column=1, padx=50, sticky="ew")


def search_treeview(tree_to_search: Treeview, detached_items: list, search_query: StringVar):
    search_string: str = search_query.get()
    for node in detached_items:
        if tree_to_search.exists(node):
            tree_to_search.reattach(node, '', 0)
    if len(search_string) > 0:
        for node in tree_to_search.get_children():
            match: bool = False
            for value in tree_to_search.item(node)['values']:
                if search_string.lower() in str(value).lower():
                    match = True
                    break
            if match:
                tree_to_search.reattach(node, '', 0)
            else:
                detached_items.append(node)
                tree_to_search.detach(node)
    sort_treeview(tree_to_search, "Last Name", False)


def sort_treeview(tree_to_sort: Treeview, column: str, is_descending: bool):
    data = [(tree_to_sort.set(item, column), item) for item in tree_to_sort.get_children('')]
    data.sort(reverse=is_descending)
    for index, (val, item) in enumerate(data):
        tree_to_sort.move(item, '', index)


def create_tool_tip(widget, text):
    tool_tip = ToolTip(widget)

    def enter(event):
        tool_tip.showtip(text)

    def leave(event):
        tool_tip.hidetip()

    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


def calibrate_width(tree_to_calibrate: Treeview, columns: tuple, width):
    for column in columns:
        tree_to_calibrate.column(column, width=width)


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


def populate_pillpack_production_data(application: App):
    application.collected_patients.set_pillpack_patient_dict(
        get_patient_medicine_data(application.loaded_prns_and_linked_medications, consts.PPC_SEPARATING_TAG)
    )
    save_collected_patients(application.collected_patients)


def archive_pillpack_production_dialog(home_screen: HomeScreen = None):
    archive_file = filedialog.asksaveasfile(initialfile="Untitled.zip", defaultextension=".zip",
                                            filetypes=[("All files", ".*"), ("ZIP files", ".zip")])
    archive_pillpack_production(archive_file)
    if home_screen is not None:
        home_screen.threaded_production_data_retrieval()


def set_pillpack_production_directory():
    directory = filedialog.askdirectory()
    directory = directory.replace("/", "\\")
    modify_pillpack_location(directory)
    set_config(load_settings())


if __name__ == '__main__':
    try:
        app = App()
        app.mainloop()
        app.filesystem_observer.stop()
        if config["pillpackDataLocation"] != consts.UNSET_LOCATION:
            app.filesystem_observer.join()
    except E:
        raise
