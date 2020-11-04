# Philip Bailey
# 2 October 2019
# Walk the CHaMP folder structure looking for empty folders, files of zero bytes and
# duplicate site folders that only differ because of spaces
import os
import sys, traceback
import argparse
import sqlite3
from lib.loghelper import Logger
from datetime import datetime


def champ_topo_checker(workbench, folder):

    log = Logger('CHaMP Files')
    log.setup(logPath=os.path.join(folder, datetime.now().strftime("%Y%m%d-%H%M%S") + '_champ_folder_check.log'))

    # # Loop over site names organized by field season and watershed
    # dbCon = sqlite3.connect(workbench)
    # dbCurs = dbCon.cursor()
    # dbCurs.execute('SELECT WatershedName, VisitYear, SiteName' +
    #     ' FROM vwVisits WHERE ProgramID = 1 AND ProtocolID IN (2030, 416, 806, 1966, 2020, 1955, 1880, 10036, 9999)' +
    #     ' GROUP BY WatershedName, VisitYear, SiteName' +
    #     ' ORDER BY VisitYear, WatershedName, SiteName')
    #
    # for row in dbCurs.fetchall():
    #
    #     watershed = row[0]
    #     visit_year = row[1]
    #     site = row[2]
    #     # visitID = row[3]
    #
    #     visit_path1 = os.path.join(folder, str(visit_year), watershed.replace(' ', ''), site)
    #     visit_path2 = visit_path1.replace(' ', '')
    #     if ' ' in site and os.path.isdir(visit_path1) and os.path.isdir(visit_path2):
    #         try:
    #             process_duplicate_folder(visit_path1, visit_path2)
    #         except Exception as e:
    #             log.error('Error processing {}'.format(visit_path1))

    # Create a List
    listOfEmptyDirs = list()
    # Iterate over the directory tree and check if directory is empty.
    for (dirpath, dirnames, filenames) in os.walk(folder):
        if len(dirnames) == 0 and len(filenames) == 0:
            listOfEmptyDirs.append(dirpath)

    print(len(listOfEmptyDirs), 'empty folders')
    for empty in listOfEmptyDirs:
        os.rmdir(empty)

    log.info('Process Complete')


def process_duplicate_folder(with_spaces, no_spaces):

    log = Logger('Duplicate')

    movers = []
    for root, dirs, files in os.walk(with_spaces):
        for name in files:
            old_path = os.path.join(root, name)
            new_path = old_path.replace(with_spaces, no_spaces)

            # Simply delete the file if it is zero bytes
            if os.stat(old_path).st_size == 0:
                log.info('Deleting zero byte file {}'.format(old_path))
                os.remove(old_path)
                continue

            if not os.path.isdir(os.path.dirname(new_path)):
                os.makedirs(os.path.dirname(new_path))

            if os.path.isfile(new_path):
                os.remove(old_path)
            else:
                print('Moving file {}'.format(old_path))
                os.rename(old_path, new_path)

        # for name in dirs:
            # print(os.path.join(root, name))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('workbench', help='CHaMP Workbench database', type=argparse.FileType('r'))
    parser.add_argument('folder', help='Top level folder where API files exist.', type=str)
    args = parser.parse_args()

    try:
        champ_topo_checker(args.workbench.name, args.folder)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    main()
