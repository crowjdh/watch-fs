import sys
import shutil
import time
import logging
import traceback

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


LOG_FILE = './fs.log'


class Watcher:

  def __init__(self, directory_to_watch, frequency_in_sec):
    self.observer = Observer()
    self.directory_to_watch = directory_to_watch
    self.frequency_in_sec = frequency_in_sec

  def run(self):
    event_handler = Handler()
    logger = get_logger()

    self.observer.schedule(event_handler, self.directory_to_watch, recursive=False)
    self.observer.start()

    try:
      while True:
        time.sleep(self.frequency_in_sec)
    except KeyboardInterrupt:
      logger.info("Received keyboard interrupt. Halting...")
    except:
      logger.error(traceback.format_exc())
    finally:
      self.observer.stop()

    self.observer.join()


class Handler(FileSystemEventHandler):

  @staticmethod
  def on_any_event(event):
    if event.is_directory:
      return None

    logger = get_logger()

    remaining_disk_space_gb = get_remaining_disk_space() // (1024 ** 3)
    message = f"\n- Event: {event.event_type}\n- Target: {event.src_path}\n- Avail: {remaining_disk_space_gb}"
    logger.info(message)

    global storage_limit
    if remaining_disk_space_gb < storage_limit:
      logger.warning("Not enough storage. Performing clean up...")
      # TODO: Clean up old files
      # 1. List all videos under target directory
      # 2. Gather files to remove to conform storage limit
      # 3. Remove


def get_logger():
  logging.basicConfig(filename=LOG_FILE,
                      format='%(asctime)s %(message)s',
                      filemode='a')

  logger = logging.getLogger()
  logger.setLevel(logging.INFO)

  return logger


def parse_args():
  if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} PATH LIMIT")
    exit()

  [_, path, storage_limit] = sys.argv
  return { "path": path, "storage_limit": storage_limit }


def get_remaining_disk_space():
  usage = shutil.disk_usage('/')

  return usage.free


def main():
  args = parse_args()

  global storage_limit
  storage_limit = int(args['storage_limit'])

  w = Watcher(args['path'], 3)
  w.run()


if __name__ == '__main__':
  main()
