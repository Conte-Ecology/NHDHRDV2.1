# NHDHRDV2.1


This repository contains scripts used to update the NHDHRDV2 (link) catchment layers representing the immediate drainages into large rivers. Specifically, it is necessary to capture the small tributary drainages that flow directly into large rivers. In some cases these tributaries are too small to have been captured by the minimum drainage area threshold established in Version 2. Instead, the small tributaries are encompassed by a single catchment representing the area immediately flowing into a reach on the mainstem of a large river [[IMAGE]]. 

The update in Version 2.1 addresses the need to differentiate between the landscape attributes of the drainage contributing directly to the mainstem reaches from the reaches themselves which receive flow from a large upstream area. Edits are made only to catchments with a 200 sq km or greater drainage area. Each of these catchments is split into 3 new catchments: one representing the river channel, and one on each side of the channel representing the immediate contributing drainage area to the reach. [[IMAGE]]


# Processing


## Identify Features to Split

The existing catchment attribute tables are used to determine which catchments will be broken into separate channel and landscape(name?) sections. A total upstream drainage area (measured from the pour point of the catchment) is set at 200 sq km. The FEATUREIDs of all catchments with a drainage area larger than this threshold are saved to the `splitCatchments.dbf` table. The `splitFlowlines.dbf` contains all of these FEATUREIDs as well as those for the flowlines immediately above the farthest upstream catchment. These features are included for continuity when splitting the catchments. 

### Execute
Open the `identifyFeatures.R` script and set the following variables in the "Specify inputs" section:


- areaDirectory  - The directory containing the catchment attribute tables defining upstream area

- catchmentDirectory <- The directory containing the catchment attribute tables defining the network structure. These tables are the DBF files associated with the spatial catchment layers.

- outDirectory <- The directory to ouput the tables to

- hydroRegions <- The hydrologic regions of NHDHRDV2 to be processed

Execute the script in R. 








