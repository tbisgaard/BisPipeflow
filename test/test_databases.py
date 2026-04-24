""" Test databases"""
from pathlib import Path

from BisPipeflow.database import fitting_db
from BisPipeflow.database import line_size_material_db
from BisPipeflow.database import substance_db

def test_substance_load():
    """Case insensitive loader"""
    for subs_name in ['Water', 'water', 'wAter', 'WATER']:
        substance = substance_db.get_substance(subs_name)
    assert substance is not None

def test_substance_water_property():
    """Test parsing of density"""
    substance = substance_db.get_substance('water')
    calculated = substance.density(298, 101325)
    target = 1000
    atol = 10
    assert abs(calculated - target) < atol

def test_material_load():
    """Loop through default database"""
    db_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "BisPipeflow"
        / "database"
        / "line_data"
        / "materials.csv"
    )

    material_names = [
        "316L Stainless Steel Electropolished",
        "316L Stainless Steel Mechanically Polished",
        "304 Stainless Steel",
        "Carbon Steel New",
        "Carbon Steel Aged",
        "PVC",
        "PTFE Lined Steel",
        "Copper"
    ]
    #print(f'THOMAS {str(db_path)}')
    for material_name in material_names:
        material = line_size_material_db.load_material(str(db_path), material_name)
    assert material is not None

def test_material_property_steel():
    """Test surface roughness on one steel type"""
    db_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "BisPipeflow"
        / "database"
        / "line_data"
        / "materials.csv"
    )
    material_name = '316L Stainless Steel Electropolished'
    material = line_size_material_db.load_material(str(db_path), material_name)
    calculated = material.surface_roughness
    target = 0.0000015
    atol = target * 0.01

    assert abs(calculated - target) < atol

def test_line_size_load():
    """Load one element from each of the default databases"""
    db_sets = [
        ["asme_b36_pipe.csv", "2 in Sch 40"],
        ["asme_bpe_tube.csv", "2.5 in BPE"],
        ["din_tube.csv", "DN50 DIN Tube"]
    ]
    db_path_parent = (Path(__file__).resolve().parent.parent
        / "src"
        / "BisPipeflow"
        / "database"
        / "line_data"
    )
    for db_set in db_sets:
        db_file = db_set[0]
        designation = db_set[1]

        line_size = line_size_material_db.load_line_size(
            str(db_path_parent / db_file),
            designation
        )
    assert line_size is not None

def test_fitting_load():
    fitting = 'gate_valve_open'
    assert True