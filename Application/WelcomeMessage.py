from tkinter import Toplevel, Label, Button


class NoPillpackFolderLocationSetWarning(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("400x200")
        self.attributes('-topmost', 'true')
        self.parent = parent
        self.warning_label = Label(self, text="It looks like this is your first time using Script Checker!"
                                              " Please select where your pillpack production files are located"
                                              " by clicking 'Select pillpack directory' and navigating to the "
                                              " correct folder.",
                                   wraplength=300)
        self.ok_button = Button(self, text="OK", command=self.destroy)
        self.warning_label.grid(row=0, column=0, pady=25, sticky="ew", columnspan=2)
        self.ok_button.grid(row=1, column=0, padx=50, sticky="ew")
