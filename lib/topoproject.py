from os import path
from xml.etree import ElementTree as ET
from exception import DataException, MissingException
from loghelper import Logger
from lib.util import getAbsInsensitivePath

# TODO: This shares a lot in common with riverscapes.py. Let's look at refactoring

class TopoProject():
    # Dictionary with layer { layernname : layerxpath }
    LAYERS = {
        "DEM": "./Realizations/Topography/TIN[@active='true']/DEM/Path",
        "DetrendedDEM": "./Realizations/Topography/TIN[@active='true']/Detrended/Path",
        "WaterDepth": "./Realizations/Topography/TIN[@active='true']/WaterDepth/Path",
        "ErrorSurface": "./Realizations/Topography/TIN[@active='true']/AssocSurfaces/ErrSurface/Path",
        "WaterSurfaceDEM": "./Realizations/Topography/TIN[@active='true']/WaterSurfaceDEM/Path",
        "AssocPointQuality": "./Realizations/Topography/TIN[@active='true']/AssocSurfaces/PointQuality3D/Path",
        "AssocSlope": "./Realizations/Topography/TIN[@active='true']/AssocSurfaces/Slope/Path",
        "AssocRough": "./Realizations/Topography/TIN[@active='true']/AssocSurfaces/Roughness/Path",
        "AssocPointDensity": "./Realizations/Topography/TIN[@active='true']/AssocSurfaces/PointDensity/Path",
        "AssocInterpolationError": "./Realizations/Topography/TIN[@active='true']/AssocSurfaces/InterpolationError/Path",
        "Topo_Points": "./Realizations/SurveyData[@projected='true']/Vector[@id='topo_points']/Path",
        "StreamFeatures": "./Realizations/SurveyData[@projected='true']/Vector[@id='stream_features']/Path",
        "EdgeofWater_Points": "./Realizations/SurveyData[@projected='true']/Vector[@id='eow_points']/Path",
        "Control_Points": "./Realizations/SurveyData[@projected='true']/Vector[@id='control_points']/Path",
        "Error_Points": "./Realizations/SurveyData[@projected='true']/Vector[@id='error_points']/Path",
        "Breaklines": "./Realizations/SurveyData[@projected='true']/Vector[@id='breaklines']/Path",
        "WaterExtent": "./Realizations/Topography/TIN[@active='true']/Stages/Vector[@stage='wetted'][@type='extent']/Path",
        "BankfullExtent": "./Realizations/Topography/TIN[@active='true']/Stages/Vector[@stage='bankfull'][@type='extent']/Path",
        "WettedIslands": "./Realizations/Topography/TIN[@active='true']/Stages/Vector[@stage='wetted'][@type='islands']/Path",
        "BankfullIslands": "./Realizations/Topography/TIN[@active='true']/Stages/Vector[@stage='bankfull'][@type='islands']/Path",
        "ChannelUnits": "./Realizations/Topography/TIN[@active='true']/ChannelUnits/Path",
        "Thalweg": "./Realizations/Topography/TIN[@active='true']/Thalweg/Path",
        "WettedCenterline": "./Realizations/Topography/TIN[@active='true']/Stages/Vector[@stage='wetted'][@type='centerline']/Path",
        "BankfullCenterline": "./Realizations/Topography/TIN[@active='true']/Stages/Vector[@stage='bankfull'][@type='centerline']/Path",
        "WettedCrossSections": "./Realizations/Topography/TIN[@active='true']/Stages/Vector[@stage='wetted'][@type='crosssections']/Path",
        "BankfullCrossSections": "./Realizations/Topography/TIN[@active='true']/Stages/Vector[@stage='bankfull'][@type='crosssections']/Path",
        "SurveyExtent": "./Realizations/SurveyData/SurveyExtents/Vector[@active='true']/Path", #MR?
        "ControlPoints": "./Realizations/SurveyData/Vector[@id='control_points']/Path",
        "TopoTin": "./Realizations/Topography/TIN[@active='true']/Path",
        "Survey_Extent": "./Realizations/SurveyData[@projected='true']/SurveyExtents/Vector[@id='survey_extent']/Path"} #KMW

    def __init__(self, sProjPath):
        """
        :param sProjPath: Either the folder containing the project.rs.xml or the filepath of the actual project.rs.xml
        """
        log = Logger('TopoProject')
        try:
            if path.isfile(sProjPath):
                self.projpath = path.dirname(sProjPath)
                self.projpathxml = sProjPath
            elif path.isdir(sProjPath):
                self.projpath = sProjPath
                self.projpathxml = path.join(sProjPath, "project.rs.xml")
            else:
                raise MissingException("No project file or directory with the name could be found: {}".format(sProjPath))
        except Exception, e:
            raise MissingException("No project file or directory with the name could be found: {}".format(sProjPath))

        self.isrsproject = False

        if path.isfile(self.projpathxml):
            log.info("Attempting to load project file: {}".format(self.projpathxml))
            self.isrsproject = True
            try:
                self.domtree = ET.parse(self.projpathxml)
            except ET.ParseError, e:
                raise DataException("project.rs.xml exists but could not be parsed.")

            self.domroot = self.domtree.getroot()
            log.info("XML Project file loaded")


    def getdir(self, layername):
        return path.dirname(self.getpath(layername))

    def getpath(self, layername):
        """
        Turn a relative path into an absolute one.
        :param project_path:
        :param root:
        :param xpath:
        :return:
        """

        if layername not in TopoProject.LAYERS:
            raise DataException("'{}' is not a valid layer name".format(layername))

        try:
            node = self.domroot.find(TopoProject.LAYERS[layername]).text.replace("\\", path.sep).replace("/", path.sep)
        except Exception, e:
            raise DataException("Error retrieving layer '{}' from project file.".format(layername))

        if node is not None:
            finalpath = path.join(self.projpath, node)
            if not path.isfile(finalpath) and not path.isdir(finalpath):
                # One last, desparate call to see if there's a case error. This is expensive and should not be run
                # as default
                finalpath = getAbsInsensitivePath(finalpath, ignoreAbsent=True)
            return finalpath
        else:
            raise DataException("Could not find layer '{}' with xpath '{}'".format(layername, TopoProject.LAYERS[layername]))


    def getMeta(self, metaname):
        """
        Retrieve Meta tags from the project.rs.xml file
        :param metaname:
        :return:
        """
        try:
            return self.domroot.find('./MetaData/Meta[@name="{}"]'.format(metaname)).text
        except Exception, e:
            raise DataException("Error retrieving metadata with name '{}' from project file.".format(metaname, self.projpathxml))


    def get_guid(self, layername):
        """
        Get the guid from a given layer
        :param layername:
        :return:
        """
        if layername not in TopoProject.LAYERS:
            raise DataException("'{}' is not a valid layer name".format(layername))

        node = self.domroot.find(TopoProject.LAYERS[layername].rstrip("/Path"))

        if node is not None:
            return node.get("guid")
        else:
            raise DataException("Could not find layer '{}' with xpath '{}'".format(layername, TopoProject.LAYERS[layername]))

    def layer_exists(self, layername):

        node = self.domroot.find(TopoProject.LAYERS[layername])
        return True if node is not None else False
