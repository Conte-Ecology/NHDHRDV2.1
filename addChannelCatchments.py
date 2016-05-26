# ===========
# Description
# ===========
# This script depends on the output from the "splitcatchments.py" script. 
#   Catchments for the main stem channels are created and merged with the 
#   existing split catchments layer.


# ==============
# Load libraries
# ==============
import arcpy
from arcpy import env
from arcpy.sa import *


# ==============
# Specify inputs
# ==============
# Base directory
baseDirectory = "C:/KPONEIL/HRD/V2.1"

# Trunacted flowlines stream grid
flowGrid = "C:/KPONEIL/HRD/V2.1/spatial/source.gdb/strLnkFinal"


# =====================
# Establish directories
# =====================
# Workspace geodatabase
workspace_db = baseDirectory + "/spatial/addChannelCatchments.gdb"
if not arcpy.Exists(workspace_db): arcpy.CreateFileGDB_management (baseDirectory + "/spatial", "addChannelCatchments", "CURRENT")

# Products directory
product_directory = baseDirectory + "/products"
if not arcpy.Exists(product_directory): arcpy.CreateFolder_management(baseDirectory, "products")

# Product geodatabase
products_db = product_directory + "/hydrography.gdb"
if not arcpy.Exists(products_db): arcpy.CreateFileGDB_management (product_directory, "hydrography", "CURRENT")

# Working directory from catchment splitting
split_db = baseDirectory + "/spatial/splitCatchments.gdb"


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
# Mainstem catchments
cats = split_db + "/cats"

# Create main channel polygons
# ----------------------------
# Convert stream grid to polygon layer
selectFlowGrid = ExtractByMask(flowGrid, cats)
selectFlowGrid.save(workspace_db + "/select_flow_grid")

flowPolygons = arcpy.RasterToPolygon_conversion(selectFlowGrid, 
												workspace_db + "/flow_polygons", 
												"NO_SIMPLIFY",
												"VALUE")

# Assign FEATUREIDs
flowPolygonsIDs = arcpy.SpatialJoin_analysis(flowPolygons, 
										     cats, 
										     workspace_db + "/flow_polygons_FIDs",
										     "JOIN_ONE_TO_ONE",
										     "KEEP_ALL",
										     "#", 
										     "HAVE_THEIR_CENTER_IN")

# Create final polygons
mainChannelCats = arcpy.Dissolve_management(flowPolygonsIDs, 
											workspace_db + "/main_channel_cats",
											"FEATUREID", 
											"", 
											"MULTI_PART")											
											
# Add NextDownID field
arcpy.AddField_management(mainChannelCats, 
						  "NextDownID", 
						  "DOUBLE")	
						  
arcpy.MakeFeatureLayer_management (mainChannelCats, 
								   "mainChannelCatsLyr")											

arcpy.AddJoin_management("mainChannelCatsLyr", 
						 "FEATUREID", 
						 cats, 
						 "FEATUREID")

arcpy.CalculateField_management("mainChannelCatsLyr", 
								"main_channel_cats.NextDownID", 
								"!cats.NextDownID!", 
								"PYTHON_9.3")							 
						 
arcpy.RemoveJoin_management("mainChannelCatsLyr", 
							"cats")								   

mainChannelCatsIDs = arcpy.FeatureClassToFeatureClass_conversion("mainChannelCatsLyr", 
																 workspace_db, 
																 "main_channel_cats_IDs")

arcpy.AddField_management(mainChannelCatsIDs, 
						  "NativeID", 
						  "DOUBLE")																	 
									
arcpy.CalculateField_management(mainChannelCatsIDs, 
								"NativeID", 
								"!FEATUREID!", 
								"PYTHON_9.3")


# Create side catchment polygons
# ------------------------------
sideCats = arcpy.Erase_analysis(split_db + "/mainstem_split_catchments",
								 mainChannelCats,
								 workspace_db + "/side_cats")

arcpy.AddField_management(sideCats, 
						  "NextDownID", 
						  "DOUBLE")	
						  
arcpy.CalculateField_management(sideCats, 
								"NextDownID", 
								"!NativeID!", "PYTHON_9.3")	


# Combine catchment layers
# ------------------------
# Join mainstem and side catchments
combinedCats = arcpy.Merge_management([mainChannelCatsIDs, sideCats], 
										workspace_db + "/combined_cats")
										
								
# ====================
# Export final product
# ====================										
											
arcpy.FeatureClassToFeatureClass_conversion(combinedCats, 
											product_directory, 
											"mainstemCatchments.shp")