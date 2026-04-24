"""
Features:
- tank calculate density
- fix Tee
- Q/dP relation import on fittings
- position + visuals
- 3D visuals
"""
import numpy as np
import csv
#import math

from BisPipeflow import util
from BisPipeflow import fluid_flow
from BisPipeflow import subcomponents
from BisPipeflow import auxiliary
#from BisPipeflow import constraints
from BisPipeflow.database import fitting_db
from BisPipeflow import global_parameters

class Component:
    """
    Component manipulates streams.
    Components - define physics
    """
    def __init__(self, name: str):
        self.name = name

        self.streams = []
    
    def connect(self, stream: fluid_flow.Stream):
        if stream not in self.streams:
            self.streams.append(stream)
            stream.connected_units.append(self)

class LineSegment(Component):
    """
    Component.
    Tube introduces a pressure drop.
    """
    is_directional = False
    def __init__(self, name, length, line_size: auxiliary.LineSize, material: auxiliary.Material):
        super().__init__(name)

        self.length = length
        self.line_size = line_size
        self.material = material

        self.fittings: list[subcomponents.Fitting] = []

    @property
    def length_over_diameter_fittings(self):
        return sum(fitting.length_over_diameter for fitting in self.fittings)

    def add_fitting_by_name(self, name: str):
        """
        Convenience function
        """
        fitting = fitting_db.get_fitting(name)
        self.add_fitting(fitting)

    def add_fitting(self, fitting: "subcomponents.Fitting"):
        """
        Add sub-unit
        """
        self.fittings.append(fitting)

    @property
    def num_equations(self):
        """Pressure, temperature, and flowrate"""
        return 3

    def solve(self):
        if len(self.streams) != 2:
            raise ValueError("PipeSegment must have exactly 2 streams")

        s1 = self.streams[0]
        s2 = self.streams[1]

        # only proceed if one side is known
        if s1.pressure is None and s2.pressure is None:
            return  # skip until solvable

        if s1.pressure is not None:
            upstream, downstream = s1, s2
        else:
            upstream, downstream = s2, s1

        density = upstream.mixture.density(upstream.temperature, upstream.pressure)
        viscosity = upstream.mixture.viscosity(upstream.temperature, upstream.pressure)
        velocity = upstream.velocity(self.line_size.diameter_inner)

        pressure_drop = util.compute_pressure_drop(
            self.material.surface_roughness,
            velocity,
            self.line_size.diameter_inner,
            self.length,
            density,
            viscosity,
            self.length_over_diameter_fittings
        )
        downstream.pressure = upstream.pressure - pressure_drop
        downstream.temperature = upstream.temperature
        downstream.flowrate = upstream.flowrate
        downstream.mixture = upstream.mixture
    
    def residuals(self):
        s1 = self.streams[0]
        s2 = self.streams[1]

        effective_flowrate = s1.flow_sign_for_unit(self) * s1.flowrate
        if effective_flowrate > 0:
            inlet = s1
            outlet = s2
        else:
            inlet = s2
            outlet = s1
        
        # Pressure drop calculation
        density = inlet.mixture.density(inlet.temperature, inlet.pressure)
        viscosity = inlet.mixture.viscosity(inlet.temperature, inlet.pressure)
        velocity = inlet.velocity(self.line_size.diameter_inner)
        pressure_drop = util.compute_pressure_drop(
            self.material.surface_roughness,
            abs(velocity),
            self.line_size.diameter_inner,
            self.length,
            density,
            viscosity,
            self.length_over_diameter_fittings
        )

        residuals = [
            (outlet.pressure + pressure_drop - inlet.pressure) / global_parameters.SCALING_PRESSURE,
            (outlet.temperature - inlet.temperature) / global_parameters.SCALING_TEMPERATURE,
            (outlet.flowrate - inlet.flowrate) / global_parameters.SCALING_FLOWRATE
        ]
        return residuals
    
    def apply_corrections(self, residuals, alpha):
        s1 = self.streams[0]
        s2 = self.streams[1]
        
        effective_flowrate = s1.flow_sign_for_unit(self) * s1.flowrate
        if effective_flowrate > 0:
            inlet = s1
            outlet = s2
        else:
            inlet = s2
            outlet = s1

        rP, rT, rQ = residuals
        rP *= global_parameters.SCALING_PRESSURE
        rT *= global_parameters.SCALING_TEMPERATURE
        rQ *= global_parameters.SCALING_FLOWRATE

        # --- temperature equalization ---
        dT = -alpha * rT * 0.5
        inlet.temperature -= dT
        outlet.temperature += dT

        # --- pressure (Pa) ---
        dP = -alpha * rP * 0.5
        inlet.pressure -= dP
        outlet.pressure += dP

        # --- flow ---
        dQ = -alpha * rQ * 0.5
        inlet.flowrate -= dQ
        outlet.flowrate += dQ

class Pump(Component):
    is_directional = True
    def __init__(self, name: str):
        super().__init__(name)

        self.flowrate_curve = None
        self.head_curve = None
        self.pressure_lift_curve = None

    def load_curve(self, filepath, curve_type):
        flowrate = []
        output = []

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                flowrate.append(float(row["flowrate"]))
                output.append(float(row["head"]))

        self.flowrate_curve = np.array(flowrate)
        if curve_type=='head':
            self.head_curve = np.array(output)
        elif curve_type=='pressure':
            self.pressure_lift_curve = np.array(output)

    def get_head(self, flowrate):
        if self.flowrate_curve is None:
            raise ValueError("Pump curve not loaded")

        return np.interp(flowrate, self.flowrate_curve, self.head_curve)

    @property
    def num_equations(self):
        """Equations: Pump curve and connection mass balance"""
        return 2

    def solve(self):
        if len(self.streams) != 2:
            raise ValueError("Pump must have exactly 2 streams")

        s1 = self.streams[0]
        s2 = self.streams[1]

        if s1.pressure is None and s2.pressure is None:
            return

        # infer causality from which stream already has flow info
        if s1.flowrate is not None:
            upstream, downstream = s1, s2
        else:
            upstream, downstream = s2, s1

        density = upstream.mixture.density(upstream.temperature, upstream.pressure)
        flowrate = upstream.flowrate

        head = self.get_head(flowrate)
        pressure_lift = 9.81 * density * head

        downstream.pressure = upstream.pressure + pressure_lift
        downstream.temperature = upstream.temperature
        downstream.flowrate = upstream.flowrate
        downstream.mixture = upstream.mixture

    def residuals(self):
        inlet = self.streams[0]
        outlet = self.streams[1]

        # Calculation
        density = inlet.mixture.density(inlet.temperature, inlet.pressure)
        flowrate = inlet.flowrate
        head = self.get_head(flowrate)
        pressure_lift = 9.81 * density * head

        # Residuals
        residuals = [
            (outlet.pressure - inlet.pressure + pressure_lift) / global_parameters.SCALING_PRESSURE,
            (outlet.temperature - inlet.temperature) / global_parameters.SCALING_TEMPERATURE,
            (outlet.flowrate - inlet.flowrate) / global_parameters.SCALING_FLOWRATE,
        ]
        return residuals

    def apply_corrections(self, residuals, alpha):
        inlet = self.streams[0]
        outlet = self.streams[1]

        rP, rT, rQ = residuals
        rP *= global_parameters.SCALING_PRESSURE
        rT *= global_parameters.SCALING_TEMPERATURE
        rQ *= global_parameters.SCALING_FLOWRATE

        # --- temperature equalization ---
        dT = -alpha * rT * 0.5
        inlet.temperature -= dT
        outlet.temperature += dT

        # --- pressure (Pa) ---
        dP = -alpha * rP * 0.5
        inlet.pressure -= dP
        outlet.pressure += dP

        # --- flow ---
        dQ = -alpha * rQ * 0.5
        inlet.flowrate -= dQ
        outlet.flowrate += dQ

class Tank(Component):
    is_directional = True
    def __init__(self, name, head_pressure: float=0, level: float=0):
        super().__init__(name)

        self.head_pressure = head_pressure
        self.level = level

        self.density = None
    
    @property
    def num_equations(self):
        """Pressure, temperature, flowrate"""
        return 3
     
    def solve(self):
        if len(self.streams) < 2:
            raise ValueError("Tank must have at least 2 connected streams")

        # # split streams into inlets/outlets based on pressure
        # inlets = []
        # outlets = []

        inlet = self.streams[0]
        outlet = self.streams[1]

        pressure_outlet = self.head_pressure + self.density * 9.81 * self.level

        if self.head_pressure is None:
            # simplest: headspace follows inlet
            self.head_pressure = inlet.pressure
        
        outlet.pressure = pressure_outlet
        outlet.temperature = inlet.temperature
        outlet.flowrate = inlet.flowrate
        outlet.mixture = inlet.mixture
    
    def residuals(self):
        inlet = self.streams[0]  # above liquid level
        outlet = self.streams[1]  # below liquid level

        pressure_drop_inlet = 0
        pressure_hydrostatic = self.density * 9.81 * self.level

        residuals = [
            (outlet.pressure - inlet.pressure + pressure_drop_inlet - pressure_hydrostatic) / global_parameters.SCALING_PRESSURE,
            (outlet.temperature - inlet.temperature) / global_parameters.SCALING_TEMPERATURE,
            (outlet.flowrate - inlet.flowrate) / global_parameters.SCALING_FLOWRATE
        ]
        return residuals

    def apply_corrections(self, residuals, alpha):
        inlet = self.streams[0]
        outlet = self.streams[1]

        rP, rT, rQ = residuals
        rP *= global_parameters.SCALING_PRESSURE
        rT *= global_parameters.SCALING_TEMPERATURE
        rQ *= global_parameters.SCALING_FLOWRATE

        # --- temperature equalization ---
        dT = -alpha * rT * 0.5
        inlet.temperature -= dT
        outlet.temperature += dT

        # --- pressure (Pa) ---
        dP = -alpha * rP * 0.5
        inlet.pressure -= dP
        outlet.pressure += dP

        # --- flow ---
        dQ = -alpha * rQ * 0.5
        inlet.flowrate -= dQ
        outlet.flowrate += dQ

class Source(Component):
    is_directional = False
    def __init__(self, name, pressure:float = None, temperature:float = None, flowrate:float = None):
        super().__init__(name)

        self.pressure = pressure
        self.temperature = temperature
        self.flowrate = flowrate
        # self.mixture = mixture

    @property
    def num_equations(self):
        """Constraints: """
        return sum(
            x is not None
            for x in (self.pressure, self.temperature, self.flowrate)
        )
    
    def solve(self):
        if len(self.streams) != 1:
            raise ValueError("Source must have exactly 1 stream")

        stream = self.streams[0]
        stream.pressure = self.pressure
        stream.temperature = self.temperature
        stream.flowrate = self.flowrate
        #stream.mixture = self.mixture
    
    def residuals(self):
        stream = self.streams[0]
        
        specs = [
            ("pressure", self.pressure, global_parameters.SCALING_PRESSURE),
            ("temperature", self.temperature, global_parameters.SCALING_TEMPERATURE),
            ("flowrate", self.flowrate, global_parameters.SCALING_FLOWRATE),
        ]

        residuals = [
            (getattr(stream, attr) - value) / scaling
            for attr, value, scaling in specs
            if value is not None
        ]
        return residuals
    
    def apply_corrections(self, _residuals, alpha):
        stream = self.streams[0]

        if self.pressure is not None:
            stream.pressure += alpha * (self.pressure - stream.pressure)

        if self.temperature is not None:
            stream.temperature += alpha * (self.temperature - stream.temperature)

        if self.flowrate is not None:
            stream.flowrate += alpha * (self.flowrate - stream.flowrate)

class Sink(Component):
    is_directional = False
    def __init__(self, name, pressure:float = None, temperature:float = None, flowrate:float = None):
        super().__init__(name)

        self.pressure = pressure
        self.temperature = temperature
        self.flowrate = flowrate

    @property
    def num_equations(self):
        """Constraints: """
        return sum(
            x is not None
            for x in (self.pressure, self.temperature, self.flowrate)
        )

    def solve(self):
        if len(self.streams) != 1:
            raise ValueError("Sink must have exactly 1 stream")

    def residuals(self):
        stream = self.streams[0]

        specs = [
            ("pressure", self.pressure, global_parameters.SCALING_PRESSURE),
            ("temperature", self.temperature, global_parameters.SCALING_TEMPERATURE),
            ("flowrate", self.flowrate, global_parameters.SCALING_FLOWRATE),
        ]

        residuals = [
            (getattr(stream, attr) - value) / scaling
            for attr, value, scaling in specs
            if value is not None
        ]
        return residuals

    def apply_corrections(self, _residuals, alpha):
        stream = self.streams[0]

        if self.pressure is not None:
            stream.pressure += alpha * (self.pressure - stream.pressure)

        if self.temperature is not None:
            stream.temperature += alpha * (self.temperature - stream.temperature)

        if self.flowrate is not None:
            stream.flowrate += alpha * (self.flowrate - stream.flowrate)

# class Tee(Component):
#     """Three-way"""

#     is_directional = False

#     @property
#     def num_equations(self):
#         """Constraints: Mass balance"""
#         return 3

#     def solve(self):
#         if len(self.streams) != 3:
#             raise ValueError("Tee must have exactly 3 connected streams")

#         # pick inlet as highest pressure stream
#         inlet = max(self.streams, key=lambda s: s.pressure)
#         outlets = [s for s in self.streams if s is not inlet]

#         flowrate_inlet = inlet.flowrate

#         # simple equal split
#         for s in outlets:
#             s.flowrate = flowrate_inlet / 2
#             s.pressure = inlet.pressure
#             s.temperature = inlet.temperature
#             s.mixture = inlet.mixture

#     def residuals(self):
#         s1 = self.streams[0]
#         s2 = self.streams[1]
#         s3 = self.streams[2]

#         if s1.pressure >= s2.pressure and s1.pressure >= s3.pressure:
#             inlet = s1
#             outlet1 = s2
#             outlet2 = s3
#         elif s2.pressure >= s1.pressure and s2.pressure >= s3.pressure:
#             inlet = s2
#             outlet1 = s1
#             outlet2 = s3
#         else:
#             inlet = s3
#             outlet1 = s1
#             outlet2 = s2
        

#         residuals = [
#             (outlet1.pressure - inlet.pressure) / global_parameters.SCALING_PRESSURE,
#             (outlet1.temperature - inlet.temperature) / global_parameters.SCALING_TEMPERATURE,
#             (outlet2.pressure - inlet.pressure) / global_parameters.SCALING_PRESSURE,
#             (outlet2.temperature - inlet.temperature) / global_parameters.SCALING_TEMPERATURE,
#             (outlet1.flowrate + outlet2.flowrate - inlet.flowrate) / global_parameters.SCALING_FLOWRATE,
#         ]
#         return residuals
    
#     def apply_corrections(self, residuals, alpha):
#         s1 = self.streams[0]
#         s2 = self.streams[1]
#         s3 = self.streams[2]

#         rP1, rT1, rP2, rT2, rQ = residuals
#         rP1 *= global_parameters.SCALING_PRESSURE
#         rP2 *= global_parameters.SCALING_PRESSURE
#         rT1 *= global_parameters.SCALING_TEMPERATURE
#         rT2 *= global_parameters.SCALING_TEMPERATURE
#         rQ *= global_parameters.SCALING_FLOWRATE

#         # --- temperature equalization ---
#         dT1 = -alpha * rT1 * 0.5
#         dT2 = -alpha * rT2 * 0.5

#         s1.temperature -= dT1
#         s3.temperature += dT1

#         s2.temperature -= dT2
#         s3.temperature += dT2

#         # --- pressure equalization ---
#         dP1 = -alpha * rP1 * 0.5
#         dP2 = -alpha * rP2 * 0.5

#         s1.pressure -= dP1
#         s3.pressure += dP1

#         s2.pressure -= dP2
#         s3.pressure += dP2

#         # --- mass balance ---
#         dQ = -alpha * rQ / 3.0

#         s1.flowrate -= dQ
#         s2.flowrate -= dQ
#         s3.flowrate -= dQ


class Connector(Component):
    """N-way"""

    is_directional = False

    @property
    def num_equations(self):
        """Constraints: 2 * (pressure + temperature) balances plus 1 mass balance"""
        return 2 * len(self.streams) - 1

    def residuals(self):
        residuals = []
        stream_ref = self.streams[0]
        abs_residual_flowrate = stream_ref.flow_sign_for_unit(self) * stream_ref.flowrate

        for stream in self.streams[1:]:
            abs_residual_flowrate += stream.flow_sign_for_unit(self) * stream.flowrate
            residuals.append((stream.pressure - stream_ref.pressure) / global_parameters.SCALING_PRESSURE)
            residuals.append((stream.temperature - stream_ref.temperature) / global_parameters.SCALING_TEMPERATURE)
        residuals.append(abs_residual_flowrate / global_parameters.SCALING_FLOWRATE)
        
        return residuals
    
    def apply_corrections(self, residuals, alpha):
        stream_ref = self.streams[0]

        i = 0

        # Pressure and temperature corrections
        for stream in self.streams[1:]:

            rP = residuals[i]
            rT = residuals[i + 1]
            rP *=  global_parameters.SCALING_PRESSURE
            rT *= global_parameters.SCALING_TEMPERATURE

            # pressure equalization
            dP = alpha * rP * 0.5
            stream.pressure -= dP
            stream_ref.pressure += dP

            # temperature equalization
            dT = alpha * rT * 0.5
            stream.temperature -= dT
            stream_ref.temperature += dT

            i += 2

        # Mass balance correction
        rQ = residuals[-1]
        rQ *= global_parameters.SCALING_FLOWRATE

        dQ = alpha * rQ / len(self.streams)

        for stream in self.streams:
            # correct toward mass balance
            stream.flowrate -= stream.flow_sign_for_unit(self) * dQ



class ControllerInline(Component):
    """
    Controller applied to single stream.
    """
    def __init__(self, name):
        super().__init__(name)
        self.streams = []
        self.constraints = []

    @property
    def num_equations(self):
        return len(self.constraints)

    def residuals(self):
        s = self.streams[0]   # assume single connected stream

        R = []

        for c in self.constraints:
            if c.variable == "pressure":
                R.append(s.pressure - c.value)

            elif c.variable == "temperature":
                R.append(s.temperature - c.value)

            elif c.variable == "flowrate":
                R.append(s.flowrate - c.value)

        return R

    def apply_corrections(self, R, alpha):
        s = self.streams[0]

        i = 0
        for c in self.constraints:

            r = R[i]

            if c.variable == "pressure":
                s.pressure -= alpha * r

            elif c.variable == "temperature":
                s.temperature -= alpha * r

            elif c.variable == "flowrate":
                s.flowrate -= alpha * r

            i += 1




class StreamController(Component):
    """
    Inline controller
    """
    def __init__(
        self,
        name: str,
        variable: str,
        stream1: fluid_flow.Stream,
        stream2: fluid_flow.Stream = None,
        target_value: float = None,
    ):
        super().__init__(name)

        self.variable = variable
        scaling_map = {
            "pressure": global_parameters.SCALING_PRESSURE,
            "temperature": global_parameters.SCALING_TEMPERATURE,
            "flowrate": global_parameters.SCALING_FLOWRATE,
        }
        self.scaling = scaling_map.get(variable, 1.0)
        
        self.stream1 = stream1

        # Option 1, add link of one stream to another stream
        self.stream2 = stream2

        # Option 2, specify variable on stream
        self.target_value = target_value

    @property
    def num_equations(self):
        return 1

    def residuals(self):
        value1 = getattr(self.stream1, self.variable)

        # equality constraint
        if self.stream2 is not None:
            value2 = getattr(self.stream2, self.variable)
            return [(value1 - value2) / self.scaling]

        # fixed target constraint
        elif self.target_value is not None:
            return [(value1 - self.target_value) / self.scaling]

        else:
            return []
        
    def apply_corrections(self, residuals, alpha):
        r = residuals[0]
        r *= self.scaling

        value1 = getattr(self.stream1, self.variable)

        # Equality constraint
        # stream1.variable = stream2.variable
        if self.stream2 is not None:
            value2 = getattr(self.stream2, self.variable)

            correction = alpha * r * 0.5

            setattr(self.stream1, self.variable, value1 - correction)
            setattr(self.stream2, self.variable, value2 + correction)

        # Fixed target constraint
        # stream1.variable = target_value
        elif self.target_value is not None:
            correction = alpha * r

            setattr(self.stream1, self.variable, value1 - correction)