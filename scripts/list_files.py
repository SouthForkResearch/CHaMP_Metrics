import os, sys, traceback
import argparse
import csv

def list_files(folder, output):

    with open(output, mode='wb') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(['File Path', 'Size'])

        # Iterate over the directory tree and check if directory is empty.
        for (dirpath, dirnames, filenames) in os.walk(folder):
            for file in filenames:
                file_path = os.path.join(dirpath, file)
                writer.writerow([file_path, os.stat(file_path).st_size])

    print('Process Complete')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', help='Top level folder where API files exist.', type=str)
    parser.add_argument('output', help='Path to CSV file that will get created.', type=str)
    args = parser.parse_args()

    try:
        list_files(args.folder, args.output)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)


if __name__ == "__main__":
    main()