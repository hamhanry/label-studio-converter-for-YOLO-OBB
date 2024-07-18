import math
import pandas as pd
import json
import os
from tqdm import tqdm


class YOLOOBBConverter:
    def __init__(
        self,
        file_path = "",
        target_path = "/labels", #destination folder
        column_label = "label", #csh header that contains label
        column_filename = "ocr", #csv header that contains filename
    ):
        self.file_path = file_path
        self.target_path = target_path
        self.column_label = column_label
        self.column_filename = column_filename

    def rotate_point(self, x, y, angle, cx, cy):
        angle_rad = math.radians(angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)
        x_rotated = cos_angle * (x - cx) - sin_angle * (y - cy) + cx
        y_rotated = sin_angle * (x - cx) + cos_angle * (y - cy) + cy
        return x_rotated, y_rotated

    def rotate_bbox(self, left, top, right, bottom, angle):
        cx = (left) / 2
        cy = (top) / 2

        corners = [(left, top), (right, top), (right, bottom), (left, bottom)]

        rotated_corners = [self.rotate_point(x, y, angle, cx, cy) for x, y in corners]

        return rotated_corners

    def encode_label(self, label_list=[]):
        # label_list = [["aaa"], ["bbb"], ["ccc"], ["aaa"], ["ddd"], ["bbb"]] ==> flatten the list
        # label_list = ["aaa", "bbb", "ccc", "aaa", "ddd", "bbb"]
        label_list = [item for sublist in label_list for item in sublist]

        unique_labels = list(set(label_list))
        label_map = {label: i for i, label in enumerate(unique_labels)}
        encoded_labels = [label_map[label] for label in label_list]
        return encoded_labels

    def read_export_csv_label_studio(
        self,
    ):
        df = pd.read_csv(self.file_path)

        left_list = []
        top_list = []
        right_list = []
        bottom_list = []
        rotation_list = []
        label_list = []
        filename_list = []
        ori_width_list = []
        ori_height_list = []

        for idx, row in df.iterrows():
            try:
                label_dict = json.loads(row[self.column_label])
            except:
                print(f"Error in row {idx} \n {row}")

            for i in range(len(label_dict)):  # some images have multiple labels
                x = label_dict[i]["x"]
                y = label_dict[i]["y"]
                w = label_dict[i]["width"]
                h = label_dict[i]["height"]
                rotation = label_dict[i]["rotation"]
                label = label_dict[i]["labels"]
                ori_width = label_dict[i]["original_width"]
                ori_height = label_dict[i]["original_height"]
                filename = (
                    os.path.splitext(os.path.basename(row[self.column_filename]))[0]
                    + ".txt"
                )

                left = x / 100 * ori_width
                top = y / 100 * ori_height
                right = left + (w / 100 * ori_width)
                bottom = top + (h / 100 * ori_height)

                left_list.append(left)
                top_list.append(top)
                right_list.append(right)
                bottom_list.append(bottom)
                rotation_list.append(rotation)
                label_list.append(label)
                ori_width_list.append(ori_width)
                ori_height_list.append(ori_height)
                filename_list.append(filename)

        encoded_labels_list = self.encode_label(label_list)

        return (
            left_list,
            top_list,
            right_list,
            bottom_list,
            rotation_list,
            label_list,
            ori_width_list,
            ori_height_list,
            filename_list,
            encoded_labels_list,
        )

    def convert_to_obb(
        self,
        left_list,
        top_list,
        right_list,
        bottom_list,
        rotation_list,
        ori_width_list,
        ori_height_list,
    ):
        obb_list = []
        for i in range(len(left_list)):
            left = left_list[i]
            top = top_list[i]
            right = right_list[i]
            bottom = bottom_list[i]
            rotation = rotation_list[i]

            obb = self.rotate_bbox(left, top, right, bottom, rotation)
            obb = [(x / ori_width_list[i], y / ori_height_list[i]) for x, y in obb]
            obb_list.append(obb)

        return obb_list

    def write_obb_to_txt(self, obb_list, encoded_labels_list, filename_list):
        for idx, filepath in enumerate(tqdm(filename_list)):
            filepath = os.path.join(self.target_path, filepath)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, "a+") as f:
                obb = obb_list[idx]
                label = encoded_labels_list[idx]
                f.write(
                    f"{label} {obb[0][0]} {obb[0][1]} {obb[1][0]} {obb[1][1]} {obb[2][0]} {obb[2][1]} {obb[3][0]} {obb[3][1]}\n"
                )


if __name__ == "__main__":

    OBBconverter = YOLOOBBConverter(
        # file_path="/home/ham/Downloads/project-1-at-2024-07-12-11-15-980b6fe0.csv",
        file_path="/home/ham/Downloads/test.csv",
        target_path="labels",
    )
    (
        left_list,
        top_list,
        right_list,
        bottom_list,
        rotation_list,
        label_list,
        ori_width_list,
        ori_height_list,
        filename_list,
        encoded_labels_list,
    ) = OBBconverter.read_export_csv_label_studio()

    rotated_bbox = OBBconverter.convert_to_obb(
        left_list,
        top_list,
        right_list,
        bottom_list,
        rotation_list,
        ori_width_list,
        ori_height_list,
    )

    OBBconverter.write_obb_to_txt(rotated_bbox, encoded_labels_list, filename_list)
