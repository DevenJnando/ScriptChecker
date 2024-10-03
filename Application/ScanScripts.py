import logging
import tkinter
import App
from functools import reduce
from tkinter import Toplevel, PhotoImage, Label, Entry, Button
from tkinter.ttk import Treeview

from Functions.ConfigSingleton import consts
from Functions.Mutations import scan_script_and_check_medications
from Models import PillpackPatient


class ScanScripts(Toplevel):
    def __init__(self, parent, master: App.App):
        super().__init__(parent)
        self.attributes('-topmost', 'true')
        warning_image_path = App.icons_dir + "\\warning.png"
        warning_image = PhotoImage(file=warning_image_path)
        self.warning_image = warning_image.subsample(40, 40)
        ready_to_produce_path = App.icons_dir + "\\check.png"
        ready_to_produce = PhotoImage(file=ready_to_produce_path)
        self.ready_to_produce = ready_to_produce.subsample(40, 40)
        self.patient_tree = None
        self.matched_patients = None
        self.minor_mismatched_patients = None
        self.severe_mismatched_patients = None
        self.main_application: App.App = master
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
                            self.main_application.match_patient_to_pillpack_patient
                            (patient, self.main_application.collected_patients.pillpack_patient_dict)
                        )
                        if self.patient_tree.exists(patient.first_name + " " + patient.last_name):
                            logging.info("Patient {0} {1} exists within {2}."
                                         .format(patient.first_name, patient.last_name, iterator))
                            if (len(patient.matched_medications_dict) ==
                                    len(matching_pillpack_patient.production_medications_dict)):
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
