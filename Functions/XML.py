import logging
import re
import sys
import xml
from xml.dom import minidom

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)


def remove_whitespace(node):
    if node.nodeType == minidom.Node.TEXT_NODE:
        if node.nodeValue.strip() == "":
            node.nodeValue = ""
    for child in node.childNodes:
        remove_whitespace(child)


def parse_xml(list_of_orders_raw_text: list):
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
            sanitised_xml_text += character
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
