import logging
import tkinter
import App
from tkinter import Frame, Label, Button, StringVar, font, ttk, Toplevel

from SideBar import SideBar
from Application.WatchdogEventHandler import WatchdogEventHandler
from Application.WelcomeMessage import NoPillpackFolderLocationSetWarning
from Functions.ConfigSingleton import consts


class ViewPillpackProductionFolder(Frame):
    def __init__(self, parent, master: App.App):
        Frame.__init__(self, parent)
        self.master: App.App = master
        self.descriptor_font = font.Font(family='Verdana', size=20, weight="bold")
        self.folder_location_font = font.Font(family='Verdana', size=14, weight="normal")
        self.folder_location = self.master.config["pillpackDataLocation"]
        self.handler = None
        side_bar = SideBar(self, self.master)
        side_bar.pack(side="left", fill="both")
        container_frame = tkinter.ttk.Frame(self)
        container_frame.pack(side="top", fill="both")
        self.folder_descriptor_label = Label(container_frame, font=self.descriptor_font,
                                             text="Pillpack Production Folder Location:")
        self.folder_descriptor_label.grid(row=0, column=0)
        self.folder_location_string_var: StringVar = StringVar()
        self.folder_location_string_var.set(self.folder_location)
        self.folder_location_label = Label(container_frame, font=self.folder_location_font,
                                           textvariable=self.folder_location_string_var)
        self.folder_location_label.grid(row=1, column=0)
        self.change_pillpack_directory_button = Button(container_frame, text="Select pillpack directory",
                                                       command=lambda: [self.master.set_pillpack_production_directory(),
                                                                        self.update()])
        self.change_pillpack_directory_button.grid(row=2, column=0, pady=50)
        if self.master.config["pillpackDataLocation"] == consts.UNSET_LOCATION:
            warning_message: NoPillpackFolderLocationSetWarning = NoPillpackFolderLocationSetWarning(self)
            warning_message.grab_set()
            logging.warning("No directory for pillpack data has been set by the user.")

    def update(self):
        logging.info("ViewPillpackProductionFolder update function called.")
        self.folder_location = self.master.config["pillpackDataLocation"]
        self.folder_location_string_var.set(self.folder_location)
        self.handler = WatchdogEventHandler(self.master)
        try:
            self.master.filesystem_observer.unschedule(self.master.current_directory_to_watch)
        except KeyError as e:
            logging.exception("{0}".format(e))
        try:
            self.master.current_directory_to_watch = (
                self.master.filesystem_observer.schedule(self.handler, self.master.config["pillpackDataLocation"],
                                                         recursive=False))
            if not self.master.filesystem_observer.is_alive():
                self.master.filesystem_observer.start()
        except Exception as e:
            logging.exception("{0}".format(e))
            warning = Toplevel(master=self.master)
            warning.attributes('-topmost', 'true')
            warning.geometry("400x200")
            warning_label = Label(warning, text="Failed to start filesystem observer...",
                                  wraplength=300)
            warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
            ok_button = Button(warning, text="OK", command=warning.destroy)
            ok_button.grid(row=1, column=0, padx=50, sticky="ew", columnspan=2)
            warning.grab_set()
            logging.info("File system observer started in directory {0} successfully."
                         .format(self.master.config["pillpackDataLocation"]))
            logging.info("ViewPillpackProductionFolder update function call complete.")
