import datetime
import logging
import threading
from tkinter import Toplevel, Label, Entry, Button
from tkinter.ttk import Treeview

from tkcalendar import Calendar

import App
from Functions.ConfigSingleton import consts
from Functions.DAOFunctions import save_collected_patients
from Functions.ModelFactory import get_patient_medicine_data_ppc
from DataStructures.Repositories import CollectedPatients


class PopulatePatientData(Toplevel):
    def __init__(self, parent, master: App.App):
        super().__init__(parent)
        self.geometry("600x400")
        self.attributes('-topmost', 'true')
        self.parent = parent
        self.master: App.App = master
        self.loading_message_thread: threading.Thread = threading.Thread(target=self.execute_loading_message)
        self.get_production_thread = threading.Thread(target=self.threaded_get_production_data)
        self.delete_loading_message_thread = threading.Thread(target=self.delete_loading_message)
        self.update_thread = threading.Thread(target=self.threaded_update)
        self.production_group_label = Label(self, text="Pillpack Production Group Name:", wraplength=200)
        self.production_group_input = Entry(self, width=20)
        self.production_date_label = Label(self, text="Start Date for Group", wraplength=200)
        self.production_date_calendar = Calendar(self, selectmode="day", year=datetime.date.today().year,
                                                 month=datetime.date.today().month,
                                                 day=datetime.date.today().day, date_pattern='y-mm-dd')
        self.production_scan_dir_button = Button(self, text="Scan for Patients",
                                                 command=lambda:
                                                 self.verify_group_name(
                                                     datetime.date.fromisoformat(
                                                         self.production_date_calendar.get_date())
                                                    )
                                                 )
        self.production_group_label.grid(row=0, column=0, padx=25, pady=30)
        self.production_group_input.grid(row=0, column=1, padx=25, pady=30)
        self.production_date_label.grid(row=1, column=0, padx=25, pady=30)
        self.production_date_calendar.grid(row=1, column=1, padx=25, pady=30)
        self.production_scan_dir_button.grid(row=2, column=0, padx=50, pady=30)

    def verify_group_name(self, earliest_start_date: datetime.date = None):
        if self.production_group_input.get() == "" or self.production_group_input.get() is None:
            enter_group_name_message = Label(self, text="*Group name is required", fg="red")
            enter_group_name_message.grid(row=0, column=2, padx=10, pady=30)
        else:
            for child in self.winfo_children():
                child.configure(state='disabled')
            self.production_scan_dir_button.configure(text="Loading...")
            self.threaded_production_data_retrieval(earliest_start_date)

    def threaded_production_data_retrieval(self, earliest_start_date: datetime.date = None):
        self.loading_message_thread: threading.Thread = threading.Thread(target=self.execute_loading_message)
        self.get_production_thread = threading.Thread(
            target=lambda: self.threaded_get_production_data(earliest_start_date))
        self.delete_loading_message_thread = threading.Thread(target=self.delete_loading_message)
        self.update_thread = threading.Thread(target=self.threaded_update)
        for thread in [self.loading_message_thread, self.get_production_thread,
                       self.delete_loading_message_thread, self.update_thread]:
            thread.daemon = True
            thread.start()

    def threaded_get_production_data(self, earliest_start_date: datetime.date = None):
        self.loading_message_thread.join()
        logging.info("Loading message thread finished.")
        self.master.collected_patients = CollectedPatients()
        self.master.collected_patients.production_group_name = self.production_group_input.get()
        self.master.collected_patients.set_pillpack_patient_dict(
            get_patient_medicine_data_ppc(self.master.loaded_prns_and_linked_medications, consts.PPC_SEPARATING_TAG,
                                          self.master.config, earliest_start_date=earliest_start_date)
        )
        save_collected_patients(self.master.collected_patients)
        return

    def execute_loading_message(self):
        for trees_results_and_dicts in self.parent.list_of_trees:
            tree: Treeview = trees_results_and_dicts[0]
            key = "loading"
            tree.delete(*tree.get_children())
            tree.insert('', 'end', key, text=key)
            tree.set(key, 'First Name', "Loading...")
            tree.set(key, 'Last Name', "Loading...")
            tree.set(key, 'Date of Birth', "Loading...")
            tree.set(key, 'Start Date', "Loading...")
            tree.set(key, 'No. of Medications', "Loading...")
            tree.set(key, 'Condition', "Loading...")

    def delete_loading_message(self):
        self.get_production_thread.join()
        logging.info("Production data re-population finished.")
        for trees_results_and_dicts in self.parent.list_of_trees:
            tree: Treeview = trees_results_and_dicts[0]
            key = "loading"
            tree.delete(key)
        return

    def threaded_update(self):
        self.delete_loading_message_thread.join()
        logging.info("Loading message removed from tree.")
        self.parent.update()
        self.destroy()