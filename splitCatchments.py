# ===========
# Description
# ===========
# This script can be executed at first in its entirety. The "Erase" step may 
#   crash and close Arc completely without an error message. If this happens, 
#   reopen the program and redefine the script up to the end of the "Define 
#   Functions" section. Delete the partially created layers (e.g. 
#   "select_polygons_erase") and re-run the script from the last successfully 
#   completed process.


# ==============
# Load libraries
# ==============
import arcpy


# ==============
# Specify inputs
# ==============
# Catchments
catchments = "C:/KPONEIL/HRD/V2/products/hydrography.gdb/Catchments"

# Truncated Flowlines
flowlines = "C:/KPONEIL/HRD/V2.1/spatial/source.gdb/correctedFlowlines"

# Table of flowlines used for splitting
splitFlowlines = "C:/KPONEIL/HRD/V2.1/tables/splitFlowlines.dbf"

# Table of catchments to split
splitCatchments = "C:/KPONEIL/HRD/V2.1/tables/splitCatchments.dbf"

# Base directory
baseDirectory = "C:/KPONEIL/HRD/V2.1"


# ==================
# Create directories
# ==================
# Spatial directory
spatial_directory = baseDirectory + "/spatial"
if not arcpy.Exists(spatial_directory): arcpy.CreateFolder_management(baseDirectory, "spatial")

# Workspace geodatabase
workspace_db = spatial_directory + "/splitCatchments.gdb"
if not arcpy.Exists(workspace_db): arcpy.CreateFileGDB_management (spatial_directory, "splitCatchments", "CURRENT")


# ================
# Define functions
# ================
# Delete all fields except those specified
def deleteExtraFields(layer, fieldsToKeep):
	fields = arcpy.ListFields(layer) 
	dropFields = [x.name for x in fields if x.name not in fieldsToKeep]
	arcpy.DeleteField_management(layer, dropFields)   


# ==========
# Processing
# ==========

# Select catchments to split
# --------------------------
# Also select corresponding flowlines

# Temp layers
arcpy.MakeFeatureLayer_management (flowlines, 
								   "flowlinesLyr")

arcpy.MakeFeatureLayer_management (catchments, 
								   "catchmentsLyr")

# Join selections
arcpy.AddJoin_management("flowlinesLyr", 
						 "FEATUREID", 
						 splitFlowlines, 
						 "FEATUREID")

arcpy.AddJoin_management("catchmentsLyr", 
						 "FEATUREID", 
						 splitCatchments, 
						 "FEATUREID")

# Export selections
arcpy.FeatureClassToFeatureClass_conversion("flowlinesLyr", 
											workspace_db, 
											"lines",
											""" "splitFlowlines.FEATUREID" IS NOT NULL """)

arcpy.FeatureClassToFeatureClass_conversion("catchmentsLyr", 
											workspace_db, 
											"cats",
											""" "splitCatchments.FEATUREID" IS NOT NULL """)

# Delete extra fields
deleteExtraFields(workspace_db + "/cats", 
				  ["OBJECTID", "Shape", "Catchments_FEATUREID", "Catchments_NextDownID", "Shape_Length","Shape_Area"])											
											
# Correct field names
arcpy.AlterField_management(workspace_db + "/cats", 
							'Catchments_FEATUREID', 
							'FEATUREID')	

arcpy.AlterField_management(workspace_db + "/cats", 
							'Catchments_NextDownID', 
							'NextDownID')								

# Delete temp layers
arcpy.Delete_management("flowlinesLyr")
arcpy.Delete_management("catchmentsLyr")


# Split catchments with flowlines
# -------------------------------
# This step cuts the polygons using the flowline layer. Conversion from multipart 
#   to singlepart polygons as well as the creation of excess polygons occurs in 
#   this step and must be remedied.
arcpy.FeatureToPolygon_management([workspace_db + "/cats", workspace_db + "/lines"],
								  workspace_db + "/raw_polygons",
								  "", 
								  "NO_ATTRIBUTES")		
		  
# Delete extra fields
deleteExtraFields(workspace_db + "/raw_polygons", 
				  ["OBJECTID", "Shape", "Shape_Length","Shape_Area"])							  

# Add a new unique ID field
arcpy.AddField_management(workspace_db + "/raw_polygons", 
						  "splitID", 
						  "LONG", 
						  9)
						  
arcpy.CalculateField_management(workspace_db + "/raw_polygons", 
								"splitID", 
								"!OBJECTID!", 
								"PYTHON_9.3")


# Remove extra polygons 
# ---------------------
# Some excess polygons are created by imperfect alignment between catchments and 
#    flowlines (depending on the layer used) or by zones enclosed by catchments.
#    These excess polygons must be deleted. This step is completed by selecting 
#    those catchments whose centroids fall within the original catchment layer. 
#	 A spatial join is used to complete this process and at the same time reassign 
#	 FEATUREIDs that were dropped in the splitting step.

# Determine polygon centroids
arcpy.FeatureToPoint_management(workspace_db + "/raw_polygons", 
								workspace_db + "/raw_points",
								"INSIDE")

# Identify and export the polygon centroids that fall inside the select catchments
arcpy.MakeFeatureLayer_management (workspace_db + "/raw_points", 
								   "rawPointsLyr")

arcpy.SpatialJoin_analysis("rawPointsLyr", 
						   workspace_db + "/cats", 
						   workspace_db + "/raw_points_ids",
						   "JOIN_ONE_TO_ONE", 
						   "KEEP_ALL",
						   "",
						   "COMPLETELY_WITHIN")

# Use the centroids to select the split polygons to keep								
arcpy.MakeFeatureLayer_management (workspace_db + "/raw_polygons", 
								   "rawPolygonsLyr")

arcpy.JoinField_management("rawPolygonsLyr", 
						   "splitID", 
						   workspace_db + "/raw_points_ids", 
						   "splitID", 
						   ["FEATUREID"])

arcpy.FeatureClassToFeatureClass_conversion("rawPolygonsLyr", 
											workspace_db, 
											"select_polygons",
											""" "FEATUREID" IS NOT NULL """)
arcpy.Delete_management("rawPointsLyr")
arcpy.Delete_management("rawPolygonsLyr")


# Join broken polygons
# --------------------
# The splitting process also breaks apart polygon pieces connected by only one 
#   vertex (e.g. 2 touching cell corners). These pieces need to be dissolved back 
#   together without dissolving across the split lines. A small buffer polygon is 
#   generated to separate adjacent, but intentionally split polygons. Then, the 
#   polygons are buffered by an even smaller (1/10x) buffer to create connection 
#   between polygon pieces needing to be joined. This allows adjacent, but 
#   unintentionally split, pieces to be dissolved by a common field as needed 
#   without undoing the work of the split. 

arcpy.Buffer_analysis(workspace_db + "/lines", 
					  workspace_db + "/lines_buffer", 
					  "1 Meter", 
					  "FULL", 
					  "ROUND")

# Delete extra fields
deleteExtraFields(workspace_db + "/lines_buffer", 
				  ["OBJECTID", "Shape", "Shape_Length", "Shape_Area"])										

# This is the problem step described at the top of this script
arcpy.Erase_analysis(workspace_db + "/select_polygons",
					 workspace_db + "/lines_buffer",
					 workspace_db + "/select_polygons_erase")

arcpy.Buffer_analysis(workspace_db + "/select_polygons_erase", 
					  workspace_db + "/select_polygons_buffer", 
					  "0.1 Meter", 
					  "FULL", 
					  "ROUND")
										
arcpy.Dissolve_management(workspace_db + "/select_polygons_buffer", 
						  workspace_db + "/select_polygons_dissolve",
						  "FEATUREID", 
						  "", 
						  "SINGLE_PART")

arcpy.AddField_management(workspace_db + "/select_polygons_dissolve", 
						  "newID", 
						  "DOUBLE")
						  
arcpy.CalculateField_management(workspace_db + "/select_polygons_dissolve", 
								"newID", 
								"!OBJECTID!", 
								"PYTHON_9.3")


# Assign new IDs to catchments
# ----------------------------
# The polygons created in the previous step have the tiny (0.1 meter) buffer around them. 
#   The correctly assigned "newID" field from this layer is assigned to to the original, 
#   un-buffered shapes. Finally, the column names are corrected.

arcpy.FeatureToPoint_management(workspace_db + "/select_polygons", 
								workspace_db + "/select_points",
								"INSIDE")

arcpy.MakeFeatureLayer_management (workspace_db + "/select_points", 
								   "selectPointsLyr")

arcpy.SpatialJoin_analysis("selectPointsLyr", 
						   workspace_db + "/select_polygons_dissolve", 
						   workspace_db + "/select_points_newIDs",
						   "JOIN_ONE_TO_ONE",
						   "KEEP_ALL",
						   "",
						   "COMPLETELY_WITHIN")

arcpy.MakeFeatureLayer_management (workspace_db + "/select_polygons", 
								   "selectPolygonsLyr")
								   
arcpy.JoinField_management("selectPolygonsLyr", 
						   "splitID", 
						   workspace_db + "/select_points_newIDs", 
						   "splitID", 
						   ["newID"])

arcpy.Dissolve_management("selectPolygonsLyr", 
						  workspace_db + "/split_cats",
						  "newID", 
						  "", 
						  "MULTI_PART")


# Reassign FEATUREID
# ------------------
# The dissolve tool drops the FEATUREID field. This may be re-assigned with the 
#   previously used methodology												
arcpy.FeatureToPoint_management(workspace_db + "/split_cats", 
								workspace_db + "/split_points", 
								"INSIDE")								  
											  
arcpy.MakeFeatureLayer_management (workspace_db + "/split_points", 
								   "splitPointsLyr")

arcpy.SpatialJoin_analysis("splitPointsLyr", 
						   workspace_db + "/cats", 
						   workspace_db + "/split_points_ids",
						   "JOIN_ONE_TO_ONE",
						   "KEEP_ALL",
						   "",
						   "COMPLETELY_WITHIN")

arcpy.MakeFeatureLayer_management (workspace_db + "/split_cats", 
								   "splitCatsLyr")		
								   
arcpy.JoinField_management("splitCatsLyr", 
						   "newID", 
						   workspace_db + "/split_points_ids", 
						   "newID", 
						   ["FEATUREID"])											 

arcpy.FeatureClassToFeatureClass_conversion("splitCatsLyr", 
											workspace_db, 
											"mainstem_split_catchments")													

arcpy.Delete_management("splitPointsLyr")
arcpy.Delete_management("splitCatsLyr")										
											
# Rename fields											
arcpy.AlterField_management(workspace_db + "/mainstem_split_catchments", 
							'FEATUREID',  
							'NativeID',  
							'NativeID')
							
arcpy.AlterField_management(workspace_db + "/mainstem_split_catchments",     
							'newID', 
							'FEATUREID', 
							'FEATUREID')
