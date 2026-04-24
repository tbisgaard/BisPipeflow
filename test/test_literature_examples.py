"""
Testing straight pipe
"""

from BisPipeflow import flowsheet, fluid_flow, components, auxiliary


def test_pressure_drop_in_line_with_resistances():
    # Chemical Process Equipment, Walas, Example 6.5, page 101
    # 12 inch steel line at Re=6000
    # eps=0.00015
    # 1000 ft pipe = 304.8 metres
    # 12 inch = 0.3048 metres
    # 6 LR elbows
    # 4 tees, branched
    # 2 gate valve
    # 1 globe valve
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
    source1 = components.Source('IN1', pressure=10e5, temperature=298, flowrate=flowrate)
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
    denominator = s2.density() * s2.velocity(line_size1.diameter_inner)**2 / (2*9.82)
    calculated = numerator / denominator
    target = 61.3
    atol = 6.13
    print(calculated)

    assert abs(calculated - target) < atol

def test_three_to_one_network():
    # Example 6.7


    assert True