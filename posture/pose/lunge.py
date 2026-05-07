import os
import cv2
import csv
import math
import ast
import shutil
import pandas as pd

from .utils import video_div, save_progress


def lunge_calculate_angle(point_a, point_b, point_c):
    vector_ab = (point_b[0] - point_a[0], point_b[1] - point_a[1])
    vector_bc = (point_c[0] - point_b[0], point_c[1] - point_b[1])
    magnitude_ab = math.sqrt(vector_ab[0]**2 + vector_ab[1]**2)
    magnitude_bc = math.sqrt(vector_bc[0]**2 + vector_bc[1]**2)
    dot_product = vector_ab[0] * vector_bc[0] + vector_ab[1] * vector_bc[1]
    cosine_theta = dot_product / (magnitude_ab * magnitude_bc)
    angle_rad = math.acos(cosine_theta)
    angle_deg = math.degrees(angle_rad)
    return 180 - angle_deg


def detect_front_leg(Lhip_point, Rhip_point):
    if Lhip_point[1] < Rhip_point[1]:
        return "left"
    else:
        return "right"


def lunge_get_y_value(coord_str):
    if pd.isna(coord_str) or coord_str == "None":
        return math.nan
    coord_tuple = ast.literal_eval(coord_str)
    return coord_tuple[1]


def lunge_find_max_y_frames(df, column_name, num):
    y_values = []
    frame_names = []
    for index, row in df.iterrows():
        y_value = lunge_get_y_value(row[column_name])
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


BODY_PARTS_BODY_25 = {
    0: "Nose", 1: "Neck", 2: "RShoulder", 3: "RElbow", 4: "RWrist",
    5: "LShoulder", 6: "LElbow", 7: "LWrist", 8: "MidHip", 9: "RHip",
    10: "RKnee", 11: "RAnkle", 12: "LHip", 13: "LKnee", 14: "LAnkle",
    15: "REye", 16: "LEye", 17: "REar", 18: "LEar", 19: "LBigToe",
    20: "LSmallToe", 21: "LHeel", 22: "RBigToe", 23: "RSmallToe", 24: "RHeel", 25: "Background"
}

POSE_PAIRS_BODY_25 = [
    [0, 1], [0, 15], [0, 16], [1, 2], [1, 5], [1, 8], [8, 9], [8, 12],
    [9, 10], [12, 13], [2, 3], [3, 4], [5, 6], [6, 7], [10, 11], [13, 14],
    [15, 17], [16, 18], [14, 21], [19, 21], [20, 21], [11, 24], [22, 24], [23, 24]
]


def lunge_tool(request):
    save_progress(0)
    folder_path = "media"
    style = 'lunge'
    request.session['style'] = style

    output_folder = "frame_split/lunge/lunge_co"
    image_output_folder = "frame_split/lunge/lungeimage"
    output_csv_file_folder = "frame_split/lunge/lunge_co"

    for folder in [output_folder, image_output_folder, output_csv_file_folder]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    video_div(style, folder_path, output_folder)

    net = cv2.dnn.readNetFromCaffe("pose_deploy.prototxt", "pose_iter_584000.caffemodel")

    output_csv_file = "frame_point/lunge/lunge_co/all_points.csv"
    os.makedirs(os.path.dirname(output_csv_file), exist_ok=True)

    folder_path = "frame_split/lunge/lunge_co"
    file_list = os.listdir(folder_path)
    image_paths = [os.path.join(folder_path, f) for f in file_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    if os.path.exists(output_csv_file):
        os.remove(output_csv_file)

    with open(output_csv_file, "w", newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([
            "Frame Name", "Point 0", "Point 1", "Point 2", "Point 3", "Point 4",
            "Point 5", "Point 6", "Point 7", "Point 8", "Point 9", "Point 10",
            "Point 11", "Point 12", "Point 13", "Point 14", "Point 15", "Point 16",
            "Point 17", "Point 18", "Point 19", "Point 20", "Point 21", "Point 22",
            "Point 23", "Point 24", "Point 25", "knee_angle_left", "knee_angle_right"
        ])

        for idx, image_path in enumerate(image_paths):
            points = []
            frame_name = os.path.basename(image_path)
            image = cv2.imread(image_path)
            image_height, image_width, _ = image.shape

            input_blob = cv2.dnn.blobFromImage(image, 1.0 / 255, (image_width, image_height), (0, 0, 0), swapRB=False, crop=False)
            net.setInput(input_blob)
            output = net.forward()

            for i in range(len(BODY_PARTS_BODY_25)):
                prob_map = output[0, i, :, :]
                min_val, prob, min_loc, point = cv2.minMaxLoc(prob_map)
                x = (image_width * point[0]) / output.shape[3]
                y = (image_height * point[1]) / output.shape[2]
                points.append((int(x), int(y)) if prob > 0.2 else None)

            Rknee_point = points[10]
            Lknee_point = points[13]
            Rankle_point = points[11]
            Lankle_point = points[14]
            Rhip_point = points[9]
            Lhip_point = points[12]

            if Rknee_point and Lknee_point and Rankle_point and Lankle_point and Rhip_point and Lhip_point:
                knee_angle_left = lunge_calculate_angle(Lankle_point, Lknee_point, Lhip_point)
                knee_angle_right = lunge_calculate_angle(Rankle_point, Rknee_point, Rhip_point)
                csvwriter.writerow([frame_name] + points + [knee_angle_left, knee_angle_right])

            for pair in POSE_PAIRS_BODY_25:
                if points[pair[0]] and points[pair[1]]:
                    cv2.line(image, points[pair[0]], points[pair[1]], (0, 255, 0), 2)

            save_path = os.path.join(image_output_folder, os.path.splitext(frame_name)[0] + '_image.jpg')
            save_progress(10 + (idx / len(image_paths)) * 40)
            cv2.imwrite(save_path, image)

    save_progress(99)

    df = pd.read_csv(output_csv_file, encoding='CP949')
    max_y_result = lunge_find_max_y_frames(df, 'Point 8', 5)

    for frame_name in max_y_result:
        frame_df = df[df['Frame Name'] == frame_name]
        points = frame_df.iloc[0][1:16]
        points = [ast.literal_eval(p) if pd.notna(p) and p != "None" else None for p in points]

        Rknee_point = points[10]
        Lknee_point = points[13]
        Rankle_point = points[11]
        Lankle_point = points[14]
        Rhip_point = points[9]
        Lhip_point = points[12]

        posture = ""
        if Rknee_point and Lknee_point and Rankle_point and Lankle_point and Rhip_point and Lhip_point:
            knee_angle_left = lunge_calculate_angle(Lankle_point, Lknee_point, Lhip_point)
            knee_angle_right = lunge_calculate_angle(Rankle_point, Rknee_point, Rhip_point)
            if detect_front_leg(Lhip_point, Rhip_point) == "left":
                posture = "올바른 자세" if 80 <= knee_angle_left <= 100 else "올바르지 못한 자세"
            else:
                posture = "올바른 자세" if 80 <= knee_angle_right <= 100 else "올바르지 못한 자세"
        else:
            posture = "올바르지 못한 자세"

        df.loc[df['Frame Name'] == frame_name, 'front'] = detect_front_leg(Lhip_point, Rhip_point)
        df.loc[df['Frame Name'] == frame_name, 'Posture'] = posture

    save_progress(100)
    df.to_csv(output_csv_file, index=False, encoding='cp949')
    return style
