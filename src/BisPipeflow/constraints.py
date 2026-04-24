"""Controller"""

class Constraint:
    def __init__(self, varriable: str, value: float):
        self.variable = varriable        # "pressure", "temperature", "flowrate"
        self.value = value

class EqualityConstraint:
    def __init__(self, stream1, stream2, variable):
        self.stream1 = stream1
        self.stream2 = stream2
        self.variable = variable