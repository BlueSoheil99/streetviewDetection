from streetview import search_panoramas, get_panorama_meta, get_streetview, get_panorama
import requests
import geopandas as gpd


apiKey = 'google_api_key'
output_folder = 'images'


def _download_panorama(lat, lon):
    panos = search_panoramas(lat=lat, lon=lon)
    # # meta = get_panorama_meta(pano_id=panos[0].pano_id, api_key=apiKey)
    # # print(meta)
    # print('panos:')
    # for i in range(len(panos)):
    #     print(f'{i}     {panos[i]}')

    myPano = panos[-1]
    panoID = myPano.pano_id
    # filename = f'{myPano.lat},{myPano.lon}-pano'
    filename = f'{lat},{lon}-pano'
    # image = get_streetview(pano_id=panoID, api_key=apiKey, heading=151.78, pitch=-0.76, fov=90)
    image = get_panorama(pano_id=panoID, zoom=4)
    image.save(f'{output_folder}/{filename}.jpg', "jpeg")


def _download_street_view_image(api_key, location, pitch, heading=None, fov='90', size="640x640", return_error_code=True):
    '''
    want older pictures? use search_panoramas() and get older pano_ids and use them instead of location in the request

    https://developers.google.com/maps/documentation/streetview/request-streetview
    :param api_key: GOOGLE_MAPS_API_KEY
    :param location:
    :param heading: heading indicates the compass heading of the camera. Accepted values are from 0 to 360 (both values indicating North, with 90 indicating East, and 180 South). If you don't specify a heading, a value is calculated that directs the camera towards the specified location, from the point at which the closest photograph was taken.
    :param pitch:
    :param fov:
    :param size:
    :param return_error_code:
    :return:
    '''
    lat, lon = location.split(',')
    filename = f'{lat},{lon}-{heading}'
    url = f"https://maps.googleapis.com/maps/api/streetview?size={size}&location={location}&pitch={pitch}&return_error_code={str(return_error_code).lower()}&key={api_key}&fov={fov}"

    if heading is not None:
        url = url + f'&heading={heading}'

    response = requests.get(url)

    if response.status_code == 200:
        with open(f"{output_folder}/{filename}.jpg", "wb") as file:
            file.write(response.content)
        print("Image downloaded successfully")
    else:
        print("Failed to download image")


def collect_images(lat, lon, if_pano=True, headings:list =[None, 0, 90, 180, 270]):
    if if_pano:
        _download_panorama(lat, lon)

    location = f'{lat}, {lon}'
    pitch = "0"
    fov = "90"
    for heading in headings:
        _download_street_view_image(api_key=apiKey, location=location, pitch=pitch, heading=heading, fov=fov)


if __name__ == '__main__':
    '''
    use a QGIS layer to make a shapefile with location of selected points.
    read the locations here and create images for each point
    '''
    df = gpd.read_file('data shapefile/sample.shp')
    for index, row in df.iterrows():
        lat, lon = row.geometry.y, row.geometry.x
        collect_images(lat, lon, if_pano=False, headings=[None])

    # collect_images(lat=37.800868, lon=-122.443323)
    # collect_images(lat=37.804052, lon=-122.433490)
