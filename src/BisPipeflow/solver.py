def build_variable_vector(streams):
    """mapping from streams to vector indices"""
    x = []
    index = {}

    i = 0
    for s in streams:
        index[(s, "P")] = i; x.append(s.pressure); i += 1
        index[(s, "T")] = i; x.append(s.temperature); i += 1
        index[(s, "Q")] = i; x.append(s.flowrate); i += 1

    return x, index

def update_streams(x, index):
    """write back to streams"""
    for (s, var), i in index.items():
        if var == "P":
            s.pressure = x[i]
        elif var == "Q":
            s.flowrate = x[i]
        elif var == "T":
            s.temperature = x[i]

def compute_residuals(units):
    """collect residuals"""
    R = []
    for u in units:
        R.extend(u.residuals())
    return R

def solve(flowsheet, max_iter=10000, atol=1e-6, alpha=0.2):

    for it in range(max_iter):

        max_res = 0.0

        for u in flowsheet.components:

            residuals = u.residuals()
            u.apply_corrections(residuals, alpha)

            res_unit = max(abs(r) for r in residuals) if residuals else 0.0
            max_res = max(max_res, res_unit)
            # for s in u.streams:
            #     print(f'Stream {s.name}: p={s.pressure/101325}, T={s.temperature}, Q={s.flowrate}')
            # print(max_res)
        if max_res < atol:
            print(f"Converged in {it} iterations")
            return

    #raise RuntimeError("Did not converge")
    print("Did not converge")