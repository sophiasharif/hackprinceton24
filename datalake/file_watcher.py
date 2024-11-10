# file_watcher.py

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from update_data_frame import update_data_frame
from add_metadata import add_metadata

class NewImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New image detected: {event.src_path}")
            update_data_frame()
            add_metadata()

if __name__ == "__main__":
    path = "../images"
    event_handler = NewImageHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
