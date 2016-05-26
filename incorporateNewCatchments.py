# ===========
# Description
# ===========
# This script incorporates the split mainstem catchments from version 2.1 into 
#	the catchment layers from version 2. The result is a new catchment layer 
#	for each hydrologic region. The new catchment layer has catchments 
#	exclusively denoting the main channel of rivers with a drainage area of 200 
#	sq km or larger. The remaining area of the original catchment is split into
#	contiguous sections draining into the main channel.


# ==============
# Specify inputs
# ==============
# Base directory
baseDirectory = "C:/KPONEIL/HRD/V2.1"

# Hydrologic regions
hydroRegions = ["01", "02", "03", "04", "05", "06"]

# Original version database
original_db = "C:/KPONEIL/HRD/V2/products/hydrography.gdb"


# =====================
# Establish directories
# =====================
# Workspace geodatabase
workspace_db = baseDirectory + "/spatial/incorporateNewCatchments.gdb"
if not arcpy.Exists(workspace_db): arcpy.CreateFileGDB_management (baseDirectory + "/spatial", "incorporateNewCatchments", "CURRENT")

# Products directory
product_directory = baseDirectory + "/products"
if not arcpy.Exists(product_directory): arcpy.CreateFolder_management(baseDirectory, "products")

# Product geodatabase
products_db = product_directory + "/hydrography.gdb"
if not arcpy.Exists(products_db): arcpy.CreateFileGDB_management (product_directory, "hydrography", "CURRENT")

# Working directory from catchment splitting
splitCatchments_db = baseDirectory + "/spatial/splitCatchments.gdb"

# Working directory from catchment splitting
addChannelCats_db = baseDirectory + "/spatial/addChannelCatchments.gdb"


# ======================
# Define existing layers 
# ======================
# Selected catchments to split
cats = splitCatchments_db + "/cats"

# The final split catchments layer from 'addChannelCatchments.py'
splitCatchments = addChannelCats_db + "/combined_cats"

# Loop through hydrologic regions
for region in hydroRegions:

	# Version 2 catchments layer
	catchments = original_db + "/Catchments" + region


	# Index existing catchments to keep
	# ---------------------------------
	arcpy.MakeFeatureLayer_management (catchments, 
									   "catchmentsLyr")	

	arcpy.AddJoin_management("catchmentsLyr", 
							 "FEATUREID", 
							 cats, 
							 "FEATUREID")

	arcpy.SelectLayerByAttribute_management ("catchmentsLyr", 
											 "NEW_SELECTION", 
											 """ "cats.FEATUREID" IS NULL""")			

	arcpy.RemoveJoin_management("catchmentsLyr", 
								"cats")						 
							 
	keepCats = arcpy.FeatureClassToFeatureClass_conversion("catchmentsLyr", 
														   workspace_db, 
														   "keepCats" + region)

	arcpy.Delete_management("catchmentsLyr")		

	# Add columns
	# -----------
	# Add a new unique ID field
	arcpy.AddField_management(keepCats, 
							  "NativeID", 
							  "DOUBLE")																 
									
	arcpy.CalculateField_management(keepCats, 
									"NativeID", 
									"!FEATUREID!", 
									"PYTHON_9.3")						  


	# Index new catchments to add
	# ---------------------------										   
	arcpy.MakeFeatureLayer_management (splitCatchments, 
									   "splitCatchmentsLyr")																	 

	arcpy.SelectLayerByLocation_management ("splitCatchmentsLyr", 
											"HAVE_THEIR_CENTER_IN",
											catchments)																 
																	 
	newCats = arcpy.FeatureClassToFeatureClass_conversion("splitCatchmentsLyr", 
														  workspace_db, 
														  "newCats" + region)		

	arcpy.Delete_management("splitCatchmentsLyr")
														  
														  
	# Add columns
	# -----------
	arcpy.AddField_management(newCats, 
							  "Source", 
							  "TEXT")

	arcpy.CalculateField_management(newCats, 
									"Source", 
									 ' "Mainstem Split" ', 
									 "VB")

	arcpy.AddField_management(newCats, 
							  "AreaSqKM", 
							  "DOUBLE")

	arcpy.CalculateField_management(newCats, 
									"AreaSqKM", 
									"!SHAPE.LENGTH@SQUAREKILOMETERS !", 
									"PYTHON_9.3")						  


	# Join catchments
	# ---------------								
	finalCats = arcpy.Merge_management([keepCats, newCats], 
									   workspace_db + "/combined_cats" + region)								

	arcpy.FeatureClassToFeatureClass_conversion(finalCats, 
												products_db, 
												"Catchments" + region)
