---
title: Topo Validation
---

The Topo File Validator is run on survey topography data that has been generated using the [CHaMP Topographic Toolbar](http://champtools.northarrowresearch.com/).  The Topo File Validator assesses file format, data integrity, and data consistency on single-visit topo survey shapefiles.   The validation engine  was put into production in 2017 to replace the validation checks previously managed by the River Bathymetry Toolkit prior to metric generation and model use.  The validation checks ensure the input data for metrics and models is complete and formatted according to current (2017) model-specific requirements.
Separate validation checks are made for data integrity and consistency across multiple visits and only dataset and dataset-dataset relationships are checked that exist within the visit and not other visits for the site. 

# Usage
[Validation checks](https://docs.google.com/spreadsheets/d/1nlVYtqw8S5gsp83_EXSj4BD0Wmtc4AYBp5RUGWdCJGw/edit) are reviewed annually to ensure consistency with the CHaMP Protocol and Models utilizing the CHaMP Topographic Data.   

[Validation code](https://github.com/SouthForkResearch/CHaMP_Metrics/tree/master/tools/validation) is managed by SFR and NAR.
Validation code is managed by SFR and NAR.

## Inputs

The primary input to this tool is a CHaMP Topo Survey Project, at any stage of completeness. If channel unit information can be obtained (from CHaMP API or local), the channel units will be evaluated against aux data measurements.

## Outputs

The output of the tool is an xml file that performs a series of tests on each expected layer in the Topo Project. Each test for each layer will have a status of 

* `Pass` Layer successfully passes the test.
* `warning` Layer does not pass the test, but the test is not critical to overall success of the topo project.
* `error` Layer does not pass the test, and the topo project will have an overall status of `error` as well. Tests with a status of `error` should be resolved to ensure high data quality standards and successful metric and model results.
* `nottested` Layer was unable to run a particular test due to missing data requirements.

These xml file outputs for each visit are scraped by SFR, imported into an SQL database, and then summarized for crews. Results are posted to crews as Google Docs.

The Program QA Lead reviews the FAIL_DATA.json products to prioritize survey repairs. 
Surveys can almost always be updated to current validation standards by using the current [CHaMP Topographic Toolbar](http://champtools.northarrowresearch.com/) version (2013-2017) and reviewing the Validation window.  We recommend using additional documentation (see QA) for updating 2011-2012 surveys as files may require additional manual formatting updates.

## Summary of Methods

1. Load project as a `CHaMPSurvey` object
2. Validate the survey
   1. Each dataset/gis exists within a class structure and is evaluated for all of the rules for each parent class of that dataset object.
   2. If a rule cannot be performed (i.e. due to a missing data requirement), it will not be tested.
3. Parse the results to xml.

# Syntax

Command Line parameters for `validation.py`

* Positional Arguments
  * `visitID` (int) The visit id for the visit to validate.
  * `outputfolder` (str) folder to save results (xml and log files).
* Optional Arguments
  * `datafolder` (str) Top level folder to search for the topo project with the specified visit id if the data exists locally. Otherwise, script will download the project from cm.org.
  * `verbose` (bool) Get more information in your logs. 

# About

* * **Code Repository** https://github.com/SouthForkResearch/CHaMP_Metrics
  * **Software Architecture** Python 2.7 with standard library and the following 3rd-Party Dependencies:
    - CHaMP_Metrics/Lib:
      - shapely
      - numpy
      - gdal, ogr, osr
  * **Batch Processing** this script is designed to work with CHaMP_Automation on AWS or with `batch_run.py` tool
  * Code written and maintained by Kelly Whitehead at South Fork Research.

# Release Notes

* `version 0.0.4` 2017-11-01
  * ​
* `version 0.0.3` 

[TOOL HOME](index.md)






