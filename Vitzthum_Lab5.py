import os
import numpy as np
import pandas as pd
import rasterio
from lab5functions import *


def zonalStats (value_array, zone_array):
    """Calculates Zonal Statistics as Table

    Parameters
    ----------
    value_array : numpy array
    zone_array : numpy array

    Returns
    -------
    pandas dataframe with fields of zone, mean, std_dev, min, max, count    
    """
    unique_values = np.unique(zone_array)
    df = pd.DataFrame(columns=['zone', 'mean', 'std_dev', 'min', 'max', 'count']) 
    df['zone'] = unique_values[~np.isnan(unique_values)].astype(np.int8)
    for zone in df['zone']:
        in_zone = value_array[zone_array == zone]
        df.at[df['zone'] ==zone, 'mean'] = in_zone.mean()
        df.at[df['zone'] ==zone, 'std_dev'] = in_zone.std()
        df.at[df['zone'] ==zone, 'min'] = in_zone.min()
        df.at[df['zone'] ==zone, 'max'] = in_zone.max()
        df.at[df['zone'] ==zone, 'count'] = (zone_array == zone).sum()
    return df


data_dir = './data/L5_big_elk/'
fire_file = rasterio.open('./data/fire_perimeter.tif')
dem_file = rasterio.open('./data/bigElk_dem.tif')

dem_array = dem_file.read(1)
fire_array =fire_file.read(1)

slope, aspect = slopeAspect(dem_array, 30)

reclassed_aspect = reclassAspect(aspect)
reclassed_slope = reclassByHisto(slope, 10)

files = sorted(os.listdir(data_dir))

b3_files = []
for i in files: 
    if i.endswith('B3.tif'):
        b3_file = data_dir+i
        b3_files.append(b3_file)
        
b4_files = []        
for i in files: 
    if i.endswith('B4.tif'):
        b4_file = data_dir+i
        b4_files.append(b4_file)

recovery_list = []
for i in range (len(b3_files)):
    with rasterio.open(b3_files[i]) as b3_raster:
        b3_data = b3_raster.read(1).astype('float32')
    with rasterio.open(b4_files[i]) as b4_raster:
        b4_data = b4_raster.read(1).astype('float32')
        
    ndvi_array = (b4_data - b3_data) / (b4_data + b3_data)

    ndvi_mean = ndvi_array[fire_array ==2].mean()
    recovery_rate = ndvi_array / ndvi_mean
    
    print(f'The mean RR for {b3_files[i][-11:-7]} is', recovery_rate.mean())
    
    recovery_list.append(recovery_rate.flatten())
    
coefficient_array = np.zeros_like(recovery_list[0]) 
xs = range(10)

for px in range(recovery_list[0].size):
    ys = [p[px] for p in recovery_list]
    coefficient_array[px] = np.polyfit(xs, ys, 1)[0]

coefficient_array = coefficient_array.reshape(b3_data.shape)

print('The mean coefficient of recovery is', coefficient_array[fire_array == 1].mean())
coefficient_array[fire_array !=1] = np.nan


#Part 2
aspect_array = np.where(fire_array == 1, reclassed_aspect, np.nan)
aspect_results = zonalStats (coefficient_array, aspect_array).to_csv('./out_data/aspect_results.csv', sep=',')

slope_array = np.where(fire_array == 1, reclassed_slope, np.nan)
slope_results = zonalStats (coefficient_array, slope_array).to_csv('./out_data/slope_results.csv', sep=',')

out_meta = b3_raster.meta.copy()
out_meta.update({'dtype': 'float32'})   
        
with rasterio.open('./out_data/coefficient_recovery.tif', 'w', **out_meta) as out_raster:
    out_raster.write(coefficient_array, 1)

print('Areas within the 1,2,8 (N,NW, NE) aspect classes had the best recovery. While areas with less slope had better recovery.') 
