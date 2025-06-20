import ctypes
import os
import shutil
import tkinter
import logging
import sys
import typing
from zipfile import ZipFile

logger = logging.getLogger()

try:
    from multiprocessing import Queue
    from tkinter import font, filedialog, Toplevel, Label, Button
    from tkinter.ttk import Treeview
    from Functions.ModelFactory import get_patient_data_from_specific_file, get_patient_medicine_data_xml
    from DataStructures.Models import PillpackPatient, Medication
    from DataStructures.Repositories import CollectedPatients
    from Application import HomeScreen, PatientDetails, ProductionDirectorySettings
    from Application.AppObserver import Observer
    from Application.WatchdogEventHandler import WatchdogEventHandler
    from Functions.ConfigSingleton import load_settings, consts, modify_pillpack_location
    from Functions.DAOFunctions import (load_collected_patients_from_object,
                                        load_prns_and_linked_medications_from_object,
                                        save_collected_patients)
    from watchdog.observers import Observer as WatchdogObserver
    from watchdog.events import FileCreatedEvent, FileMovedEvent
except Exception as e:
    error = e
    logger.error("{0}".format(e))

"""

The main module for the Script Checker application, and the entry point for the application.
The main tkinter loop is started here, and all relevant objects, repositories and patient data are stored and organised
here.

"""

if getattr(sys, 'frozen', False):
    """
    
    The location of the script directory and the logging directory is determined at runtime. This is based on whether
    the application is a production build (frozen as an executable) or a development build (running natively on the 
    python interpreter).
    
    """
    script_dir = os.path.dirname(sys.executable)
    logging_dir = os.environ['APPDATA'] + "\\ScriptCheckerLogs"
    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)
    logger.info("Script is running as a frozen executable at the following location: {0}"
                 .format(os.path.dirname(sys.executable)))
else:
    script_dir = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
    logging_dir = script_dir
    logger.info("Script is running on the python interpreter at the following location: {0}"
                 .format(os.path.dirname(os.path.abspath(__file__))))


logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler(logging_dir + '\\logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)


logger.addHandler(file_handler)
logger.addHandler(stdout_handler)

resources_dir = script_dir + "\\Resources"
icons_dir = resources_dir + "\\icons"
themes_dir = resources_dir + "\\themes"
collected_patients: CollectedPatients = CollectedPatients()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class App(tkinter.Tk):
    """

    Main class which contains all the main application fields and functions. Any prerequisites before running are
    satisfied where possible.

    """
    def __init__(self):
        """

        Constructor for the application class. The watchdog filesystem observer is started which begins monitoring the
        designated file path.

        If the filesystem observer cannot be started, or the specified file path is missing,
        an error is displayed to the user. Script checker can still be used when the filesystem observer is
        not functioning in a lesser state.

        """
        super().__init__()
        self.handler = None
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
        self.group_production_name = ""
        self.collected_patients = load_collected_patients_from_object()
        self.loaded_prns_and_linked_medications: dict = load_prns_and_linked_medications_from_object()
        self.app_observer: Observer = Observer()
        self.total_medications = 0
        self.title_font = font.Font(family='Verdana', size=28, weight="bold")
        self.container = tkinter.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.bind("<<WatchdogEvent>>", self.on_watchdog_event)
        self.define_filesystem_observer_location()

    def define_filesystem_observer_location(self):
        """
        Checks the current location for the filesystem observer to listen and sees if it has not been set. If it has
        not been set, the user is directed to the "Set pillpack location" screen where they can set it manually.

        Under normal circumstances, the filesystem observer location will be set to its default location,
        which is a path common to all Farmadosis systems.

        The filesystem observer will attempt to start and begin listening in the selected filepath location. If the
        filesystem observer cannot start, or the provided filepath does not exist, an error message will be
        displayed to the user informing them that the filesystem observer failed to start.

        :return: None
        """
        if self.config["pillpackDataLocation"] == consts.UNSET_LOCATION:
            self.show_frame(consts.VIEW_PILLPACK_FOLDER_LOCATION)
        else:
            self.show_frame(consts.HOME_SCREEN)
            self.handler = WatchdogEventHandler(self)
            try:
                self.current_directory_to_watch = (
                    self.filesystem_observer.schedule(self.handler, self.config["pillpackDataLocation"],
                                                      recursive=False))
                self.filesystem_observer.start()
                logger.info("File system observer started in directory {0} successfully."
                            .format(self.config["pillpackDataLocation"]))
            except Exception as ex:
                logger.exception("{0}".format(ex))
                warning = Toplevel(master=self.master)
                warning.attributes('-topmost', 'true')
                warning.geometry("400x200")
                warning_label = Label(warning, text="Failed to start filesystem observer...",
                                      wraplength=300)
                warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
                ok_button = Button(warning, text="OK", command=warning.destroy)
                ok_button.grid(row=1, column=0, padx=50, sticky="ew", columnspan=2)
                warning.grab_set()

    def show_frame(self, view_name: str, patient_to_view: PillpackPatient = None):
        """
        Function which checks the requested screen to be shown to the user and performs view-specific logic
        to correctly process the request/display information to the user

        When a patient is selected, the specified PillpackPatient object is passed along to this function along with
        the name of the view.

        A "history" observer has been implemented for a user to be able to navigate backwards and forwards between
        previously selected views. However, this functionality is not currently operational in this build of
        Script Checker.

        :param view_name: The screen to be moved to the top and shown to the user
        :param patient_to_view: An optional argument which contains either a PillpackPatient object, or a None value
        :return: None
        """
        match view_name:
            case consts.HOME_SCREEN:
                for patient_view_name in list(self.app_observer.connected_views):
                    patient_view = self.app_observer.connected_views[patient_view_name]
                    if isinstance(patient_view, PatientDetails.PatientMedicationDetails):
                        self.app_observer.connected_views[patient_view_name].grid_remove()
                        self.app_observer.disconnect(patient_view_name)
                        patient_view.display_canvas.unbind_all("<MouseWheel>")
                        logger.info("Unbound mouse wheel from patient view {0}".format(patient_view_name))
                        patient_view.grid_remove()
                        logger.info("Disconnected patient view {0} from the application grid"
                                     .format(patient_view_name))
                        patient_view.destroy()
                        logger.info("Destroyed patient view {0}".format(patient_view_name))
                    else:
                        logger.warning("The view {0} was not of type PatientMedicationDetails"
                                       .format(patient_view_name))
                if self.app_observer.connected_views.__contains__(view_name):
                    frame: HomeScreen = self.app_observer.connected_views[view_name]
                    logger.info("Accessed home screen view {0} from application observer.".format(view_name))
                else:
                    frame: HomeScreen.HomeScreen = HomeScreen.HomeScreen(parent=self.container, master=self)
                    logger.info("No home screen view connected to application observer. "
                                "A new home screen frame has been created.")
                    self.app_observer.connect(view_name, frame)
                    frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                frame.tkraise()
                logger.info("Home screen view is now the current view.")
            case consts.VIEW_PATIENT_SCREEN:
                if isinstance(patient_to_view, PillpackPatient):
                    key = view_name + patient_to_view.first_name + patient_to_view.last_name
                    if self.app_observer.connected_views.__contains__(key):
                        frame: PatientDetails.PatientMedicationDetails = self.app_observer.connected_views[key]
                        logger.info("Accessed patient view {0} from application observer.".format(key))
                    else:
                        frame: PatientDetails.PatientMedicationDetails = (PatientDetails.PatientMedicationDetails
                                                                          (parent=self.container, master=self,
                                                                           patient=patient_to_view)
                                                                          )
                        logger.info("No patient view connected to application observer. "
                                    "A new patient view has been created.")
                        self.app_observer.connect(key, frame)
                        frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                    frame.tkraise()
                    logger.info("Patient view {0} is now the current view.".format(key))
                else:
                    logger.warning("The object {0} was not of type PillpackPatient".format(patient_to_view))
            case consts.VIEW_PILLPACK_FOLDER_LOCATION:
                if self.app_observer.connected_views.__contains__(consts.VIEW_PILLPACK_FOLDER_LOCATION):
                    frame: ProductionDirectorySettings.ViewPillpackProductionFolder = self.app_observer.connected_views[
                        consts.VIEW_PILLPACK_FOLDER_LOCATION]
                    logger.info("Accessed pillpack location view from application observer")
                else:
                    frame: ProductionDirectorySettings.ViewPillpackProductionFolder = (
                        ProductionDirectorySettings.ViewPillpackProductionFolder(parent=self.container,
                                                                                 master=self))
                    logger.info("No pillpack location view connected to application observer. "
                                "A new pillpack location view has been created")
                    self.app_observer.connect(consts.VIEW_PILLPACK_FOLDER_LOCATION, frame)
                    frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                frame.tkraise()
                logger.info("The pillpack location view is now the current view.")

    def set_pillpack_production_directory(self):
        """
        Function which tells the filesystem observer which filepath to listen for any filesystem events.
        The application config object is then updated to reflect these changes and to restart the filesystem observer
        in the newly selected location.

        :return: None
        """
        directory = filedialog.askdirectory()
        directory = directory.replace("/", "\\")
        modify_pillpack_location(directory)
        self.config = load_settings()

    def on_watchdog_event(self, event):
        """
        Function which is called whenever a filesystem event is detected by the filesytem observer.
        Currently, only Pillpaccare (ppc_processed) and AMCO (fd) file extensions are supported. When a file with
        one of these extensions is detected by the filesystem observer, the appropriate data extraction procedure is
        executed

        A ppc_processed file extension is just an XML extension with a proprietary name. This means the data can
        be extracted directly and parsed into a PillpackPatient object with no additional preparation required.

        A fd file extension is a ZIP file with a propreitary name. This means that before extracting the XML data,
        the ZIP file has to be copied and the appropriate XML files in the ZIP file have to be individually
        extracted and parsed into their own respective PillpackPatient objects.

        The reason the file has to be copied before extraction is because a competing script is ran on fd files by the
        Farmadosis .NET filesystem observer. Unless the fd file is copied and saved as a generic ZIP file, a race
        condition would be created and data corruption/data locking would be a likely outcome.

        :param event: Any filesystem event which occurs in the filepath the observer is listening e.g. Create, move,
        rename, delete
        :return: None
        """
        watchdog_event = self.queue.get()
        full_path = ""
        if isinstance(watchdog_event, FileCreatedEvent):
            full_path = str(watchdog_event.src_path)
        if isinstance(watchdog_event, FileMovedEvent):
            full_path = str(watchdog_event.dest_path)
        logger.info("Full path of file monitored by watchdog observer: {0}".format(full_path))
        split_file_name = full_path.rsplit('\\')
        file_name = split_file_name[len(split_file_name) - 1]
        file_extension = full_path.rsplit('.')[1]
        if file_extension == "ppc_processed":
            logger.info("The modified file has a ppc_processed file extension. Executing patient(s) update...")
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
        """
        Function which queues each filesystem event detected by the filesystem observer before processing.
        This prevents race conditions and allows every event to be processed with certainty.

        :param event: Any filesystem event which occurs in the filepath the observer is listening e.g. Create, move,
        rename, delete
        :return: None
        """
        self.queue.put(event)
        self.event_generate("<<WatchdogEvent>>", when="tail")
        logger.info("Watchdog event {0} has been added to the queue.".format(event))

    @staticmethod
    def match_patient_to_pillpack_patient(patient_to_be_matched: PillpackPatient, pillpack_patient_dict: dict):
        """
        IMPORTANT: FUNCTION NEEDS REWRITTEN - NO LOGIC FLOW TO INDICATE A PATIENT COULD NOT BE FOUND WITHIN SPECIFIED
        DICTIONARY

        Static function which checks if any arbitrary PillpackPatient object is contained as a value in any arbitrary
        dictionary.

        As is standard in Script Checker, a PillpackPatient will be stored in a dictionary with the last name of said
        patient as the dictionary's key. If more than one patient has the same last name, the value in the dictionary
        will be a list of PillpackPatient objects.

        If the specified PillpackPatient object is found in the specified dictionary, that PillpackPatient object will
        be the return value. If no such PillpackPatient object can be found, a None value is returned instead.

        :param patient_to_be_matched: PillpackPatient object to be searched for within the dictionary
        :param pillpack_patient_dict: Dictionary in which to search for the PillpackPatient object
        :return: PillpackPatient, or None
        """
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

    """
    The main App loop. The filesystem observer attempts to start, as well as the main tkinter loop of the application.
    """
    if getattr(sys, 'frozen', False):
        if is_admin():
            try:
                app = App()
                app.iconbitmap(icons_dir + "\\script_checker_prototype_icon.ico")
                app.mainloop()
                app.filesystem_observer.stop()
                if app.config["pillpackDataLocation"] != consts.UNSET_LOCATION:
                    app.filesystem_observer.join()
            except Exception as e:
                logger.error(e)
                raise
        else:
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1)
    else:
        try:
            app = App()
            app.iconbitmap(icons_dir + "\\script_checker_prototype_icon.ico")
            app.mainloop()
            app.filesystem_observer.stop()
            if app.config["pillpackDataLocation"] != consts.UNSET_LOCATION:
                app.filesystem_observer.join()
        except Exception as e:
            logger.error(e)
            raise

