# Philip Bailey
# 2 October 2019
# loops over all files listed in the CHaMP Workbench and reports whether they exist on the local system
import os
import sys, traceback
import argparse
import sqlite3
import json
from lib.sitkaAPI import APIGet
from lib import env
from lib.loghelper import Logger
from datetime import datetime


def champ_topo_checker(workbench, folder):
    log = Logger('CHaMP Files')
    log.setup(logPath=os.path.join(folder, datetime.now().strftime("%Y%m%d-%H%M%S") + '_champ_files.log'))

    dbCon = sqlite3.connect(workbench)
    dbCurs = dbCon.cursor()
    dbCurs.execute('SELECT WatershedName, VisitYear, SiteName, VisitID' +
                   ' FROM vwVisits WHERE ProgramID = 1 AND  ProtocolID IN (2030, 416, 806, 1966, 2020, 1955, 1880, 10036, 9999)' +
                   ' ORDER BY VisitYear, WatershedName')

    for row in dbCurs.fetchall():
        watershed = row[0]
        visit_year = row[1]
        site = row[2]
        visitID = row[3]

        visit_path = os.path.join(folder, str(visit_year), watershed.replace(' ', ''), site.replace(' ', ''), 'VISIT_{}'.format(visitID))
        log.info('Processing {}'.format(visit_path))

        if not os.path.isdir(visit_path):
            os.makedirs(visit_path)

        try:
            visit_data = APIGet('visits/{}'.format(visitID))

            # Write visit information to json file
            with open(os.path.join(visit_path, 'visit_info.json'), 'w') as json_file:
                json.dump(visit_data, json_file)

            # Loop over the two lists of folders per visit: field folders and visit folders
            for api_key, local_folder in {'fieldFolders': 'Field Folders', 'folders': 'Visit Folders'}.items():

                if api_key in visit_data and isinstance(visit_data[api_key], list):
                    for folder_name in visit_data[api_key]:
                        field_folder_path = os.path.join(visit_path, local_folder, folder_name['name'])
                        field_folder_data = APIGet(folder_name['url'], True)

                        if isinstance(field_folder_data, dict) and 'files' in field_folder_data:
                            [download_file(file_dict, field_folder_path) for file_dict in field_folder_data['files']]

            # Get all the miscellaneous files for the visit
            [download_file(file_dict, os.path.join(visit_path, 'Files')) for file_dict in visit_data['files']]

        except Exception as e:
            log.error('Error for visit {}: {}'.format(visitID, e))

    log.info('Process Complete')


def download_file(file_dict, folder):

    log = Logger('Download')

    if not file_dict['name']:
        log.warning('Missing file name in folder {}'.format(folder))
        return

    if not file_dict['downloadUrl'] or file_dict['downloadUrl'].lower() == '?download':
        log.warning('Missing download URL in folder {}'.format(folder))
        return

    file_path = os.path.join(folder, file_dict['name'])

    if not os.path.isdir(folder):
        os.makedirs(folder)

    # Write file info as JSON
    with open( os.path.splitext(file_path)[0] + '.json', 'w') as json_file:
        json.dump(file_dict, json_file)

    # Skip files that exist unless they are zero bytes in which case remove them
    if os.path.isfile(file_path):
        if os.stat(file_path).st_size == 0:
            log.warning('Removing zero byte file {}'.format(file_path))
            os.remove(file_path)
        else:
            return

    # Download missing file
    with open(file_path, 'w+b') as f:
        response = APIGet(file_dict['downloadUrl'], absolute=True)
        f.write(response.content)

    log.info('Downloaded missing file {}'.format(file_path))


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
