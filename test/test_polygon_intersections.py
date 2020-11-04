from shapely.geometry import *


def PolygonInside(inner, outer, expected, name):

    result = inner.within(outer)
    if not result:
        #result = inner.touches(outer) and not inner.crosses(outer)

        test = outer.intersection(inner)
        if test:
            result = test.area == inner.area
        else:
            test = False


    print '{0} expected {1} actually {2}'.format(name, expected, result)

# Reference polygon
a = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])

# Repeating the reference polygon
b = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])

# Outside not touching
c = Polygon([(10, 10), (10, 21), (21, 21), (21, 10)])

# Outside touching
d = Polygon([(1, 0), (1, 1), (2, 1), (2, 0)])

# Completely inside
e = Polygon([(0.5, 0.5), (0.5, 0.75), (0.75, 0.75), (0.75, 0.5)])

# Inside but sharing an edge with the outside
f = Polygon([(0,0), (0,1), (0.5,0.5)])

PolygonInside(b, a, True, 'b')
PolygonInside(c, a, False, 'c')
PolygonInside(d, a, False, 'd')
PolygonInside(e, a, True, 'e')
PolygonInside(f, a, True, 'f')