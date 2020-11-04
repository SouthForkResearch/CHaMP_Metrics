import xml.etree.ElementTree as ET
import csv
import copy

def LoadMetricDefs(metric_def_csv):
    """
    Load metric definitions from CSV file
    :param metric_def_csv: Full absolute path to the CSV file that contains metric definitions
    :return: Dictionary of metric definitions. Key is verbose metric name (e.g. 'Bankfull Side Channel Width') to dictionary of properties
    """
    metricDefs = {}
    with open(metric_def_csv, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            metricDefs[row['name']] = copy.deepcopy(row)

    return metricDefs

def LoadManualMetricValues(manual_metric_xml_report, metricDefs):

    dMetrics = {}

    # Loop over all the topometrics in the validation report XML file
    tree = ET.parse(manual_metric_xml_report)
    root = tree.getroot()
    for metricTag in root.find('topometrics'):

        # Retrieve the verbose, full name of the metric (e.g. 'Bankfull Side Channel Width')
        # and only proceed if it exists in the metric definitions
        nameTag = metricTag.find('name')
        if nameTag.text in metricDefs:
            dMetrics[nameTag.text] = {}

            # Loop over all the visits in the report. Each visit contains an (optional) manual metric
            # and one or more RBT metric values
            for visitTag in metricTag.find('visits'):
                visitMetrics = {}

                # Retrieve the visit ID and the manual metric value (that may not exist)
                visitID = int(visitTag.find('visit_id').text)
                manualTag = visitTag.find('manual_result')
                if manualTag.text != "":
                    visitMetrics['manual'] = float(manualTag.text)

                # Loop over all the RBT results for this metric and visit and add them the the dict
                for resultTag in visitTag.find("results"):
                    visitMetrics["RBT " + resultTag.find('version').text] = float(resultTag.find('value').text)

                # Finally, assign the list of metric values to the main dictionary
                dMetrics[nameTag.text][visitID] = visitMetrics
    return dMetrics

# dictionary of visit IDs to dictionaries of manual and RBT values
# MetricName :
#    2546 : {
#       'Manual' : 2.5467
#       'RBT 5.0.18' : 7.45
#    }
dMetrics = {}

# Load the CSV file that defines topometrics
metricDefs = LoadMetricDefs('D:/Code/tools/test_data/metric_definitions.csv')

# Load the manual metric values from validation report XML, for just the topometrics defined in the dictionary
metricValues = LoadManualMetricValues('D:/Code/tools/test_data/manual_metric_values.xml', metricDefs)

print(metricValues)
