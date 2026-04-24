from dataclasses import dataclass
from typing import Optional

@dataclass#(frozen=True)
class Material:
    name: str
    surface_roughness: float   # absolute roughness in meters
    notes: str
    source: str

    @classmethod
    def custom(
        cls,
        name: str,
        surface_roughness: float,
        notes: str = ""
    ):
        return cls(
            name=name,
            surface_roughness=surface_roughness,
            notes=notes,
            source="User Defined"
        )

@dataclass#(frozen=True)
class LineSize:
    designation: str              # "2 in", "DN50", "1.5 in BPE"
    standard: str                 # "ASME B36.10", "ASME BPE"
    nps_in: Optional[str]
    dn_mm: Optional[int]
    od_mm: float
    wall_thickness_mm: float
    schedule: Optional[str] = None   # only for schedule pipe
    source: str = ""

    @property
    def diameter_inner(self) -> float:
        return self.od_mm / 1000 - 2 * self.wall_thickness_mm / 1000

    @classmethod
    def custom_from_id(
        cls,
        id_mm: float,
        designation: str = "Custom ID Line"
    ):
        return cls(
            designation=designation,
            standard="Custom",
            nps_in=None,
            dn_mm=None,
            od_mm=id_mm,
            wall_thickness_mm=0.0,
            schedule=None,
            source="Custom"
        )
