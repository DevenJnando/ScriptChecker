import datetime
import sys
import tkinter
import typing
from tkinter.ttk import Treeview
from tkinter import *
from tkinter import font
from PIL import Image

import pillpackData
import scriptScanner

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


class OptionSelectFrame(Frame):
    def __init__(self, master, option_title, option_image, function, row, col, **kwargs):
        super().__init__(master, **kwargs)
        self.font = font.Font(family='Verdana', size=18, weight="normal")
        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.labels = []
        self.buttons = []
        label = Label(self, text=option_title, font=self.font)
        button_image = tkinter.Image(light_image=Image.open(option_image), dark_image=Image.open(option_image),
                                size=(64, 64), imgtype="png")
        button = Button(self, text="", image=button_image, command=function, width=5, height=5)
        label.grid(row=row, column=col, padx=50, pady=(10, 0), sticky="ew")
        button.grid(row=row+1, column=col, padx=50, pady=(10, 0), sticky="w")
        self.labels.append(label)
        self.buttons.append(button)


class App(tkinter.Tk):
    def __init__(self):
        super().__init__()
        self.style = tkinter.ttk.Style(self)
        self.tk.call("source", themes_dir + "\\" + "forest-dark.tcl")
        self.style.theme_use("forest-dark")
        self.geometry("1080x720")
        self.title("Pillpack Script Checker")
        self.collected_patients = scriptScanner.CollectedPatients()
        self.total_medications = 0
        self.title_font = font.Font(family='Verdana', size=28, weight="bold")
        self.container = Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.show_frame()

        #set_appearance_mode("dark")

    def show_frame(self, patient_to_view: pillpackData.PillpackPatient = None):
        if patient_to_view is None:
            frame: HomeScreen = HomeScreen(parent=self.container, master=self)
            frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
            frame.tkraise()
        elif isinstance(patient_to_view, pillpackData.PillpackPatient):
            frame: Frame = PatientMedicationDetails(parent=self.container, master=self, patient=patient_to_view)
            frame.grid(row=0, column=0, padx=50, pady=(50, 50), sticky="nsew", columnspan=4, rowspan=4)
            frame.tkraise()


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
        title_label = Label(self, text="Pillpack Script Checker", font=self.master.title_font,
                            justify="center")
        title_label.grid(row=0, column=0, pady=20, columnspan=2)

        options_frame = tkinter.ttk.Frame(self)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(2, weight=1)
        options_frame.grid(row=1, column=0, pady=(25, 5), sticky="ew")
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
                                     command=lambda: self.open_scan_scripts_window())
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
        paned_window.grid(row=3, column=0, pady=(25, 5), sticky="nsew", rowspan=4)

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
                    self.master.show_frame(selected_patient)
            except IndexError as e:
                print("IndexError: ", e)


class PatientMedicationDetails(Frame):
    def __init__(self, parent, master: App, patient: pillpackData.PillpackPatient):
        Frame.__init__(self, parent)
        self.font = font.Font(family='Verdana', size=14, weight="normal")
        self.home_screen: HomeScreen = parent
        self.master: App = master
        self.patient_object: pillpackData.PillpackPatient = patient
        self.patient_tree_key = self.patient_object.first_name + " " + self.patient_object.last_name

        display_frame = tkinter.ttk.Frame(self)
        display_frame.columnconfigure(0, weight=0)
        display_frame.columnconfigure(1, weight=2)
        display_frame.grid(row=0, column=0, sticky="ew")

        test_label = Label(display_frame, font=self.font,
                           text=self.patient_tree_key)
        test_label.grid(row=0, column=0)

        back_button = Button(display_frame, text="Go back",
                             command=self.master.show_frame)
        back_button.grid(row=1, column=0)

        test_label_2 = Label(display_frame, font=self.font, text="This is another label")
        test_label_2.grid(row=0, column=1)

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


class ScanScripts(Toplevel):
    def __init__(self, parent: HomeScreen, master: App):
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
        self.home_screen: HomeScreen = parent
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
        self.home_screen.refresh_treeview(self.home_screen.production_patients_tree,
                                          self.main_application.collected_patients.pillpack_patient_dict)
        self.home_screen.refresh_treeview(self.home_screen.perfect_patients_tree,
                                          self.main_application.collected_patients.matched_patients)
        self.home_screen.refresh_treeview(self.home_screen.imperfect_patients_tree,
                                          self.main_application.collected_patients.minor_mismatch_patients)
        self.home_screen.refresh_treeview(self.home_screen.mismatched_patients_tree,
                                          self.main_application.collected_patients.severe_mismatch_patients)
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
                            self.main_application.show_frame(patient)
                            self.home_screen.focus()


def load_patients_from_object(application: App):
    patients: scriptScanner.CollectedPatients = scriptScanner.load_collected_patients_from_object()
    application.collected_patients = patients


def populate_pillpack_production_data(application: App):
    patients: scriptScanner.CollectedPatients = scriptScanner.load_collected_patients_from_object()
    patients.set_pillpack_patient_dict(scriptScanner.load_pillpack_data())
    application.collected_patients = patients


app = App()
app.mainloop()
