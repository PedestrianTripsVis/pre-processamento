import contextily as cx
import xyzservices.providers as xyz
import geopandas as gpd
import pyproj
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Loading env variables
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Default settings 
JAWG_ACCESS_TOKEN = os.environ.get("JAWG_ACCESS_TOKEN")
ESRI_ACCESS_TOKEN = os.environ.get("ESRI_ACCESS_TOKEN")
CRS = pyproj.CRS({'proj': 'longlat', 'ellps': 'WGS84', 'no_defs': True})      
AREAS = ['Se', 'Pinheiros', 'Mooca', 'Lapa', 'Vila_Mariana']
MAPS_DIR='./entrada/maps'
RASTER_DIR = "./entrada/raster_maps"

def read_shape(shapefile):
    # Read the shapefile pointed in the spec.json
    print("Reading shapefile: ", shapefile)
    zones_shape = gpd.read_file(shapefile, encoding='latin')
    zones_shape.crs = {'init': 'epsg:22523'}
    print("Current projection: ", zones_shape.crs)

    projection = {'proj': 'longlat', 'ellps': 'WGS84', 'no_defs': True}

    # Change projection for long/lat if different and save to new file
    if(zones_shape.crs != projection):
        print("Changing projection.\n")
        zones_shape.to_crs(projection, inplace=True)
        print("New projection: ", zones_shape.crs)
        print("Written to ", os.path.dirname(shapefile) + '_modified\n\n')
        zones_shape.to_file(os.path.dirname(shapefile) + '_modified')

    return zones_shape


def reproject_raster(in_path, out_path, dst_crs, bounds):
    # Reproject raster to project crs
    with rio.open(in_path) as src:
        src_crs = src.crs
        print(f"Current projection: {src_crs}")
        transform, width, height = calculate_default_transform(src_crs, dst_crs, src.width, src.height, *bounds)
        kwargs = src.meta.copy()

        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height})

        with rio.open(out_path, 'w+', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear)
            print(f"New projection: {dst.crs}")
    return out_path


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
        read_shape(f'{maps_dir}/{area}/{area}.shp')

        db = gpd.read_file(f"{maps_dir}/{area}_modified/{area}_modified.shp")
        db.to_crs({'init': 'epsg:3857'}, inplace=True)

        w, s, e, n = db.total_bounds
        img, ext = cx.bounds2raster(w, s, e, n, f"{raster_dir}/{area}.tiff", source=xyz.Jawg.Dark(accessToken=JAWG_ACCESS_TOKEN))

        reproject_raster(f"{raster_dir}/{area}.tiff", f"{raster_dir}/{area}_modified.tiff", CRS, db.total_bounds)
