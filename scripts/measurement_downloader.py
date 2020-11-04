import lib.env
from lib.loghelper import Logger
from lib.sitkaAPI import APIGet
from lib.progressbar import ProgressBar
import sqlite3
import argparse
import os
import sys
import traceback
import json
from lib.exception import DataException, MissingException, NetworkException


def metric_downloader(workbench, outputfolder):

    log = Logger("Measurement Downloader")

    conn = sqlite3.connect(workbench)
    curs = conn.cursor()
    visits = {}
    for row in curs.execute('SELECT WatershedName, SiteName, VisitYear, V.VisitID' 
        ' FROM CHaMP_Visits V'
        ' INNER JOIN CHaMP_Sites S ON V.SiteID = S.SiteID' 
        ' INNER JOIN CHaMP_Watersheds W ON S.WatershedID = W.WatershedID' 
        ' WHERE V.ProgramID IN (1, 5, 6)'
        ' AND W.WatershedID IN (15, 32)' # NOT IN ("Asotin", "Big-Navarro-Garcia (CA)", "CHaMP Training")'
        ' ORDER BY WatershedName, visitYear'):

        if not row[0] in visits:
            visits[row[0]] = []
        visits[row[0]].append({'VisitID': row[3], 'Year': row[2], 'Site': row[1]})

    watersheds = list(visits.keys())
    watersheds.sort()
    curs.close()

    for watershed in watersheds:
        visitCount = len(visits[watershed])

        p = ProgressBar(end=len(visits[watershed]), width=20, fill='=', blank='.', format='[%(fill)s>%(blank)s] %(progress)s%%')

        for visit in visits[watershed]:
            p + 1
            print p

            visit_path = os.path.join(outputfolder,
                                      str(visit['Year']),
                                      watershed.replace(' ',''),
                                      visit['Site'].replace(' ', ''),
                                      'VISIT_{}'.format(visit['VisitID']))

            measurements = APIGet("visits/{0}/measurements".format(visit['VisitID']))
            for meas in measurements:

                if not os.path.isdir(visit_path):
                    os.makedirs(visit_path)
                meas_path = os.path.join(visit_path, '{}.json'.format(meas['name'].replace(' ','')))

                data = APIGet(meas['url'], True)

                json_string = json.dumps(data['values'])
                with open(meas_path, 'w') as outfile:
                    json.dump(data, outfile)

    print('Process completed')


def print_progress(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='0'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print '\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix),'\r'
    # sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percent, '%', suffix))
    # sys.stdout.flush()  # As suggested by Rom Ruben

    # Print New Line on Complete
    if iteration == total:
        print()

def main():
    # parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('workbench', help='Workbench database path', type=argparse.FileType('r'))
    parser.add_argument('outputfolder', help='Path to output folder', type=str)
    args = parser.parse_args()

    if not os.path.isdir(args.outputfolder):
        os.makedirs(args.outputfolder)

    # Initiate the log file
    logg = Logger("Measurement Downloader")
    logfile = os.path.join(args.outputfolder, "measurement_downloader.log")
    logg.setup(logPath=logfile, verbose=False)

    try:

        metric_downloader(args.workbench.name, args.outputfolder)

    except (DataException, MissingException, NetworkException) as e:
        # Exception class prints the relevant information
        traceback.print_exc(file=sys.stdout)
        sys.exit(e.returncode)
    except AssertionError as e:
        logg.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    except Exception as e:
        logg.error(e.message)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
