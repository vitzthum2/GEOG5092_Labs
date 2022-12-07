import geopandas as gpd
import pandas as pd
import fiona
import random
from shapely.geometry import Point


def create_sample_points(layer, point_density, seed_value):
    """
    Create a random sample of points within a HUC polygon when given the layer, point density,
    and seed value and then returns a geodataframe. Once the random point is created, its checked to verify
    that the point falls within the bound of the HUC polygon. It also adds the HUC8 value to the points.

    Args:
        layer (geopandas.GeoDataFrame): Input Layer
        point_density (float): Input Point Density
        seed_value (float): Seed Value for random point generation
    """
    random.seed(seed_value)
    df = []
    
    for idx, row in layer.iterrows():
        poly_bounds = row['geometry'].bounds
        sq_km = (row['geometry'].area / 1000**2)
        n_points = round(sq_km * point_density)
        sample_points = {'point_id': [], 'geometry': [], 'huc_id':[]}

        for i in range(n_points):
            intersects = False

            while intersects == False:
                x = random.uniform(poly_bounds[0], poly_bounds[2])
                y = random.uniform(poly_bounds[1], poly_bounds[3])
                point = Point(x, y)
                results = layer['geometry'].intersects(point)

                if True in results.unique():
                    sample_points['geometry'].append(Point((x, y)))
                    sample_points['point_id'].append(i)
                    try:
                        sample_points['huc_id'] = row['HUC8']
                    except:
                        sample_points['huc_id'] = row['HUC12'][0:8]
                    intersects = True

            gdf = gpd.GeoDataFrame(sample_points, crs="EPSG:26913")
        df.append(gdf)
    new_df = pd.concat(df)

    return new_df


data_file = './lab3.gpkg'
layers = fiona.listlayers(data_file)

nsrdb = gpd.read_file(data_file, layer = 'ssurgo_mapunits_lab3')

for layer_name in layers:
    if layer_name.startswith('wdbhuc'):
        data_layer = gpd.read_file(data_file, layer = layer_name)

        processed_points = create_sample_points(data_layer, 0.05, 0)

        sampled = gpd.overlay(processed_points, nsrdb, how='intersection')
        sampled_mean = sampled.groupby(by=['huc_id']).mean()

        i = 0
        for row in sampled_mean.iterrows():
            print (f'In {layer_name}, the mean aws0150 for HUC_ID {sampled_mean.index[i]} is {round(sampled_mean.aws0150.values[i],4)}.')
            i = i + 1