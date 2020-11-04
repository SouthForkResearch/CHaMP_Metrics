import argparse
import sys, traceback
from tools.validation.classes.vector import CHaMP_Polygon

def polyinsidepoly(inner, outer):

    for innerPoly in inner.features:
        results = []
        for outPoly in outer.features:
            buffered = outPoly['geometry'].buffer(0.001)
            results.append(buffered.contains(innerPoly['geometry']))

        if not any(results):
            return False

    return True

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('testShapeFile', help='Path ShapeFile that must occur inside.', type=argparse.FileType('r'))
    parser.add_argument('outerShapeFile', help='Path to the outer ShapeFile that must contain the test.', type=argparse.FileType('r'))
    args = parser.parse_args()

    try:
        inner = CHaMP_Polygon('test', args.testShapeFile.name)
        outer = CHaMP_Polygon('outer', args.outerShapeFile.name)

        print polyinsidepoly(inner, outer)

    except Exception as e:
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main()




