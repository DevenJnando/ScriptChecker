import datetime
import sys
import tkinter
import types
import typing
from tkinter.ttk import Treeview
from tkinter import *
from tkinter import font

import pillpackData
import scriptScanner

consts = types.SimpleNamespace()
consts.HOME_SCREEN = "HomeScreen"
consts.VIEW_PATIENT_SCREEN = "ViewPatientScreen"

script_dir = sys.path[0]
resources_dir = script_dir + "\\Resources"
icons_dir = resources_dir + "\\icons"
themes_dir = resources_dir + "\\themes"
collected_patients: scriptScanner.CollectedPatients = scriptScanner.CollectedPatients()


#class PatientReportTabViewer(CTkTabview):
#    def __init__(self, master, **kwargs):
#        super().__init__(master, **kwargs)
#
#    def add_tab(self, tab_text):
#        self.add(tab_text)


#class DarkModeFrame(CTkFrame):
#    def __init__(self, master, **kwargs):
#        super().__init__(master, **kwargs)
#        self.dark_mode_toggle: bool = True
#        dark_mode_image = CTkImage(light_image=Image.open(icons_dir + "\\dark-mode.png"),
#                                   dark_image=Image.open(icons_dir + "\\light-mode.png"),
#                                   size=(30, 30))

#        def dark_mode():
#            self.dark_mode_toggle = not self.dark_mode_toggle
#            if self.dark_mode_toggle is True:
#                set_appearance_mode("dark")
#            else:
#                set_appearance_mode("light")

#        self.dark_mode_toggle = CTkButton(self, text="", command=dark_mode, image=dark_mode_image,
#                                          width=2, height=2, fg_color="transparent")
#        self.dark_mode_toggle.grid(row=0, column=0, sticky="w")


class Observer:
    def __init__(self):
        self.connected_views: list = []

    def connect(self, view_to_connect):
        if not self.connected_views.__contains__(view_to_connect):
            self.connected_views.append(view_to_connect)

    def clear(self):
        self.connected_views.clear()

    def update(self, view_to_update):
        if self.connected_views.__contains__(view_to_update):
            update_method = getattr(view_to_update, "update", None)
            if callable(update_method):
                view_to_update.update()

    def update_all(self):
        for view in self.connected_views:
            self.update(view)


class App(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.style = tkinter.ttk.Style(self)
        self.tk.call("source", themes_dir + "\\" + "forest-dark.tcl")
        self.style.theme_use("forest-dark")
        self.geometry("1080x720")
        self.title("Pillpack Script Checker")
        self.collected_patients = scriptScanner.CollectedPatients()
        self.app_observer: Observer = Observer()
        self.total_medications = 0
        self.title_font = font.Font(family='Verdana', size=28, weight="bold")
        self.container = Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.show_frame(consts.HOME_SCREEN)

        #set_appearance_mode("dark")

    def show_frame(self, view_name: str, patient_to_view: pillpackData.PillpackPatient = None):
        match view_name:
            case consts.HOME_SCREEN:
                if patient_to_view is None:
                    frame: HomeScreen = HomeScreen(parent=self.container, master=self)
                    self.app_observer.connect(frame)
                    frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                    frame.tkraise()
            case consts.VIEW_PATIENT_SCREEN:
                if isinstance(patient_to_view, pillpackData.PillpackPatient):
                    frame: Frame = PatientMedicationDetails(parent=self.container, master=self, patient=patient_to_view)
                    self.app_observer.connect(frame)
                    frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
                    frame.tkraise()


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
                                          command=lambda: self.check_if_pillpack_data_is_loaded())
        self.scan_scripts_button.grid(row=1, column=0, pady=50)
        self.view_changes_button = Button(self, text="View changes")
        self.view_changes_button.grid(row=2, column=0, pady=50)
        self.archive_production_data_button = Button(self, text="Archive Production Data")
        self.archive_production_data_button.grid(row=3, column=0)

    def check_if_pillpack_data_is_loaded(self):
        if len(self.master.collected_patients.pillpack_patient_dict) == 0:
            warning = Toplevel(master=self.master)
            warning.geometry("400x200")
            warning_label = Label(warning, text="You have not loaded any pillpack production data! "
                                                "It is highly recommended that you do this before "
                                                "scanning in scripts.",
                                  wraplength=200)
            warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
            go_back_button = Button(warning, text="Go back", command=warning.destroy)
            go_back_button.grid(row=1, column=0, padx=50, sticky="ew")
            continue_button = Button(warning, text="Continue anyway",
                                     command=lambda: [warning.destroy(),
                                                      self.open_scan_scripts_window()
                                                      ])
            continue_button.grid(row=1, column=1, padx=50, sticky="ew")
        else:
            self.open_scan_scripts_window()

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
        self.warning_image = warning_image.subsample(30, 30)
        ready_to_produce_path = icons_dir + "\\check.png"
        ready_to_produce = PhotoImage(file=ready_to_produce_path)
        self.ready_to_produce = ready_to_produce.subsample(30, 30)
        side_bar = SideBar(self, self.master)
        side_bar.grid(row=0, column=0)

        options_frame = tkinter.ttk.Frame(self)
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
                                      command=lambda: [populate_pillpack_production_data(self.master),

                                                       self.refresh_treeview(self.production_patients_tree,
                                                       self.master.collected_patients.pillpack_patient_dict),

                                                       self.refresh_treeview(self.perfect_patients_tree,
                                                       self.master.collected_patients.matched_patients),

                                                       self.refresh_treeview(self.imperfect_patients_tree,
                                                       self.master.collected_patients.minor_mismatch_patients),

                                                       self.refresh_treeview(self.mismatched_patients_tree,
                                                       self.master.collected_patients.severe_mismatch_patients)
                                                       ])
        load_pillpack_label.grid(row=1, column=0, sticky="nsew")
        load_pillpack_button.grid(row=2, column=0, sticky="nsew")

        scan_scripts_image = icons_dir + "\\scan_scripts.png"
        scan_scripts_label = Label(options_frame, text="Scan scripts", font=self.font, wraplength=100, justify="center")
        scan_scripts_button_image = PhotoImage(file=scan_scripts_image)
        self.scripts_button_image = scan_scripts_button_image.subsample(5, 5)
        scan_scripts_button = Button(options_frame, image=self.scripts_button_image,
                                     command=lambda: self.check_if_pillpack_data_is_loaded())
        scan_scripts_label.grid(row=1, column=1, sticky="nsew")
        scan_scripts_button.grid(row=2, column=1, sticky="nsew")

        archive_production_label = Label(options_frame, text="Archive production data", font=self.font, wraplength=120,
                                         justify="center")
        archive_production_image = icons_dir + "\\archive.png"
        archive_production_button_image = PhotoImage(file=archive_production_image)
        self.archive_button_production_image = archive_production_button_image.subsample(5, 5)
        archive_production_button = Button(options_frame, image=self.archive_button_production_image)
        archive_production_label.grid(row=1, column=2, sticky="nsew")
        archive_production_button.grid(row=2, column=2, sticky="nsew")

        paned_window = tkinter.ttk.PanedWindow(self)
        paned_window.grid(row=3, column=1, pady=(25, 5), sticky="nsew", rowspan=4)

        paned_frame = tkinter.ttk.Frame(paned_window)
        paned_window.add(paned_frame, weight=1)

        results_notebook = tkinter.ttk.Notebook(paned_frame)

        production_patients_results = tkinter.ttk.Frame(results_notebook)
        production_patients_results.columnconfigure(index=0, weight=1)
        production_patients_results.columnconfigure(index=1, weight=1)
        production_patients_results.rowconfigure(index=0, weight=1)
        production_patients_results.rowconfigure(index=1, weight=1)
        results_notebook.add(production_patients_results, text="Patients in Pillpack Production")

        self.production_patients_tree = Treeview(production_patients_results,
                                                 columns=('Date of Birth',
                                                          'No. of Medications',
                                                          'Condition'),
                                                 height=10)

        self.production_patients_tree.heading('#0', text="Patient Name")
        self.production_patients_tree.heading('Date of Birth', text="Date of Birth")
        self.production_patients_tree.heading('No. of Medications', text="No. of Medications")
        self.production_patients_tree.heading('Condition', text="Condition")
        self.production_patients_tree.bind('<Double-1>',
                                           lambda e: self.on_treeview_double_click
                                           (self.production_patients_tree,
                                            self.master.collected_patients.pillpack_patient_dict)
                                           )
        self.production_patients_tree.grid(row=0, column=0, sticky="ew")

        perfect_match_patients = tkinter.ttk.Frame(results_notebook)
        results_notebook.add(perfect_match_patients, text="Perfectly Matched Patients")

        self.perfect_patients_tree = Treeview(perfect_match_patients,
                                              columns=('Date of Birth',
                                                       'No. of Medications',
                                                       'Condition'),
                                              height=10)
        self.perfect_patients_tree["displaycolumns"] = ('Date of Birth', 'No. of Medications', 'Condition')

        self.perfect_patients_tree.heading('#0', text="Patient Name")
        self.perfect_patients_tree.heading('Date of Birth', text="Date of Birth")
        self.perfect_patients_tree.heading('No. of Medications', text="No. of Medications")
        self.perfect_patients_tree.heading('Condition', text="Condition")
        self.perfect_patients_tree.bind('<Double-1>',
                                        lambda e: self.on_treeview_double_click
                                        (self.perfect_patients_tree,
                                         self.master.collected_patients.matched_patients)
                                        )
        self.perfect_patients_tree.grid(row=0, column=0, sticky="ew")

        minor_mismatch_patients = tkinter.ttk.Frame(results_notebook)
        results_notebook.add(minor_mismatch_patients, text="Minor Mismatched Patients")

        self.imperfect_patients_tree = Treeview(minor_mismatch_patients,
                                                columns=('Date of Birth',
                                                         'No. of Medications',
                                                         'Condition'),
                                                height=10)
        self.imperfect_patients_tree["displaycolumns"] = ('Date of Birth', 'No. of Medications', 'Condition')

        self.imperfect_patients_tree.heading('#0', text="Patient Name")
        self.imperfect_patients_tree.heading('Date of Birth', text="Date of Birth")
        self.imperfect_patients_tree.heading('No. of Medications', text="No. of Medications")
        self.imperfect_patients_tree.heading('Condition', text="Condition")
        self.imperfect_patients_tree.bind('<Double-1>',
                                          lambda e: self.on_treeview_double_click
                                          (self.imperfect_patients_tree,
                                           self.master.collected_patients.minor_mismatch_patients)
                                          )
        self.imperfect_patients_tree.grid(row=0, column=0, sticky="ew")

        severe_mismatch_patients = tkinter.ttk.Frame(results_notebook)
        results_notebook.add(severe_mismatch_patients, text="Severely Mismatched Patients")

        self.mismatched_patients_tree = Treeview(severe_mismatch_patients,
                                                 columns=('Date of Birth',
                                                          'No. of Medications',
                                                          'Condition'),
                                                 height=10)
        self.mismatched_patients_tree["displaycolumns"] = ('Date of Birth', 'No. of Medications', 'Condition')

        self.mismatched_patients_tree.heading('#0', text="Patient Name")
        self.mismatched_patients_tree.heading('Date of Birth', text="Date of Birth")
        self.mismatched_patients_tree.heading('No. of Medications', text="No. of Medications")
        self.mismatched_patients_tree.heading('Condition', text="Condition")
        self.mismatched_patients_tree.bind('<Double-1>',
                                           lambda e: self.on_treeview_double_click
                                           (self.mismatched_patients_tree,
                                            self.master.collected_patients.severe_mismatch_patients)
                                           )
        self.mismatched_patients_tree.grid(row=0, column=0, sticky="ew")

        results_notebook.pack(expand=True, fill="both", padx=5, pady=5)

        self.refresh_treeview(self.production_patients_tree,
                              self.master.collected_patients.pillpack_patient_dict),

        self.refresh_treeview(self.perfect_patients_tree,
                              self.master.collected_patients.matched_patients),

        self.refresh_treeview(self.imperfect_patients_tree,
                              self.master.collected_patients.minor_mismatch_patients),

        self.refresh_treeview(self.mismatched_patients_tree,
                              self.master.collected_patients.severe_mismatch_patients)
        self.script_window = None

    def refresh_treeview(self, tree_to_refresh: tkinter.ttk.Treeview, dictionary: dict):
        iterator = dictionary.values()
        for patient_list in iterator:
            if isinstance(patient_list, list):
                for patient in patient_list:
                    if isinstance(patient, scriptScanner.PillpackPatient):
                        pillpack_patients: list = self.master.collected_patients.pillpack_patient_dict.get(
                            patient.last_name)
                        pillpack_patients = list(
                            filter
                            (lambda entity:
                             typing.cast(scriptScanner.PillpackPatient, entity).first_name == patient.first_name,
                             pillpack_patients)
                        )
                        matching_pillpack_patient: scriptScanner.PillpackPatient = pillpack_patients[0]
                        key = patient.first_name + " " + patient.last_name
                        if not tree_to_refresh.exists(key):
                            tree_to_refresh.insert('', 'end', key, text=key)
                        if matching_pillpack_patient.date_of_birth == datetime.date.today():
                            tree_to_refresh.set(key, 'Date of Birth', "Not provided...")
                        else:
                            tree_to_refresh.set(key, 'Date of Birth', matching_pillpack_patient.date_of_birth)
                        tree_to_refresh.set(key, 'No. of Medications', len(matching_pillpack_patient.medication_dict))
                        if len(matching_pillpack_patient.missing_medications_dict) > 0:
                            tree_to_refresh.set(key, 'Condition', "Missing medications")
                            tree_to_refresh.item(key, image=self.warning_image)
                        elif len(matching_pillpack_patient.incorrect_dosages_dict) > 0:
                            tree_to_refresh.set(key, 'Condition', "Incorrect dosages")
                            tree_to_refresh.item(key, image=self.warning_image)
                        elif len(matching_pillpack_patient.unknown_medications_dict) > 0:
                            tree_to_refresh.set(key, 'Condition', "Unknown medications")
                            tree_to_refresh.item(key, image=self.warning_image)
                        elif (len(matching_pillpack_patient.matched_medications_dict)
                              == len(matching_pillpack_patient.medication_dict)):
                            tree_to_refresh.set(key, 'Condition', "Ready to produce")
                            tree_to_refresh.item(key, image=self.ready_to_produce)
                        else:
                            tree_to_refresh.set(key, 'Condition', "No scripts scanned")

    def update(self):
        self.refresh_treeview(self.production_patients_tree,
                              self.master.collected_patients.pillpack_patient_dict),

        self.refresh_treeview(self.perfect_patients_tree,
                              self.master.collected_patients.matched_patients),

        self.refresh_treeview(self.imperfect_patients_tree,
                              self.master.collected_patients.minor_mismatch_patients),

        self.refresh_treeview(self.mismatched_patients_tree,
                              self.master.collected_patients.severe_mismatch_patients)

    def check_if_pillpack_data_is_loaded(self):
        if len(self.master.collected_patients.pillpack_patient_dict) == 0:
            warning = Toplevel(master=self.master)
            warning.geometry("400x200")
            warning_label = Label(warning, text="You have not loaded any pillpack production data! "
                                                "It is highly recommended that you do this before "
                                                "scanning in scripts.",
                                  wraplength=200)
            warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
            go_back_button = Button(warning, text="Go back", command=warning.destroy)
            go_back_button.grid(row=1, column=0, padx=50, sticky="ew")
            continue_button = Button(warning, text="Continue anyway",
                                     command=lambda: [warning.destroy(),
                                                      self.open_scan_scripts_window()
                                                      ])
            continue_button.grid(row=1, column=1, padx=50, sticky="ew")
        else:
            self.open_scan_scripts_window()

    def open_scan_scripts_window(self):
        if self.script_window is None or not self.script_window.winfo_exists():
            self.script_window = ScanScripts(self, self.master)  # create window if its None or destroyed
            self.script_window.grab_set()
        else:
            self.script_window.focus()  # if window exists focus it

    def on_treeview_double_click(self, tree_to_select_from: Treeview, dictionary_to_lookup: dict):
        if isinstance(tree_to_select_from, Treeview):
            try:
                item = tree_to_select_from.selection()[0]
                split_patient_name = tree_to_select_from.item(item, "text").split(" ")
                patient_list = dictionary_to_lookup.get(split_patient_name[1])
                if isinstance(patient_list, list):
                    filtered_patients = (list
                                         (filter
                                             (lambda patient: patient.first_name == split_patient_name[0],
                                              patient_list)
                                          )
                                         )
                    selected_patient = filtered_patients[0]
                    self.master.show_frame(consts.VIEW_PATIENT_SCREEN, selected_patient)
            except IndexError as e:
                print("IndexError: ", e)


class PatientMedicationDetails(Frame):
    def __init__(self, parent, master: App, patient: pillpackData.PillpackPatient):
        Frame.__init__(self, parent)
        self.font = font.Font(family='Verdana', size=14, weight="normal")
        self.home_screen: HomeScreen = parent
        self.master: App = master
        side_bar = SideBar(self, self.master)
        side_bar.pack(side="left", fill="both")
        self.patient_object: pillpackData.PillpackPatient = patient
        self.patient_tree_key = self.patient_object.first_name + " " + self.patient_object.last_name

        display_frame = tkinter.ttk.Frame(self)
        display_frame.pack(side="top", fill="both")

        test_label = Label(display_frame, font=self.font,
                           text=self.patient_tree_key)
        test_label.grid(row=0, column=0)

        self.production_medication_frame = LabelFrame(display_frame)
        self.production_medication_frame.columnconfigure(0, weight=1)
        self.production_medication_frame.columnconfigure(1, weight=2)
        production_medication_label = Label(display_frame, text="All Production Medications")
        production_medication_label.grid(row=1, column=0)
        self.production_medication_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

        production_medication_name_label = Label(self.production_medication_frame, text="Medication Name")
        production_medication_name_label.grid(row=0, column=0)
        production_medication_dosage_label = Label(self.production_medication_frame, text="Dosage")
        production_medication_dosage_label.grid(row=0, column=1)

        self.matched_medication_frame = LabelFrame(display_frame)
        self.matched_medication_frame.columnconfigure(0, weight=1)
        self.matched_medication_frame.columnconfigure(1, weight=2)
        matched_medication_label = Label(display_frame, text="Matched Medications")
        matched_medication_label.grid(row=1, column=1)
        self.matched_medication_frame.grid(row=2, column=1, padx=20, pady=20, sticky="ew")

        matched_medication_name_label = Label(self.matched_medication_frame, text="Medication Name")
        matched_medication_name_label.grid(row=0, column=0)
        matched_medication_dosage_label = Label(self.matched_medication_frame, text="Dosage")
        matched_medication_dosage_label.grid(row=0, column=1)

        self.missing_medication_frame = LabelFrame(display_frame)
        self.missing_medication_frame.columnconfigure(0, weight=1)
        self.missing_medication_frame.columnconfigure(1, weight=2)
        missing_medication_label = Label(display_frame, text="Missing Medications")
        missing_medication_label.grid(row=3, column=0)
        self.missing_medication_frame.grid(row=4, column=0, padx=20, pady=20, sticky="ew")

        missing_medication_name_label = Label(self.missing_medication_frame, text="Medication Name")
        missing_medication_name_label.grid(row=0, column=0)
        missing_medication_dosage_label = Label(self.missing_medication_frame, text="Dosage")
        missing_medication_dosage_label.grid(row=0, column=1)

        self.unknown_medication_frame = LabelFrame(display_frame)
        self.unknown_medication_frame.columnconfigure(0, weight=1)
        self.unknown_medication_frame.columnconfigure(1, weight=2)
        unknown_medication_label = Label(display_frame, text="Unknown Medications")
        unknown_medication_label.grid(row=3, column=1)
        self.unknown_medication_frame.grid(row=4, column=1, padx=20, pady=20, sticky="ew")

        unknown_medication_name_label = Label(self.unknown_medication_frame, text="Medication Name")
        unknown_medication_name_label.grid(row=0, column=0)
        unknown_medication_dosage_label = Label(self.unknown_medication_frame, text="Dosage")
        unknown_medication_dosage_label.grid(row=0, column=1)

        self.incorrect_medication_dosage_frame = LabelFrame(display_frame)
        self.incorrect_medication_dosage_frame.columnconfigure(0, weight=1)
        self.incorrect_medication_dosage_frame.columnconfigure(1, weight=2)
        incorrect_medication_dosage_label = Label(display_frame,
                                                  text="Incorrect Dosage Medications")
        incorrect_medication_dosage_label.grid(row=5, column=0)
        self.incorrect_medication_dosage_frame.grid(row=6, column=0, padx=20, pady=20, sticky="ew", columnspan=2)

        incorrect_medication_dosage_name_label = Label(self.incorrect_medication_dosage_frame, text="Medication Name")
        incorrect_medication_dosage_name_label.grid(row=0, column=0)
        incorrect_medication_dosage_in_production_label = Label(self.incorrect_medication_dosage_frame,
                                                                text="Dosage in Production")
        incorrect_medication_dosage_in_production_label.grid(row=0, column=1)
        incorrect_medication_dosage_on_script_label = Label(self.incorrect_medication_dosage_frame,
                                                            text="Dosage on Script")
        incorrect_medication_dosage_on_script_label.grid(row=0, column=2)

        self.update()

    @staticmethod
    def populate_label_frame(label_frame_to_populate: LabelFrame, dictionary_to_iterate: dict):
        dictionary_values: list = list(dictionary_to_iterate.values())
        for i in range(0, len(dictionary_values)):
            medication = dictionary_values[i]
            if isinstance(medication, pillpackData.Medication):
                medication_name_label = Label(label_frame_to_populate, text=medication.medication_name)
                medication_dosage_label = Label(label_frame_to_populate, text=medication.dosage)
                medication_name_label.grid(row=i+1, column=0)
                medication_dosage_label.grid(row=i+1, column=1)

    def populate_incorrect_dosages_treeview(self, incorrect_medication_dosage_frame):
        incorrect_dosages_values = list(self.patient_object.incorrect_dosages_dict.values())
        for i in range(0, len(incorrect_dosages_values)):
            medication = incorrect_dosages_values[i]
            if isinstance(medication, pillpackData.Medication):
                if self.patient_object.medication_dict.__contains__(medication.medication_name):
                    medication_in_production: pillpackData.Medication = self.patient_object.medication_dict.get(
                        medication.medication_name
                    )
                    medication_name_label = Label(incorrect_medication_dosage_frame, text=medication.medication_name)
                    medication_dosage_in_production_label = Label(incorrect_medication_dosage_frame,
                                                                  text=medication_in_production.dosage)
                    medication_dosage_on_script_label = Label(incorrect_medication_dosage_frame,
                                                              text=medication.dosage)
                    medication_name_label.grid(row=i + 1, column=0)
                    medication_dosage_in_production_label.grid(row=i + 1, column=1)
                    medication_dosage_on_script_label.grid(row=i + 1, column=2)

    def update(self):
        self.populate_label_frame(self.production_medication_frame, self.patient_object.medication_dict)
        self.populate_label_frame(self.matched_medication_frame, self.patient_object.matched_medications_dict)
        self.populate_label_frame(self.missing_medication_frame, self.patient_object.missing_medications_dict)
        self.populate_label_frame(self.unknown_medication_frame, self.patient_object.unknown_medications_dict)
        self.populate_incorrect_dosages_treeview(self.incorrect_medication_dosage_frame)

"""
        self.production_medication_treeview = Treeview(display_frame,
                                                       columns='Dosage',
                                                       height=5)

        self.production_medication_treeview.heading('#0', text="All Production Medications")
        self.production_medication_treeview.heading('Dosage', text="Dosage")
        self.production_medication_treeview.grid(row=1, column=1, sticky="ew")

        self.matched_medication_treeview = Treeview(display_frame,
                                                    columns='Dosage',
                                                    height=5)

        self.matched_medication_treeview.heading('#0', text="Matched Medications")
        self.matched_medication_treeview.heading('Dosage', text="Dosage")
        self.matched_medication_treeview.grid(row=1, column=2, sticky="ew")

        self.missing_medication_treeview = Treeview(display_frame,
                                                    columns='Dosage',
                                                    height=5)

        self.missing_medication_treeview.heading('#0', text="Missing Medications")
        self.missing_medication_treeview.heading('Dosage', text="Dosage")
        self.missing_medication_treeview.grid(row=2, column=1, sticky="ew")

        self.unknown_medication_treeview = Treeview(display_frame,
                                                    columns='Dosage',
                                                    height=5)

        self.unknown_medication_treeview.heading('#0', text="Unknown Medications")
        self.unknown_medication_treeview.heading('Dosage', text="Dosage")
        self.unknown_medication_treeview.grid(row=2, column=2, sticky="ew")

        incorrect_dosage_frame = tkinter.ttk.Frame(self)
        incorrect_dosage_frame.columnconfigure(0, weight=0)
        incorrect_dosage_frame.columnconfigure(1, weight=2)
        incorrect_dosage_frame.grid(row=1, column=0, sticky="ew")

        self.incorrect_dosages_treeview = Treeview(incorrect_dosage_frame,
                                                   columns=('Recorded Dosage',
                                                            'Dosage on Script'),
                                                   height=5)

        self.incorrect_dosages_treeview.heading('#0', text="Incorrect Dosages")
        self.incorrect_dosages_treeview.heading('Recorded Dosage', text="Recorded Dosage")
        self.incorrect_dosages_treeview.heading('Dosage on Script', text="Dosage on Script")
        self.incorrect_dosages_treeview.grid(row=3, column=1, sticky="ew")

        self.matched_medication_treeview.tag_configure('matched', background='#2f8000')
        self.missing_medication_treeview.tag_configure('missing', background='#a8a82c')
        self.unknown_medication_treeview.tag_configure('unknown', background='#a30202')
        self.incorrect_dosages_treeview.tag_configure('bad dosage', background='#a8a82c')

        self.populate_treeview(self.production_medication_treeview, self.patient_object.medication_dict)
        self.populate_treeview(self.matched_medication_treeview, self.patient_object.matched_medications_dict,
                               "matched")
        self.populate_treeview(self.missing_medication_treeview, self.patient_object.missing_medications_dict,
                               "missing")
        self.populate_treeview(self.unknown_medication_treeview, self.patient_object.unknown_medications_dict,
                               "unknown")
        self.populate_incorrect_dosages_treeview()

    @staticmethod
    def populate_treeview(treeview_to_populate: Treeview, medication_dict: dict, tag: str = ""):
        medicine_dict_values = medication_dict.values()
        for medication in medicine_dict_values:
            if isinstance(medication, pillpackData.Medication):
                medication_key = medication.medication_name + " " + str(medication.dosage)
                if not treeview_to_populate.exists(medication_key):
                    treeview_to_populate.insert('', 'end', medication_key,
                                                text=medication.medication_name,
                                                tags=tag)
                treeview_to_populate.set(medication_key, 'Dosage', medication.dosage)

    def populate_incorrect_dosages_treeview(self):
        incorrect_dosages_values = self.patient_object.incorrect_dosages_dict.values()
        for medication in incorrect_dosages_values:
            if isinstance(medication, pillpackData.Medication):
                medication_key = medication.medication_name + " " + str(medication.dosage)
                if not self.incorrect_dosages_treeview.exists(medication_key):
                    self.incorrect_dosages_treeview.insert('', 'end', medication_key,
                                                           text=medication.medication_name,
                                                           tags="missing")
                if self.patient_object.medication_dict.__contains__(medication.medication_name):
                    medication_in_production: pillpackData.Medication = self.patient_object.medication_dict.get(
                        medication.medication_name)
                    self.incorrect_dosages_treeview.set(medication_key, 'Recorded Dosage',
                                                        medication_in_production.dosage)
                self.incorrect_dosages_treeview.set(medication_key, 'Dosage on Script', medication.dosage)
"""


class ScanScripts(Toplevel):
    def __init__(self, parent, master: App):
        super().__init__(parent)
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
        self.geometry("400x300")
        self.label = Label(self, text="Scan scripts below: ")
        self.label.pack(padx=20, pady=20)
        self.entry = Entry(self, width=400)
        self.entry.bind("<Return>", lambda func: self.scan_scripts(self.main_application, self.entry.get()))
        self.entry.pack(padx=20, pady=20)

        self.patient_tree = Treeview(self, columns=('No. of Patients',), height=3)
        self.patient_tree.heading('No. of Patients', text="No. of Patients")
        self.patient_tree.insert('', 'end', 'perfect_matches', text="Perfect Matches", tags=('perfect',))
        self.__iterate_patients(self.main_application.collected_patients.matched_patients.values(), 'perfect_matches')
        self.patient_tree.insert('', 'end', 'minor_mismatches', text="Minor Mismatches", tags=('minor',))
        self.__iterate_patients(self.main_application.collected_patients.minor_mismatch_patients, 'minor_mismatches')
        self.patient_tree.insert('', 'end', 'severe_mismatches', text="Severe Mismatches", tags=('severe',))
        self.__iterate_patients(self.main_application.collected_patients.severe_mismatch_patients, 'severe_mismatches')
        self.patient_tree.tag_configure('perfect', background='#2f8000')
        self.patient_tree.tag_configure('minor', background='#a8a82c')
        self.patient_tree.tag_configure('severe', background='#a30202')
        self.patient_tree.set('perfect_matches', 'No. of Patients',
                              str(len(self.main_application.collected_patients.matched_patients)) + "/"
                              + str(len(self.main_application.collected_patients.pillpack_patient_dict)))
        self.patient_tree.set('minor_mismatches', 'No. of Patients',
                              len(self.main_application.collected_patients.minor_mismatch_patients))
        self.patient_tree.set('severe_mismatches', 'No. of Patients',
                              len(self.main_application.collected_patients.severe_mismatch_patients))
        self.patient_tree.bind('<Double-1>', self.on_treeview_double_click)
        self.patient_tree.pack(padx=20)

    def scan_scripts(self, application: App, script_input: str):
        scriptScanner.scan_script_and_check_medications(application.collected_patients, script_input)
        if self.patient_tree is None:
            if (len(application.collected_patients.matched_patients) > 0
                    or len(application.collected_patients.minor_mismatch_patients) > 0
                    or len(application.collected_patients.severe_mismatch_patients) > 0):
                self.patient_tree = Treeview(self, columns=('No. of Patients',), height=3)
                self.patient_tree.heading('No. of Patients', text="No. of Patients")
                self.patient_tree.insert('', 'end', 'perfect_matches', text="Perfect Matches", tags=('perfect',))
                self.__iterate_patients(application.collected_patients.matched_patients.values(), 'perfect_matches')
                self.patient_tree.insert('', 'end', 'minor_mismatches', text="Minor Mismatches", tags=('minor',))
                self.__iterate_patients(application.collected_patients.minor_mismatch_patients, 'minor_mismatches')
                self.patient_tree.insert('', 'end', 'severe_mismatches', text="Severe Mismatches", tags=('severe',))
                self.__iterate_patients(application.collected_patients.severe_mismatch_patients, 'severe_mismatches')
                self.patient_tree.tag_configure('perfect', background='#2f8000')
                self.patient_tree.tag_configure('minor', background='#a8a82c')
                self.patient_tree.tag_configure('severe', background='#a30202')
                self.patient_tree.set('perfect_matches', 'No. of Patients',
                                      str(len(application.collected_patients.matched_patients)) + "/"
                                      + str(len(application.collected_patients.pillpack_patient_dict)))
                self.patient_tree.set('minor_mismatches', 'No. of Patients',
                                      len(application.collected_patients.minor_mismatch_patients))
                self.patient_tree.set('severe_mismatches', 'No. of Patients',
                                      len(application.collected_patients.severe_mismatch_patients))
                self.patient_tree.bind('<Double-1>', self.on_treeview_double_click)
                self.patient_tree.pack(padx=20)
        else:
            self.patient_tree.set('perfect_matches', 'No. of Patients',
                                  str(len(application.collected_patients.matched_patients)) + "/"
                                  + str(len(application.collected_patients.pillpack_patient_dict)))
            self.__iterate_patients(application.collected_patients.matched_patients.values(), 'perfect_matches')
            self.patient_tree.set('minor_mismatches', 'No. of Patients',
                                  len(application.collected_patients.minor_mismatch_patients))
            self.__iterate_patients(application.collected_patients.minor_mismatch_patients, 'minor_mismatches')
            self.patient_tree.set('severe_mismatches', 'No. of Patients',
                                  len(application.collected_patients.severe_mismatch_patients))
            self.__iterate_patients(application.collected_patients.severe_mismatch_patients, 'severe_mismatches')
        self.main_application.app_observer.update_all()
        self.entry.delete(0, tkinter.END)
        self.entry.focus()

    def __iterate_patients(self, iterator, tree_parent_id):
        for patient_list in iterator:
            if isinstance(patient_list, list):
                for patient in patient_list:
                    if isinstance(patient, scriptScanner.PillpackPatient):
                        pillpack_patients: list = self.main_application.collected_patients.pillpack_patient_dict.get(
                            patient.last_name)
                        pillpack_patients = list(
                            filter
                            (lambda entity:
                             typing.cast(scriptScanner.PillpackPatient, entity).first_name == patient.first_name,
                             pillpack_patients)
                        )
                        matching_pillpack_patient: scriptScanner.PillpackPatient = pillpack_patients[0]
                        if self.patient_tree.exists(patient.first_name + " " + patient.last_name):
                            if len(patient.matched_medications_dict) == len(matching_pillpack_patient.medication_dict):
                                self.patient_tree.item(patient.first_name + " " + patient.last_name,
                                                       text=patient.first_name + " " + patient.last_name,
                                                       image=self.ready_to_produce)
                            else:
                                self.patient_tree.item(patient.first_name + " " + patient.last_name,
                                                       text=patient.first_name + " " + patient.last_name,
                                                       image=self.warning_image)
                        else:
                            if len(patient.matched_medications_dict) == len(matching_pillpack_patient.medication_dict):
                                self.patient_tree.insert(tree_parent_id, 'end',
                                                         patient.first_name + " " + patient.last_name,
                                                         text=patient.first_name + " " + patient.last_name,
                                                         image=self.ready_to_produce)
                            else:
                                self.patient_tree.insert(tree_parent_id, 'end',
                                                         patient.first_name + " " + patient.last_name,
                                                         text=patient.first_name + " " + patient.last_name,
                                                         image=self.warning_image)

    def on_treeview_double_click(self, event):
        tree = self.patient_tree
        if isinstance(tree, Treeview):
            item = tree.selection()[0]
            first_name = item.split(" ")[0]
            last_name = item.split(" ")[1]
            if self.main_application.collected_patients.pillpack_patient_dict.__contains__(last_name):
                list_of_patients: list = self.main_application.collected_patients.pillpack_patient_dict.get(last_name)
                for patient in list_of_patients:
                    if isinstance(patient, pillpackData.PillpackPatient):
                        if patient.first_name == first_name:
                            self.main_application.show_frame(consts.VIEW_PATIENT_SCREEN, patient)
                            self.parent.focus()


def load_patients_from_object(application: App):
    patients: scriptScanner.CollectedPatients = scriptScanner.load_collected_patients_from_object()
    application.collected_patients = patients


def populate_pillpack_production_data(application: App):
    patients: scriptScanner.CollectedPatients = scriptScanner.load_collected_patients_from_object()
    patients.set_pillpack_patient_dict(scriptScanner.load_pillpack_data())
    application.collected_patients = patients


app = App()
app.mainloop()
