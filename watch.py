import os
import sys
from datetime import datetime
from pathlib2 import Path
import shutil
import time
import logging
import traceback
import psutil

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


MEGABYTE = 1024 ** 2
GIGABYTE = 1024 ** 3


class Watcher:

  def __init__(self, frequency_in_sec):
    self.observer = Observer()
    self.frequency_in_sec = frequency_in_sec

  def run(self):
    event_handler = Handler()
    logger = get_logger()

    global directory_to_watch
    self.observer.schedule(event_handler, directory_to_watch, recursive=True)
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

    global directory_to_watch
    global storage_limit

    remaining_disk_space = get_remaining_disk_space(directory_to_watch)
    message = "\n- Event: {}\n- Target: {}\n- Limit | Avail | Remaining: {} mb | {} mb | {} mb".format(event.event_type, event.src_path, storage_limit // MEGABYTE, remaining_disk_space // MEGABYTE, (remaining_disk_space - storage_limit) // MEGABYTE)
    logger.info(message)

    if remaining_disk_space < storage_limit:
      size_to_cleanup = storage_limit - remaining_disk_space
      logger.warning("Not enough storage. Claiming {} mb to guarantee {} gb of storage...".format(size_to_cleanup // MEGABYTE, storage_limit // GIGABYTE))
      cleanup_old_files(directory_to_watch, size_to_cleanup)


def cleanup_old_files(target, size_to_cleanup):
  paths = Path(target).rglob('*')
  paths = sorted(paths, key=lambda path: os.path.getmtime(str(path)))
  paths = filter(lambda path: not path.is_dir(), paths);

  collected_file_size = 0
  paths_to_remove = []
  logger = get_logger()

  for path in paths:
    size = int(path.stat().st_size)
    collected_file_size += size

    logger.warning("\n- Collected: {}({} mb)\n- Remaining: {} mb".format(path, size // MEGABYTE, (size_to_cleanup - collected_file_size) // MEGABYTE))
    paths_to_remove.append(path)

    if collected_file_size > size_to_cleanup:
      break;

  for path in paths_to_remove:
    size_mb = path.stat().st_size // MEGABYTE
    logger.warning("Removing {}({} mb)".format(path, size_mb))

    global is_dry
    if is_dry:
      continue

    os.remove(str(path))


def get_logger():
  date_str = datetime.today().strftime('%Y-%m-%d')
  log_file_name = './{}.log'.format(date_str)

  logging.basicConfig(filename=log_file_name,
                      format='%(asctime)s %(message)s',
                      filemode='a')

  logger = logging.getLogger('watch-fs')
  logger.setLevel(logging.INFO)

  return logger


def parse_args():
  if len(sys.argv) < 3:
    print("Usage: {} PATH LIMIT [test]".format(sys.argv[0]))
    exit()

  args = list(sys.argv)
  if len(args) < 4:
    args += [False]
  else:
    args[3] = True

  [_, path, storage_limit, is_dry] = args
  return { "path": path, "storage_limit": storage_limit, "is_dry": is_dry }


def get_remaining_disk_space(target='/'):
  disk_usage = psutil.disk_usage(target)

  return disk_usage.free


def main():
  args = parse_args()

  global directory_to_watch
  directory_to_watch = args['path']
  global is_dry
  is_dry = args['is_dry']

  global storage_limit
  storage_limit = int(args['storage_limit']) * GIGABYTE

  w = Watcher(3)
  w.run()


if __name__ == '__main__':
  main()
