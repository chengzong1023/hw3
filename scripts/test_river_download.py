import requests
import zipfile
import io
import geopandas as gpd

# Test the WRA river data download
url = 'https://gic.wra.gov.tw/Gis/gic/API/Google/DownLoad.aspx?fname=RIVERPOLY&filetype=SHP'

print("Testing WRA river data download...")
try:
    r = requests.get(url)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type')}")
    print(f"Content-Length: {len(r.content)}")
    
    # Try to save and extract the zip file
    with open('river_data.zip', 'wb') as f:
        f.write(r.content)
    
    # Extract and examine contents
    with zipfile.ZipFile('river_data.zip', 'r') as zip_ref:
        print("Files in zip:")
        for file in zip_ref.namelist():
            print(f"  - {file}")
        
        # Extract all files
        zip_ref.extractall('river_data')
    
    # Try to read the shapefile
    import os
    shp_files = []
    for root, dirs, files in os.walk('river_data'):
        for file in files:
            if file.endswith('.shp'):
                shp_files.append(os.path.join(root, file))
    
    if shp_files:
        shp_path = shp_files[0]
        print(f"Found shapefile: {shp_path}")
        rivers = gpd.read_file(shp_path)
        print(f"\nSuccessfully loaded {len(rivers)} river polygons")
        print(f"CRS: {rivers.crs}")
        print(f"Bounds: {rivers.total_bounds}")
        print(f"Columns: {list(rivers.columns)}")
    else:
        print("No .shp file found in the extracted data")
        
except Exception as e:
    print(f"Error: {e}")
