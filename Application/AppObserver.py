import logging
from tkinter import Frame


class Observer:
    """
    The application observer class. This observer acts as a "history" bookkeeper and allows a user to navigate
    forwards and backwards between views they have previously viewed. The observer also allows views which are not
    currently being accessed by the user to be updated seamlessly.

    This includes data related to the view itself, and any data contained within objects which are a part of the
    view(s).
    """
    def __init__(self):
        """
        Constructor to instantiate the dictionary which will contain all views connected to the application observer.

        """
        self.connected_views: dict = {}

    def connect(self, view_name: str, view_to_connect: Frame):
        """
        Function which connects an arbitrary view to the dictionary of all views within the observer's scope.

        :param view_name: The name of the view to be connected - this will act as the key in the dictionary
        :param view_to_connect: The Frame object of the view to be connected - this will be the value in the dictionary.
        :return: None
        """
        if not self.connected_views.__contains__(view_name):
            self.connected_views[view_name] = view_to_connect
            logging.info("Connected view: {0} to the application observer.".format(view_name))

    def disconnect(self, view_name: str):
        """
        Function which disconnects an aribtary view from the dictionary of all views within the observer's scope.

        :param view_name: The name of the view to be disconnected - will be a key in the dictionary if it exists.
        :return: None
        """
        if self.connected_views.__contains__(view_name):
            self.connected_views.pop(view_name)
            logging.info("Disconnected view: {0} from the application observer.".format(view_name))

    def clear(self):
        """
        Function which removes all connected views from the Observer's scope.

        :return: None
        """
        self.connected_views.clear()
        logging.info("Cleared all views from application observer.")

    def update(self, key_of_view_to_update):
        """
        Function which calls the update function of a specified view within the scope of the Observer object (if such
        an update function exists and is callable).

        :param key_of_view_to_update: The key of the specified view to be updated.
        :return: None
        """
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
        """
        Function which calls the update function of every view within the scope of the Observer.

        :return: None
        """
        for view_key in self.connected_views.keys():
            self.update(view_key)
