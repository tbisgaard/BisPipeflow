from BisPipeflow import subcomponents

def get_fitting(name: str) -> subcomponents.Fitting:
    if name not in FITTING_DB:
        raise ValueError(f"Unknown fitting: {name}")
    return subcomponents.Fitting(name, FITTING_DB[name])

FITTING_DB = {
    "elbow_90_standard": {"length_over_diameter": 32.4},
    "elbow_90_medium": {"length_over_diameter": 27.6},
    "elbow_90_large": {"length_over_diameter": 20.4},
    "elbow_45": {"length_over_diameter": 15.6},
    "gate_valve_open": {"length_over_diameter": 7.2},
    "globe_valve_open": {"length_over_diameter": 324},
    "swing_check_open": {"length_over_diameter": 80.4},
}