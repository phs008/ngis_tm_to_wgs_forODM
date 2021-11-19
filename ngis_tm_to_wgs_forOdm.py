import glob
import os.path
import xml.etree.ElementTree as ET
from pyproj import Proj, transform
import PIL.Image as pl
import exif as ex


def lat_to_degree(value: float) -> str:
    min, sec = divmod(value * 3600, 60)
    deg, min = divmod(min, 60)
    print('def : {} , min : {} , sec : {}'.format(deg, min, sec))
    return (deg, min, sec)


def ChangeCoordiante(img_folde_path: str):
    tif_file_list = glob.glob('{}/*.tif'.format(img_folde_path))
    proj_korea = Proj(init='EPSG:5186')  # 중부원점(Bessel) - false y: 60000  (EASTING : 20000 , NORTHING : 60000)
    proj_wgs = Proj(init='epsg:4326', zone=10, ellps='WGS84')  # WGS84
    for tif_file in tif_file_list:
        compare_xml_file = tif_file.replace('tif', 'xml')
        print(tif_file, compare_xml_file)
        compare_xml_file = os.path.join(img_folde_path, compare_xml_file)
        if not os.path.isfile(compare_xml_file):
            print('No exist meta file or , dosn`t matching file name each img file and meta file : {}'.format(compare_xml_file))
            continue
        tree_ = ET.parse(compare_xml_file)
        coordinate = tree_.find('./좌표계')
        coord_x = coordinate.find('./원점X좌표')
        coord_y = coordinate.find('./원점Y좌표')
        x = int(coord_x.text)
        y = int(coord_y.text)
        lon, lat = transform(proj_korea, proj_wgs, x, y)
        # lat_to_degree(lat)
        print('lat : {} , lon : {}'.format(lat, lon))
        new_jpeg_path = tif_file.replace('tif', 'jpg')
        with pl.open(os.path.join(img_folde_path, tif_file)) as im:
            im.save(os.path.join(img_folde_path, new_jpeg_path), 'jpeg')
        with open(os.path.join(new_jpeg_path), 'rb') as meta_file:
            meta_data = ex.Image(meta_file)
            meta_data.gps_latitude = lat_to_degree(lat)
            meta_data.gps_longitude = lat_to_degree(lon)
            meta_data.gps_latitude_ref = 'North'
            meta_data.gps_longitude_ref = 'West'
            with open(os.path.join(img_folde_path, new_jpeg_path), 'wb') as updated_meta_file:
                updated_meta_file.write(meta_data.get_file())


if __name__ == '__main__':
    ChangeCoordiante('/home/phs/Downloads/seoul_aerial')
