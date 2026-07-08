"""
ForgeMind AI
YOLO11 Training Script

Author: ForgeMind AI

Supports:
- Apple Silicon (MPS)
- NVIDIA CUDA
- CPU
- Resume Training
- Automatic Dataset Detection
"""

from pathlib import Path
import argparse
import torch
from ultralytics import YOLO

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = CURRENT_DIR.parent

DATASET_YAML = PROJECT_ROOT / "merged_dataset" / "dataset.yaml"

RUNS_DIR = PROJECT_ROOT / "runs"

WEIGHTS_DIR = PROJECT_ROOT / "weights"

WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Arguments
# ---------------------------------------------------------


def parse_arguments():

    parser = argparse.ArgumentParser(
        description="ForgeMind AI Training"
    )

    parser.add_argument(
        "--model",
        default="yolo11n.pt",
        type=str,
        help="YOLO model"
    )

    parser.add_argument(
        "--data",
        default=str(DATASET_YAML),
        type=str,
        help="Dataset YAML"
    )

    parser.add_argument(
        "--epochs",
        default=100,
        type=int,
    )

    parser.add_argument(
        "--imgsz",
        default=640,
        type=int,
    )

    parser.add_argument(
        "--batch",
        default=8,
        type=int,
    )

    parser.add_argument(
        "--workers",
        default=8,
        type=int,
    )

    parser.add_argument(
        "--device",
        default="auto",
        type=str,
        help="auto | mps | cpu | cuda"
    )

    parser.add_argument(
        "--project",
        default=str(RUNS_DIR),
        type=str,
    )

    parser.add_argument(
        "--name",
        default="industrial_detector",
        type=str,
    )

    parser.add_argument(
        "--patience",
        default=25,
        type=int,
    )

    parser.add_argument(
        "--resume",
        action="store_true",
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Device
# ---------------------------------------------------------


def get_device(device):

    if device != "auto":
        return device

    if torch.backends.mps.is_available():
        return "mps"

    if torch.cuda.is_available():
        return "0"

    return "cpu"


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------


def main():

    args = parse_arguments()

    device = get_device(args.device)

    print("=" * 60)
    print("ForgeMind AI")
    print("=" * 60)
    print(f"Device      : {device}")
    print(f"Model       : {args.model}")
    print(f"Dataset     : {args.data}")
    print(f"Epochs      : {args.epochs}")
    print(f"Image Size  : {args.imgsz}")
    print(f"Batch Size  : {args.batch}")
    print("=" * 60)

    if not Path(args.data).exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{args.data}"
        )

    model = YOLO(args.model)

    results = model.train(

        data=args.data,

        epochs=args.epochs,

        imgsz=args.imgsz,

        batch=args.batch,

        workers=args.workers,

        device=device,

        project=args.project,

        name=args.name,

        patience=args.patience,

        resume=args.resume,

        cache=True,

        pretrained=True,

        save=True,

        save_period=10,

        plots=True,

        verbose=True,

        amp=True,

        val=True,

    )

    print("\nTraining Finished.\n")

    best = (
        RUNS_DIR /
        args.name /
        "weights" /
        "best.pt"
    )

    if best.exists():

        destination = WEIGHTS_DIR / "best.pt"

        destination.write_bytes(best.read_bytes())

        print(f"Best model copied to:\n{destination}")

    else:

        print("Warning: best.pt not found.")


# ---------------------------------------------------------

if __name__ == "__main__":

    main()