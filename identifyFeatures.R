# ===========
# Description
# ===========
# Existing attribute tables are referenced in order to identify the catchments 
#   to be edited. All catchments with a drainage area of 200 sq km or greater 
#   are selected and the FEATUREIDs exported as the "splitCatchments.dbf" file. 
#   Additionally, the feature immediately upstream of the furthest upstream 
#   catchments are identified so the truncated flowlines may be extended to 
#   complete the split. The FEATUREIDs are included with the selected catchments 
#   and exported as the "splitLines.dbf" file.


# ==============
# Load libraries
# ==============
rm(list = ls())

library(foreign)
library(dplyr)


# ==============
# Specify inputs
# ==============
# Location of attribute tables with upstream areas
areaDirectory <- 'C:/KPONEIL/SHEDS/basinCharacteristics/zonalStatistics/versions/NHDHRDV2/rTables'

# Location of attribute tables with network structure ("NextDownID" field)
catchmentDirectory <- 'C:/KPONEIL/SHEDS/basinCharacteristics/zonalStatistics/gisFiles/vectors'

# Directory to output to
outDirectory <- 'C:/KPONEIL/HRD/V2.1/tables'

# Hydro regions to process
hydroRegions <- c('01', '02', '03', '04', '05', '06')


# ==========
# Processing
# ==========
# Loop through regions and join relevant stats
for (i in seq_along(hydroRegions)){
  
  # Status update
  print(i)
  
  # Network structure
  structure <- read.dbf(paste0(catchmentDirectory, 
                               '/Catchments', 
                               hydroRegions[i], 
                               '.dbf'))[,c('FEATUREID', 'NextDownID')]
  
  # Upstream areas
  area <- read.csv(paste0(areaDirectory, 
                          '/Catchments', 
                          hydroRegions[i], 
                          '/upstream_AreaSqKM.csv'))
  
  join <- left_join(structure, area, by = 'FEATUREID')
  
  if (i == 1){
    stats <- join
  }else(stats <- rbind(stats, join))
}


# Identify catchments to split (remove headwater catchments)
selectCats <- stats[which(stats$AreaSqKM >= 200),]
splitCats <- selectCats[which(selectCats$FEATUREID %in% stats$NextDownID),]

# Furthest upstream catchments to split
heads <- splitCats[which(!splitCats$FEATUREID %in% splitCats$NextDownID),]

# Identify inflows to furthest upstream catchments
above <- stats[which(stats$NextDownID %in% heads$FEATUREID),]

# Select line to use by choosing largest drainage area
newHeads <- group_by(above, NextDownID) %>%
             filter(AreaSqKM == max(AreaSqKM))

# Lines to split catchments (extend beyond last headwater catchment)
splitLines <- rbind(splitCats, newHeads)


# ======
# Output
# ======
# Write tables
write.dbf(splitCats,  file = file.path(outDirectory, 'splitCatchments.dbf'))
write.dbf(splitLines, file = file.path(outDirectory, 'splitFlowlines.dbf'))
