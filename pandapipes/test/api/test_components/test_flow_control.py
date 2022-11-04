import numpy as np
import pytest

import pandapipes


@pytest.mark.parametrize("use_numba", [True, False])
def test_flow_control_simple(use_numba):
    net = pandapipes.create_empty_network("net", add_stdtypes=True, fluid="water")

    j = pandapipes.create_junctions(net, 8, pn_bar=5, tfluid_k=360)
    j1, j2, j3, j4, j5, j6, j7, j8 = j

    p12, p25, p48, p74 = pandapipes.create_pipes_from_parameters(
        net, [j1, j2, j4, j7], [j2, j5, j8, j4], 0.2, 0.1, k_mm=0.1, alpha_w_per_m2k=20.,
        text_k=280)

    pandapipes.create_heat_exchanger(net, j3, j4, 0.1, 50000, 1)
    pandapipes.create_heat_exchanger(net, j6, j7, 0.1, 50000, 1)

    pandapipes.create_flow_control(net, j2, j3, 2, 0.1)
    pandapipes.create_flow_control(net, j5, j6, 2, 0.1, control_active=False)

    pandapipes.create_ext_grid(net, j1, p_bar=5, t_k=360, type="pt")

    pandapipes.create_sink(net, j8, 3)

    pandapipes.pipeflow(net, mode="all", use_numba=use_numba)

    assert np.allclose(net.res_pipe.loc[[p12, p48, p25, p74], "mdot_from_kg_per_s"], [3, 3, 1, 1])
    assert np.allclose(net.res_flow_control["mdot_from_kg_per_s"].values, [2, 1])

    j_new = pandapipes.create_junctions(net, 2, pn_bar=5, tfluid_k=360)
    pandapipes.create_flow_control(net, j_new[0], j_new[1], 2, 0.1)

    pandapipes.pipeflow(net, mode="all", use_numba=use_numba, check_connectivity=True)

    assert np.allclose(net.res_pipe.loc[[p12, p48, p25, p74], "mdot_from_kg_per_s"], [3, 3, 1, 1])
    assert np.allclose(net.res_flow_control["mdot_from_kg_per_s"].values[:2], [2, 1])
    assert np.isnan(net.res_flow_control["mdot_from_kg_per_s"].values[2])
