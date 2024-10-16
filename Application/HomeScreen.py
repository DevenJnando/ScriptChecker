import datetime
import logging
import tkinter
from tkinter import Frame, PhotoImage, Label, Button, Entry, Menu, StringVar, font, filedialog
from tkinter.ttk import Treeview

import App
from AppFunctions.TreeviewFunctions import popup_menu, calibrate_width, retrieve_patient_from_tree, search_treeview, \
    sort_treeview
from AppFunctions.Warnings import display_warning_if_pillpack_data_is_not_empty, \
    display_warning_if_pillpack_data_is_empty
from Application.ScanScripts import ScanScripts
from Application.LoadNewProduction import PopulatePatientData
from Functions.ConfigSingleton import warning_constants, consts
from Functions.DAOFunctions import save_collected_patients, archive_pillpack_production
from DataStructures.Models import PillpackPatient
from DataStructures.Repositories import CollectedPatients
import SideBar


class HomeScreen(Frame):
    def __init__(self, parent, master: App.App):
        Frame.__init__(self, parent)
        self.tab_variable = tkinter.DoubleVar(value=75.0)
        self.font = font.Font(family='Verdana', size=14, weight="normal")
        self.master: App.App = master
        warning_image_path = App.icons_dir + "\\warning.png"
        warning_image = PhotoImage(file=warning_image_path)
        self.warning_image = warning_image.subsample(30, 30)
        ready_to_produce_path = App.icons_dir + "\\check.png"
        ready_to_produce = PhotoImage(file=ready_to_produce_path)
        self.ready_to_produce_image = ready_to_produce.subsample(30, 30)
        no_scripts_scanned_path = App.icons_dir + "\\question.png"
        no_scripts_scanned_image = PhotoImage(file=no_scripts_scanned_path)
        self.no_scripts_scanned_image = no_scripts_scanned_image.subsample(30, 30)
        do_not_produce_path = App.icons_dir + "\\remove.png"
        do_not_produce_image = PhotoImage(file=do_not_produce_path)
        self.do_not_produce_image = do_not_produce_image.subsample(30, 30)
        self.list_of_trees = []

        side_bar = SideBar.SideBar(self, self.master)
        side_bar.pack(side="left", fill="both")

        container_frame = tkinter.ttk.Frame(self)
        container_frame.pack(side="top", fill="both")

        options_frame = tkinter.ttk.Frame(container_frame)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(2, weight=1)
        options_frame.grid(row=0, column=1, pady=(25, 5), sticky="ew")
        load_pillpack_image = App.icons_dir + "\\pillpack-data.png"
        load_pillpack_label = Label(options_frame, text="Load Pillpack Production Data", font=self.font, wraplength=150,
                                    justify="center")
        load_pillpack_button_image = PhotoImage(file=load_pillpack_image)
        self.pillpack_button_image = load_pillpack_button_image.subsample(5, 5)
        load_pillpack_button = Button(options_frame, image=self.pillpack_button_image,
                                      command=lambda: display_warning_if_pillpack_data_is_not_empty
                                      (self.master,
                                       self.open_populate_patients_window,
                                       warning_constants.PILLPACK_DATA_OVERWRITE_WARNING)
                                      )
        load_pillpack_label.grid(row=1, column=0, sticky="nsew")
        load_pillpack_button.grid(row=2, column=0, sticky="nsew")

        scan_scripts_image = App.icons_dir + "\\scan_scripts.png"
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
        archive_production_image = App.icons_dir + "\\archive.png"
        archive_production_button_image = PhotoImage(file=archive_production_image)
        self.archive_button_production_image = archive_production_button_image.subsample(5, 5)
        archive_production_button = Button(options_frame, image=self.archive_button_production_image,
                                           command=lambda: self.confirm_production_archival(self.master))
        archive_production_label.grid(row=1, column=2, sticky="nsew")
        archive_production_button.grid(row=2, column=2, sticky="nsew")

        self.group_production_name_var = StringVar()
        self.group_production_name_var.set(self.master.collected_patients.production_group_name)
        self.master.group_production_name = self.group_production_name_var.get()
        production_font = font.Font(family="Arial", size=28, weight="bold")
        production_font.config(underline=True)
        self.group_production_name_label = Label(options_frame,
                                                 textvariable=self.group_production_name_var,
                                                 font=production_font)
        self.group_production_name_label.grid(row=3, column=1)

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
        self.production_right_click_menu = Menu(self.production_patients_tree, tearoff=0)
        self.production_right_click_menu.add_command(label="View Patient",
                                                     command=lambda: self.on_treeview_double_click(
                                                         self.production_patients_tree)
                                                     )
        self.production_right_click_menu.add_command(label="Delete Patient",
                                                     command=lambda: self.delete_patient_and_remove_from_tree(
                                                         self.production_patients_tree)
                                                     )
        self.production_patients_tree.bind("<Button-3>", lambda e: popup_menu(e,
                                                                              self.production_patients_tree,
                                                                              self.production_right_click_menu)
                                           )
        calibrate_width(self.production_patients_tree, self.columns, 150)
        self.production_patients_tree["displaycolumns"] = (
            'Date of Birth', 'Start Date', 'No. of Medications', 'Condition'
        )
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
        self.perfect_patients_right_click_menu = Menu(self.perfect_patients_tree, tearoff=0)
        self.perfect_patients_right_click_menu.add_command(label="View Patient",
                                                           command=lambda: self.on_treeview_double_click(
                                                               self.perfect_patients_tree)
                                                           )
        self.perfect_patients_right_click_menu.add_command(label="Delete Patient",
                                                           command=lambda: self.delete_patient_and_remove_from_tree(
                                                               self.perfect_patients_tree)
                                                           )
        self.perfect_patients_tree.bind("<Button-3>", lambda e: popup_menu(e,
                                                                           self.perfect_patients_tree,
                                                                           self.perfect_patients_right_click_menu)
                                        )
        calibrate_width(self.perfect_patients_tree, self.columns, 150)
        self.perfect_patients_tree["displaycolumns"] = (
            'Date of Birth', 'Start Date', 'No. of Medications', 'Condition'
        )
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
        self.imperfect_patients_right_click_menu = Menu(self.imperfect_patients_tree, tearoff=0)
        self.imperfect_patients_right_click_menu.add_command(label="View Patient",
                                                             command=lambda: self.on_treeview_double_click(
                                                                 self.imperfect_patients_tree)
                                                             )
        self.imperfect_patients_right_click_menu.add_command(label="Delete Patient",
                                                             command=lambda: self.delete_patient_and_remove_from_tree(
                                                                 self.imperfect_patients_tree)
                                                             )
        self.imperfect_patients_tree.bind("<Button-3>", lambda e: popup_menu(e,
                                                                             self.imperfect_patients_tree,
                                                                             self.imperfect_patients_right_click_menu)
                                          )
        calibrate_width(self.imperfect_patients_tree, self.columns, 150)
        self.imperfect_patients_tree["displaycolumns"] = (
            'Date of Birth', 'Start Date', 'No. of Medications', 'Condition'
        )
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
        self.mismatched_right_click_menu = Menu(self.mismatched_patients_tree, tearoff=0)
        self.mismatched_right_click_menu.add_command(label="View Patient",
                                                     command=lambda: self.on_treeview_double_click(
                                                         self.mismatched_patients_tree)
                                                     )
        self.mismatched_right_click_menu.add_command(label="Delete Patient",
                                                     command=lambda: self.delete_patient_and_remove_from_tree(
                                                         self.mismatched_patients_tree)
                                                     )
        self.mismatched_patients_tree.bind("<Button-3>", lambda e: popup_menu(e,
                                                                              self.mismatched_patients_tree,
                                                                              self.mismatched_right_click_menu)
                                           )
        calibrate_width(self.mismatched_patients_tree, self.columns, 150)
        self.mismatched_patients_tree["displaycolumns"] = (
            'Date of Birth', 'Start Date', 'No. of Medications', 'Condition'
        )
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
        self.populate_patients_window = None

    def delete_patient_and_remove_from_tree(self, tree_to_delete_from: Treeview):
        if isinstance(tree_to_delete_from, Treeview):
            selected_patient = retrieve_patient_from_tree(tree_to_delete_from, self.master)
            if isinstance(selected_patient, PillpackPatient):
                self.master.collected_patients.remove_pillpack_patient(selected_patient)
                self.master.collected_patients.remove_matched_patient(selected_patient)
                self.master.collected_patients.remove_minor_mismatched_patient(selected_patient)
                self.master.collected_patients.remove_severely_mismatched_patient(selected_patient)
                self.master.collected_patients.remove_patient(selected_patient)
                tree_to_delete_from.delete(tree_to_delete_from.focus())
                save_collected_patients(self.master.collected_patients)
                self.update()

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
                            self.master.match_patient_to_pillpack_patient
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
                        tree_to_refresh.set(key, 'No. of Medications',
                                            len(matching_pillpack_patient.production_medications_dict))
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
                                self.master.match_patient_to_pillpack_patient
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

    def clear_all_trees(self):
        for i in range(len(self.list_of_trees)):
            tree: Treeview = self.list_of_trees[i][0]
            tree.delete(*tree.get_children())

    def update(self):
        logging.info("HomeScreen update function called.")
        self._update_list_of_trees()
        self._refresh_patient_status()
        self.set_tree_widgets()
        self.group_production_name_var.set(self.master.collected_patients.production_group_name)
        self.master.group_production_name = self.group_production_name_var.get()
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

    def confirm_production_archival(self, application: App):
        warning = tkinter.Toplevel(master=application)
        warning.attributes('-topmost', 'true')
        warning.geometry("400x200")
        warning_label = Label(warning, text="Warning: Archiving this production will PERMENANTLY archive "
                                            "all working data. This means you will not be able to make any more "
                                            "modifications on the current production after archival. "
                                            "Are you sure you wish to archive the current production? ",
                              wraplength=300)
        warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
        archive_button = Button(warning, text="OK",
                                command=lambda: [warning.destroy(), self.archive_pillpack_production_dialog()])
        archive_button.grid(row=1, column=0, padx=50, sticky="ew")
        cancel_button = Button(warning, text="Cancel", command=warning.destroy)
        cancel_button.grid(row=1, column=1, padx=50, sticky="ew")

    def archive_pillpack_production_dialog(self):
        archive_file = filedialog.asksaveasfile(initialfile="Untitled", defaultextension=".zip",
                                                filetypes=[("ZIP files", ".zip"), ("All files", ".*")])
        if archive_file:
            archive_pillpack_production(archive_file, self.master.config, self.master.collected_patients)
            self.master.collected_patients = CollectedPatients()
            self.clear_all_trees()
            self.update()

    def open_populate_patients_window(self):
        if self.populate_patients_window is None or not self.populate_patients_window.winfo_exists():
            logging.info("No Populate Patients view has been instatiated. Creating new Populate Patients view...")
            self.populate_patients_window = PopulatePatientData(self, self.master)
            self.populate_patients_window.grab_set()
        else:
            logging.info("Populate Patients view is now in focus.")
            self.populate_patients_window.focus()

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
                selected_patient = retrieve_patient_from_tree(tree_to_select_from, self.master)
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