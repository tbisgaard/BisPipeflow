import csv
from pathlib import Path
from BisPipeflow import auxiliary
from typing import Optional


def _optional_str(value: str) -> Optional[str]:
    value = value.strip()
    return value if value else None


def _optional_int(value: str) -> Optional[int]:
    value = value.strip()
    return int(value) if value else None


def load_line_size(
    csv_path: str | Path,
    designation: str,
) -> auxiliary.LineSize:
    """
    Returns ONE LineSize object

    Example:
        pipe = load_line_size(
            "data/asme_b36_pipe.csv",
            "2 in Sch 40"
        )
    """
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["designation"].strip() == designation:
                return auxiliary.LineSize(
                    designation=row["designation"].strip(),
                    standard=row["standard"].strip(),
                    nps_in=_optional_str(row.get("nps_in", "")),
                    dn_mm=_optional_int(row.get("dn_mm", "")),
                    od_mm=float(row["od_mm"]),
                    wall_thickness_mm=float(row["wall_thickness_mm"]),
                    schedule=_optional_str(row.get("schedule", "")),
                    source=Path(csv_path).name,
                )

    raise ValueError(
        f"LineSize '{designation}' not found in {csv_path}"
    )


def load_material(
    csv_path: str | Path,
    name: str,
) -> auxiliary.Material:
    """
    Returns ONE Material object

    Example:
        mat = load_material(
            "data/materials.csv",
            "Carbon Steel New"
        )
    """
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["name"].strip() == name:
                return auxiliary.Material(
                    name=row["name"].strip(),
                    surface_roughness=float(row["roughness_m"]),
                    notes=_optional_str(row.get("notes", "")),
                    source=Path(csv_path).name,
                )

    raise ValueError(
        f"Material '{name}' not found in {csv_path}"
    )