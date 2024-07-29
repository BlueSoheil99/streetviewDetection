from downloader import download_street_view_image
from configuration import get_config

from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageTk
import tkinter as tk
from io import BytesIO

apiKeyGoogle, output_folder, locations = get_config(['GOOGLE_API_KEY', 'output_dir', 'input_locations_dir'])
apiKeyRobo = get_config(['ROBOFLOW_API_KEY'])
app_url = get_config(['app_url'])
model_id = get_config(['model_id'])
temp_name = 'tempimage.jpg'

CLIENT = InferenceHTTPClient( api_url=app_url, api_key=apiKeyRobo)


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
    root.mainloop()


def make_inference():
    result = CLIENT.infer(temp_name, model_id=model_id)
    print(result)
    dic = {}
    return dic


def collect_inferences(lat, lon, pitch='0', fov='100',
                       selective_inference=True,
                       headings: list =[None, 0, 45, 90, 135, 180, 225, 270, 315]):
    global stop_flag
    stop_flag = False

    location = f'{lat}, {lon}'
    for heading in headings:
        if stop_flag: return
        responseContent = download_street_view_image(api_key=apiKeyGoogle, location=location,
                                                      pitch=pitch, heading=heading, fov=fov)
        if responseContent is not None:
            with open(temp_name, "wb") as file:
                file.write(responseContent)
            make_inference()
        else:
            print('image download failed')

        # if responseContent is not None:
        #     filepath = f"{output_folder}/{lat},{lon}-{heading}.jpg"
        #     if selective_save:
        #             _show_image(responseContent, filepath)
        #     else:
        #         with open(filepath, "wb") as file:
        #             file.write(responseContent)


if __name__ == '__main__':
    collect_inferences(lat=37.804052, lon=-122.433490)
