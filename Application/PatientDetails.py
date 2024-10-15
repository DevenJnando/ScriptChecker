import logging
import tkinter
import App
from tkinter import Label, Button, Frame, LabelFrame, PhotoImage, font, ttk
from tkinter.constants import VERTICAL, Y

from AppFunctions.CreateToolTip import create_tool_tip
from Application.LinkMedication import LinkMedication
from Functions.KardexAndPRNGeneration import generate_patient_kardex, generate_prn_list_for_current_cycle
from Application.UnlinkMedication import UnlinkMedication
from Functions.ConfigSingleton import consts
from Functions.DAOFunctions import save_collected_patients, update_current_prns_and_linked_medications
from Application.SideBar import SideBar
from Application.HomeScreen import HomeScreen
from DataStructures.Models import PillpackPatient, Medication


class PatientMedicationDetails(Frame):
    def __init__(self, parent, master: App.App, patient: PillpackPatient):
        Frame.__init__(self, parent)
        self.link_medication_window = None
        self.unlink_medication_window = None
        self.change_toggle_button_image = None
        link_icon_path = App.icons_dir + "\\link.png"
        link_icon_image = PhotoImage(file=link_icon_path)
        self.linked_medication_image = link_icon_image.subsample(20, 20)
        self.do_not_produce_image = None
        self.missing_scripts_image = None
        self.no_scripts_scanned_image = None
        self.ready_to_produce_image = None
        self.font = font.Font(family='Verdana', size=14, weight="normal")
        self.home_screen: HomeScreen = parent
        self.master: App.App = master
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
        self.generate_kardex_button = Button(self.display_frame, text="Generate Kardex",
                                             command=lambda: generate_patient_kardex(
                                                 self.patient_object,
                                                 self.master.group_production_name
                                             ))
        self.generate_prns_button = Button(self.display_frame, text="Generate Dispensation list",
                                           command=lambda: generate_prn_list_for_current_cycle(
                                               self.patient_object,
                                               self.master.group_production_name
                                           ))
        manually_checked_toggle_label.grid(row=1, column=1)
        self.changes_toggle_button.grid(row=1, column=2)
        self.generate_kardex_button.grid(row=2, column=1)
        self.generate_prns_button.grid(row=3, column=1)

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
            on_button_path = App.icons_dir + "\\on-button.png"
            on_button_image = PhotoImage(file=on_button_path)
            self.change_toggle_button_image = on_button_image.subsample(10, 10)
            self.changes_toggle_button.config(image=self.change_toggle_button_image)
        else:
            off_button_path = App.icons_dir + "\\off-button.png"
            off_button_image = PhotoImage(file=off_button_path)
            self.change_toggle_button_image = off_button_image.subsample(10, 10)
            self.changes_toggle_button.config(image=self.change_toggle_button_image)

        match self.patient_object.ready_to_produce_code:
            case consts.READY_TO_PRODUCE_CODE:
                ready_to_produce_path = App.icons_dir + "\\check.png"
                ready_to_produce_image = PhotoImage(file=ready_to_produce_path)
                self.ready_to_produce_image = ready_to_produce_image.subsample(5, 5)
                ready_to_produce_label = Label(self.display_frame, font=self.font,
                                               image=self.ready_to_produce_image)
                ready_to_produce_label.grid(row=0, column=1)
            case consts.NOTHING_TO_COMPARE_CODE:
                no_scripts_scanned_path = App.icons_dir + "\\question.png"
                no_scripts_scanned_image = PhotoImage(file=no_scripts_scanned_path)
                self.no_scripts_scanned_image = no_scripts_scanned_image.subsample(5, 5)
                no_scripts_scanned_label = Label(self.display_frame, font=self.font,
                                                 image=self.no_scripts_scanned_image)
                no_scripts_scanned_label.grid(row=0, column=1)
            case consts.MISSING_MEDICATIONS_CODE:
                missing_scripts_path = App.icons_dir + "\\warning.png"
                missing_scripts_image = PhotoImage(file=missing_scripts_path)
                self.missing_scripts_image = missing_scripts_image.subsample(5, 5)
                missing_scripts_label = Label(self.display_frame, font=self.font,
                                              image=self.missing_scripts_image)
                missing_scripts_label.grid(row=0, column=1)
            case consts.DO_NOT_PRODUCE_CODE:
                do_not_produce_path = App.icons_dir + "\\remove.png"
                do_not_produce_image = PhotoImage(file=do_not_produce_path)
                self.do_not_produce_image = do_not_produce_image.subsample(5, 5)
                do_not_produce_label = Label(self.display_frame, font=self.font,
                                             image=self.do_not_produce_image)
                do_not_produce_label.grid(row=0, column=1)
            case consts.MANUALLY_CHECKED_CODE:
                ready_to_produce_path = App.icons_dir + "\\check.png"
                ready_to_produce_image = PhotoImage(file=ready_to_produce_path)
                self.ready_to_produce_image = ready_to_produce_image.subsample(5, 5)
                ready_to_produce_label = Label(self.display_frame, font=self.font,
                                               image=self.ready_to_produce_image, text="Proceed with caution")
                ready_to_produce_label.grid(row=0, column=1)

    def populate_label_frame(self, label_frame_to_populate: LabelFrame, frame_title: str,
                             row_number: int, dictionary_to_iterate: dict = None,
                             list_to_iterate: list = None,
                             include_prn_medications_button: bool = False,
                             include_delete_prn_medications_button: bool = False,
                             create_medication_link_button: bool = False,
                             remove_from_ignored_medications_button=False,
                             include_doctors_directions: bool = False
                             ):
        values: list = []
        if dictionary_to_iterate is not None:
            values: list = list(dictionary_to_iterate.values())
        elif list_to_iterate is not None:
            values: list = list_to_iterate
        if len(values) > 0:
            medication_label = Label(self.display_frame, text=frame_title)
            medication_label.grid(row=row_number, column=0, pady=20)
            label_frame_to_populate.grid(row=row_number + 1, column=0, padx=20, pady=20, sticky="ew")
            medication_name_label = Label(label_frame_to_populate, text="Medication Name")
            medication_name_label.grid(row=0, column=0)
            medication_dosage_label = Label(label_frame_to_populate, text="Dosage")
            medication_dosage_label.grid(row=0, column=1)
            if include_doctors_directions:
                doctors_directions_label = Label(label_frame_to_populate, text="Doctor's Orders")
                doctors_directions_label.grid(row=0, column=2)
        for i in range(0, len(values)):
            medication = values[i]
            if isinstance(medication, Medication):
                logging.info("Displaying medication {0}".format(medication.medication_name))
                medication_name_label = Label(label_frame_to_populate, text=medication.medication_name,
                                              wraplength=150)
                medication_dosage_label = Label(label_frame_to_populate, text=medication.dosage)
                medication_name_label.grid(row=i + 1, column=0)
                medication_dosage_label.grid(row=i + 1, column=1)
                if include_doctors_directions:
                    doctors_directions = Label(label_frame_to_populate, text=medication.doctors_orders, wraplength=150)
                    doctors_directions.grid(row=i + 1, column=2)
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
            self.link_medication_window = LinkMedication(self,
                                                         self.patient_object,
                                                         selected_medication,
                                                         self.master)
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
        self.patient_object.add_medication_to_prns_for_current_cycle(selected_medication)
        self.patient_object.add_medication_to_prn_dict(selected_medication)
        save_collected_patients(self.master.collected_patients)
        update_current_prns_and_linked_medications(self.patient_object,
                                                   self.master.collected_patients,
                                                   self.master.loaded_prns_and_linked_medications)
        self.master.app_observer.update_all()

    def remove_prn_medication(self, selected_medication: Medication):
        if self.patient_object.prn_medications_dict.__contains__(selected_medication.medication_name):
            self.patient_object.remove_medication_from_prns_for_current_cycle(selected_medication)
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
        if (len(self.patient_object.matched_medications_dict) != len(self.patient_object.production_medications_dict)
                and not self.patient_object.manually_checked_flag):
            self.generate_prns_button.configure(state="disabled")
        else:
            self.generate_prns_button.configure(state="normal")
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
                                  dictionary_to_iterate=self.patient_object.production_medications_dict
                                  )
        self.populate_label_frame(self.matched_medication_frame,
                                  "Matched Medications",
                                  3,
                                  dictionary_to_iterate=self.patient_object.matched_medications_dict,
                                  include_doctors_directions=True
                                  )
        self.populate_label_frame(self.prn_medications_frame,
                                  "PRN Medications Outside Pillpack",
                                  5,
                                  list_to_iterate=self.patient_object.prns_for_current_cycle,
                                  include_prn_medications_button=False,
                                  include_delete_prn_medications_button=True,
                                  include_doctors_directions=True
                                  )
        self.populate_label_frame(self.missing_medication_frame,
                                  "Missing Medications",
                                  7,
                                  dictionary_to_iterate=self.patient_object.missing_medications_dict,
                                  include_prn_medications_button=True,
                                  include_delete_prn_medications_button=False,
                                  )
        self.populate_label_frame(self.unknown_medication_frame,
                                  "Unknown Medications",
                                  9,
                                  dictionary_to_iterate=self.patient_object.unknown_medications_dict,
                                  include_prn_medications_button=True,
                                  include_delete_prn_medications_button=False,
                                  create_medication_link_button=True,
                                  include_doctors_directions=True
                                  )
        self.populate_label_frame(self.ignore_medications_frame,
                                  "Ignored Incorrect Dosages",
                                  11,
                                  dictionary_to_iterate=self.patient_object.medications_to_ignore,
                                  include_prn_medications_button=False,
                                  include_delete_prn_medications_button=False,
                                  create_medication_link_button=False,
                                  remove_from_ignored_medications_button=True
                                  )
        self.populate_incorrect_dosages_label_frame(self.incorrect_medication_dosage_frame,
                                                    13)
        self.display_canvas.update_idletasks()
        self.display_canvas.config(scrollregion=self.display_frame.bbox())
        logging.info("PatientMedicationDetails update function call complete.")
