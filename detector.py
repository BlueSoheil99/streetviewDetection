from downloader import download_street_view_image
from configuration import get_config

import pandas as pd

from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageTk
import tkinter as tk
from io import BytesIO

import roboflow


apiKeyGoogle, output_folder = get_config(['GOOGLE_API_KEY', 'output_location'])
apiKeyRobo, app_url, project, version = get_config(['ROBOFLOW_API_KEY', 'app_url', 'model_id', 'version'])
input_locations_dir = get_config(['input_crash_locations_dir'])
temp_name = 'tempimage.jpg'

CLIENT = InferenceHTTPClient( api_url=app_url, api_key=apiKeyRobo)

rf = roboflow.Roboflow(api_key=apiKeyRobo)
project = rf.workspace().project("road-objects-qvjnl")
model = project.version("2").model


def make_inference( filename):
    # optionally, change the confidence and overlap thresholds
    # values are percentages
    model.confidence = 30
    model.overlap = 25

    prediction = model.predict(temp_name, confidence=30)
    # prediction.plot()
    prediction.save(output_path=f'{output_folder}/{filename}')
    prediction.json()
    return prediction


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
            img = Image.open(BytesIO(responseContent))
            # may want to do batch prediction
            # https://inference.roboflow.com/inference_helpers/inference_sdk/#parallel-batch-inference
            predictions = make_inference(f'{location}-{heading}.jpg')
            print(predictions)
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
    # collect_inferences(lat=37.804052, lon=-122.433490)
    df = pd.read_csv('crash_data_unique.csv')
    for index, row in df.iterrows():
        collect_inferences(lat=row['Latitude'], lon=row['Longitude'])
