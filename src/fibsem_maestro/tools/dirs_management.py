import logging
import os


def make_dirs(dirs):
    """
    :param kwargs: A dictionary containing the directories to be created. The key 'dirs' should have a list of directory paths as its value.
    :return: None

    This method creates directories that do not already exist. It logs the creation of each directory using the logging module.

    Example usage:
        make_dirs(dirs=['/path/to/dir1', '/path/to/dir2'])
    """
    for d in dirs:
        if not os.path.isdir(d):
            logging.info(f"{d} created.")
            os.makedirs(d)