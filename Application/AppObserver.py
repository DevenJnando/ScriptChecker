import logging
from tkinter import Frame


class Observer:
    def __init__(self):
        self.connected_views: dict = {}

    def connect(self, view_name: str, view_to_connect: Frame):
        if not self.connected_views.__contains__(view_name):
            self.connected_views[view_name] = view_to_connect
            logging.info("Connected view: {0} to the application observer.".format(view_name))

    def disconnect(self, view_name: str):
        if self.connected_views.__contains__(view_name):
            self.connected_views.pop(view_name)
            logging.info("Disconnected view: {0} from the application observer.".format(view_name))

    def clear(self):
        self.connected_views.clear()
        logging.info("Cleared all views from application observer.")

    def update(self, key_of_view_to_update):
        if self.connected_views.__contains__(key_of_view_to_update):
            view_object = self.connected_views[key_of_view_to_update]
            update_method = getattr(view_object, "update", None)
            if callable(update_method):
                view_object.update()
                logging.info("The update method in the specified view ({0}) "
                             "was called successfully.".format(view_object))
            else:
                logging.error("The update method in the specified view ({0}) "
                              "could not be called because the update method is not callable."
                              .format(view_object))
        else:
            logging.warning("No view with the key: {0} is currently connected to the application observer."
                            .format(key_of_view_to_update))

    def update_all(self):
        for view_key in self.connected_views.keys():
            self.update(view_key)