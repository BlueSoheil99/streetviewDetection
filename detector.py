import configuration
from downloader import download_street_view_image
from configuration import get_config

import pandas as pd
import json
import roboflow
import supervision as sv
import cv2
from inference_sdk import InferenceHTTPClient
from PIL import Image
from io import BytesIO


# INITIALIZE PARAMETERS
apiKeyGoogle, output_folder = get_config(['GOOGLE_API_KEY', 'output_location'])
apiKeyRobo, app_url, project, version = get_config(['ROBOFLOW_API_KEY', 'app_url', 'model_id', 'version'])
input_locations_dir, csv_output_dir = get_config(['input_crash_locations_dir', 'csv_output_dir'])
inference_db_adr = get_config(['inference_database'])[0]
temp_name = 'tempimage.jpg'

classes_and_confidences = {'intersection':0.3, 'crosswalk':0.5, 'bus-bike lane':0.5, 'two-way road':0.5,
                           'traffic light':0.5, 'light pole':0.5, 'stop line':0.5, 'stop sign':0.5}

# classes_and_confidences = {'intersection':(60->17%), 'crosswalk':0.5, 'bus-bike lane':0.5, 'two-way road':0.5,
#                            'traffic light':0.5, 'light pole':0.5, 'stop line':0.5, 'stop sign':0.5}


# LOADING THE MODEL
rf = roboflow.Roboflow(api_key=apiKeyRobo)
project = rf.workspace().project("road-objects-qvjnl")
model = project.version("2").model
confidence, overlap = configuration.get_config(['confidence', 'overlap'])


def single_inference(filename, save=True):
    output_path = f'{output_folder}/{filename}'
    prediction = model.predict(temp_name, confidence=confidence, overlap=overlap)
    result = prediction.json()
    if save:
        ## short way to plot and save annotations
        # prediction.plot()
        # prediction.save(output_path=output_path)
        ## better way to plot and save annotations
        labels = [item["class"] for item in result["predictions"]]
        detections = sv.Detections.from_inference(result)
        label_annotator = sv.LabelAnnotator()
        box_annotator = sv.BoxAnnotator()
        image = cv2.imread(temp_name)
        annotated_image = box_annotator.annotate(scene=image, detections=detections)
        annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections, labels=labels)
        # sv.plot_image(image=annotated_image, size=(16, 16))
        cv2.imwrite(output_path, annotated_image)
    return result


def make_inferences(output_name, headings, pitch='0', fov='100'):
    location = output_name.split('_')[1]
    # location = f'{lat}, {lon}'
    prediction_dict ={str(heading):[] for heading in headings}
    for heading in headings:
        responseContent = download_street_view_image(api_key=apiKeyGoogle, location=location,
                                                      pitch=pitch, heading=heading, fov=fov)
        if responseContent is not None:
            with open(temp_name, "wb") as file:
                file.write(responseContent)
            # img = Image.open(BytesIO(responseContent))
            # TODO 1) avoid saving and reading a temp file here and in make_reference to speed up
            # TODO 2) may want to do batch prediction
            # https://inference.roboflow.com/inference_helpers/inference_sdk/#parallel-batch-inference
            predictions = single_inference(f'{output_name}-{heading}.jpg')
            print(f'for {str(heading)}: {predictions}')
            prediction_dict[str(heading)] = predictions
        else:
            print(f'{location}-{heading}: image download failed')

    return prediction_dict


def collect_predictions(crash_df,
                        headings:list =[None, 0, 45, 90, 135, 180, 225, 270, 315],
                        save_adr=inference_db_adr,
                        append=False):
    locations_dict = dict()
    for index, row in crash_df.iterrows():
        print(f"Processing row:{index} --> {row['Date']}, {row['Time']}  \n at:    {row['Google Street View']}")
        lat, lon = row['Latitude'], row['Longitude']
        output_name = f'{index}_{lat},{lon}'
        predictions = make_inferences(output_name, headings=headings)
        locations_dict[index] = {'location':{'lat':lat, 'lon':lon}, 'predictions':predictions}

    if append:
        print('hey fix here')
    else:
        with open(save_adr, 'w') as json_file:
            json.dump(locations_dict, json_file, indent=4)


def update_data(crash_df, inference_json):
    for key in classes_and_confidences.keys():
        crash_df[f'near {key}'] = False
    crash_df['detection applied']=True

    for idx, val in inference_json.items():
        try:
            results = {key:False for key in classes_and_confidences.keys()}
            lat, lon = val['location']['lat'], val['location']['lon']

            for heading, heading_data in val['predictions'].items():
                predictions = heading_data['predictions']
                for prediction in predictions:
                    prediction_class = prediction['class']
                    prediction_confidence = prediction['confidence']
                    if classes_and_confidences[prediction_class] <= prediction_confidence:
                        results[prediction_class] = True
            for key, value in results.items():
                crash_df.loc[idx, f'near {key}'] = value
            print(f'index {idx} updated')
        except TypeError as e:
            print(f'error in updating index {idx}')
            crash_df.loc[idx, 'detection applied'] = False

    return crash_df


if __name__ == '__main__':
    # collect_inferences(lat=37.804052, lon=-122.433490)
    df = pd.read_csv(input_locations_dir)

    # COMMENT THE LINE BELOW IF YOU ALREADY HAVE INFERENCE DATABASE
    # collect_predictions(df.iloc[14:15], save_adr=inference_db_adr, append=True)

    inference_json = pd.read_json(inference_db_adr)
    df = update_data(df, inference_json)
    df.to_csv(csv_output_dir)
