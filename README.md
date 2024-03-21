# The R3 Model

The Resource Recovery and Reuse (R3) model was built in Python and ArcGIS Pro to optimize recovered resource distribution across a spatial grid of reuse. The R3 model was developed to model compost recovery and resuse to croplands in Sri Lanka but can be applied to other resource recovery and resuse questions at various landscape scales. 

## About the Model
![schematic](https://github.com/mayafeincole/R3-Model/assets/82042162/15e8145a-5f6d-4252-b08f-beb3338fcbe9)

The R3 model was built using Python and ArcGIS Pro (Version 2.8.2). Distribution occurs from recovery locations from smallest to largest, operating under the assumption that smaller recovery locations have fewer distribution resources and opportunities, and therefore should be prioritized for local reuse. For each compost recovery location, the closest pixels of potential reuse are identified using the minimum Euclidean distance. Often, multiple pixels of potential resuse reuse are equidistant from the recovery location, so their potential resuse values are summed to make a total closest reuse value. The recovered material supply is compared to the total closest reuse value. There are three potential outcomes of this comparison: 
1. Recovered material supply is greater than total closest reuse:
   - The recovered material supply is updated to reflect the distributed material.
   - The closest potential resuse is fully met, and those cells are set to 0. 
2. Recovered material supply is less than total closest reuse:
   - The recovered material supply is fully distributed, and that cell is set to 0.
   - Material is distributed proportionally between closest potential resuse cells based on their magnitudes. 
3. Recovered material supply is equal to total closest reuse:
   - Both recovered material supply and closest potential resuse cells are set to 0 as supply is fully distributed and potential use is fully met.

The model repeats the selection of closest pixels of potential material reuse until recovery supply at that location is fully distributed. The process repeats at the next smallest recovery location, until all compost for the study area has been distributed. A final distribution map is produced by subtracting the updated potential material reuse reuse layer from the original potential material reuse.

Transport distance and mass are added to a CSV for each distribution cycle. These data are used to visualize the spread of material transport distances for a modeled scenario. The minimum, maximum, and average distance compost must be transported under each scenario is calculated. 


## Using the Model
The model requires 4 user-specified inputs - paths to 2 input files and paths to 2 output files. 
- Input Recovery Raster (line 23)
- Input Potential Reuse Raster (line 24)
- Output Distance Table (line 27)
- Output Difference Raster (line 28)

Input rasters must be identical spatial resolution and snapped for the model to run. 

## Citation and Other Resources
Please use the following citation for the R3 model:  
blah blah blah citation

For questions and more information, please contact:  
Eric Roy, Eric.Roy@uvm.edu \
Kate Porterfield, Katherine.K.Porterfield@uvm.edu
