import logging
from tkinter import Toplevel, Label, Button
from tkinter.ttk import Treeview

import App
from Functions.DAOFunctions import save_collected_patients, update_current_prns_and_linked_medications
from DataStructures.Models import PillpackPatient, Medication


class LinkMedication(Toplevel):
    def __init__(self, parent, patient: PillpackPatient,
                 medication: Medication, master: App.App):
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
        self.application: App.App = master
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
