"""
ff
"""
import numpy as np

from BisPipeflow import flowsheet
from BisPipeflow import fluid_flow
from BisPipeflow import components
from BisPipeflow import solver


def case_2():
    fs = flowsheet.Flowsheet("water")


def case_1():
    # Source -> tank -> pump -> tube -> Sink
    #        S1      S2      S3      S4
    
    mix1 = fluid_flow.Mixture({
        "water": 0.8,
        "oil": 0.2
    })
    S1 = fluid_flow.Stream("S1")
    S2 = fluid_flow.Stream("S2")
    S3 = fluid_flow.Stream("S3")
    S4 = fluid_flow.Stream("S4")

    source = components.Source("X1", pressure=2e5, temperature=300, flowrate=10/3600)
    tank = components.Tank("TANK-1")
    pump = components.Pump("PUMP-1")
    pipe = components.PipeSegment("TUBE-1", diameter=0.1, length=50)
    sink = components.Sink("Y1")
    
    pipe.add_fitting_by_name("elbow_90_standard")
    pump.head_curve = np.array([5, 5])
    pump.flowrate_curve = np.array([0, 100])
    tank.density = 1000

    source.connect(S1)
    tank.connect(S1)
    tank.connect(S2)
    pump.connect(S2)
    pump.connect(S3)
    pipe.connect(S3)
    pipe.connect(S4)
    sink.connect(S4)

    source.solve()
    tank.solve()
    pump.solve()
    pipe.solve()
    sink.solve()

    print(f'S1: p={S1.pressure}, T={S1.temperature}, Q={S1.flowrate}')
    print(f'S2: p={S2.pressure}, T={S2.temperature}, Q={S2.flowrate}')
    print(f'S3: p={S3.pressure}, T={S3.temperature}, Q={S3.flowrate}')
    print(f'S4: p={S4.pressure}, T={S4.temperature}, Q={S4.flowrate}')



def case_3():
    mix1 = fluid_flow.Mixture({
        "water": 0.8,
        "oil": 0.2
    })
    S1 = fluid_flow.Stream("S1")
    S2 = fluid_flow.Stream("S2")
    S3 = fluid_flow.Stream("S3")
    S4 = fluid_flow.Stream("S4")

    source = components.Source("X1", pressure=2e5, temperature=300, flowrate=10/3600)
    tank = components.Tank("TANK-1", head_pressure=2e5)
    pump = components.Pump("PUMP-1")
    pipe = components.PipeSegment("TUBE-1", diameter=0.1, length=50)
    sink = components.Sink("Y1")
    
    pipe.add_fitting_by_name("elbow_90_standard")
    pump.head_curve = np.array([5, 5])
    pump.flowrate_curve = np.array([0, 100])
    tank.density = 1000

    source.connect(S1)
    tank.connect(S1)
    tank.connect(S2)
    pump.connect(S2)
    pump.connect(S3)
    pipe.connect(S3)
    pipe.connect(S4)
    sink.connect(S4)

    dof = 0

    for s in (S1, S2, S3, S4):
        s.temperature = 300
        s.pressure = 101325
        s.flowrate = 10/3600
        s.mixture = mix1
        dof += s.num_variables
    
    residuals = []
    
    for u in (source, tank, pump, pipe, sink):
        residuals.append(u.residuals())
        dof -= u.num_equations


    print(residuals)
    print(f'dof={dof}')

    fs = flowsheet.Flowsheet('water')
    for u in (source, tank, pump, pipe, sink):
        fs.add_unit(u)
    for s in (S1, S2, S3, S4):
        fs.add_stream(s)
    solver.solve(fs)


def case_4():
    mix1 = fluid_flow.Mixture({
        "water": 0.8,
        "oil": 0.2
    })
    s1 = fluid_flow.Stream("S1")
    s2 = fluid_flow.Stream("S1")
    source = components.Source("X1", pressure=2e5, temperature=300, flowrate=10/3600)
    tank = components.Tank("TANK-1", head_pressure=2e5)
    pump = components.Pump("PUMP-1")
    pipe = components.PipeSegment("TUBE-1", diameter=0.1, length=50)
    sink = components.Sink("Y1")
    tank.density = 1000
    dof = 0
    for s in (s1, s2):
        s.temperature = 300
        s.pressure = 101325
        s.flowrate = 10/3600
        s.mixture = mix1
        dof += s.num_variables
    for u in (source, tank, sink):
        dof -= u.num_equations

    source.connect(s1)
    pipe.connect(s1)
    pipe.connect(s2)
    sink.connect(s2)
    fs = flowsheet.Flowsheet("test")
    fs.add_unit(source)
    fs.add_unit(sink)
    fs.add_unit(pipe)
    fs.add_stream(s1)
    fs.add_stream(s2)
    print(fs.degrees_of_freedom)
    solver.solve(fs, alpha = 0.4)

    
    print(s2.pressure)

if __name__ == "__main__":
    case_4()