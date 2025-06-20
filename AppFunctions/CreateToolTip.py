import Application.ToolTip

"""

This module creates and destroys a Tooltip object when requested by the user

"""


def create_tool_tip(widget, text):
    """
    Constructor for the Tooltip object

    :param widget: Object for the Tooltip to be bound to
    :param text: The displayed text when the Tooltip is accessed
    :return: None
    """
    tool_tip = Application.ToolTip.ToolTip(widget)

    def enter(event):
        """
        Event function triggered when the Tooltip widget is interacted with.
        Causes the Tooltip text to be displayed to the user inside the Tooltip's widget

        :param event: The trigger to call this function
        :return: None
        """
        tool_tip.showtip(text)

    def leave(event):
        """
        Event function triggered when the Tooltip widget is no longer being interacted with.
        Causes the Tooltip text to stop being displayed to the user inside the Tooltip's widget

        :param event: The trigger to call this function
        :return: None
        """
        tool_tip.hidetip()

    """
    Binds the enter and leave functions to the Tooltip's widget
    """
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)
