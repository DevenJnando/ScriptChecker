import datetime
from tkinter import filedialog

from Functions.DocxGeneration import generate_kardex_doc_file, generate_prn_list_doc_file
from Models import PillpackPatient


def generate_patient_kardex(patient: PillpackPatient, production_name: str):
    default_file_name = "{0} {1} {2} {3} generated kardex".format(patient.first_name,
                                                                  patient.last_name,
                                                                  production_name,
                                                                  datetime.date.today()
                                                                  )
    kardex_file = filedialog.asksaveasfile(initialfile=default_file_name, defaultextension=".docx",
                                           filetypes=[("docx files", ".docx"), ("All files", ".*")])
    if kardex_file:
        generate_kardex_doc_file(patient, production_name, kardex_file.name)


def generate_prn_list_for_current_cycle(patient: PillpackPatient, production_name: str):
    default_file_name = "{0} {1} {2} {3} generated PRN list".format(patient.first_name,
                                                                    patient.last_name,
                                                                    production_name,
                                                                    datetime.date.today()
                                                                    )
    prn_file = filedialog.asksaveasfile(initialfile=default_file_name, defaultextension=".docx",
                                        filetypes=[("docx files", ".docx"), ("All files", ".*")])
    if prn_file:
        generate_prn_list_doc_file(patient, production_name, prn_file.name)
