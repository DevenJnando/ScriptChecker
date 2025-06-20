from tkinter import Toplevel, Label, Button

from Application import App


"""
A convenient module for reuse of generic warning messages and notifications to the user before the execution of various
other functions within the application.
"""


def display_warning_if_pillpack_data_is_empty(application: App, function, warning_text: str):
    """
    Generic warning box which is displayed when there are no PillpackPatient objects in the main App base class.
    If no warning is displayed, a function callable will be executed with no extra prompt.

    :param application: The base App class which contains all objects used by the rest of application
    :param function: A wrapper for a function which will be passed to the display_warning function
    :param warning_text: Warning text to be passed to the display_warning function
    :return: None
    """
    if len(application.collected_patients.pillpack_patient_dict) == 0:
        display_warning(application, function, warning_text)
    else:
        function()


def display_warning_if_pillpack_data_is_not_empty(application: App, function, warning_text: str):
    """
    Generic warning box which is displayed when there are PillpackPatient objects present in the main App base class.
    If no warning is displayed, a function callable will be executed with no extra prompt.

    :param application: The base App class which contains all objects used by the rest of application
    :param function: A wrapper for a function which will be passed to the display_warning function
    :param warning_text: Warning text to be passed to the display_warning function
    :return: None
    """
    if len(application.collected_patients.pillpack_patient_dict) > 0:
        display_warning(application, function, warning_text)
    else:
        function()


def display_warning(application: App, function, warning_text: str):
    """
    Generic warning box will be displayed to the user. 'Continue' and 'Go back' options are presented to the user.
    Upon selecting the 'Continue' option, a generic callable associated with some function will be executed.
    Selecting 'Go back' destroys the warning box and cancels any further action.

    :param application: The base App class which contains all objects used by the rest of the application
    :param function: A wrapper for a function which will be called upon the user selecting 'Continue'
    :param warning_text: Warning text which will be displayed to the user
    :return: None
    """
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
