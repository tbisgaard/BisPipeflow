from BisPipeflow import fluid_flow

def get_substance(name: str) -> fluid_flow.Substance:
    if name not in SUBSTANCE_DB:
        raise ValueError(f"Unknown component: {name}")
    return fluid_flow.Substance(name, SUBSTANCE_DB[name])

def water_density(temperature, pressure):
    return 1000 - 0.3 * (temperature - 273.15)  # very rough

def water_viscosity(temperature, pressure):
    return 1e-3 * (1 - 0.02 * (temperature - 293.15))

def oil_density(temperature, pressure):
    return 850 - 0.5 * (temperature - 273.15)

def oil_viscosity(temperature, pressure):
    return 5e-3 * (1 - 0.03 * (temperature - 293.15))


SUBSTANCE_DB = {
    "water": {
        "density": water_density,
        "viscosity": water_viscosity,
    },
    "oil": {
        "density": oil_density,
        "viscosity": oil_viscosity,
    },
}