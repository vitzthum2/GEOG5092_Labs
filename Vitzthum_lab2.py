import os
import geopandas as gpd
from shapely.geometry import Polygon
from rasterstats import zonal_stats

district_dir = './Lab2/data/districts'
ag_dir = './Lab2/data/agriculture'

district_list = os.listdir(district_dir)
ag_list = os.listdir(ag_dir)

list_of_str =[]

for dist_name in district_list:
    if dist_name.endswith('.txt'):
        
        with open(district_dir + '/' + dist_name, 'r') as fp:
            
            file_input = fp.read().split('\n')

            line_count = 0
            output = []
            
            for row in file_input[1:]:
                
                line_count = line_count +1
                list_of_str = row.split()
        
                x = float(list_of_str[0])
                y = float(list_of_str[1])
              
                output.append((x,y))

            poly_out = Polygon(output)

            d = {'numcoords': line_count, 'district': dist_name[-6:-4], 'geom': poly_out}
            gdf = gpd.GeoDataFrame([d], geometry = 'geom')

            for ag_name in ag_list:
                if ag_name.endswith('.tif'):

                    z_stats = zonal_stats(gdf, ag_dir + '/' + ag_name, stats = 'sum count mean')
                    mean_val = ([f['mean'] for f in z_stats])
                    sum_val = ([f['sum'] for f in z_stats])
                    percentage = round(float(mean_val[0]) * 100, 2)
                    print(f'There are {int(sum_val[0])} agricultural pixels in District {gdf.district.values[0]} during {ag_name[10:14]}, {percentage}% of all land is agricultural.')