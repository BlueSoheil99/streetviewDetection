from streetview import search_panoramas, get_panorama_meta, get_streetview, get_panorama
import requests
import geopandas as gpd

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
from io import BytesIO

from configuration import get_config


apiKey, output_folder, locations = get_config(['GOOGLE_API_KEY', 'download_location', 'input_shapefile_dir'])
stop_flag = False

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
    # filename = f'{lat},{lon}-pano'
    # image = get_streetview(pano_id=panoID, api_key=apiKey, heading=151.78, pitch=-0.76, fov=90)
    image = get_panorama(pano_id=panoID, zoom=4)
    # image.save(f'{output_folder}/{filename}.jpg', "jpeg")
    return image


def download_street_view_image(api_key, location, pitch, heading=None, fov='90', size="640x640", return_error_code=True):
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
        # with open(f"{output_folder}/{filename}.jpg", "wb") as file:
        #     file.write(response.content)
        print("Image downloaded successfully")
        return response.content
    else:
        print("Failed to download image")
        return None


def _save_image(image, file_path, root):
    try:
        image.save(file_path)
        root.destroy()  # Close the window after saving the image
    except IOError as e:
        messagebox.showerror("Error", f"Failed to save image: {e}")


def _raise_stop_flag(root):
    global stop_flag
    stop_flag = True
    root.destroy()


def _show_image(imageContent, path):
    global stop_flag
    img = Image.open(BytesIO(imageContent))
    # Create a GUI window
    root = tk.Tk()
    root.title(path)
    fixed_x = 20
    fixed_y = 20
    root.geometry(f"{img.size[0]}x{img.size[1]+50}+{fixed_x}+{fixed_y}")
    # Convert the image to PhotoImage
    img_tk = ImageTk.PhotoImage(img)
    # Create a label to display the image
    label = tk.Label(root, image=img_tk)
    label.pack()
    # Create a button to save the image
    save_button = tk.Button(root, text="Save Image", command=lambda: _save_image(img, path, root))
    save_button.pack(side=tk.RIGHT)
    exit_button = tk.Button(root, text="enough of this place!", command= lambda: _raise_stop_flag(root))
    exit_button.pack(side=tk.LEFT)
    # Start the GUI event loop
    root.mainloop()


def collect_images(lat, lon,
                   pitch='0',
                   fov='100',
                   selective_save=True,
                   if_pano=True,
                   headings: list =[None, 0, 45, 90, 135, 180, 225, 270, 315]):
    global stop_flag
    stop_flag = False

    if if_pano:
        pano = _download_panorama(lat, lon)
        pano.save(f'{output_folder}/{lat},{lon}-pano.jpg', "jpeg")

    location = f'{lat}, {lon}'
    for heading in headings:
        if stop_flag: return
        responseContent = download_street_view_image(api_key=apiKey, location=location,
                                                      pitch=pitch, heading=heading, fov=fov)
        if responseContent is not None:
            filepath = f"{output_folder}/{lat},{lon}-{heading}.jpg"
            if selective_save:
                    _show_image(responseContent, filepath)
            else:
                with open(filepath, "wb") as file:
                    file.write(responseContent)



if __name__ == '__main__':
    '''
    use a QGIS layer to make a shapefile with location of selected points.
    read the locations here and create images for each point
    '''
    df = gpd.read_file(locations)
    for index, row in df.iterrows():
        lat, lon = row.geometry.y, row.geometry.x
        collect_images(lat, lon, pitch='0', fov='100',
                       selective_save=True, if_pano=False,
                       headings=[None, 0, 45, 90, 135, 180, 225, 270, 315])

    # collect_images(lat=37.800868, lon=-122.443323, if_pano=False, selective_save=False)
    # collect_images(lat=37.804052, lon=-122.433490, if_pano=False, selective_save=False)
