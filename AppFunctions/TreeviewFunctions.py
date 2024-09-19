from tkinter import StringVar, Menu
from tkinter.ttk import Treeview

from App import App


def search_treeview(tree_to_search: Treeview, detached_items: list, search_query: StringVar):
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
    data = [(tree_to_sort.set(item, column), item) for item in tree_to_sort.get_children('')]
    data.sort(reverse=is_descending)
    for index, (val, item) in enumerate(data):
        tree_to_sort.move(item, '', index)


def popup_menu(event, tree_to_highlight: Treeview, menu: Menu):
    try:
        iid = tree_to_highlight.identify_row(event.y)
        if iid:
            tree_to_highlight.selection_set(iid)
            tree_to_highlight.focus(tree_to_highlight.selection()[0])
        menu.tk_popup(event.x_root, event.y_root, 0)
    finally:
        menu.grab_release()


def retrieve_patient_from_tree(tree: Treeview, application: App):
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
    for column in columns:
        tree_to_calibrate.column(column, width=width)
