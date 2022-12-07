import glob
import numpy as np
import rasterio
import random
from moving_window import mean_filter
from rasterio.warp import calculate_default_transform, reproject, Resampling
from scipy.spatial import cKDTree


data_dir = './data/'
master_crs = 'ESRI:102028'
out_geotiff = './out_data/lab4.tif'

transmission_file = './data/transmission_stations.txt'
transmission_geom = {'num_coords': [], 'geometry': []}

wind_file = rasterio.open('./data/ws80m.tif')
protected_file = rasterio.open('./data/protected_areas.tif')

wind_array = wind_file.read(1)
protected_array = protected_file.read(1)

window_rows = 11
window_columns = 9

data = glob.glob(data_dir + '*tif')
for d in data:
    with rasterio.open(d) as src:      
        
        data = src.read(1)
        if src.crs == 'ESRI:102028':
            pass
        else:       
            transform, width, height = calculate_default_transform(
                src.crs, master_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': master_crs,
                'width': width,
                'height': height
            })
            
            destination = np.zeros((1765, 1121), np.uint8)

            for i in range(1, src.count + 1):
                reproject(
                    source = rasterio.band(src, i), 
                    destination = destination,
                    src_crs = src.crs,
                    dst_crs = master_crs,
                    resampling = Resampling.nearest)   

            if d == data_dir + 'slope.tif':
                slope_array = destination
            elif d == data_dir + 'urban_areas.tif':
                urban_array = destination
            elif d == data_dir + 'water_bodies.tif':
                water_array = destination

            
mask = np.ones((window_rows, window_columns))

wind_array = np.where(wind_array < 0, 0, wind_array)
slope_array = np.where(slope_array < 0, 0, slope_array)

slope_sites = mean_filter(slope_array, mask)
slope_sites = np.where(slope_sites < 15, 0, 1)
 
protected_sites = mean_filter(protected_array, mask)
protected_sites = np.where(protected_sites < 0.05, 0, 1)

urban_sites = mean_filter(urban_array, mask)
urban_sites = np.where(urban_sites, 1, 0)


water_sites = mean_filter(water_array, mask)
water_sites = np.where(water_sites < 0.02, 1, 0)

wind_sites = mean_filter(wind_array, mask)
wind_sites = np.where(wind_sites < 8.5, 0, 1)

sum_sites = (slope_sites + water_sites + wind_sites + protected_sites + urban_sites)

suitability = np.where(sum_sites == 5, 1, 0)

with rasterio.open(out_geotiff, 'w',
                   driver='GTiff',
                   height=suitability.shape[0],
                   width=suitability.shape[1],
                   count=1,
                   dtype='float32',
                   crs=master_crs,
                   transform=transform,
                   nodata=src.nodata,

) as out_raster:
    tif_data = suitability.astype('float32')
    out_raster.write(tif_data, indexes=1)

suitability_val = np.sum(suitability)
    
print(f'There are {suitability_val} suitable areas found with a score of 5.')



#Part 2


random.seed(0)

wkt_path = out_geotiff

sampling_factor = 1/8

with rasterio.open(wkt_path) as wtk_raster:
    data = wtk_raster.read(
        out_shape=[
            wtk_raster.count,
            int(wtk_raster.height * sampling_factor),
            int(wtk_raster.width * sampling_factor)
        ],
        resampling=Resampling.average
    )

    old_transform = wtk_raster.transform
    new_transform = wtk_raster.transform * wtk_raster.transform.scale(
        (wtk_raster.width / data.shape[2]),
        (wtk_raster.height / data.shape[1])
    )

    with rasterio.open('./out_data/resampled_wtk.tif', 'w',
                       driver='GTiff',
                       height=data.shape[1],
                       width=data.shape[2],
                       count=1,
                       dtype='float32',
                       crs=wtk_raster.crs,
                       transform=new_transform,
                       nodata=wtk_raster.nodata,
    ) as out_raster:
        data = data.astype('float32')
        out_raster.write(data[0], indexes=1)

with rasterio.open('./out_data/resampled_wtk.tif') as resampled_raster:
    cell_size = resampled_raster.transform[0]
    
    n_samples = 1
    created_samples = 0
    extent = resampled_raster.bounds
    points = []

    while created_samples < n_samples:
        point = [random.uniform(extent[0], extent[2]),
                 random.uniform(extent[1], extent[3])]

        value_generator = resampled_raster.sample([point])
        
        for value in value_generator:
            if value > 0:
                points.append(point)
                created_samples += 1

    rasWidth = resampled_raster.shape[0]
    rasHeight= resampled_raster.shape[1]
    cellSize = cell_size

x_coords = np.arange(extent[0] + cell_size /2, extent[2], cell_size)   
y_coords = np.arange(extent[1] + cell_size /2, extent[3], cell_size)

x, y = np.meshgrid(x_coords, y_coords)

coords = np.vstack([x.flatten(),y.flatten()])
coords = coords.T

tree = cKDTree(coords)

with open(transmission_file) as f:
    lines = f.readlines()
    pairs = []
    line_count=0
    for pair in lines[1:]:

        line_count = line_count +1
        list_of_str = pair.split(',')

        x_coords = float(list_of_str[0])
        y_coords = float(list_of_str[1])
        point = [x_coords, y_coords]
        pairs.append(point)

dist, indexes = tree.query(pairs, k=1)

min_dist = np.min(dist)
max_dist = np.max(dist)

print(f'The nearest substation is {min_dist} away and furthest is {max_dist}.')