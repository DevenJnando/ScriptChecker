import App
from tkinter import Frame, Button, filedialog, Toplevel, Label
from zipfile import ZipFile

from AppFunctions.Warnings import display_warning_if_pillpack_data_is_empty
from Application.ScanScripts import ScanScripts
from Functions.ConfigSingleton import consts, warning_constants
from Functions.DAOFunctions import load_collected_patients_from_zip_file, save_collected_patients


class SideBar(Frame):
    def __init__(self, parent, master: App.App):
        Frame.__init__(self, parent)
        self.configure(width=50, height=master.winfo_height())
        self.master: App.App = master
        self.script_window = None
        self.view_patients_button = Button(self, text="Home Screen",
                                           command=lambda: self.master.show_frame(consts.HOME_SCREEN))
        self.view_patients_button.grid(row=0, column=0, pady=10)
        self.scan_scripts_button = Button(self, text="Scan Scripts",
                                          command=lambda: display_warning_if_pillpack_data_is_empty
                                          (self.master,
                                           self.open_scan_scripts_window,
                                           warning_constants.NO_LOADED_PILLPACK_DATA_WARNING))
        self.scan_scripts_button.grid(row=1, column=0, pady=50)
        self.archive_production_data_button = Button(self, text="Archive Production Data",
                                                     command=lambda: parent.confirm_production_archival(self.master))
        self.archive_production_data_button.grid(row=2, column=0, pady=50)
        self.load_previous_production_data_button = Button(self, text="Load Previous Production Data",
                                                           command=self.open_production_archive)
        self.load_previous_production_data_button.grid(row=3, column=0, pady=50)
        self.view_pillpack_folder_location_button = Button(self, text="View Pillpack Folder location",
                                                           command=lambda: self.master.show_frame
                                                           (consts.VIEW_PILLPACK_FOLDER_LOCATION))
        self.view_pillpack_folder_location_button.grid(row=4, column=0, pady=50)

    def open_production_archive(self):
        archived_production_path = filedialog.askopenfilename(initialdir=self.master.config["pillpackDataLocation"],
                                                              title="Select Production Archival",
                                                              filetypes=(("ZIP files", "*.zip"), ))
        if archived_production_path:
            with ZipFile(archived_production_path, 'r') as archived_production:
                if isinstance(archived_production, ZipFile):
                    loaded_collected_patients = load_collected_patients_from_zip_file(archived_production)
                    if loaded_collected_patients is None:
                        warning = Toplevel(master=self.master)
                        warning.attributes('-topmost', 'true')
                        warning.geometry("400x200")
                        warning_label = Label(warning, text="No archived production file could be found in this archive. "
                                                            "Please choose a valid production archive.",
                                              wraplength=300)
                        warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
                        archive_button = Button(warning, text="OK",
                                                command=warning.destroy)
                        archive_button.grid(row=1, column=0, padx=50, sticky="ew")
                    else:
                        self.master.collected_patients = loaded_collected_patients
                        save_collected_patients(self.master.collected_patients)
                        self.master.app_observer.update_all()
                        success = Toplevel(master=self.master)
                        success.attributes('-topmost', 'true')
                        success.geometry("400x200")
                        warning_label = Label(success, text="Successfully loaded the archived production file!",
                                              wraplength=300)
                        warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
                        archive_button = Button(success, text="OK",
                                                command=success.destroy)
                        archive_button.grid(row=1, column=0, padx=50, sticky="ew")

    def open_scan_scripts_window(self):
        if self.script_window is None or not self.script_window.winfo_exists():
            self.script_window = ScanScripts(self, self.master)
            self.script_window.grab_set()
        else:
            self.script_window.focus()
