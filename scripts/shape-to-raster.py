import contextily as cx
import xyzservices.providers as xyz
import geopandas as gpd
from osgeo import gdal
import pyproj
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Loading env variables
import os
from os.path import join, dirname
# from dotenv import load_dotenv

# dotenv_path = join(dirname(__file__), '.env')
# load_dotenv(dotenv_path)

# # Default settings 
# JAWG_ACCESS_TOKEN = os.environ.get("JAWG_ACCESS_TOKEN")
# ESRI_ACCESS_TOKEN = os.environ.get("ESRI_ACCESS_TOKEN")

JAWG_ACCESS_TOKEN="laGXnA7M9QfsEnrAWGVe1HSfgDF9ghAYeVn9bbTKLl7ClITmEUUCb1qKbQffeXnJ"
ESRI_ACCESS_TOKEN="AAPKa9fe3755a9f149e8957319837fc2a4e10P_k8HkiTW2z7MzIZgCVtDrMSMfNmRQrQe9wea2DLCTZfiDL-nTsQth4zmk2C9G1"
CRS = pyproj.CRS({'proj': 'longlat', 'ellps': 'WGS84', 'no_defs': True})
SRS="+proj=longlat +ellps=WGS84 +no_defs"      
AREAS = ['Se', 'Pinheiros', 'Mooca', 'Lapa', 'Vila_Mariana']
MAPS_DIR='./entrada/maps'
RASTER_DIR = "./entrada/raster_maps"

def reproject_shapefile(shapefile):
    # Read the shapefile pointed in the spec.json
    print(f"Reading shapefile: {shapefile}\n")
    zones_shape = gpd.read_file(shapefile, encoding='latin')
    zones_shape = zones_shape.set_crs('epsg:22523')
    print(f"Current projection: {zones_shape.crs}")

    # Change projection for long/lat if different and save to new file
    if(zones_shape.crs != CRS):
        print("Changing projection...")
        zones_shape.to_crs(CRS, inplace=True)
        print(f"New projection: {zones_shape.crs}\n", )
        print("Written to ", os.path.dirname(shapefile) + '_modified\n')
        zones_shape.to_file(os.path.dirname(shapefile) + '_modified')
    return zones_shape


def reproject_raster(in_path, out_path, dst_srs, bounds):
    # Reproject raster to project crs
    input_raster =  gdal.Open(in_path)
    warp = gdal.Warp(out_path, input_raster, dstSRS=dst_srs, outputBounds=bounds)
    warp = None # Closes the files    


if __name__ == '__main__':
    maps_dir = input("Maps dir: ").strip()
    maps_dir = maps_dir if maps_dir else MAPS_DIR

    raster_dir = input("Maps dir: ").strip()
    raster_dir = raster_dir if raster_dir else RASTER_DIR

    areas = input("Data to process (use space to divide files): ").strip()
    areas = [a for a in areas.split(' ') if a]
    
    areas = areas if areas else AREAS

    # If there is no input data, use default 
    for area in areas:
        print("\n\n--------------------------REPROJECTING SHAPEFILE--------------------------\n\n")
        reproject_shapefile(f'{maps_dir}/{area}/{area}.shp')


        print("\n\n-----------------------------SAVING TMP RASTER----------------------------\n\n")
        db = gpd.read_file(f"{maps_dir}/{area}_modified/{area}_modified.shp")
        db = db.to_crs(CRS)
        
        w, s, e, n = db.total_bounds
        img, ext = cx.bounds2raster(w, s, e, n, f"{raster_dir}/{area}.tiff", source=xyz.Jawg.Dark(accessToken=JAWG_ACCESS_TOKEN), ll=True)
        print(f"Bounding box: {w, s, e, n}")

        print("\n\n----------------------------REPROJECTING RASTER---------------------------\n\n")
        reproject_raster(f"{raster_dir}/{area}.tiff", f"{raster_dir}/{area}_modified.tiff", SRS, db.total_bounds)
        print("--------------------------------------------------------------------------\n\n")
        