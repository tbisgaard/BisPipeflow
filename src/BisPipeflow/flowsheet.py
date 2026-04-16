"""
Flowsheet contains the the overall system
"""
import numpy as np
from BisPipeflow import fluid_flow
from BisPipeflow import components



class Flowsheet:
    """
    Flowsheet - controls execution
    """
    def __init__(self, name: str):
        self.id_tag = name
        self.components: list["components.Component"] = []
        self.streams: list["fluid_flow.Stream"] = []

    def add_unit(self, component: "components.Component"):
        self.components.append(component)
    
    def add_stream(self, stream: "fluid_flow.Stream"):
        self.streams.append(stream)
    
    @property
    def degrees_of_freedom(self):
        dof = 0
        for stream in self.streams:
            dof += stream.num_variables
        for unit in self.components:
            dof -= unit.num_equations
        return dof
    # def propagate_mixtures(self, flowsheet, streams_from_sources):
    #     for stream in streams_from_sources:
    #         dfs = []
    #         #dfs(stream)






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
# #     pipe = PipeSegment("auto_pipe", diameter, length)

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

