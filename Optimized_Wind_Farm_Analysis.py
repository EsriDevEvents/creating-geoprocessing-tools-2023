import arcpy, sys

arcpy.env.overwriteOutput = True

proposed_windfarm = arcpy.GetParameter(0)
field_for_query = arcpy.GetParameterAsText(1)
wildland_area = arcpy.GetParameter(2)
selected_windfarms = arcpy.GetParameterAsText(3)
road_network = arcpy.GetParameterAsText(4)

# building the query string based on the field choice
arcpy.SetProgressor("step", "Querying proposals with a query string...")
layer_property = arcpy.Describe(proposed_windfarm).dataType
arcpy.AddMessage(f"Analyzing input wind farm layer as the type {layer_property}")

queryString = ""
if field_for_query == "STATUS":
    queryString = " STATUS = 'Application' Or STATUS = 'Scoping' "
elif field_for_query == "RENEWABLES":
    queryString = "RENEWABLES > 1500"
else:
    arcpy.AddError(f"Invalid choice the {field_for_query} field, "
                   f"please select either the STATUS or RENEWABLES field.")
    sys.exit(1)

windfarm_to_be_analyzed, queryed_count = \
    arcpy.management.SelectLayerByAttribute(in_layer_or_view=proposed_windfarm,
                                            where_clause=queryString)

# Choose those windfarms NOT in a wild land area
arcpy.SetProgressorLabel(f"Selecting {queryed_count} wind farms not in a wild land area...")
arcpy.SetProgressorPosition(20)

outside_wildland_windfarm, selected_layer_names, non_wildland_count = \
    arcpy.management.SelectLayerByLocation(in_layer=windfarm_to_be_analyzed,
                                           select_features=wildland_area,
                                           selection_type="REMOVE_FROM_SELECTION")
if non_wildland_count == 0:
    arcpy.AddWarning("All wind farms are on wild land area before the near analysis.")

# Choose wind farms with close proximity to a road only with a provided road network input
if road_network == "":
    arcpy.AddWarning("No road network is available, and the script will skip the near analysis.")
    result_layer = outside_wildland_windfarm
    result_count = non_wildland_count
else:
    arcpy.SetProgressorLabel("Selecting wind farms next to a road")
    arcpy.SetProgressorPosition(40)

    close_to_road_windfarms = arcpy.analysis.Near(in_features=outside_wildland_windfarm,
                                                  near_features=[road_network])[0]
    roadside_windfarms, roadside_count = \
        arcpy.management.SelectLayerByAttribute(in_layer_or_view=close_to_road_windfarms,
                                                where_clause="NEAR_DIST = 0")
    result_layer = roadside_windfarms
    result_count = roadside_count

# Finalize the result
arcpy.SetProgressorLabel("Generating final selections ...")
arcpy.SetProgressorPosition(80)

arcpy.management.CopyFeatures(in_features=result_layer,
                              out_feature_class=selected_windfarms)

arcpy.AddMessage(f"There are {result_count} wind farms in the final selection.")
arcpy.SetParameter(5, result_count)

arcpy.SetProgressorLabel("Results are ready.")
arcpy.SetProgressorPosition(100)
