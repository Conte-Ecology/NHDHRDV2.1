library(foreign)
library(dplyr)


split <- read.dbf("C:/KPONEIL/HRD/V2.1/products/mainstemCatchments.dbf")


originals <- which(split$nativeID == 0)
split$nativeID[originals] <- split$FEATUREID[originals]



newSplit <- group_by(split, nativeID) %>%
              summarise(count = n())


newSplit[which(newSplit$count > 3),]


# compare area stats

range(split$Shape_Area)


hist(split$Shape_Area)


# compare areas with missing values

forest <- read.dbf("C:/KPONEIL/SHEDS/basinCharacteristics/zonalStatistics/versions/NHDHRDV2.1/gisTables/mainstemSplitCatchments/forest.dbf")