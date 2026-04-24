"""
Ye
"""
#from dataclasses import dataclass
from typing import Optional
import math
#import csv

#from BisPipeflow import components
from BisPipeflow.database import substance_db


class Substance:
    """
    Pure substance properties.
    """
    def __init__(self, name: str, data: dict):
        self.name = name
        self.data = data

    def density(self, temperature, pressure):
        return self.data["density"](temperature, pressure)

    def viscosity(self, temperature, pressure):
        return self.data["viscosity"](temperature, pressure)
    
    def heat_capacity(self):
        return self.data["heat_capacity"]

    def enthalpy_formation(self):
        return self.data["enthalpy_formation"]

class Mixture:
    """
    This class keeps track of temperature dependency on density and viscosity and component.
    """
    def __init__(self, composition: dict[str, float]):
        """
        Substance: dict like {"water": 0.8, "ethanol": 0.2}
        """
        self.components = {
            name: substance_db.get_substance(name)
            for name in composition
        }
        self.fractions = composition

    def density(self, temperature, pressure):
        """
        Compute mixture density from temperature and pressure.
        """
        return sum(
            self.fractions[name] * comp.density(temperature, pressure)
            for name, comp in self.components.items()
        )

    def viscosity(self, temperature, pressure):
        """
        Compute mixture viscosity from temperature and pressure.
        """
        return sum(
            self.fractions[name] * comp.viscosity(temperature, pressure)
            for name, comp in self.components.items()
        )
    
    def heat_capacity(self):
        """
        Compute mixture heat capacity
        """
        return sum(
            self.fractions[name] * comp.heat_capacity()
            for name, comp in self.components.items()
        )
    
    def enthalpy_formation(self):
        """
        Compute mixture enthalpy of formation
        """
        return sum(
            self.fractions[name] * comp.enthalpy_formation()
            for name, comp in self.components.items()
        )

class Stream:
    """
    Streams stores temperature, pressure, flowrate, and mixture.
    Streams - carry state
    Positive direction of flow: self.connected_units[0] -> self.connected_units[1]
    """
    def __init__(self, name:str):
        self.name = name

        # Topology
        self.connected_units = []

        # state
        self.pressure: float | None = None
        self.temperature: float | None = None
        self.flowrate: float | None = None

        self.mixture: Optional["Mixture"] = None

    def density(self):
        """Density"""
        if self.mixture is None:
            raise ValueError("No mixture assigned to stream")
        return self.mixture.density(self.temperature, self.pressure)

    def viscosity(self):
        """Viscosity"""
        if self.mixture is None:
            raise ValueError("No mixture assigned to stream")
        return self.mixture.viscosity(self.temperature, self.pressure)

    def velocity(self, diameter: float):
        """Velocity"""
        if self.flowrate is None:
            raise ValueError("Flowrate not defined")

        crossarea = math.pi * diameter**2 / 4
        return self.flowrate / crossarea
    
    def flow_sign_for_unit(self, unit):
        """Sign for unit connected to stream"""
        if self.connected_units[0] == unit:
            return -1
        elif self.connected_units[1] == unit:
            return +1
        else:
            raise ValueError("Unit not connected to stream")

    @property
    def num_variables(self):
        """Pressure, temperature, and flowrate"""
        return 3

    @property
    def enthalpy(self):
        """Enthalpy of mixture"""
        return (self.mixture.enthalpy_formation()
                + self.mixture.heat_capacity() * self.temperature
        )