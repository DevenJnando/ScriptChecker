from watchdog.events import FileSystemEventHandler, FileSystemEvent


class WatchdogEventHandler(FileSystemEventHandler):
    def __init__(self, application):
        FileSystemEventHandler.__init__(self)
        self.app = application

    def on_created(self, event: FileSystemEvent) -> None:
        self.app.notify(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self.app.notify(event)
