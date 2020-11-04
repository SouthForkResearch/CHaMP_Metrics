# Philip Bailey
# 2 October 2019
# loops over all files listed in the CHaMP Workbench and reports whether they exist on the local system
import os
import sys, traceback
import argparse
import sqlite3
from lib.sitkaAPI import APIGet, NamedTemporaryFile
from lib import env
from lib.loghelper import Logger
from datetime import datetime

def champ_topo_checker(workbench, folder):

    log = Logger('Topo Checker')
    log.setup(logPath=os.path.join(folder, datetime.now().strftime("%Y%m%d-%H%M%S") + '_topo_checker.log'))

    dbCon = sqlite3.connect(workbench)
    dbCurs = dbCon.cursor()
    dbCurs.execute('SELECT WatershedName, VisitYear, SiteName, VisitID' +
        ' FROM vwVisits WHERE ProgramID = 1 AND ProtocolID IN (2030, 416, 806, 1966, 2020, 1955, 1880, 10036, 9999)')
    
    file_exists = 0
    file_zero = 0
    file_download = []
    file_errors = []

    for row in dbCurs.fetchall():
        watershed = row[0]
        visit_year = row[1]
        site = row[2]
        visitID = row[3]

        topo_path = os.path.join(folder, str(visit_year), watershed.replace(' ', ''), site, 'VISIT_{}'.format(visitID), 'Field Folders', 'Topo', 'TopoData.zip')

        download_needed = False
        if os.path.isfile(topo_path):
            file_exists += 1

            if os.stat(topo_path).st_size == 0:
                file_zero += 0
                download_needed = True
        else:
            download_needed = True

        if not download_needed:
            continue

        file_download.append(topo_path)

        try:
            topoFieldFolders = APIGet('visits/{}/fieldFolders/Topo'.format(visitID))
            file = next(file for file in topoFieldFolders['files'] if file['componentTypeID'] == 181)
            downloadUrl = file['downloadUrl']
        except Exception, e:
            log.warning('No topo data for visit information {}: {}'.format(visitID, topo_path))
            continue

        # Download the file to a temporary location
        if not os.path.isdir(os.path.dirname(topo_path)):
            os.makedirs(os.path.dirname(topo_path))

        with open(topo_path, 'w+b') as f:
            response = APIGet(downloadUrl, absolute=True)
            f.write(response.content)
            log.info(topo_path)

        log.info('Downloaded {}'.format(topo_path))

    log.info('Existing files: {}'.format(file_exists))
    log.info('Zero byte files: {}'.format(file_zero))
    log.info('Download files: {}'.format(len(file_download)))

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
    