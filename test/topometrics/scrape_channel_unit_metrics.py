# PGB 12 May 2017
# Temporary script to scrape manually calculated channel unit topometrics for Validation sites
# Results provided by Carol Volk via spreadsheet on 11 May 2017. The Channel Units tab of
# this spreadsheet was exported to CSV to work with this script

import sqlite3
import csv

resultfile = 'D:/CHaMP/Temp/2017_05_12_channelunit_metrics.csv'
workbenchDB = 'D:/CHaMP/Workbench/workbench.db'

# Open the database
conn = sqlite3.connect(workbenchDB)
c = conn.cursor()
successful = 0
with open(resultfile, 'rb') as csvfile:
    csvReader = csv.DictReader(csvfile)
    for csvRow in csvReader:

        # Step 1: Look up the Channel Unit ID based on the result and channel unit number
        resultID = csvRow["ResultID"]
        cuNum = csvRow['ChannelUnitNumber']

        c.execute('SELECT VisitID FROM Metric_Results WHERE ResultID = ?', [resultID])
        aRow = c.fetchone()
        visitID = aRow[0]

        c.execute('SELECT ID FROM CHaMP_ChannelUnits C INNER JOIN Metric_Results R ON C.VisitID = R.VisitID WHERE C.ChannelUnitNumber = ? and R.ResultID = ?', [cuNum, resultID])
        aRow = c.fetchone()
        if aRow:
            cuID = aRow[0]
            c.execute(
                'INSERT INTO Metric_ChannelUnitMetrics (ResultID, MetricID, ChannelUnitID, ChannelUnitNumber, MetricValue) VALUES (?, ?, ?, ?, ?)',
                [resultID, csvRow['MetricID'], cuID, cuNum, csvRow['MetricValue']])
            successful += 1
        else:
            print('Failed to find channel unit ID for result {0}, visit ID {1} and channel unit number {2}'.format(resultID, visitID, cuNum))

conn.commit()

print "Completed {0} successfully".format(successful)