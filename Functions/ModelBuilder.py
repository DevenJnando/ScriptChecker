import datetime
import logging
from xml.dom import minidom

from Models import PillpackPatient, Medication


def _create_datetime(date_string: str):
    date = datetime.date.today()
    try:
        date = datetime.date.fromisoformat(date_string)
    except ValueError as e:
        logging.error("Datetime could not be obtained from the given string: {0}".format(e))
    finally:
        return date


def get_medication_take_times(time_of_day: str, no_of_meds_to_take: float, medication: Medication):
    match time_of_day:
        case "MORNING":
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.morning_dosage = no_of_meds_to_take
        case "Morning":
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.morning_dosage = no_of_meds_to_take
        case "AFTERNOON":
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.afternoon_dosage = no_of_meds_to_take
        case "Midday":
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.afternoon_dosage = no_of_meds_to_take
        case "EVENING":
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.evening_dosage = no_of_meds_to_take
        case "NIGHT":
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.night_dosage = no_of_meds_to_take
        case "Bedtime":
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.night_dosage = no_of_meds_to_take
        case _:
            get_specified_medication_take_times(time_of_day, no_of_meds_to_take, medication)


def get_specified_medication_take_times(time_of_day: str, no_of_meds_to_take: float, medication: Medication):
    try:
        time_of_day_as_int: int = int(time_of_day.split("H")[0])
        hours = time_of_day_as_int
        mins = time_of_day.split("H")[1]
        if 0 <= time_of_day_as_int < 12:
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.morning_dosage = str(no_of_meds_to_take) + "\n({0}:{1})".format(hours, mins)
        elif 12 <= time_of_day_as_int < 17:
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.afternoon_dosage = str(no_of_meds_to_take) + "\n({0}:{1})".format(hours, mins)
        elif 17 <= time_of_day_as_int < 20:
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.evening_dosage = str(no_of_meds_to_take) + "\n({0}:{1})".format(hours, mins)
        elif 20 <= time_of_day_as_int < 23:
            if no_of_meds_to_take != 0.0:
                if no_of_meds_to_take % 1 == 0:
                    no_of_meds_to_take = int(no_of_meds_to_take)
                medication.night_dosage = str(no_of_meds_to_take) + "\n({0}:{1})".format(hours, mins)
    except ValueError as e:
        logging.error(e)


def generate_medication_dict(medication_element):
    if isinstance(medication_element, minidom.Element):
        # Only requires the first instance of a medicine name tag
        medications = medication_element.getElementsByTagName("MedNm")[0]
        medication_name = medications.firstChild.nodeValue if medications.hasChildNodes() else ""

        # Since pillpack states each individual day that a medicine is to be taken, it is enough to just count the total
        # number of MedItemDose tags and obtain the number of days this way
        list_of_dosages = medication_element.getElementsByTagName("MedItemDose")
        number_of_days_to_take = list_of_dosages.length

        # Only require the first instance of a medication start date
        start_date = list_of_dosages[0].getElementsByTagName("TakeDt")[0]
        start_date_value = start_date.firstChild.nodeValue if start_date.hasChildNodes() else ""
        start_date_final = _create_datetime(start_date_value)

        # DoseList represents each moment in the day a medicine has to be taken; this is represented in the following
        # format: Time_of_day:Dose - if there are multiple times in the day a medicine needs to be taken, then these
        # will be separated by a semicolon, like this: ToD:Dose;AnotherToD:AnotherDose
        dosage_list = list_of_dosages[0].getElementsByTagName("DoseList")[0]
        dosage_list_value = dosage_list.firstChild.nodeValue if dosage_list.hasChildNodes() else ""

        # Because of this, we need to split each dosage entry by semicolons
        trimmed_dosage_list = list(filter(lambda entity: entity != "", dosage_list_value.split(";")))
        final_dosage: float = -1
        try:
            final_dosage = sum([float(e.split(":")[1]) for e in trimmed_dosage_list])
        except ValueError as e:
            logging.error("ValueError: {0}".format(e))
        total_dosage = number_of_days_to_take * final_dosage
        medication_object: Medication = Medication(medication_name, total_dosage, start_date_final)
        for e in trimmed_dosage_list:
            get_medication_take_times(e.split(":")[0], float(e.split(":")[1]), medication_object)
        return medication_object
    else:
        logging.error("The medication parameter: {0} is not a valid XML element.".format(medication_element))
        return


def update_medication_dosage(patient_object: PillpackPatient, medication_object: Medication):
    if patient_object.production_medications_dict.__contains__(medication_object.medication_name):
        medication_to_update: Medication = patient_object.production_medications_dict[medication_object.medication_name]
        medication_to_update.dosage = medication_to_update.dosage + medication_object.dosage
        patient_object.production_medications_dict[medication_object.medication_name] = medication_to_update
        logging.info("Updated medication {0} dosage to {1}"
                     .format(medication_to_update.medication_name, medication_to_update.dosage))


def create_medication_object_from_script(medicine_element: minidom.Element):
    medicine_name_on_script = medicine_element.getAttribute("d")
    medicine_dosage_on_script = medicine_element.getAttribute("q")
    medication: Medication = Medication(medicine_name_on_script, float(medicine_dosage_on_script),
                                        datetime.date.today())
    logging.info("Extracted Medicine information ({0} x{1}) from the script's XML"
                 .format(medicine_name_on_script, medicine_dosage_on_script))
    return medication


def create_patient_object_from_script(script_xml):
    if isinstance(script_xml, minidom.Document) and script_xml.hasChildNodes():
        patient_details = script_xml.getElementsByTagName("pa")[0]
        patient_last_name = patient_details.getAttribute("l")
        patient_first_name = patient_details.getAttribute("f")
        patient_dob = datetime.date.fromisoformat(patient_details.getAttribute("b"))
        surgery = patient_details.getAttribute("n")
        medicines_on_script = script_xml.getElementsByTagName("dd")
        patient_object = PillpackPatient(patient_first_name, patient_last_name, patient_dob, surgery)
        logging.info("Extracted Patient information ({0} {1} {2}) from script's XML"
                     .format(patient_first_name, patient_last_name, patient_dob))
        for medicine in medicines_on_script:
            medication_object: Medication = create_medication_object_from_script(medicine)
            patient_object.add_medication_to_production_dict(medication_object)
        return patient_object
    else:
        return None


def create_patient_object_from_pillpack_data(order_element):
    if isinstance(order_element, minidom.Element):
        patient_name_element = order_element.getElementsByTagName("PtntNm")[0]
        patient_dob_element = order_element.getElementsByTagName("Birthday")[0]
        patient_full_name: list = patient_name_element.firstChild.nodeValue.split(
            ",") if patient_name_element.hasChildNodes() else []
        patient_first_name: str = patient_full_name[1].strip() if len(patient_full_name) > 0 else ""
        patient_last_name: str = patient_full_name[0].strip() if len(patient_full_name) > 0 else ""
        patient_dob_string: str = patient_dob_element.firstChild.nodeValue if patient_dob_element.hasChildNodes() else ""

        # There are no separators for day, month and year in the pillpack XML file, so these need to be added in
        # manually
        patient_dob_string = patient_dob_string[:4] + "-" + patient_dob_string[4:] if patient_dob_string != "" else ""
        patient_dob_string = patient_dob_string[:7] + "-" + patient_dob_string[7:] if patient_dob_string != "" else ""
        patient_dob = _create_datetime(patient_dob_string)

        patient_object = PillpackPatient(patient_first_name, patient_last_name, patient_dob)
        medication_items: list = order_element.getElementsByTagName("MedItem")
        start_date_list: list = []
        for medication in medication_items:
            medication_object = generate_medication_dict(medication)
            start_date_list.append(medication_object.start_date)
            if isinstance(medication_object, Medication):
                update_medication_dosage(patient_object, medication_object)
                patient_object.add_medication_to_production_dict(medication_object)

        # Sets the start date for the patient's medication cycle as the earliest date relative to now.
        patient_object.set_start_date(min(start_date_list))
        return patient_object
    else:
        logging.error("The order parameter: {0} is not a valid XML element. Actual type is {1}"
                      .format(order_element, type(order_element)))
        return None
