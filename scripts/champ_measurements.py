# Philip Bailey
# 30 Oct 2019
# Script to convert CHaMP measurement XML provided by Sitka
# into CSV format.
# Boyd provided several visits by email on 30th Oct and I
# returned the output CSVs the same day.
import os
import sys
import csv
import argparse
import traceback
import xml.etree.ElementTree as ET

def champ_measurements(components, attributes, data_file):
        
    # Load component type definitions from CSV
    comps = {}
    with open(components, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            comps[int(row['ComponentTypeID'])] = row['DisplayName']
            
    # Load measurement types from CSV 
    atts = {}
    with open(attributes, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            atts[int(row['MeasAttribID'])] = row['DisplayName']

    # Load visit measurements from XML file      
    tree = ET.parse(data_file)
    root = tree.getroot()
    records = []
    for dtg in root.findall('DataTableGroups/DataTableGroup'):
        for dt in dtg.findall('DataTables/DataTable'):
            for iv in dt.findall('DataRecords/DataRecord/InputValues/InputValue'):
                records.append([
                    root.attrib['siteName'],
                    root.attrib['visitID'],
                    dtg.attrib['validationStatus'],
                    dt.attrib['componentTypeID'],
                    comps[int(dt.attrib['componentTypeID'])],
                    iv.attrib['measAttribID'],
                    atts[int(iv.attrib['measAttribID'])],
                    iv.attrib['inputValue']
                ])

    # Write outputs to CSV file
    output_csv = os.path.join(os.path.dirname(data_file), 'VISIT_{}_measurements.csv'.format(root.attrib['visitID']))
    with open(output_csv, 'w') as csvfile:
        writer = csv.writer(csvfile) 
        writer.writerow(['Site Name','Visit ID','Validation Status', 'Component Type ID', 'Component Type', 'Measurement Attribute ID', 'Measurement Attribute', 'Value'])
        for record in records:
            writer.writerow(record)
            
    print('Process Complete. {:,} records written to {}'.format(len(records), output_csv))


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('components', help='CSV lookup file that defines component types', type=argparse.FileType('r'))
    parser.add_argument('attributes', help='CSV lookup file that defines measurement attributes types', type=argparse.FileType('r'))
    parser.add_argument('data_file', help='XML data file containing visit measurements', type=argparse.FileType('r'))
    args = parser.parse_args()

    try:
        champ_measurements(args.components.name, args.attributes.name, args.data_file.name)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main()
    