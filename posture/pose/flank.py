import os
import cv2
import csv
import math
import shutil
import pandas as pd

from .utils import video_div, save_progress


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


def flank_calculate_angle(point_a, point_b, point_c):
    vector_ab = (point_b[0] - point_a[0], point_b[1] - point_a[1])
    vector_bc = (point_c[0] - point_b[0], point_c[1] - point_b[1])
    magnitude_ab = math.sqrt(vector_ab[0]**2 + vector_ab[1]**2)
    magnitude_bc = math.sqrt(vector_bc[0]**2 + vector_bc[1]**2)
    dot_product = vector_ab[0] * vector_bc[0] + vector_ab[1] * vector_bc[1]
    cosine_theta = dot_product / (magnitude_ab * magnitude_bc)
    angle_rad = math.acos(cosine_theta)
    return math.degrees(angle_rad)


def flank_tool(request):
    save_progress(10)
    folder_path = "media"
    style = 'flank'
    request.session['style'] = style

    output_folder = "frame_split/flank/flank_co"
    image_output_folder = "frame_split/flank/flankimage"
    output_csv_file_folder = "frame_point/flank/flank_co"

    for folder in [output_folder, image_output_folder, output_csv_file_folder]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    save_progress(10)
    video_div(style, folder_path, output_folder)

    net = cv2.dnn.readNetFromCaffe("pose_deploy.prototxt", "pose_iter_584000.caffemodel")

    output_csv_file = "frame_point/flank/flank_co/all_points.csv"
    os.makedirs(os.path.dirname(output_csv_file), exist_ok=True)

    folder_path = "frame_split/flank/flank_co"
    file_list = os.listdir(folder_path)
    image_paths = [os.path.join(folder_path, f) for f in file_list if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    with open(output_csv_file, "w", newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([
            "Frame Name", "Point 0", "Point 1", "Point 2", "Point 3", "Point 4",
            "Point 5", "Point 6", "Point 7", "Point 8", "Point 9", "Point 10",
            "Point 11", "Point 12", "Point 13", "Point 14", "Point 15", "Point 16",
            "Point 17", "Point 18", "Point 19", "Point 20", "Point 21", "Point 22",
            "Point 23", "Point 24", "Point 25", "knee_angle_left", "Posture"
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

            for i in range(len(BODY_PARTS_BODY_25)):
                probMap = output[0, i, :, :]
                minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)
                x = (imageWidth * point[0]) / output.shape[3]
                y = (imageHeight * point[1]) / output.shape[2]
                points.append((int(x), int(y)) if prob > 0.1 else None)

            for pair in POSE_PAIRS_BODY_25:
                if points[pair[0]] and points[pair[1]]:
                    cv2.line(image, points[pair[0]], points[pair[1]], (0, 255, 0), 2)

            save_path = os.path.join(image_output_folder, os.path.splitext(frame_name)[0] + '_image.jpg')
            cv2.imwrite(save_path, image)

            Lknee_point = points[13]
            Lshoulder_point = points[5]
            Lhip_point = points[12]

            save_progress(10 + (idx / len(image_paths)) * 80)

            if Lknee_point and Lhip_point and Lshoulder_point:
                y_shoulder = Lshoulder_point[1]
                y_hip = Lhip_point[1]
                y_knee = Lknee_point[1]
                knee_angle_left = flank_calculate_angle(Lshoulder_point, Lknee_point, Lhip_point)
                posture = "올바른 자세" if (y_shoulder <= y_hip <= y_knee and 160 <= knee_angle_left <= 180) else "올바르지 못한 자세"
                csvwriter.writerow([frame_name] + points + [knee_angle_left, posture])

    save_progress(100)
    df = pd.read_csv(output_csv_file, encoding='CP949')
    return style
