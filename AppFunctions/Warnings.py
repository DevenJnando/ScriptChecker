from tkinter import Toplevel, Label, Button

from App import App


def display_warning_if_pillpack_data_is_empty(application: App, function, warning_text: str):
    if len(application.collected_patients.pillpack_patient_dict) == 0:
        display_warning(application, function, warning_text)
    else:
        function()


def display_warning_if_pillpack_data_is_not_empty(application: App, function, warning_text: str):
    if len(application.collected_patients.pillpack_patient_dict) > 0:
        display_warning(application, function, warning_text)
    else:
        function()


def display_warning(application: App, function, warning_text: str):
    warning = Toplevel(master=application)
    warning.attributes('-topmost', 'true')
    warning.geometry("300x240")
    warning_label = Label(warning, text=warning_text,
                          wraplength=200)
    warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
    continue_button = Button(warning, text="Continue",
                             command=lambda: [warning.destroy(),
                                              function()
                                              ])
    continue_button.grid(row=1, column=0, padx=50, sticky="ew")
    go_back_button = Button(warning, text="Go back", command=warning.destroy)
    go_back_button.grid(row=1, column=1, padx=50, sticky="ew")
