import contextily as cx
import xyzservices.providers as xyz
import geopandas as gpd
import pyproj
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import os

MAPS_DIR='../maps/'
RASTER_DIR = "../raster_maps/"
JAWG_ACCESS_TOKEN="laGXnA7M9QfsEnrAWGVe1HSfgDF9ghAYeVn9bbTKLl7ClITmEUUCb1qKbQffeXnJ"
ESRI_ACCESS_TOKEN="AAPKa9fe3755a9f149e8957319837fc2a4e10P_k8HkiTW2z7MzIZgCVtDrMSMfNmRQrQe9wea2DLCTZfiDL-nTsQth4zmk2C9G1"

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


areas = ['Se', 'Campo_Limpo', 'MBoi_Mirim', 'Penha']
crs = pyproj.CRS({'proj': 'longlat', 'ellps': 'WGS84', 'no_defs': True})      

for area in areas:
    read_shape(f'{MAPS_DIR}{area}/{area}.shp')

    db = gpd.read_file(f"{MAPS_DIR}{area}_modified/{area}_modified.shp")
    db.to_crs({'init': 'epsg:3857'}, inplace=True)

    w, s, e, n = db.total_bounds
    # img, ext = cx.bounds2raster(w, s, e, n, f"{RASTER_DIR}{area}.tiff", source=xyz.CartoDB.Positron)
   
    # JAWG
    # img, ext = cx.bounds2raster(w, s, e, n, f"{RASTER_DIR}{area}.tiff", source=xyz.Jawg.Streets(accessToken=JAWG_ACCESS_TOKEN))
    # img, ext = cx.bounds2raster(w, s, e, n, f"{RASTER_DIR}{area}.tiff", source=xyz.Jawg.Sunny(accessToken=JAWG_ACCESS_TOKEN))
    # img, ext = cx.bounds2raster(w, s, e, n, f"{RASTER_DIR}{area}.tiff", source=xyz.Jawg.Light(accessToken=JAWG_ACCESS_TOKEN))
   
    # img, ext = cx.bounds2raster(w, s, e, n, f"{RASTER_DIR}{area}.tiff", source=xyz.OpenStreetMap.France)

    # ESRI
    # img, ext = cx.bounds2raster(w, s, e, n, f"{RASTER_DIR}{area}.tiff", source=xyz.Esri.WorldTopoMap(accessToken=ESRI_ACCESS_TOKEN))
    img, ext = cx.bounds2raster(w, s, e, n, f"{RASTER_DIR}{area}.tiff", source=xyz.Esri.WorldStreetMap(accessToken=ESRI_ACCESS_TOKEN))

    reproject_raster(f"{RASTER_DIR}{area}.tiff", f"{RASTER_DIR}{area}_modified.tiff", crs, db.total_bounds)



