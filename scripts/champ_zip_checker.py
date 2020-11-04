# Philip Bailey
# 2 October 2019
# loops over all files listed in the CHaMP Workbench and reports whether they exist on the local system
import os
import sys, traceback
import argparse
import sqlite3


def champ_zip_checker(workbench, top_level_dir):

    dbCon = sqlite3.connect(workbench)
    dbCurs = dbCon.cursor()
    dbCurs.execute('SELECT V.VisitYear, V.WatershedName, V.SiteName, V.VisitID, F.URL' +
        ' FROM vwVisits V INNER JOIN CHaMP_VisitFileFolders F ON V.VisitID = F.VisitID' + 
        ' WHERE (V.ProgramID = 1) AND (F.IsFile <> 0)' +
        ' GROUP BY  V.WatershedName, V.VisitYear, V.SiteName, V.VisitID, F.URL' +
        ' ORDER BY  V.WatershedName, V.VisitYear, V.SiteName, V.VisitID, F.URL')

    present = 0
    missing = 0
    for row in dbCurs.fetchall():
        local_path = os.path.join(top_level_dir, str(row[0]), row[1].replace(' ', ''), row[2], 'VISIT_{}'.format(row[3]), 'Files', os.path.basename(row[4]))

        if os.path.isfile(local_path):
            present += 1
        else:
            missing += 1
            print(local_path)

    print('Present files: {:,}'.format(present))
    print('Missing files: {:,}'.format(missing))
    print ('Processed complete.')

def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('workbench', help='CHaMP Workbench database', type=argparse.FileType('r'))
    parser.add_argument('folder', help='Top level folder where API files exist.', type=str)
    args = parser.parse_args()

    try:
        champ_zip_checker(args.workbench.name, args.folder)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main()