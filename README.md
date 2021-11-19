# 국토지리정보원 데이터 변환 작업

##국토지리정보원 데이터 를 ODM 에서 사용할수 있게 변환 하는 작업이 필요

### why?

ODM 에서는 이미지의 exif 메타데이터로 부터 Lat , Lon 및 기타 정보를 사용하여 파이프라인을 구성하고 있음.

특히 ODM exif 파싱 하는 코드는 Lat , Lon 이 도분초로 구성되어있는것을 decimal 로 구성하게 되어있어서  (dsm → decimal)  exif 메타데이터에 도분초로 넣어야함.

국토지리정보원(이하 국지원) 데이터의 경우 이미지 1장 (tif 파일) - 메타데이터 파일(xml 파일) 로 구성되어있음

또한 국지원의 메타데이터 기준은 중부원점 , East 20000 , North 6000 으로 설정되어있음

### How?

ODM 파이프라인에서 Dataset loading 은 python 으로 구성되어있으 python lib 중 좌표계 변환 라이브러리 선택 필요 : pyproj

국지원 메터데이터 기준은 EPSG:5186 으로 정의되어있음

- EPSG
    - 전세계 좌표계 정의에 대한 고유 명칭 (European Petroleum Survey Group) , [EPSG.io](http://EPSG.io) 를 통해 제원값 파악이 가능

pyproj 를 통해 EPSG:5186 → EPSG:4326 (WGS84 타원체 경위도 좌표계) 변환 진행

ODM 은 tif 를 지원하지 않는것으로 보여 일단 tif 를 png 또는 jpg 로 변환 필요

### Result

ODM 에서는 exif 메터 데이터가 dms (degree , min , second) 형태로 들어가져야함.

- process
    1. Get EPSG:5186 coordinate from xml metadata
    2. transform EPSG:5186 to EPSG:4326 ( tm coordinate → wgs84 coornidate)
    3. change decimal lat,lon to dms valu
    4. convert original image to jpeg type image
    5. set exif metadata in jpeg type image
    6. done.



```python
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

main_path = '/home/phs/Downloads/seoul_aerial' #image folder
tif_file_list = glob.glob('{}/*.tif'.format(main_path))
proj_korea = Proj(init='EPSG:5186')  # 중부원점(Bessel) - false y: 60000  (EASTING : 20000 , NORTHING : 60000)
proj_wgs = Proj(init='epsg:4326', zone=10, ellps='WGS84')  # WGS84
for tif_file in tif_file_list:
    compare_xml_file = tif_file.replace('tif', 'xml')
    print(tif_file, compare_xml_file)
    tree_ = ET.parse(os.path.join(main_path, compare_xml_file))
    coordinate = tree_.find('./좌표계')
    coord_x = coordinate.find('./원점X좌표')
    coord_y = coordinate.find('./원점Y좌표')
    x = int(coord_x.text)
    y = int(coord_y.text)
    lon, lat = transform(proj_korea, proj_wgs, x, y)
    # lat_to_degree(lat)
    print('lat : {} , lon : {}'.format(lat, lon))
    new_jpeg_path = tif_file.replace('tif', 'jpg')
    with pl.open(os.path.join(main_path, tif_file)) as im:
        im.save(os.path.join(main_path, new_jpeg_path), 'jpeg')
    with open(os.path.join(new_jpeg_path), 'rb') as meta_file:
        meta_data = ex.Image(meta_file)
        meta_data.gps_latitude = lat_to_degree(lat)
        meta_data.gps_longitude = lat_to_degree(lon)
        meta_data.gps_latitude_ref = 'North'
        meta_data.gps_longitude_ref = 'West'
        with open(os.path.join(main_path, new_jpeg_path), 'wb') as updated_meta_file:
            updated_meta_file.write(meta_data.get_file())
```