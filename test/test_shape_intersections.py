from shapely.geometry import *

def LineStartsAndStopsWithinPolygon(name1, line, poly, expected):
    print "{0} intersects poly: {1}".format(name1, line.intersects(poly))
    print "{0} touches poly: {1}".format(name1,line.touches(poly))
    print "{0} within poly: {1}".format(name1,line.within(poly))
    print "poly contains {0}: {1}".format(name1,poly.contains(line))
    print "{0} crosses poly: {1}".format(name1,line.crosses(poly))

    inter = poly.intersection(line)
    print "intersection with {0}: {1}".format(name1, inter)

    result = line.within(poly)
    if not result:
        startInside = Point(line.coords[0]).within(poly) or Point(line.coords[0]).touches(poly)
        endsInside = Point(line.coords[-1]).within(poly) or Point(line.coords[-1]).touches(poly)
        result = startInside and endsInside and not line.crosses(poly)

    print "\tExpected {0} got {1}".format(expected, result)
    print '\n'

a = Polygon([(0, 0), (0,1), (1, 1), (1, 0)])

# inside polygon but ends touch the polygon
b = LineString([(0, 0), (1, 1)])

# starts inside and ends outside
c = LineString([(0.5,0.5), (2, 2)])

# entirely outside, no touching
d = LineString([(5,5), (6,6)])

# entirely within polygon. No touching
e = LineString([(0.5, 0.5), (0.75, 0.75)])

# runs along edge of polygon
f = LineString([(0,0), (0, 1)])

# Touches polygon but is outside
g = LineString([(1,1), (2, 2)])

LineStartsAndStopsWithinPolygon('b', b, a, True)
LineStartsAndStopsWithinPolygon('c', c, a, False)
LineStartsAndStopsWithinPolygon('d', d, a, False)
LineStartsAndStopsWithinPolygon('e', e, a, True)
LineStartsAndStopsWithinPolygon('f', f, a, True)
LineStartsAndStopsWithinPolygon('g', g, a, False)
