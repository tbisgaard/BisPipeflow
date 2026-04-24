"""
Flowsheet contains the the overall system
"""
from BisPipeflow import fluid_flow
from BisPipeflow import components
from BisPipeflow import solver
from BisPipeflow import global_parameters


class Flowsheet:
    """
    Flowsheet - controls execution
    """
    def __init__(self, name: str):
        self.id_tag = name
        self.components: list["components.Component"] = []
        self.streams: list["fluid_flow.Stream"] = []
        self.media = None

    def add_unit(self, component: "components.Component"):
        self.components.append(component)
    
    def add_stream(self, stream: "fluid_flow.Stream"):
        # If media is specified in flowsheet, propagate to streams
        if self.media is None:
            print('WARNING No media is defined.')
        else:
            stream.mixture = self.media
        self.streams.append(stream)
    
    def set_media(self, media: "fluid_flow.Mixture"):
        if self.media is not None:
            print('Media has been overwritten.')
        self.media = media

        # Automatically propagate media to streams
        for stream in self.streams:
            stream.mixture = media
    
    @property
    def degrees_of_freedom(self):
        dof = 0
        for stream in self.streams:
            dof += stream.num_variables
        for unit in self.components:
            dof -= unit.num_equations
        return dof

    def _propagate_known_values(self):
        """
        Propagate know values to all streams in flowsheet.
        """
        changed = False

        attrs = ["pressure", "flowrate", "temperature"]
        known_values = {}

        for attr in attrs:
            for unit in self.components:
                value = getattr(unit, attr, None)

                if value is not None:  # and value != 0
                    known_values[attr] = value
                    break

        for stream in self.streams:
            for attr, value in known_values.items():
                current = getattr(stream, attr, None)

                if current is None:  # or current == 0
                    setattr(stream, attr, value)
                    changed = True

        return changed
    
    def _enforce_directional_pressure(self, delta_p=1e5):
        """
        Enforce pressure diffence for predefined flow directions
        delta_p = default pressure drop (Pa)
        """
        changed = False

        for unit in self.components:

            if not getattr(unit, "is_directional", False):
                continue

            if getattr(unit, "is_pump", False):
                continue

            unit_pressure = getattr(unit, "pressure", None)

            if unit_pressure is None or unit_pressure == 0:
                continue

            if hasattr(unit, "inlet_streams"):
                for stream in unit.inlet_streams:
                    upstream = getattr(stream, "source", None)

                    if upstream is None:
                        continue

                    required_pressure = unit_pressure + delta_p
                    current_pressure = getattr(upstream, "pressure", 0)

                    if current_pressure < required_pressure:
                        upstream.pressure = required_pressure
                        changed = True

        return changed
    
    def set_initial_state_all(self, pressure=None, temperature=None, flowrate=None):
        for stream in self.streams:
            if pressure is not None:
                stream.pressure = pressure
            else:
                stream.pressure = global_parameters.SCALING_PRESSURE * 2
            if temperature is not None:
                stream.temperature = temperature
            else:
                stream.temperature = global_parameters.SCALING_TEMPERATURE * 2
            if flowrate is not None:
                stream.flowrate = flowrate
            else:
                stream.flowrate = global_parameters.SCALING_FLOWRATE * 2

    def initialise(self, changed=True):
        changed = True

        while changed:
            changed = False

            changed |= self._propagate_known_values()
            changed |= self._enforce_directional_pressure()


    def solve(self):
        solver.solve(self)





#     def _get_dependencies(self):
#         deps = {comp: set() for comp in self.components}

#         for comp in self.components:
#             for port in comp.inlets:
#                 if port.connected_port:
#                     upstream = port.connected_port.owner
#                     deps[comp].add(upstream)

#         return deps

#     def _topological_sort(self):
#         deps = self._get_dependencies()

#         resolved = set()
#         order = []

#         while len(order) < len(self.components):
#             progress = False

#             for comp in self.components:
#                 if comp in resolved:
#                     continue

#                 if all(d in resolved for d in deps[comp]):
#                     order.append(comp)
#                     resolved.add(comp)
#                     progress = True

#             if not progress:
#                 raise RuntimeError("Cycle detected (recycle loop not supported yet)")

#         return order

#     # def analyse(self):
#     #     """
#     #     Step through connections to build incidence matrix
#     #     """
#     #     unknowns = 4 * len(self.units)
#     #     equations = 2 * len(self.units) + 2 * len(self.streams) + len(self.constraints)
#     #     degrees_of_freedom = unknowns - equations

#     #     if degrees_of_freedom==0:
#     #         print('Ready to solve!')
#     #     elif degrees_of_freedom<0:
#     #         print(f'Error! The system is overdetermined! Relax {-degrees_of_freedom} constraints.')
#     #     else:
#     #         print(f'Error! The system is underdetermined! Include {degrees_of_freedom} additional constraints.')
        


#     def solve(self):
#         order = self._topological_sort()

#         for comp in order:
#             comp.solve()
#         """
#         # System:
#         tolerance = 1e-3
#         max_iter = 50
#         alpha = 0.5  # relaxation factor
#         for iteration in range(max_iter):
#             old_recycle_flow = recycle.flow

#             # Solve units sequentially
#             pump.solve()
#             tank.solve()
#             mixer.solve()

#             # Update recycle with relaxation
#             recycle.flow = alpha * tank.outlets[0].flow + (1 - alpha) * old_recycle_flow

#             error = abs(recycle.flow - old_recycle_flow)
#             print(f"Iter {iteration+1}: Recycle Flow = {recycle.flow:.3f}, Error = {error:.6f}")
#             if error < tolerance:
#                 print("Converged!")
#                 break
#         """



# # def insert_pipe(stream, diameter, length):
# #     pipe = LineSegment("auto_pipe", diameter, length)

# #     u1, u2 = stream.connected_units

# #     # disconnect old stream
# #     u1.streams.remove(stream)
# #     u2.streams.remove(stream)

# #     # create two new streams
# #     s_in = Stream(stream.name + "_in")
# #     s_out = Stream(stream.name + "_out")

# #     # reconnect
# #     u1.connect(s_in)
# #     pipe.connect(s_in)

# #     pipe.connect(s_out)
# #     u2.connect(s_out)

# #     return pipe


class IncidenceMatrix:
    def __init__(self):
        self.matrix = None
        self.row_objects = None
        self.col_objects = None
        self.row_provenance = None
        self.reduction_history = None


        # variable_index = {
        #     "V1": 0,
        #     "V2": 1,
        #     "V3": 2,
        #     "V4": 3
        # }

        # equation_index = {
        #     "E1": 0,
        #     "E2": 1,
        #     "S1": 2,
        #     "S2": 3
        # }
        # index_to_variable = {
        #     0: variable_obj_V1,
        #     1: variable_obj_V2,
        #     2: variable_obj_V3,
        #     3: variable_obj_V4
        # }

        # index_to_equation = {
        #     0: equation_obj_E1,
        #     1: equation_obj_E2,
        #     2: stream_obj_S1,
        #     3: stream_obj_S2
        # }
        # A = np.array([
        #     [1, 1, 0, 0],
        #     [0, 1, 1, 0],
        #     [1, 0, 0, 1],
        #     [0, 0, 1, 1]
        # ], dtype=float)

        # I = np.eye(A.shape[0])

        # aug = np.hstack([A, I])

