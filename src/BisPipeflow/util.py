"""
Utility functions
"""
import numpy as np

def compute_reynolds_number(velocity, diameter_hydraulic, density, viscosity):
    return velocity * diameter_hydraulic * density / viscosity

def compute_fanning_friction_factor_turbulent(reynolds_number, roughness, diameter):
    """
    Schacham, Znd. Eng. Chem. Fundam. 19(5), 228 (1980).
    """
    term1 = roughness / 3.7 / diameter
    f = (-0.8686 * np.log(term1 - 2.1802 * np.log(term1 + 14.5 / reynolds_number)))**(-2)
    return f

def compute_fanning_friction_factor_laminar(reynolds_number):
    return 64 / reynolds_number

def compute_fanning_friction_factor(reynolds_number, roughness=None, diameter=None):
    # Turbulent flow regime
    if reynolds_number>=2100:
        if roughness is None or diameter is None:
            raise ValueError("Missing roughness and diameter input.")
        else:
            f = compute_fanning_friction_factor_turbulent(reynolds_number, roughness, diameter)
    
    # Laminar flow regime
    else:
        f = compute_fanning_friction_factor_laminar(reynolds_number)
    return f

def compute_pressure_drop(roughness, velocity, diameter, length, density, viscosity, length_over_diameter_fittings):
        # Darcy_weisbach
        reynolds_number = compute_reynolds_number(velocity, diameter, density, viscosity)
        f = compute_fanning_friction_factor(reynolds_number, roughness, diameter)
        return f * (length/diameter + length_over_diameter_fittings) * 0.5 * density * velocity**2
