"""
ForgeMind AI
Dataset Merger

Merges multiple single-class Roboflow datasets
into one YOLO dataset.
"""

from pathlib import Path
import shutil
import yaml

ROOT = Path(__file__).resolve().parent.parent

DATASETS = ROOT / "datasets"

OUTPUT = ROOT / "merged_dataset"

CLASS_MAPPING = {
    "Pump": 0,
    "valve": 1,
    "heat exchanger detection": 2,
    "pressure gauge": 3,
}


def make_dirs():

    for split in ["train", "valid", "test"]:

        (OUTPUT / split / "images").mkdir(
            parents=True,
            exist_ok=True,
        )

        (OUTPUT / split / "labels").mkdir(
            parents=True,
            exist_ok=True,
        )


def process_dataset(dataset_name):

    class_id = CLASS_MAPPING[dataset_name]

    dataset_root = DATASETS / dataset_name

    print(f"Processing {dataset_name}")

    for split in ["train", "valid", "test"]:

        image_dir = dataset_root / split / "images"
        label_dir = dataset_root / split / "labels"

        if not image_dir.exists():
            continue

        for image_path in image_dir.iterdir():

            # Original filenames
            original_stem = image_path.stem
            original_suffix = image_path.suffix

            # New filenames
            new_stem = f"{dataset_name}_{original_stem}"

            new_image_name = f"{new_stem}{original_suffix}"

            new_label_name = f"{new_stem}.txt"

            # Copy image
            shutil.copy2(
                image_path,
                OUTPUT / split / "images" / new_image_name,
            )

            # Original label
            label_path = label_dir / f"{original_stem}.txt"

            if not label_path.exists():
                print(f"Missing label: {label_path}")
                continue

            lines = []

            with open(label_path, "r") as f:

                for line in f:

                    parts = line.strip().split()

                    if not parts:
                        continue

                    parts[0] = str(class_id)

                    lines.append(" ".join(parts))

            with open(
                OUTPUT / split / "labels" / new_label_name,
                "w",
            ) as f:

                f.write("\n".join(lines))


def create_yaml():

    yaml_data = {

        "path": str(OUTPUT),

        "train": "train/images",

        "val": "valid/images",

        "test": "test/images",

        "names": {

            0: "Pump",

            1: "Valve",

            2: "HeatExchanger",

            3: "PressureGauge",

        },

    }

    with open(
        OUTPUT / "dataset.yaml",
        "w",
    ) as f:

        yaml.dump(
            yaml_data,
            f,
            sort_keys=False,
        )


def main():

    make_dirs()

    for dataset in CLASS_MAPPING:

        process_dataset(dataset)

    create_yaml()

    print()

    print("Dataset merged successfully.")

    print(f"Saved to: {OUTPUT}")


if __name__ == "__main__":

    main()