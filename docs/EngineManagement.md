
## AWS Engine Management Procedures  
With the development of the AWS engines for generation of CHaMP metrics and analytical model products (e.g. substrate rasters, hydraulic modeling, habitat capacity), two levels of administration and running of engines were implemented to support the system:  
* North Arrow Research is the Administrator of the AWS engines. Responsibilities include:
  * all engine deployment in AWS environment  
  * API transfer of metrics (to and from Workbench and AWS environment to champmonitoring.org)  
  * transfer of HSI/FIS, substrate rasters, GCD products, and CAD file transfer to champmonitoring.org.  
  * development of lambda Workers/Watchers and EC2 triggering of engines.  
* South Fork Research is the Production Manager of the AWS engines.  Responsibilities include:  
  * scheduling of full CHaMP Visit engine triggering (AWS)  
  * metric schema development (Workbench)  
  * individual metric and engine triggering to support survey updates (Workbench)  
  * final schema development  
  * schema deletion and upload to champmonitoring.org  

  
 Here we provide brief instructions on the Production Management Procedures implemented by SFR.
 
 ### AWS Engine Triggering  
 The Workbench is configured to allow a user to trigger AWS engines. 
 1. Select the Visits to be run through the AWS engines from the main visit display list of the Workbench.  We recommend keeping manual engine triggers less than 40 visits at a time.  Large batches of engine kickoffs should be managed and checked with North Arrow Research to enssure metrics and files will be successfully transferred through the API in a timely fashion.  
 2. Select the Run AWS engine option from the Experimental-Philip Bailey menu option.  
 3. Select the Engine and AWS EC2 instance.
 4. Repeat step 3 for all engines to be triggered.
 5. Login to the AWS account and use Simple Queue Services and CloudWatch to monitor engine progress.
 
 ### Schema Generation
Schemas can be generated in two states:  'Unpublished' and 'Published'.  Unpublished schemas on champmonitoring.org will only be viewable by users who are logged in to champmonitoring.org and have the correct level of permissions.  Contact Sitka Technology for additional information on User Permissions.  

1. Name Schema in Metric_Schemas (SQL Workbench database).  Reference the DatabaseTable holding the metrics of the appropriate dimensionality for the Schema.  Note that Schemas must only combine sets of metrics with the same dimensionality.    
2. Populate Metric_Schema_Definitions with the MetricID (Foreign Key from Metric_Definitions) and SchemaID (Foreign Key from Metric_Schemas).  
3. Switch to the CHaMP Workbench and select Metric Definitions from the Data Menu.
4. Select a Schema and then click on the Data menu item.  Export an .xml of the Metric Definitions.
5. Upload the Schema to the CHaMP_Metrics GitHub Repository (CHaMP_Metrics/xml).
6. If needed, manually update the <Name> to be the Schema Name displayed on champmonitoring.org.
7. Commit changes and then copy the root xml file location (e.g. "https://raw.githubusercontent.com/SouthForkResearch/CHaMP_Metrics/master/xml/" and add the xml file name to the end of it and then paste into the MetricSchemaXMLFile attribute of MetricSchemas in the SQL database.
 
 ### Schema Deletion  
1. Before Schemas are uploaded to champmonitoring.org, delete previous versions of the schema using Postman.  THIS SHOULD BE DONE WITH GREAT CARE AND ONLY BY API ADMINISTRATORS familiar with the CHaMP API.  
2. In Postman, get Authorization Token from Sitka for API access.
3. Identify the schema to delete.  A list of schemas are available here: https://api.CHaMPMonitoring.org/api/v1/visits/5030/metricschemas
4. Use Postman to delete the schema of interest.  

### Prepare Metrics for Upload  
The CHaMP QA versions of the metrics are 'live' versions of the metrics, meaning that they display metrics generated from the last run of the Metric Engines. However, not all metrics or VisitIDs may be appropriate to display to the public and metrics/VisitIDs can be manually updated prior to release of metrics in the Final schemas. 
1. Ensure all QA schemas are up to date with the latest metrics available from the API.
2. In the Workbench, use the Experimental/Philip Bailey menu option to 'Copy Metric Schemas'.
3. Select the Schemas to Copy 'From' and 'To'. 
4. Generate a Batch Name.  It works well to name the Batch Name similar to the Schema "To" name.  
5. Once Metrics have been copied to the new schema, the schema is static as only 'QA' versions of metrics are actively linked to champmonitoring.org via the API.  As a result, the "TO" schema metrics and Visits can now be culled and updated to the appropriate set for public access.  
6. Document Updates between the QA and 'Final' schemas as a Markdown file.  SE.g. ee [Final 2017 Metric Updates](Final2017MetricUpdates.md) for a list of the updates made between the QA and Final metrics for CHaMP.  

### Metric Upload
 The preferred method of Metric Upload is through entire Program-based schemas.  
 1. In the Workbench, select Metric Upload from the Data Menu.
 2. Select the schema to upload.
 3. Proceed to Metric Upload. Note that this can take several hours to complete per schema.
 
 
 
