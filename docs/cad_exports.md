---
title: CAD Export
---

The CAD Export Tool generates data products of a CHaMP Topographic Survey Project for use in AutoCad.

# Usage

## Inputs

* Topo Survey Project must be processed and contain the following:
  * Survey Points, Control Points, and Breaklines
  * Topo TIN


##Outputs

The following datasets are exported to the "CAD_Files" folder:

* `TopoTIN.DXF` represents the features of the crew edited TIN, including nodes, triangle edges/breaklines, and polygon area.
* `SurveyTopography.DXF` represents the data that was used to create the TIN ***prior*** to crew editing. Includes Surveyed Topographic points, breaklines, and Survey Extent boundary.
* `SurveyTopographyPoints.csv` comma-separated file output of Topo_Points and EdgeofWater_Points, used to generate the Topographic TIN.
  * Fields
    * **PNTNO** Point number as generated from survey
    * **Y** Northing Coordinate
    * **X** Easting Coordinate
    * **ELEV** Elevation (Z) Coordinate
    * **DESC** Description Code of the point.
* `ControlNetwork.csv` comma-separated file output of Control Points and Benchmarks, including:
  - Control Points and benchmarks loaded to total station prior to survey
  - Control Points and benchmarks added during survey.
  - Fields
    - **PNTNO** Point number as generated from survey
    - **Y** Northing Coordinate
    - **X** Easting Coordinate
    - **ELEV** Elevation (Z) Coordinate
    - **DESC** Description Code of the point.
* `project.rs.xml` Riverscapes Project file, contains information about the visit.
* `cad_export.log` log of processing results.

## Summery of Methods

1. Read binary TIN data and shapefiles as shapely geometry objects.
2. Generate TopoTIN.dxf and SurveyTopography.dxf of geometry objects using custom dxf function.
3. Generate CSV files
4. Generate Riverscapes project.

## Syntax

Command Line parameters for `cad_export.py`:

* Positional Arguments
  * `visitID` (int) the visit id of the site to use (no spaces)
  * `outputfolder` (str) output folder for the substrate raster.
* Optional Arguments
  * `datafolder` (str) Top level folder containing Topo Project Riverscapes projects
  * `logfile` (str) output log file.
  * `verbose` (bool) Get more information in your logs.

# About

* **Code Repository** https://github.com/SouthForkResearch/CHaMP_Metrics
* **Software Architecture** Python 2.7 with standard library and the following 3rd-Party Dependencies:
  * CHaMP_Metrics/Lib:
    * shapely
    * numpy
    * gdal, ogr, osr
* **Batch Processing** this script is designed to work with CHaMP_Automation on AWS or with `batch_run.py` tool
* Code written and maintained by Kelly Whitehead at South Fork Research.

# Release Notes

- `version 0.0.1`  2017-09-01
  - Initial production version

[TOOL HOME](index.md)
