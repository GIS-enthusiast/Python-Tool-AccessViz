'''Toolbox for finding file paths, joining tables and visualising matrix data for the Helsinki Region. 

filefinder: Return file paths as a list or text document from a provided list of YKR_ID values and folder path.
tablejoiner: Returns Shapefiles or a geopackage from a list of provided file paths.
visualiser: Returns a static or interactive map for a given YKR_ID.

Usage:

    python AccessViz.py
'''

import os
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import folium
from pathlib import Path


def filefinder(YKR_ID_Values_as_list, folder_path, output):
        """
        Function returns a list of travel time matrix files.

        Args
        ----------
        YKR_ID_Values_as_list: <[]>
            Provide a list of YKR ID values.
        folder_path: <string>
            Provide a path to the central data folder on the computer.
        output: <string>
            Either list or text file. Supported values: 'list'|'text'

        Returns
        -------
        list or text: <[]> or <.txt>
            A list or text file of time matrix travel file paths for processing. Text file is saved to current working directory.
        """
        #Implement desired assertions.
        assert len(YKR_ID_Values_as_list) > 0, "List is empty! List must contain at least one YKR_ID"
        
        #Location of shapefile saved on computer.
        ykr_grid_file_path = Path("MetropAccess_YKR_grid\MetropAccess_YKR_grid_EurefFIN.shp")
        file = gpd.read_file(ykr_grid_file_path)
        IDs = file["YKR_ID"].tolist()
        
        txt_file_path = "file_paths.txt"
        length = len(YKR_ID_Values_as_list)
        count = 0
        
        #Create list to return.
        YKR_file_paths = []

        #Loop through user provided YKR_IDs and build file paths.
        for ID in YKR_ID_Values_as_list:
            count+=1
            if ID in IDs:
                #The first two attempts below work but were superceeded with the Path function.
                #fp = "{}\{}xxx\travel_times_to_{}.txt".format(folder_path, str(ID)[0:4], ID)
                #fp = os.path.join(folder_path, str(ID)[0:4] + "xxx", "travel_times_to{}.txt".format(ID))
                fp = Path(
                    folder_path, 
                    str(ID)[0:4] + "xxx", 
                    "travel_times_to_ {}.txt".format(ID))
                YKR_file_paths.append(fp)
                print("Processing file travel_times_to_{}.txt.. Progress: {}/{}".format(ID, count, length))
            else:
                print("A file for YKR_ID {} does not appear in provided folder path: {}".format(ID, folder_path))
        #Return a list or .txt file.
        if output == 'list':       
            return YKR_file_paths
        elif output == 'text':
            df = pd.DataFrame({'file_paths':YKR_file_paths})
            return df.to_csv(
                txt_file_path, 
                index=False)


def tablejoiner(output_folder, output_format, list):
        '''
        Function returns a list of travel time matrix files.

        Args
        ----------
        list: <[]>
            Provide a list of file paths corresponding to desired YKR_IDs.
        output_format: <string>
            Either Shapefile or Geopackage. Supported values: 'shp'|'gpk'.
        output_folder: <string>
            Output folder for spatial layer.

        Returns
        -------
        ShapeFile or Geopackage: <ESRI Shapefile> or <Geopackage>
            A spatial layer which is a join of the Matrix text table(s) (e.g. travel_times_to_5797076.txt) to the Matrix file with MetropAccess_YKR_grid Shapefile.
        '''
        #Implement desired assertions. Assertions should actually not be used to validate data.
        assert len(list) > 0, "List is empty! List must contain at least one file path"
        
        ykr_grid_file_path = r"MetropAccess_YKR_grid\MetropAccess_YKR_grid_EurefFIN.shp"
        
        #Loop through paths and join the Matrix text files with the Shapefile.
        for path in list:
            #Shapefile to geodataframe.
            data_grid = gpd.read_file(ykr_grid_file_path)
            #Matrix text file to pandas dataframe.
            data = pd.read_csv(
                path, 
                sep=";"
            )
            new_name = {"from_id":"YKR_ID"}
            #Rename columns using dictionary above.
            data = data.rename(columns=new_name)
            #Joing the pandas dataframe to the geodataframe, not the only way around, which would not return a geodataframe.
            data = data_grid.merge(
                data, 
                on= "YKR_ID"
            )
            #Return results as a number of Shapefiles or a Geopackage with multiple layers.
            if output_format == "shp":
                data.to_file(Path(
                    output_folder, 
                    Path(path).stem[-7:])
                            ) #output_folder, Path(path).stem,
            elif output_format == "gpk":
                #save to the same geopackage and label the layers as per the ID using Path().stem[-7:]
                data.to_file(Path(
                    output_folder, 
                    "TravelMatrix.gpkg"), 
                             driver="GPKG", 
                             layer=Path(path).stem[-7:])
                
              
def visualiser(file, path, YKR_ID, mode, output, map):
        '''
        Returns a static or interactive map from source Shapefiles or Geopackage.

        Args
        ----------
        file: <string>
            Supported values: 'shp'|'gpkg'
        path: <string>
            File path for Shapefile or Geopackage.
        YKR_ID: <int>
            Provide YKR_ID.
        mode: <string>
            Mode of transport (car, public transport, walking, biking). Supported values: 'car_sl_t'|'pt_m_t'|'walk_t'|'bike_f_t'.    
        output: <string>
            Output folder for map. eg, C:\\Folder\Folder2\
        map: <string>
            Map type. Supported values: 'static'|'interactive'.
            

        Returns
        -------
        Static (png) or Interactive (html) Map saved to output location.
        '''
        
        if file == 'shp':
            data = gpd.read_file(path)
        elif file == 'gpkg':
            data = gpd.read_file(path, layer=YKR_ID)
        
        # Select data.
        selection = data.loc[data[mode] >=0] # Removes no value data, as no data value = -1.
        selection = selection[[mode, 'geometry']]
        
        # Import matrix grid to provide a position identifier on maps.
        ykr_grid_file_path = r"MetropAccess_YKR_grid\MetropAccess_YKR_grid_EurefFIN.shp"
        data_grid = gpd.read_file(ykr_grid_file_path)
        position = data_grid.loc[data_grid['YKR_ID'] == int(YKR_ID)].reset_index(drop=True)
        position_centroid = position.centroid
        position_WGS84 = position.to_crs(epsg=4326).centroid
        coordinates = (position_WGS84.y, 
                       position_WGS84.x
                      )

        # Create conditional statement for map title.
        title = 'Public transport ' if mode == 'pt_m_t' else 'Car ' if mode == 'car_sl_t' else 'Walking ' if mode == 'walk_t' else 'Biking ' if mode == 'bike_f_t' else 'Please enter a correct value for mode'
        
        
        if map == 'static':
            # Static Map
            fig, ax = plt.subplots(1, figsize=(10, 8))
            selection.plot(ax=ax, 
                           column=mode, 
                           scheme="Natural_Breaks", 
                           k=9, cmap="YlGnBu", 
                           linewidth=0, 
                           legend=True
                          ) #RdYlBu
            position_centroid.plot(ax=ax, 
                                   color="black", 
                                   marker="*", 
                                   markersize=100
                                  ) # Location Identifier.
            ax.set_title(f'{title} travel time (minutes) from YKR_ID {YKR_ID} (depicted by star) to other Helsinki regions')
            
            # Save the figure as png file with resolution of 300 dpi
            outfp = f'{output}{YKR_ID}_{map}.png'
            plt.savefig(outfp, dpi=300)
                                 
        elif map == 'interactive':
            # Interactive Map, location specific to Helsinki.
            m = folium.Map(location=[60.244582,24.940338], 
                           tiles = 'cartodbpositron', 
                           zoom_start=10, 
                           control_scale=True
            )
            selection = selection.to_crs(epsg=4326) # Re-project to WGS84 as Folium requires geographic coordinates.
            selection['geoid'] = selection.index.astype(str) # Create a Geo-id which is needed by Folium (it needs to have a unique identifier for each row).
            selection_json = selection.to_json() # Folium requires geojson format for the parameter geo_data.
            
            # Create conditional statement for map title.
            title = 'Public transport ' if mode == 'pt_m_t' else 'Car ' if mode == 'car_sl_t' else 'Walking ' if mode == 'walk_t' else 'Biking ' if mode == 'bike_f_t' else 'Please enter a correct value for mode'

            folium.Choropleth(geo_data=selection_json,
                              name='Travel Times in 2018',
                              data=selection, 
                              columns=['geoid', mode], 
                              key_on='feature.id', 
                              fill_color='YlOrRd', 
                              fill_opacity=0.7,
                              line_opacity=0.2,
                              line_color='white',
                              line_weight=0,
                              highlight=False,
                              smooth_factor=1.0,
                              #threshold_scale=[100, 250, 500, 1000, 2000],
                              legend_name=f'{title} travel time (minutes) from YKR_ID {YKR_ID} to other Helsinki regions'
            ).add_to(m)
        
            folium.Marker(
                location=coordinates,
                popup=YKR_ID,
                icon=folium.Icon(icon_color='#3C711E',
                                 icon='bus',    # Icon code from https://fontawesome.com/v4.7.0/icons/
                                 prefix='fa'
                                ) # Location Identifier.
            ).add_to(m)
            
            folium.features.GeoJson(selection_json,  
                        name='Labels',
                        style_function=lambda x: {'color':'transparent',
                                                  'fillColor':'transparent',
                                                  'weight':0
                                                 },
                        tooltip=folium.features.GeoJsonTooltip(fields=[mode],
                                                                aliases = ['Travel Time'],
                                                                labels=True,
                                                                sticky=False
                                                                )
            ).add_to(m) # Workaround for tooltips as choropleth does not have tooltips, so effectively adding a transperant layer.

            folium.LayerControl().add_to(m) # Create a layer control object and add it to our map instance.

            outfp = f'{output}{YKR_ID}_{map}.html'
            m.save(outfp)
            
            
def compare(file, YKR_ID, path, list):
    '''
        Function returns a list of travel time matrix files.

        Args
        ----------
        file:
            Supported values 'shp'|'gpkg'
        path:
            Path to shapefile or geopackage.
        list: <[]>
            Provide a list of two transport modes to compare either time or distance. In the calculation the first travel mode in the list is always substracted by the last one. Supported values for comparing time are: pt_r_t and car_r_t, etc. Supported values for comparing distance are: pt_r_d and car_r_d, etc.
        YKR_ID: <string>
            Corresponding YKR_ID from the travel time matrix.

        Returns
        -------
        Shapefile or Geopackage: <ESRI Shapefile> or <Geopackage>
            If a Shapefile was provided as input a Shapefile is returned. The same applies for a Geopackage. A spatial layer with a new column ['diff'] that is the difference between the two transport modes provided in the input list. File is saved to current working directory.
        '''
    # Import data
    if file == 'shp':
        data = gpd.read_file(path)
    elif file == 'gpkg':
        data = gpd.read_file(path, layer=YKR_ID)

    # Select data.
    selection = data.loc[(data[list[0]] >= 0) & (data[list[1]] >= 0)]  # Removes no value data, as no data value = -1.
    selection = selection[[list[0], list[1], 'geometry']]
    selection['diff'] = selection[list[0]] - selection[list[1]]

    #Return results as a number of Shapefiles or a Geopackage with multiple layers.
    if file == "shp":
        data.to_file(Path(f'{path}\Acessibility_{YKR_ID}_{list[0]}_vs_{list[1]}.shp'))  # Accessibility_5797076_pt_vs_car.shp 
    elif file == "gpkg":
        data.to_file(f"Acessibility_{YKR_ID}_{list[0]}_vs_{list[1]}.gpkg", 
                        driver="GPKG", 
                        layer=YKR_ID)
                
                
if __name__ == '__main__':
    filefinder() # sys.argv[1], The 0th arg is the module filename.
