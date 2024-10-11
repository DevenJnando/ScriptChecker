import logging
import re
import xml
from xml.dom import minidom
from html import unescape
from Models import PillpackPatient, Medication
from pylibdmtx.pylibdmtx import encode
from PIL import Image


def remove_whitespace(node):
    if node.nodeType == minidom.Node.TEXT_NODE:
        if node.nodeValue.strip() == "":
            node.nodeValue = ""
    for child in node.childNodes:
        remove_whitespace(child)


def parse_xml_ppc(list_of_orders_raw_text: list):
    order_information: list = []
    if list_of_orders_raw_text is not None:
        for order_raw_text in list_of_orders_raw_text:
            try:
                document = minidom.parseString(order_raw_text)
                remove_whitespace(document)
                document.normalize()
                order_information.append(document.getElementsByTagName("OrderInfo"))
                logging.info("Parsed order from XML file")
            except xml.parsers.expat.ExpatError as e:
                logging.error("Could not parse order from XML file: {0}".format(e))
            except TypeError as e:
                logging.error("Could not parse order from XML file: {0}".format(e))
    return order_information


def parse_xml_fd(xml_raw_text):
    order_information: list = []
    try:
        document = minidom.parseString(xml_raw_text)
        remove_whitespace(document)
        document.normalize()
        order_information.append(document.getElementsByTagName("OrderInfo"))
        logging.info("Parsed order from XML file")
    except xml.parsers.expat.ExpatError as e:
        logging.error("Could not parse order from XML file: {0}".format(e))
    except TypeError as e:
        logging.error("Could not parse order from XML file: {0}".format(e))
    return order_information


def sanitise_and_encode_text_from_file(filename: str, separating_tag: str, config):
    if config is not None:
        raw_file = None
        list_of_strings = None
        try:
            raw_file = open(config["pillpackDataLocation"] + "\\" + filename, "rb")
            raw_binary = raw_file.read()
            raw_text = str(raw_binary)

            # This is a really horrible hack...wraps the xml in tags
            trimmed_text = "<" + raw_text.split("<", 1)[1].rsplit(">\\n", 1)[0] + ">"

            # Makes the content within the OrderInfo tags a bit more readable.
            sanitised_text = re.sub("</" + separating_tag + ">.*?<" + separating_tag + ">",
                                    "</" + separating_tag + ">\n<" + separating_tag + ">",
                                    trimmed_text,
                                    flags=re.DOTALL)

            # For some reason, pillpack adds a bunch of garbage text before the start of the XML tag.
            # This line removes all that crap so the XML can be interpreted correctly.
            sanitised_text = re.sub(r'^.*?<\?xml', "<?xml", sanitised_text)
            encoded_text = sanitised_text.encode('utf8').decode('unicode-escape')

            # Splits each OrderInfo tag and sets each of them as an element in a list.
            list_of_strings = encoded_text.split("</" + separating_tag + ">")
            for i in range(0, len(list_of_strings)):
                string = list_of_strings[i]
                if len(string) > 0:

                    # Utterly awful, primitive way of adding the xml version + encoding if it doesn't exist in the
                    # pillpack production file for some reason
                    if '<?xml version="1.0" encoding="utf-8"?>' not in string:
                        string = '<?xml version="1.0" encoding="utf-8"?>' + string

                    # Ditto for the OrderInfo closing tags
                    if '</' + separating_tag + '>' not in string:
                        string = string + '</' + separating_tag + '>'
                    if '<' + separating_tag + '>' in string:
                        list_of_strings[i] = string
                    else:
                        list_of_strings.pop(i)
                else:
                    list_of_strings.pop(i)
        except FileNotFoundError as e:
            logging.error("File not found: {0}".format(e))
        finally:
            try:
                raw_file.close()
            except AttributeError as e:
                logging.error("Attribute Error: {0}".format(e))
        return list_of_strings


def scan_script(raw_xml_text: str):
    try:
        sanitised_xml_text = ""
        for character in raw_xml_text:
            match character:
                case '"':
                    character = '@'
                case '@':
                    character = '"'
                case '£':
                    character = '#'
                case '#':
                    character = '£'
                case '¬':
                    character = '~'
            sanitised_xml_text += character
        sanitised_xml_text = unescape(sanitised_xml_text)
        sanitised_xml_text = sanitised_xml_text.replace("&", "and")
        sanitised_xml_text = sanitised_xml_text.encode("iso-8859-1")
        document = minidom.parseString(sanitised_xml_text)
        logging.info("Successfully scanned and encoded XML from script.")
        return document
    except xml.parsers.expat.ExpatError as e:
        logging.error("Failed to read XML from script; an expat error has occurred: {0}".format(e))
        return
    except TypeError as e:
        logging.error("Failed to read XML from script; a type error has occurred: {0}".format(e))
        return


def generate_patient_script_template(patient: PillpackPatient):
    script_template = ('<xml>'
                       '<sc id="{0}" ft="{1}" t="{2}"/>'
                       '<pa h="{3}" s="{4}" f="{5}" m="{6}" l="{7}" x="{8}" '
                       'a="{9}" pc="{10}" b="{11}"/>'
                       '<pb i="{12}" d="{13}" n="{14}" pi="{15}" a="{16}" pc="{17}"/>'
                       .format(patient.script_id,
                               patient.script_issuer,
                               patient.script_date,
                               patient.healthcare_no,
                               patient.title,
                               patient.first_name,
                               patient.middle_name,
                               patient.last_name,
                               patient.script_no,
                               patient.address,
                               patient.postcode,
                               str(patient.date_of_birth),
                               patient.doctor_id_no,
                               patient.doctor_name,
                               patient.surgery,
                               patient.surgery_id_no,
                               patient.surgery_address,
                               patient.surgery_postcode)
                       )
    return script_template


def encode_prns_to_xml(patient: PillpackPatient):
    list_of_datamatrices: list = []
    script_template = generate_patient_script_template(patient)
    list_of_drugs_in_xml: list = []
    for medication in patient.prns_for_current_cycle:
        if isinstance(medication, Medication):
            list_of_drugs_in_xml.append(encode_medication_to_xml(medication))
    for drug in list_of_drugs_in_xml:
        script_template += drug
        script_template += "</xml>"
        byte_count = bytearray(script_template, "utf8")
        if len(byte_count) > 1555:
            script_template = script_template.replace(drug, "")
            list_of_datamatrices.append(script_template)
            script_template = generate_patient_script_template(patient) + drug
        else:
            script_template = script_template.replace("</xml>", "")
    script_template += "</xml>"
    list_of_datamatrices.append(script_template)
    return list_of_datamatrices


def encode_matched_medications_to_xml(patient: PillpackPatient):
    list_of_datamatrices: list = []
    script_template = generate_patient_script_template(patient)
    list_of_drugs_in_xml: list = []
    dict_values_as_list: list = list(patient.matched_medications_dict.values())
    for i in range(0, len(dict_values_as_list)):
        medication = dict_values_as_list[i]
        if isinstance(medication, Medication):
            list_of_drugs_in_xml.append(encode_medication_to_xml(medication))
    for drug in list_of_drugs_in_xml:
        script_template += drug
        script_template += "</xml>"
        byte_count = bytearray(script_template, "utf8")
        if len(byte_count) > 1555:
            script_template = script_template.replace(drug, "")
            list_of_datamatrices.append(script_template)
            script_template = generate_patient_script_template(patient) + drug
        else:
            script_template = script_template.replace("</xml>", "")
    script_template += "</xml>"
    list_of_datamatrices.append(script_template)
    return list_of_datamatrices


def encode_to_datamatrix(data_to_encode: str):
    encoded_datamatrix = encode(data_to_encode.encode("utf8"))
    img = Image.frombytes('RGB', (encoded_datamatrix.width, encoded_datamatrix.height), encoded_datamatrix.pixels)
    return img


def encode_medication_to_xml(med_to_encode: Medication):
    encoded_medication: str = ""
    medication_xml = '<dd d="{0}" do="{1}" c="{2}" q="{3}" dm="{4}" sq="{5}" u="{6}"/>'.format(
        med_to_encode.medication_name,
        med_to_encode.doctors_orders,
        med_to_encode.code,
        int(med_to_encode.dosage),
        med_to_encode.disp_code,
        med_to_encode.dosage,
        med_to_encode.med_type
    )
    for character in medication_xml:
        match character:
            case '£':
                character = '#'
            case '#':
                character = '£'
            case '~':
                character = '¬'
        encoded_medication += character
    return encoded_medication
