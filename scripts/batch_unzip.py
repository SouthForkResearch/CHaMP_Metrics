""" Recursively unzip files

Loop through all files under a source folder and find all
*.zip files. Then unzip each file into the same relative 
path within a destination folder. e.g.

Source:
C:\MyData\Zipped\Folder1\test.zip

Unzipped to:
C:\MyData\Unzipped\Folder1\...
"""
import os
import argparse
import zipfile
import sys
import traceback

def unzip(sourceDir, destDir):
    """Unzip zip files from SourceDir into destDir
    """

    zipFiles = []
    for dirpath, dirnames, files in os.walk(sourceDir):
        for name in files:
            if name.lower().endswith('.zip'):
                zipFiles.append(os.path.join(dirpath,name))

    success = 0
    failures = []

    for sourceFile in zipFiles:
        destPath = os.path.dirname(sourceFile.replace(sourceDir, destDir))

        if os.path.exists(destPath):
            if len(os.listdir(destPath) ) > 0:
                continue
        else:
            os.makedirs(destPath)

        try:
            print 'Unzipping {0}...'.format(sourceFile)
            zip_ref = zipfile.ZipFile(sourceFile, 'r')
            zip_ref.extractall(destPath)
            zip_ref.close()
            success += 1

        except Exception as e:
            failures.append(sourceFile)
    
    print 'Process complete. {0} zip files successful and {1} errors.'.format(success, len(failures))

    for aFail in failures:
        print '\t{0}'.format(aFail)


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument('sourceDir', help='Top level folder containing zip files.', type=str)
    parser.add_argument('destDir', help='Top level folder where files will be unzipped.', type=str)
    args = parser.parse_args()

    try:
        unzip(args.sourceDir, args.destDir)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main()
