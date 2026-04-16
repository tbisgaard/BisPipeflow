"""
Ye
"""
#from dataclasses import dataclass
from typing import Optional
import math
#import numpy as np
#import csv

#from BisPipeflow import components
from BisPipeflow.database import substance_db


class Substance:
    def __init__(self, name: str, data: dict):
        self.name = name
        self.data = data

    def density(self, temperature, pressure):
        return self.data["density"](temperature, pressure)

    def viscosity(self, temperature, pressure):
        return self.data["viscosity"](temperature, pressure)

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
        return sum(
            self.fractions[name] * comp.density(temperature, pressure)
            for name, comp in self.components.items()
        )

    def viscosity(self, temperature, pressure):
        return sum(
            self.fractions[name] * comp.viscosity(temperature, pressure)
            for name, comp in self.components.items()
        )

class Stream:
    """
    Streams stores temperature, pressure, flowrate, and mixture.
    Streams - carry state
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
        if self.mixture is None:
            raise ValueError("No mixture assigned to stream")
        return self.mixture.density(self.temperature, self.pressure)

    def viscosity(self):
        if self.mixture is None:
            raise ValueError("No mixture assigned to stream")
        return self.mixture.viscosity(self.temperature, self.pressure)

    def velocity(self, diameter: float):
        if self.flowrate is None:
            raise ValueError("Flowrate not defined")

        crossarea = math.pi * diameter**2 / 4
        return self.flowrate / crossarea
    
    @property
    def num_variables(self):
        """Pressure, temperature, and flowrate"""
        return 3
