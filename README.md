Script Checker
==============

Script Checker is an assistant tool designed for pharmacies.
Its primary use-case is for pharmacies which produce pillpack
medication packages for their patients. 

Script checker reads the downloaded
production data from the specified download folder, and passes it into
memory. Then, it awaits for the user to scan in scripts issued from the GP.


The script is automatically matched to the appropriate patient, so admin
work for the user is minimised.

Matched, missing, unknown, and inconsistent dosages for each scanned
medication are displayed clearly to the user. 

Since some edge-cases may exist where the exact medication cannot be
matched on the script (e.g. Patient has Venlafaxine 225mg on script,
but is receiving Venlafaxine 75mg + Venlafaxine 150mg in pillpack), there
is an option for manual override - however, it is strongly recommended to
only use this when absolutely necessary.

Entire production data sets can be scanned and entered into script checker,
however ammendments to a patient's medications will be automatically updated
upon download, which allows for modifications on the fly without the headache
of re-scanning the folder where pillpack production data is stored.

Future use-cases
================

- Script checking for Tray/Skillet patients
- Kardex generation for all production medications
- Cyclical PRN sheets for all medications outside of production
- Data analytics on scanned scripts, changed medications, PRNs, manual checks, etc.

Launching Script Checker
============
The latest release is available in the 'Releases' section of this repo.
Download the zip, extract, and navigate to the 'ScriptScanner.exe' file
located in the 'ScriptScanner.dist' folder. 
The application should then start.