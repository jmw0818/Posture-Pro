import os
import cv2
import csv
import math
import ast
import shutil
import pandas as pd

from .utils import video_div, save_progress


BODY_PARTS = {
    "Head": 0, "Neck": 1, "RShoulder": 2, "RElbow": 3, "RWrist": 4,
    "LShoulder": 5, "LElbow": 6, "LWrist": 7, "RHip": 8, "RKnee": 9,
    "RAnkle": 10, "LHip": 11, "LKnee": 12, "LAnkle": 13, "Chest": 14,
    "Background": 15
}

POSE_PAIRS = [
    ["Head", "Neck"], ["Neck", "RShoulder"], ["RShoulder", "RElbow"],
    ["RElbow", "RWrist"], ["Neck", "LShoulder"], ["LShoulder", "LElbow"],
    ["LElbow", "LWrist"], ["Neck", "Chest"], ["Chest", "RHip"], ["RHip", "RKnee"],
    ["RKnee", "RAnkle"], ["Chest", "LHip"], ["LHip", "LKnee"], ["LKnee", "LAnkle"]
]


def squat_calculate_angle(a, b, c):
    try:
        rad1 = math.atan((a[1]-b[1]) / (a[0]-b[0]))
    except ZeroDivisionError:
        rad1 = 0
    try:
        rad2 = math.atan((a[1]-c[1]) / (a[0]-c[0]))
    except ZeroDivisionError:
        rad2 = 0
    return abs((rad1-rad2) * 180/math.pi)


def squat_get_y_value(coord_str):
    if pd.isna(coord_str) or coord_str == "None":
        return math.nan
    coord_tuple = ast.literal_eval(coord_str)
    return coord_tuple[1]


def squat_find_max_y_frames(df, column_name, num):
    y_values = []
    frame_names = []
    for index, row in df.iterrows():
        y_value = squat_get_y_value(row[column_name])
        if not math.isnan(y_value):
            y_values.append(y_value)
            frame_names.append(df.iloc[index]['Frame Name'])
    top_n_y_frames = []
    for _ in range(num):
        if y_values:
            max_y_value = max(y_values)
            max_index = y_values.index(max_y_value)
            top_n_y_frames.append(frame_names[max_index])
            y_values.pop(max_index)
            frame_names.pop(max_index)
    return top_n_y_frames


def squat_tool(request):
    save_progress(10)
    folder_path = "media"
    style = 'squat'
    request.session['style'] = style

    output_folder = "frame_split/squat/squatco"
    image_output_folder = "frame_split/squat/squatimage"
    output_csv_file_folder = "frame_point/squat/squatco"

    for folder in [output_folder, image_output_folder, output_csv_file_folder]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    save_progress(10)
    video_div(style, folder_path, output_folder)

    net = cv2.dnn.readNetFromCaffe("pose_deploy_linevec_faster_4_stages.prototxt", "pose_iter_160000.caffemodel")

    output_csv_file = "frame_point/squat/squatco/all_points.csv"
    os.makedirs(os.path.dirname(output_csv_file), exist_ok=True)

    folder_path = "frame_split/squat/squatco"
    file_list = os.listdir(folder_path)
    image_paths = [os.path.join(folder_path, f) for f in file_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    with open(output_csv_file, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([
            "Frame Name", "Point 0", "Point 1", "Point 2", "Point 3", "Point 4",
            "Point 5", "Point 6", "Point 7", "Point 8", "Point 9", "Point 10",
            "Point 11", "Point 12", "Point 13", "Point 14",
            "knee_angle_left", "knee_angle_right", "Posture"
        ])

        for idx, image_path in enumerate(image_paths):
            points = []
            frame_name = os.path.basename(image_path)
            image = cv2.imread(image_path)
            imageHeight = 368
            imageWidth = 368
            image = cv2.resize(image, (imageWidth, imageHeight))

            inpBlob = cv2.dnn.blobFromImage(image, 1.0 / 255, (imageWidth, imageHeight), (0, 0, 0), swapRB=False, crop=False)
            net.setInput(inpBlob)
            output = net.forward()

            for i in range(0, 15):
                probMap = output[0, i, :, :]
                minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)
                x = (imageWidth * point[0]) / output.shape[3]
                y = (imageHeight * point[1]) / output.shape[2]
                points.append((int(x), int(y)) if prob > 0.1 else None)

            hip_left = points[BODY_PARTS["LHip"]]
            hip_right = points[BODY_PARTS["RHip"]]
            knee_left = points[BODY_PARTS["LKnee"]]
            knee_right = points[BODY_PARTS["RKnee"]]
            ankle_left = points[BODY_PARTS["LAnkle"]]
            ankle_right = points[BODY_PARTS["RAnkle"]]

            save_progress(10 + (idx / len(image_paths)) * 80)

            if hip_left and hip_right and knee_left and knee_right and ankle_left and ankle_right:
                knee_angle_right = squat_calculate_angle(knee_right, hip_right, ankle_right)
                knee_angle_left = squat_calculate_angle(knee_left, hip_left, ankle_left)
                csvwriter.writerow([frame_name] + points + [knee_angle_left, knee_angle_right])

            for pair in POSE_PAIRS:
                partA = pair[0]
                partB = pair[1]
                if points[BODY_PARTS[partA]] and points[BODY_PARTS[partB]]:
                    cv2.line(image, points[BODY_PARTS[partA]], points[BODY_PARTS[partB]], (0, 255, 0), 3)

            save_path = os.path.join(image_output_folder, os.path.splitext(frame_name)[0] + '_image.jpg')
            cv2.imwrite(save_path, image)

    save_progress(99)
    df = pd.read_csv(output_csv_file, encoding='CP949')
    max_y_result = squat_find_max_y_frames(df, 'Point 8', 10)

    for frame_name in max_y_result:
        frame_df = df[df['Frame Name'] == frame_name]
        points = frame_df.iloc[0][1:16]
        points = [ast.literal_eval(p) if pd.notna(p) and p != "None" else None for p in points]

        hip_left = points[BODY_PARTS["LHip"]]
        hip_right = points[BODY_PARTS["RHip"]]
        knee_left = points[BODY_PARTS["LKnee"]]
        knee_right = points[BODY_PARTS["RKnee"]]
        ankle_left = points[BODY_PARTS["LAnkle"]]
        ankle_right = points[BODY_PARTS["RAnkle"]]

        posture = ""
        if hip_left and hip_right and knee_left and knee_right and ankle_left and ankle_right:
            knee_angle_right = squat_calculate_angle(knee_right, hip_right, ankle_right)
            knee_angle_left = squat_calculate_angle(knee_left, hip_left, ankle_left)
            posture = "올바른 자세" if (50 <= knee_angle_left <= 90) and (50 <= knee_angle_right <= 90) else "올바르지 못한 자세"
        else:
            posture = "올바르지 못한 자세"

        df.loc[df['Frame Name'] == frame_name, 'Posture'] = posture

    save_progress(100)
    df.to_csv(output_csv_file, index=False, encoding='CP949')
    return style
