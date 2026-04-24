from BisPipeflow import fluid_flow

def get_substance(name: str) -> fluid_flow.Substance:
    name_lower = name.lower()
    if name_lower not in SUBSTANCE_DB:
        raise ValueError(f"Unknown component: {name}")
    return fluid_flow.Substance(name, SUBSTANCE_DB[name_lower])

def water_density(temperature, pressure):
    return 1000 - 0.3 * (temperature - 273.15)  # very rough

def water_viscosity(temperature, pressure):
    return 1e-3 * (1 - 0.02 * (temperature - 293.15))

def oil_density(temperature, pressure):
    return 850 - 0.5 * (temperature - 273.15)

def oil_viscosity(temperature, pressure):
    return 5e-3 * (1 - 0.03 * (temperature - 293.15))

# Lower case only
SUBSTANCE_DB = {
    "water": {
        "density": water_density,
        "viscosity": water_viscosity,
        "heat_capacity": 4184,
        "enthalpy_formation": -1.587e7
    },
    "oil": {
        "density": oil_density,
        "viscosity": oil_viscosity,
        "heat_capacity": 2000,
        "enthalpy_formation": -2.2e6
    },
}