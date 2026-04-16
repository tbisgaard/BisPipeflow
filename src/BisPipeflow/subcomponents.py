"""Subcomponents"""
class Fitting():
    """
    Sub-component used by PipeSegment
    """
    def __init__(self, name: str, data: dict):
        self.name = name
        self.length_over_diameter = data.get("length_over_diameter")
        self.const_k = data.get("K")
