import logging
import App
from tkinter import Toplevel, Label, Button

from Functions.DAOFunctions import save_collected_patients, update_current_prns_and_linked_medications
from Models import PillpackPatient, Medication


class UnlinkMedication(Toplevel):
    def __init__(self, parent, patient: PillpackPatient,
                 medication_key: str, master: App.App):
        super().__init__(parent)
        self.attributes('-topmost', 'true')
        self.selected_patient: PillpackPatient = patient
        self.medication_key_to_be_unlinked: str = medication_key
        if self.selected_patient.linked_medications[medication_key] is not None:
            self.medication_to_be_unlinked: Medication = self.selected_patient.linked_medications[medication_key]
        else:
            self.medication_to_be_unlinked: Medication = Medication("Invalid Medication", 0,
                                                                    self.medication_to_be_unlinked.start_date)
        self.application: App.App = master
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
