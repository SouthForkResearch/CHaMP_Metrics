# Philip Bailey
# 2 October 2019
# Measurements were originally downloaded from API into a separate folder structure than the
# rest of the files. This temporary, one-time script moves them into the same folder as the
# rest of the CHaMP files.
import os
import sys, traceback
import argparse
import sqlite3
from lib.loghelper import Logger
from datetime import datetime


def move_measurements(old_folder, new_folder):

    log = Logger('Move Measurements')
    log.setup(logPath=os.path.join(new_folder, datetime.now().strftime("%Y%m%d-%H%M%S") + 'move_measurements.log'))

    # Create a List
    measurements = list()
    # Iterate over the directory tree and check if directory is empty.
    for (dirpath, dirnames, filenames) in os.walk(old_folder):
        for file in filenames:
            measurements.append(os.path.join(dirpath, file))

    log.info('{} measurement files to move'.format(len(measurements)))

    for meas in measurements:
        new_path = os.path.join(os.path.dirname(meas.replace(old_folder, new_folder)), 'AuxMeasurements', os.path.basename(meas))

        if not os.path.isdir(os.path.dirname(new_path)):
            os.makedirs(os.path.dirname(new_path))

        os.rename(meas, new_path)
        log.info('Moving {} to {}'.format(meas, new_path))

    # Create a List
    listOfEmptyDirs = list()
    # Iterate over the directory tree and check if directory is empty.
    for (dirpath, dirnames, filenames) in os.walk(old_folder):
        if len(dirnames) == 0 and len(filenames) == 0:
            listOfEmptyDirs.append(dirpath)

    print(len(listOfEmptyDirs), 'empty folders')
    for empty in listOfEmptyDirs:
        os.rmdir(empty)

    log.info('Process Complete')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='Folder where measurement files exist', type=str)
    parser.add_argument('destination', help='Folder where the measurement files should be placed.', type=str)
    args = parser.parse_args()

    try:
        move_measurements(args.source, args.destination)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    main()
