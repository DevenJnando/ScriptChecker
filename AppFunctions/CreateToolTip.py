import Application.ToolTip


def create_tool_tip(widget, text):
    tool_tip = Application.ToolTip.ToolTip(widget)

    def enter(event):
        tool_tip.showtip(text)

    def leave(event):
        tool_tip.hidetip()

    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)
