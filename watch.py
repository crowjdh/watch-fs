import os
import sys
from datetime import datetime
from pathlib import Path
import shutil
import time
import logging
import traceback

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
    message = f"\n- Event: {event.event_type}\n- Target: {event.src_path}\n- Limit | Avail | Remaining: {storage_limit // MEGABYTE} mb | {remaining_disk_space // MEGABYTE} mb | {(remaining_disk_space - storage_limit) // MEGABYTE} mb"
    logger.info(message)

    if remaining_disk_space < storage_limit:
      size_to_cleanup = storage_limit - remaining_disk_space
      logger.warning(f"Not enough storage. Claiming {size_to_cleanup // MEGABYTE} mb to guarantee {storage_limit // GIGABYTE} gb of storage...")
      cleanup_old_files(directory_to_watch, size_to_cleanup)


def cleanup_old_files(target, size_to_cleanup):
  paths = sorted(Path(target).rglob('*'), key=os.path.getmtime)

  collected_file_size = 0
  paths_to_remove = []
  logger = get_logger()

  for path in paths:
    size = int(path.stat().st_size)
    if os.path.isdir(path):
      continue

    collected_file_size += size

    logger.warning(f"\n- Collected: {path}({size // MEGABYTE} mb)\n- Remaining: {(size_to_cleanup - collected_file_size) // MEGABYTE} mb")
    paths_to_remove.append(path)

    if collected_file_size > size_to_cleanup:
      break

  for path in paths_to_remove:
    size_mb = path.stat().st_size // MEGABYTE
    logger.warning(f"Removing {path}({size_mb} mb)")

    global is_dry
    if is_dry:
      continue

    os.remove(path)


def get_logger():
  date_str = datetime.today().strftime('%Y-%m-%d')
  log_file_name = f'./{date_str}.log'

  logging.basicConfig(filename=log_file_name,
                      format='%(asctime)s %(message)s',
                      filemode='a')

  logger = logging.getLogger()
  logger.setLevel(logging.INFO)

  return logger


def parse_args():
  if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} PATH LIMIT [test]")
    exit()

  args = list(sys.argv)
  if len(args) < 4:
    args += [False]
  else:
    args[3] = True

  [_, path, storage_limit, is_dry] = args
  return { "path": path, "storage_limit": storage_limit, "is_dry": is_dry }


def get_remaining_disk_space(target='/'):
  usage = shutil.disk_usage(target)

  return usage.free


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
