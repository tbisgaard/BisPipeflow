"""
Utility functions
"""
import math

def compute_reynolds_number(velocity, diameter_hydraulic, density, viscosity):
    """
    Compute Reynold's number.
    """
    return velocity * diameter_hydraulic * density / viscosity

def _compute_fanning_friction_factor_turbulent(reynolds_number, roughness, diameter):
    """
    Helper function to compute Fanning's friction factor for turbulent flow.
    Round, Can. J. Chem. Eng. 58, 122 (1980)
    """
    # Schacham, Znd. Eng. Chem. Fundam. 19(5), 228 (1980).
    # term1 = roughness / 3.7 / diameter
    # f = (-0.8686 * math.log(term1 - 2.1802 * math.log(term1 + 14.5 / reynolds_number)))**(-2)
    
    f = 1.6364 * (math.log(0.135 * roughness / diameter + 6.5 / reynolds_number))**(-2)
    return f

def _compute_fanning_friction_factor_laminar(reynolds_number):
    """
    Helper function to compute Fanning's friction factor for laminar flow.
    """
    return 64 / reynolds_number

def compute_fanning_friction_factor(reynolds_number, roughness=None, diameter=None):
    """
    Compute Fanning's friction factor.
    """
    # Turbulent flow regime
    if reynolds_number>=2100:
        if roughness is None or diameter is None:
            raise ValueError("Missing roughness and diameter input.")
        else:
            f = _compute_fanning_friction_factor_turbulent(reynolds_number, roughness, diameter)
    
    # Laminar flow regime
    else:
        f = _compute_fanning_friction_factor_laminar(reynolds_number)
    return f

def compute_pressure_drop(surface_roughness, velocity, diameter, length, density, viscosity, length_over_diameter_fittings):
        """
        Compute pressure drop based on Darcy-Weisbach in circular pipes.
        """
        # Darcy_weisbach
        reynolds_number = compute_reynolds_number(velocity, diameter, density, viscosity)
        f = compute_fanning_friction_factor(reynolds_number, surface_roughness, diameter)
        return f * (length/diameter + length_over_diameter_fittings) * 0.5 * density * velocity**2 / 9.81
