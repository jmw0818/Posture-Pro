import os
import json
import cv2
import shutil
from django.conf import settings


def save_progress(progress_value):
    progress_data = {"progress": progress_value}
    json_path = os.path.join(settings.MEDIA_ROOT, "progress.json")
    with open(json_path, "w") as f:
        json.dump(progress_data, f)


def video_div(style, folder_path, output_folder):
    video_formats = ('.mp4', '.avi', '.mov')
    file_list = os.listdir(folder_path)
    video_paths = [os.path.join(folder_path, file) for file in file_list if file.lower().endswith(video_formats)]
    video_paths_with_keyword = [path for path in video_paths if style in path.lower()]

    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    for video_path in video_paths_with_keyword:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        interval = int(fps * 0.5)
        frame_index = 0
        save_time = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_index >= save_time:
                image_path = os.path.join(
                    output_folder,
                    f"{os.path.splitext(os.path.basename(video_path))[0]}_frame_{frame_index}.jpg"
                )
                cv2.imwrite(image_path, frame)
                save_time += interval
            frame_index += 1
        cap.release()
