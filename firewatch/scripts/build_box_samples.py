"""Build the offline box benchmark from the original FURG videos and XML files."""
import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import cv2
import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "research/public-furg"
DEST = PROJECT / "app/static/furg"
REVISION = "6aff09d7baa27425f31d1df685284c26cbffe7af"
VIDEOS = [
    ("Car1", "validation", "车辆起火"),
    ("non_fire_patrolbot_onboard", "validation", "巡检机器人"),
    ("house6", "test", "建筑起火"),
    ("cleaner", "test", "室内清洁"),
]


def add_file(archive, name, data):
    entry = zipfile.ZipInfo(name)
    archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED)


def build():
    DEST.mkdir(parents=True, exist_ok=True)
    manifest = dict(version=1, target_class=0, images=[])
    catalog = dict(source=f"https://github.com/steffensbola/furg-fire-dataset/tree/{REVISION}",
                   license="CC0-1.0", videos=[], examples=[])
    with zipfile.ZipFile(DEST / "furg-boxes.zip", "w") as archive:
        for name, split, title in VIDEOS:
            video, xml = (SOURCE / f"{name}.{ext}" for ext in ("mp4", "xml"))
            root = ElementTree.parse(xml).getroot()
            labels = {int(node.findtext("frameNumber")):
                      [list(map(int, box.text.split())) for box in node.find("annotations")]
                      for node in root.find("frames")}
            capture = cv2.VideoCapture(str(video))
            try:
                total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
                ids = np.linspace(0, total - 1, 8, dtype=int)
                for i, frame_id in enumerate(ids):
                    capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_id))
                    ok, frame = capture.read()
                    if not ok or frame.shape[:2] != tuple(int(root.findtext(f"frame{v}")) for v in ("Height", "Width")):
                        raise ValueError(f"Cannot match frame dimensions for {name}/{frame_id}")
                    boxes = labels[int(frame_id)]
                    stem = f"{name}-{frame_id:05d}"
                    filename = stem + ".jpg"
                    ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 91])
                    if not ok:
                        raise ValueError(f"Cannot encode {stem}")
                    add_file(archive, filename, jpeg.tobytes())
                    manifest["images"].append(dict(id=stem, file=filename, group=name, split=split, boxes=boxes))
                    if i == 3:
                        (DEST / filename).write_bytes(jpeg.tobytes())
                        catalog["examples"].append(dict(title=title, file=filename, frame=int(frame_id),
                                                        group=name, boxes=boxes))
            finally:
                capture.release()
            catalog["videos"].append(dict(group=name, split=split,
                video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),
                xml_sha256=hashlib.sha256(xml.read_bytes()).hexdigest()))
        add_file(archive, "manifest.json", json.dumps(manifest).encode())
    (DEST / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    (DEST / "LICENSE.txt").write_bytes((SOURCE / "LICENSE").read_bytes())


if __name__ == "__main__":
    build()
