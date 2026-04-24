"""
ff
"""
import numpy as np

from BisPipeflow import flowsheet
from BisPipeflow import fluid_flow
from BisPipeflow import components
from BisPipeflow import solver
from BisPipeflow import auxiliary
from BisPipeflow import util
from BisPipeflow import constraints


def case_1():
    line_size1 = auxiliary.LineSize.custom_from_id(
        id_mm=304.8,
        designation="example_6.5"
    )
    material1 = auxiliary.Material.custom(
        name="general",
        surface_roughness=0.00015,
        notes="example_6.5"
    )
    flowrate = 6000 * 3.14 * 1e-3 * line_size1.diameter_inner / 4 / 1000
    media = fluid_flow.Mixture({'water': 1})
    fs = flowsheet.Flowsheet('Test')
    s1 = fluid_flow.Stream('S1')
    s2 = fluid_flow.Stream('S2')
    source1 = components.Source('IN1', pressure=10e5, temperature=300, flowrate=flowrate)
    sink1 = components.Sink('OUT1')
    line1 = components.LineSegment('T1', 304.8, line_size1, material1)
    for _ in range(6):
        line1.add_fitting_by_name('elbow_90_large')
    for _ in range(4):
        line1.add_fitting_by_name('tee_branched')
    for _ in range(2):
        line1.add_fitting_by_name('gate_valve_open')
    for _ in range(1):
        line1.add_fitting_by_name('globe_valve_open')
    
    source1.connect(s1)
    line1.connect(s1)
    line1.connect(s2)
    sink1.connect(s2)

    fs.set_media(media)
    fs.add_stream(s1)
    fs.add_stream(s2)
    fs.add_unit(source1)
    fs.add_unit(sink1)
    fs.add_unit(line1)
    fs.initialise()
    fs.solve()

    pressure_drop = s1.pressure - s2.pressure
    numerator = pressure_drop
    f = util.compute_fanning_friction_factor(6000,material1.surface_roughness,line_size1.diameter_inner)
    #f = util.compute_fanning_friction_factor(6000, )
    denominator = s2.density() * s2.velocity(line_size1.diameter_inner)**2 / (2*9.81)
    calculated = numerator / denominator * line_size1.diameter_inner / f
    target = 61.3
    atol = 5
    print(calculated)


def case_2():
    line_size1 = auxiliary.LineSize.custom_from_id(
        id_mm=250,
        designation="test"
    )
    material1 = auxiliary.Material.custom(
        name="general",
        surface_roughness=0.00015,
        notes="test"
    )
    media1 = fluid_flow.Mixture({'water': 1})
    fs = flowsheet.Flowsheet('Test')
    s1 = fluid_flow.Stream('S1')
    #s2 = fluid_flow.Stream('S2')
    source1 = components.Source('IN1', temperature=300,flowrate=1)
    sink1 = components.Sink('OUT1')
    controller1 = components.ControllerInline('TC1')
    controller1.constraints = [constraints.Constraint("pressure", 50e5)]
    source1.connect(s1)
    controller1.connect(s1)
    #controller1.connect(s2)
    sink1.connect(s1)
    fs.set_media(media1)
    for stream in (s1,):
        fs.add_stream(stream)
    for unit in (source1, controller1, sink1):
        fs.add_unit(unit)
    fs.set_initial_state_all()
    fs.solve()
    print(fs.degrees_of_freedom)
    print(s1.pressure)


def case_3():
    line_size14 = auxiliary.LineSize.custom_from_id(
        id_mm=0.4 * 304.8, # 0.4 ft
        designation="line14"
    )
    line_size24 = auxiliary.LineSize.custom_from_id(
        id_mm=0.5 * 304.8,
        designation="line24"
    )
    line_size34 = auxiliary.LineSize.custom_from_id(
        id_mm=0.3 * 304.8,
        designation="line34"
    )
    line_size45 = auxiliary.LineSize.custom_from_id(
        id_mm=0.75 * 304.8,
        designation="line45"
    )
    material1 = auxiliary.Material.custom(
        name="general",
        surface_roughness=0.00015,
        notes="example_6.5"
    )
    flowrate_total = 0.0943894886
    media1 = fluid_flow.Mixture({'oil': 1})
    s1a = fluid_flow.Stream("S1")
    s1b = fluid_flow.Stream("S2")
    s2a = fluid_flow.Stream("S3")
    s2b = fluid_flow.Stream("S4")
    s3a = fluid_flow.Stream("S5")
    s3b = fluid_flow.Stream("S6")
    s4a = fluid_flow.Stream("S7")
    s4b = fluid_flow.Stream("S8")
    line14 = components.LineSegment("line14", 1000 * 0.3048, line_size14, material1)
    line24 = components.LineSegment("line24", 2000 * 0.3048, line_size24, material1)
    line34 = components.LineSegment("line34", 1500 * 0.3048, line_size34, material1)
    line45 = components.LineSegment("line45", 4000 * 0.3048, line_size45, material1)
    source1 = components.Source("Node1", temperature=310)
    source2 = components.Source("Node2") #, temperature=300
    source3 = components.Source("Node3") #, temperature=300
    connector1 = components.Connector("Mix")
    sink1 = components.Sink("Sink", flowrate=flowrate_total, pressure=3e5)
    pressure_controller1 = components.StreamController("PC24", "pressure", s2a, s1a)
    pressure_controller2 = components.StreamController("PC34", "pressure", s3a, s1a)
    source1.connect(s1a)
    line14.connect(s1a)
    line14.connect(s1b)
    connector1.connect(s1b)
    source2.connect(s2a)
    line24.connect(s2a)
    line24.connect(s2b)
    connector1.connect(s2b)
    source3.connect(s3a)
    line34.connect(s3a)
    line34.connect(s3b)
    connector1.connect(s3b)
    connector1.connect(s4a)
    line45.connect(s4a)
    line45.connect(s4b)
    sink1.connect(s4b)

    fs = flowsheet.Flowsheet('Test')
    fs.set_media(media1)
    for stream in (s1a,s1b,s2a,s2b,s3a,s3b,s4a,s4b):
        fs.add_stream(stream)
    for unit in (source1, source2, source3, connector1, sink1, line14, line24, line34, line45, pressure_controller1, pressure_controller2):
        fs.add_unit(unit)
    fs.set_initial_state_all()
    fs.solve()
    print(f's1+s2+s3 pressure: pressure={s1a.pressure},{s2a.pressure},{s3a.pressure}')
    print(f's1: pressure={s1b.pressure}, flowrate={s1b.flowrate}, temperature={s1b.temperature}')
    print(f's2: pressure={s2b.pressure}, flowrate={s2b.flowrate}, temperature={s2b.temperature}')
    print(f's3: pressure={s3b.pressure}, flowrate={s3b.flowrate}, temperature={s3b.temperature}')
    print(f's4: pressure={s4b.pressure}, flowrate={s4b.flowrate}, temperature={s4b.temperature}')
    print(fs.degrees_of_freedom)
    

if __name__ == "__main__":
    case_3()