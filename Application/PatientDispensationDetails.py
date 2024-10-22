from tkinter import Toplevel, Label, Entry, Text, Button, font
from typing import Callable

from Application import App
from DataStructures.Models import PillpackPatient


class PatientDispensationDetails(Toplevel):
    def __init__(self, parent, master: App.App, patient: PillpackPatient,
                 callback_function: Callable[[PillpackPatient, str], None]):
        super().__init__(parent)
        self.geometry("1200x650")
        self.minsize(1200, 650)
        self.maxsize(1200, 650)
        self.attributes('-topmost', 'true')
        self.parent = parent
        self.master: App.App = master
        self.patient_object = patient
        self.function: Callable = callback_function
        self.font = font.Font(family='Verdana', size=14, weight="normal")

        self.entry_list: list = []
        self.header = Label(self,
                            text="Please complete the following fields using the patient's script(s) as a reference. "
                                 "(You're seeing this message because you attempted to generate a dispensation list "
                                 "without scanning in any scripts for this patient)",
                            font=self.font,
                            wraplength=1000
                            )
        self.address_label = Label(self, text="Patient Address:", wraplength=200)
        self.address_textbox = Text(self, height=3, width=50)
        self.entry_list.append(self.address_textbox)
        self.postcode_label = Label(self, text="Patient Postcode:", wraplength=200)
        self.postcode_entry = Entry(self, width=50)
        self.entry_list.append(self.postcode_entry)
        self.healthcare_no_label = Label(self, text="H+C Number:", wraplength=200)
        self.healthcare_no_entry = Entry(self, width=50)
        self.entry_list.append(self.healthcare_no_entry)
        self.doctor_name_label = Label(self, text="Prescribing Doctor:", wraplength=200)
        self.doctor_name_entry = Entry(self, width=50)
        self.entry_list.append(self.doctor_name_entry)
        self.patient_surgery_label = Label(self, text="Patient's Surgery:", wraplength=200)
        self.patient_surgery_entry = Entry(self, width=50)
        self.entry_list.append(self.patient_surgery_entry)
        self.surgery_address_label = Label(self, text="Surgery Address:", wraplength=200)
        self.surgery_address_textbox = Text(self, height=3, width=50)
        self.entry_list.append(self.surgery_address_textbox)
        self.surgery_postcode_label = Label(self, text="Surgery Postcode:", wraplength=200)
        self.surgery_postcode_entry = Entry(self, width=50)
        self.entry_list.append(self.surgery_postcode_entry)
        self.submit_button = Button(self, text="Submit",
                                    command=lambda: self.update_patient(self.verify_input_fields())
                                    )
        self.cancel_button = Button(self, text="Cancel")

        self.header.grid(row=0, column=0, padx=10, pady=10, columnspan=2)
        self.address_label.grid(row=1, column=0, padx=10, pady=10)
        self.address_textbox.grid(row=1, column=1, padx=10, pady=10)
        self.postcode_label.grid(row=2, column=0, padx=10, pady=10)
        self.postcode_entry.grid(row=2, column=1, padx=10, pady=10)
        self.healthcare_no_label.grid(row=3, column=0, padx=10, pady=10)
        self.healthcare_no_entry.grid(row=3, column=1, padx=10, pady=10)
        self.doctor_name_label.grid(row=4, column=0, padx=10, pady=10)
        self.doctor_name_entry.grid(row=4, column=1, padx=10, pady=10)
        self.patient_surgery_label.grid(row=5, column=0, padx=10, pady=10)
        self.patient_surgery_entry.grid(row=5, column=1, padx=10, pady=10)
        self.surgery_address_label.grid(row=6, column=0, padx=10, pady=10)
        self.surgery_address_textbox.grid(row=6, column=1, padx=10, pady=10)
        self.surgery_postcode_label.grid(row=7, column=0, padx=10, pady=10)
        self.surgery_postcode_entry.grid(row=7, column=1, padx=10, pady=10)
        self.submit_button.grid(row=8, column=0, padx=10, pady=10)
        self.cancel_button.grid(row=8, column=1, padx=10, pady=10)

    def verify_input_fields(self):
        fields_verified: bool = True
        for i in range(0, len(self.entry_list)):
            entry = self.entry_list[i]
            if isinstance(entry, Entry):
                if entry.get() is None or entry.get() == "":
                    fields_verified = False
                    field_required_message = Label(self, text="*Required field", fg="red", wraplength=70)
                    field_required_message.grid(row=i+1, column=2, padx=10, pady=10)
            elif isinstance(entry, Text):
                if entry.get("1.0", "end-1c") is None or entry.get("1.0", "end-1c") == "":
                    fields_verified = False
                    field_required_message = Label(self, text="*Required field", fg="red")
                    field_required_message.grid(row=i+1, column=2, padx=10, pady=30)
        return fields_verified

    def update_patient(self, fields_verified: bool):
        if fields_verified:
            self.patient_object.address = self.address_textbox.get("1.0", "end-1c")
            self.patient_object.postcode = self.postcode_entry.get()
            self.patient_object.healthcare_no = self.healthcare_no_entry.get()
            self.patient_object.doctor_name = self.doctor_name_entry.get()
            self.patient_object.surgery = self.patient_surgery_entry.get()
            self.patient_object.surgery_address = self.surgery_address_textbox.get("1.0", "end-1c")
            self.patient_object.surgery_postcode = self.surgery_postcode_entry.get()
            self.destroy()
            self.function(self.patient_object, self.master.group_production_name)
