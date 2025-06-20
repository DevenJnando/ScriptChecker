from tkinter import StringVar, Menu
from tkinter.ttk import Treeview

from Application import App


"""

This module provides common functions to be used by Treeview instances.
These functions allow a Treeview to be sorted, fields within the Treeview to be searched for, the width of the 
Treeview to be calibrated, and complex objects represented within the Treeview to be retrieved and viewed.

"""


def search_treeview(tree_to_search: Treeview, detached_items: list, search_query: StringVar):
    """
    Search for a specified string within a Treeview object.
    Each node which does not contain the specified string is detached and only matching values remain visible.
    Once the search has been completed and the search term is removed, the detached nodes are reattached to the
    Treeview object.

    :param tree_to_search: The Treeview object to search
    :param detached_items: A list object of all detached nodes within the tree
    :param search_query:
    :return: None
    """
    search_string: str = search_query.get()
    for node in detached_items:
        if tree_to_search.exists(node):
            tree_to_search.reattach(node, '', 0)

    if len(search_string) > 0:
        for node in tree_to_search.get_children():
            match: bool = False
            for value in tree_to_search.item(node)['values']:
                if search_string.lower() in str(value).lower():
                    match = True
                    break
            if match:
                tree_to_search.reattach(node, '', 0)
            else:
                detached_items.append(node)
                tree_to_search.detach(node)
    sort_treeview(tree_to_search, "Last Name", False)


def sort_treeview(tree_to_sort: Treeview, column: str, is_descending: bool):
    """
    Function which sorts a specified column within a Treeview object. The option to display the sort in ascending
    and descending order is also available

    :param tree_to_sort: The Treeview object to sort
    :param column: The Treeview column to be sorted
    :param is_descending: Flag to reverse the sort order
    :return: None
    """
    data = [(tree_to_sort.set(item, column), item) for item in tree_to_sort.get_children('')]
    data.sort(reverse=is_descending)
    for index, (val, item) in enumerate(data):
        tree_to_sort.move(item, '', index)


def popup_menu(event, tree_to_highlight: Treeview, menu: Menu):
    """
    Checks that a selected area is a valid Treeview row, and calls a Menu object's popup function if it is a
    valid row.

    :param event: The trigger for this function (a right click, for example)
    :param tree_to_highlight: The tree to check for the selected row
    :param menu: The Menu object to popup if the selected area contains a valid row
    :return: None
    """
    try:
        iid = tree_to_highlight.identify_row(event.y)
        if iid:
            tree_to_highlight.selection_set(iid)
            tree_to_highlight.focus(tree_to_highlight.selection()[0])
        menu.tk_popup(event.x_root, event.y_root, 0)
    finally:
        menu.grab_release()


def retrieve_patient_from_tree(tree: Treeview, application: App):
    """
    Called when a row is double-clicked, or otherwise selected by the user, this function is called. The function
    checks if the selected row's first two columns contain a PillpackPatient object's first and last name.
    If it does, that PillpackPatient object is retrieved from the App base class and returned.

    :param tree: The Treeview object to traverse
    :param application: The App base class which contains all loaded objects and repos.
    :return: The retrieved PillpackPatient object, or None if no valid PillpackPatient can be found
    """
    item = tree.focus()
    column_values = tree.item(item).get("values")
    if len(column_values) > 0:
        first_name = column_values[0]
        last_name = column_values[1]
        patient_list = application.collected_patients.pillpack_patient_dict.get(last_name.lower())
        if isinstance(patient_list, list):
            filtered_patients = (list
                                 (filter
                                  (lambda patient: patient.first_name.lower() == first_name.lower(),
                                   patient_list)
                                  )
                                 )
            return filtered_patients[0]
        else:
            return None
    else:
        return None


def calibrate_width(tree_to_calibrate: Treeview, columns: tuple, width):
    """
    Function which sets a column(s) in a Treeview to a specified width.

    :param tree_to_calibrate: Treeview object to apply the changes to
    :param columns: Tuple containing the columns in the Treeview
    :param width: The desired new width value which the columns should have
    :return: None
    """
    for column in columns:
        tree_to_calibrate.column(column, width=width)
