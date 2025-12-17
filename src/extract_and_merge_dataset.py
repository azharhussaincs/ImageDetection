import os
import shutil
import yaml
import uuid

# ================= PATHS =================
SOURCE_ROOT = r"C:\Users\asdf\Downloads\Documents\extracted"
DEST_ROOT = r"C:\Users\asdf\Downloads\vehicle_dataset_clean"

# ================= WINDOWS LONG PATH =================
def win_path(p):
    return r"\\?\\" + os.path.abspath(p)

# ================= CLASS NORMALIZATION =================
CLASS_MAP = {
    # people
    "person": "person",
    "Person": "person",
    "human": "person",
    "soldier": "soldier",
    "SOLDIER": "soldier",

    # cars & trucks
    "car": "car",
    "Car": "car",
    "civilian_car": "car",
    "camping car": "car",

    "truck": "truck",
    "TRUCK": "truck",
    "pickup": "pickup",
    "van": "van",

    # military trucks
    "army-truck": "military_truck",
    "military_truck": "military_truck",

    # armored vehicles
    "Armored_car": "armored_vehicle",
    "armored_car": "armored_vehicle",
    "amoured-vehicle": "armored_vehicle",
    "apc": "armored_vehicle",
    "BMP": "armored_vehicle",
    "VBCI": "armored_vehicle",
    "VBL": "armored_vehicle",
    "command-vehicle": "armored_vehicle",
    "engineer-vehicle": "armored_vehicle",

    # tanks & artillery
    "tank": "tank",
    "Tank": "tank",
    "military_tank": "tank",
    "MBT": "tank",

    "artillery": "artillery",
    "ARTILLERY": "artillery",
    "artillery-gun": "artillery",
    "RSZO": "rocket_artillery",
    "LRM": "rocket_artillery",
    "rocket-artillery": "rocket_artillery",

    # air
    "Plane": "military_aircraft",
    "civilian_aircraft": "military_aircraft",
    "military_aircraft": "military_aircraft",
    "military_helicopter": "military_helicopter",
    "UAV": "uav",

    # others
    "boat": "boat",
    "building": "building",
    "man-made construction": "building",
    "EXPLOSION": "explosion",
    "GUN": "weapon",
    "HELMET": "weapon",
    "vehicle": "unknown",
    "UNKNOWN": "unknown",
    "other": "unknown",
}

# ================= CREATE OUTPUT STRUCTURE =================
for s in ["train", "val", "test"]:
    os.makedirs(os.path.join(DEST_ROOT, "images", s), exist_ok=True)
    os.makedirs(os.path.join(DEST_ROOT, "labels", s), exist_ok=True)

# ================= GLOBAL CLASS LIST =================
global_classes = []

def get_class_id(name):
    if name not in global_classes:
        global_classes.append(name)
    return global_classes.index(name)

# ================= MERGE DATASETS =================
total = 0

for dataset in os.listdir(SOURCE_ROOT):
    ds_path = os.path.join(SOURCE_ROOT, dataset)
    yaml_path = os.path.join(ds_path, "data.yaml")

    if not os.path.isfile(yaml_path):
        continue

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    names = data.get("names", [])

    # Skip broken numeric-only datasets
    if all(str(n).isdigit() for n in names):
        continue

    for split in ["train", "valid", "test"]:
        img_src = os.path.join(ds_path, split, "images")
        lbl_src = os.path.join(ds_path, split, "labels")

        if not os.path.exists(img_src):
            continue

        out_split = "val" if split == "valid" else split
        img_dst = os.path.join(DEST_ROOT, "images", out_split)
        lbl_dst = os.path.join(DEST_ROOT, "labels", out_split)

        os.makedirs(img_dst, exist_ok=True)
        os.makedirs(lbl_dst, exist_ok=True)

        for img in os.listdir(img_src):
            if not img.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            lbl = os.path.splitext(img)[0] + ".txt"
            src_lbl = os.path.join(lbl_src, lbl)

            if not os.path.exists(src_lbl):
                continue

            uid = uuid.uuid4().hex[:8]
            img_ext = os.path.splitext(img)[1]

            new_img = f"{uid}{img_ext}"
            new_lbl = f"{uid}.txt"

            # copy image
            shutil.copy(
                win_path(os.path.join(img_src, img)),
                win_path(os.path.join(img_dst, new_img))
            )

            # remap labels
            new_lines = []
            with open(src_lbl, "r") as lf:
                for line in lf:
                    parts = line.strip().split()
                    if len(parts) < 5:
                        continue

                    cls_name = names[int(parts[0])]
                    norm_name = CLASS_MAP.get(cls_name)

                    if norm_name is None:
                        continue

                    new_id = get_class_id(norm_name)
                    parts[0] = str(new_id)
                    new_lines.append(" ".join(parts))

            with open(win_path(os.path.join(lbl_dst, new_lbl)), "w") as out:
                out.write("\n".join(new_lines))

            total += 1

print("✅ Total merged samples:", total)
print("✅ Final classes:", global_classes)

# ================= WRITE FINAL YAML =================
final_yaml = {
    "path": DEST_ROOT.replace("\\", "/"),
    "train": "images/train",
    "val": "images/val",
    "test": "images/test",
    "nc": len(global_classes),
    "names": global_classes
}

with open(os.path.join(DEST_ROOT, "data.yaml"), "w") as f:
    yaml.dump(final_yaml, f, sort_keys=False)

print("🎉 FINAL DATASET READY")
print("📁 Location:", DEST_ROOT)
