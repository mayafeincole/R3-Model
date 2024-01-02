# Import system modules
import arcpy
from arcpy import env
from arcpy.sa import *
import csv

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")

# Turn off geoprocessing log history
arcpy.SetLogHistory(False)

# Reset any environment settings
arcpy.ResetEnvironments()

env.workspace = r"in_memory" # Set workspace to system memory

######################
#USER ENTERS PARAMETERS HERE

# Paths to input files
recovery_raster =   # Path to recovery raster here
potential_reuse_raster = # Path to potential reuse raster here

# Paths to output files
distance_table_path =  # Path to distance table here
difference_raster_path =  # Path to difference raster here
######################

# Geoprocessing environment settings
arcpy.env.overwriteOutput = True
arcpy.env.cellSize = recovery_raster
arcpy.env.snapRaster = potential_reuse_raster
arcpy.env.extent = potential_reuse_raster
arcpy.env.outputCoordinateSystem = recovery_raster

# Convert recovery and potential reuse pixel types to signed integer
recovery_raster = arcpy.management.CopyRaster(recovery_raster, r"memory\recovery_rast", "", "", "0", "", "", "32_BIT_SIGNED")
original_potential_reuse = arcpy.management.CopyRaster(potential_reuse_raster, r"memory\og_reuse_raster", "", "", "0", "", "", "32_BIT_SIGNED")

# Build an attribute table for recovery raster
recovery_table = arcpy.BuildRasterAttributeTable_management(recovery_raster)

# Identify maximum and minimum values in recovery layer
in_layer = recovery_table
fieldName = "VALUE"
recovery_table_list = [r[0] for r in arcpy.da.SearchCursor (in_layer, [fieldName])]
greatest_recovery = max(recovery_table_list) # maximum recovery amount
smallest_recovery = min(recovery_table_list) # minimum recovery amount
recovery = float(smallest_recovery)
recovery = int(recovery) # value of smallest recovery location

# Set iterator variables for later use
go_on = True # are there more recovery locations with resources to be distributed? 
choose_new_site = True # is there remaining value at the current loccation?

iteration = 1 # how many loops the model has done
site_num = 1 # how many recovery locations has the model gone through

#Address potential reuse within each recovery pixel
binary_rast10 = Con(IsNull(recovery_raster), 1, 0)
recovery_rast1s = Divide(recovery_raster, recovery_raster)
potential_reuse_raster2 = Con(IsNull(potential_reuse_raster), 0, potential_reuse_raster)
potential_rr_clip = recovery_rast1s * Raster(potential_reuse_raster2)

greater_recov = recovery_raster - potential_rr_clip
greater_reuse = potential_rr_clip - recovery_raster

update_recov = Con(greater_recov < 0, 0, greater_recov)
update_reuse = Con(greater_reuse < 0, 0, greater_reuse)

update_recov_zero = Con(IsNull(update_recov), 0, update_recov)
update_reuse_zero = Con(IsNull(update_reuse), 0, update_reuse)

update_recov.save(r"memory\update_recov")
recovery_raster = r"memory\update_recov"
zeroed_reuse = binary_rast10 * potential_reuse_raster
update_reuse2 = zeroed_reuse + update_reuse_zero
update_reuse2.save(r"memory\update_reuse")
potential_reuse_raster = r"memory\update_reuse"

#build attribute table for recovery
recovery_table = arcpy.BuildRasterAttributeTable_management(recovery_raster)

in_layer = recovery_table
fieldName = "Value"
recovery_table_list = [r[0] for r in arcpy.da.SearchCursor (in_layer, [fieldName])]
sqlExp = fieldName + '=' + str(min(recovery_table_list))
recovery = int(min(recovery_table_list))

while go_on: 

    print("iteration: " + str(iteration))
    print("site num: " + str(site_num))
    if choose_new_site: # Need to select next smallest recovery location
        iteration = iteration + 1
        site_num = site_num + 1
        
        ### IDENTIFY SMALLEST RECOVERY LOCATION

        arcpy.BuildRasterAttributeTable_management(recovery_raster)
        
        # Use select by attributes to identify the next smallest recovery location (target recovery location)
        recovery_selection = SetNull(recovery_raster, recovery_raster, "Value >" + str(recovery))
        recov_sel_table = arcpy.BuildRasterAttributeTable_management(recovery_selection)
        
        recov_sel_zero = Con(IsNull(recovery_selection), 0, recovery_raster)
        arcpy.management.CopyRaster(recovery_selection, r"memory\recov_sel_zero")
        recov_sel_zero2  = Con(IsNull(r"memory\recov_sel_zero"),0, r"memory\recov_sel_zero")

        # Zonal statistic of recovery layer of recovery selection to capture if there are locations with the same recovery amount
        in_zone_data = recovery_selection
        zone_field = "Value"
        in_value_raster = recovery_raster
        out_table2 = r"memory\recov_sum_table"
        ignore_nodata = "DATA"
        statistics_type = "SUM"
        recov_sum_table = ZonalStatisticsAsTable(in_zone_data, zone_field, in_value_raster, out_table2, ignore_nodata, statistics_type)

        # Create a uniform raster with value equal to the value at the target recovery location
        empty_ras = arcpy.management.CreateRasterDataset(r"memory", "empty_rast") 
        constant_ras = Con(IsNull(empty_ras), recovery)
        
         ### IDENTIFY POTENTIAL REUSE LOCATIONS CLOSEST TO THE SELECTED RECOVERY LOCATION

        # Use Euclidean distance to determine distances between target recovery locations and potential reuse locations
        in_source_data = recovery_selection
        maximum_distance = ""
        cell_size = potential_reuse_raster
        outEucDist = EucDistance(in_source_data, maximum_distance, cell_size) # Distance from smallest recovery location
        og_outEucDist = EucDistance(in_source_data, maximum_distance, cell_size) # Distance from smallest recovery location
        zero_reuse_rast = Raster(potential_reuse_raster)/Raster(potential_reuse_raster)
        zero_reuse_rast2 = arcpy.management.CopyRaster(zero_reuse_rast, r"memory\zero_reuse_rast2", "", "", "0", "", "", "32_BIT_SIGNED")
        outEucDist = Raster(outEucDist)*Raster(zero_reuse_rast2)
        outEucDist2 = arcpy.management.CopyRaster(outEucDist, r"memory\outEucDist2", "", "", "0", "", "", "32_BIT_SIGNED")

        euc_table = arcpy.BuildRasterAttributeTable_management(outEucDist2) # Build attribute table for outEucDist
        
        # Use select by attributes to identify potential reuse pixels locations to the recovery point  (target reuse locations)
        in_layer = euc_table
        fieldName = "Value"
        dist_list = [r[0] for r in arcpy.da.SearchCursor (in_layer, [fieldName])]
        
        #USE THE TRY/EXCEPT TO MAKE MODEL RUN FASTER BY ACCESSING MORE CLOSER POTENTIAL RECOVERY PIXELS WITH EACH ITERATION
        try:
            min_dist = sorted(dist_list)[2]
        
        except: 
            min_dist = min(dist_list)
        
        sqlExp = fieldName + '<=' + str(min_dist)
        input_layer = outEucDist2
        min_dist_select = ExtractByAttributes(input_layer, sqlExp) 
        
        # Convert min_dist_select pixel type to signed integer
        min_dist_select0 = Con(min_dist_select, 1, 0, "VALUE = 0")
        min_dist_select1 = arcpy.management.CopyRaster(min_dist_select, r"memory\min_dist_sel", "", "", "", "", "", "32_BIT_SIGNED")
    
    else: # Don't need to select new smallest recovery location
        iteration = iteration + 1
        
        zero_reuse_rast = Raster(potential_reuse_raster)/Raster(potential_reuse_raster)
        zero_reuse_rast2 = arcpy.management.CopyRaster(zero_reuse_rast, r"memory\zero_reuse_rast2", "", "", "", "", "", "32_BIT_SIGNED")
        outEucDist = Raster(og_outEucDist)*Raster(zero_reuse_rast2)
        outEucDist2 = arcpy.management.CopyRaster(outEucDist, r"memory\outEucDist2", "", "", "", "", "", "32_BIT_SIGNED")
        
        in_conditional_raster = r"memory\outEucDist2"
        in_constant = r"memory\outEucDist2"
        where_clause = "Value<=" + str(min_dist)
        euc_dist_null = SetNull(in_conditional_raster, in_constant, where_clause)
        euc_dist_null.save(r"memory\euc_dist_null")
        euc_dist_null2 = SetNull(r"memory\euc_dist_null", r"memory\euc_dist_null", "Value=0")
        euc_dist_null2.save(r"memory\euc_dist_null2")
        
        euc_table = arcpy.BuildRasterAttributeTable_management(r"memory\euc_dist_null2") # Build attribute table for outEucDist
        

        # Use select by attributes to identify potential reuse pixels locations to the recovery point  (target reuse locations)
        in_layer = euc_table
        fieldName = "Value"
        dist_list = [r[0] for r in arcpy.da.SearchCursor (in_layer, [fieldName])]
        
        #USE THE TRY/EXCEPT TO MAKE MODEL RUN FASTER BY ACCESSING MORE CLOSER POTENTIAL RECOVERY PIXELS WITH EACH ITERATION
        try:
            min_dist = sorted(dist_list)[6]
        
        except: 
            min_dist = min(dist_list)
        
        sqlExp = fieldName + '<=' + str(min_dist)
        input_layer = euc_dist_null
        min_dist_select = ExtractByAttributes(input_layer, sqlExp) 
        
        # Convert min_dist_select pixel type to signed integer
        min_dist_select0 = Con(min_dist_select, 1, 0, "VALUE = 0")
        min_dist_select1 = arcpy.management.CopyRaster(min_dist_select, r"memory\min_dist_sel", "", "", "", "", "", "32_BIT_SIGNED")
        
        # Create a uniform raster with value equal to the value at the target recovery location
        empty_ras = arcpy.management.CreateRasterDataset(r"memory", "empty_rast") 
        constant_ras = Con(IsNull(empty_ras), recovery)

    # Use zonal statistics (sum function) to get a single value for potential reuse at all target reuse locations
    in_zone_data = r"memory\min_dist_sel"
    zone_field = "VALUE"
    in_value_raster = potential_reuse_raster
    statistics_type = "SUM"
    ignore_nodata = "DATA"
    outzstat = ZonalStatistics(in_zone_data, zone_field, in_value_raster, statistics_type, ignore_nodata)

    # Generate same zonal statistics as above in table form to create a variable for summed target reuse locations
    in_zone_data = r"memory\min_dist_sel"
    zone_field = "VALUE"
    in_value_raster = potential_reuse_raster
    out_table2 = r"memory\reusesumtable"
    ignore_nodata = "DATA"
    statistics_type = "SUM"
    reusesumtable = ZonalStatisticsAsTable(in_zone_data, zone_field, in_value_raster, out_table2, ignore_nodata, statistics_type)

    # Create an integer variable for total potential reuse at target reuse locations
    in_layer = r"memory\reusesumtable"
    fieldName = "SUM"
    reuse_list = [r[0] for r in arcpy.da.SearchCursor (in_layer, [fieldName])]
    current_site_reuse = sum(reuse_list)
    reuse = float(current_site_reuse)
    reuse = round(reuse)
    reuse = int(reuse)
    
    # Create a constant raster of nearby reuse
    constant_ras2 = CreateConstantRaster(reuse, "INTEGER")

    ### "DISTRIBUTE" RECOVERED MATERIAL FROM TARGET RECOVERY LOCATION TO TARGET REUSE LOCATIONS

    # Create a binary raster where target locations have values of 0 and non-target locations have values of 1
    binary_rast = Con(IsNull(min_dist_select1), 1, 0)
    binary_rast_recov = Con(IsNull(recovery_selection), 1, 0)
    
    print("Recovery: " + str(recovery))
    print("Reuse: " + str(reuse))
    
    if reuse >= recovery:
        # Update recovery raster
        update_recovery_raster = Raster(recovery_raster) * binary_rast_recov # Value at target recovery location is changed to zero

        # Update potential reuse raster
        binary_rast0 = Con(IsNull(min_dist_select1), 0, 1)
        constant_ras3 = constant_ras2 * binary_rast0
        reuse_percent = Raster(potential_reuse_raster) / constant_ras3 # Proportion of potential reuse at each location compared to total
        cell_distr = reuse_percent * Raster(constant_ras) # Proportional amount of material available for each target recovery location
        cell_distr2 = Int(cell_distr) # Round to nearest integer
        cell_distr2 = arcpy.management.CopyRaster(cell_distr2, r"memory\cell_distr2", "", "", "0", "", "", "32_BIT_SIGNED")
        update_reuse = Raster(potential_reuse_raster) - cell_distr2 # Remaining amount of potential recovery after distribution
        update_reuse2 = Con(IsNull(update_reuse), 0, update_reuse) # Set nulls to zero
        almost_potential_reuse_raster = Raster(potential_reuse_raster) *  binary_rast # Value at target reuse locations are changed to zero
        update_reuse_raster = almost_potential_reuse_raster + update_reuse2 # Replace target reuse cells with new values
        
        choose_new_site = True # No more value at current target recovery location

        distributed = recovery
        
        # Create attribute table for recovery raster
        arcpy.management.CopyRaster(update_recovery_raster, r"memory\recovveerr")
        recov_null = SetNull(Raster(r"memory\recovveerr"), Raster(r"memory\recovveerr"), "Value = 0")
        recovery_raster = Raster(recov_null)
        recovery_table = arcpy.BuildRasterAttributeTable_management(recovery_raster)
        
        arcpy.management.CopyRaster(update_reuse_raster, r"memory\reuseee")
        reuse_null = SetNull(Raster(r"memory\reuseee"), Raster(r"memory\reuseee"), "Value = 0")
        potential_reuse_raster = Raster(reuse_null)
        
        
        try: 
            in_layer = recovery_table
            fieldName = "Value"
            recovery_table_list = [r[0] for r in arcpy.da.SearchCursor (in_layer, [fieldName])]
            sqlExp = fieldName + '=' + str(min(recovery_table_list))
            recovery = int(min(recovery_table_list))

        except:
            go_on = False
            break

    else: 
        
        # Update reuse raster
        update_reuse_raster = Raster(potential_reuse_raster) * binary_rast # Value at target recovery location is changed to zero
        
        # Update recovery raster
        if reuse == recovery:
            new_recovery = recov_sel_zero2 - constant_ras2 # Subtract distributed material from target recovery location
            new_recovery2 = Con(IsNull(new_recovery), 0, new_recovery) # Set nulls to zero
            almost_recovery_raster = recovery_raster *  binary_rast_recov # Value at target recovery locations is changed to zero
            update_recovery_raster = almost_recovery_raster + new_recovery2 # Replace target recovery cells with new value

        else:
            new_recovery = recov_sel_zero2 - constant_ras2 # Subtract distributed material from target recovery location
            new_recovery1 = SetNull(new_recovery, new_recovery, "Value < 0")
            new_recovery2 = Con(IsNull(new_recovery1), 0, new_recovery1) # Set nulls to zero
            almost_recovery_raster = recovery_raster *  binary_rast_recov # Value at target recovery locations is changed to zero
            update_recovery_raster = almost_recovery_raster + new_recovery2 # Replace target recovery cells with new value
            
            arcpy.management.CopyRaster(update_recovery_raster, r"memory\new_recovery_raster") 
            recovery_raster = Raster(r"memory\new_recovery_raster")
            
         # Create attribute table for recovery raster
        arcpy.management.CopyRaster(update_recovery_raster, r"memory\recovveerr")
        recov_null = SetNull(Raster(r"memory\recovveerr"), Raster(r"memory\recovveerr"), "Value = 0")
        recovery_raster = Raster(recov_null)
        recovery_table = arcpy.BuildRasterAttributeTable_management(recovery_raster)
        
        arcpy.management.CopyRaster(update_reuse_raster, r"memory\reuseee")
        reuse_null = SetNull(Raster(r"memory\reuseee"), Raster(r"memory\reuseee"), "Value = 0")
        potential_reuse_raster = Raster(reuse_null)
        
        choose_new_site = False # More value at current target recovery location
        
        distributed = reuse
        
        recovery = recovery - reuse

    # Calculate and  distribution raster
    potential_reuse_raster = Con(IsNull(potential_reuse_raster), 0, potential_reuse_raster)
    difference_raster = original_potential_reuse - potential_reuse_raster
    difference_raster = SetNull(difference_raster, difference_raster, "Value = 0")

    filename = "difference_raster" + str(iteration) +".tif"
    difference_raster.save(filename)
    
    go_on = True
        
    ###  THE CHANGE IN POTENTIAL REUSE AFTER DISTRIBUTION HAS STOPPED
    potential_reuse_raster = Con(IsNull(potential_reuse_raster), 0, potential_reuse_raster)
    difference_raster = original_potential_reuse - potential_reuse_raster
    difference_raster2 = SetNull(difference_raster, difference_raster, "Value = 0")

    difference_raster2.save(difference_raster_path)
    
# Create a spreadsheet containing distance travelled
outeucdist = EucDistance(recovery_raster)
outeucdist_int = Int(outeucdist + 0.5)
distance_table = ZonalStatisticsAsTable(outeucdist_int, "VALUE", difference_raster2, distance_table, "NODATA", "SUM")
arcpy.conversion.TableToExcel(distance_table, distance_table_path)


