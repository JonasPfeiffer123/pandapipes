# Copyright (c) 2020-2024 by Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel, and University of Kassel. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

import os

import numpy as np
import pandas as pd
import pytest

import pandapipes
from pandapipes.test import data_path


@pytest.mark.parametrize("use_numba", [True, False])
def test_ext_grid_sorting(use_numba):
    net = pandapipes.create_empty_network(fluid="hgas")
    j1 = pandapipes.create_junction(net, 1, 293.15, index=1)
    j2 = pandapipes.create_junction(net, 1, 293.15, index=2)
    j3 = pandapipes.create_junction(net, 1, 293.15, index=4)
    j4 = pandapipes.create_junction(net, 1, 293.15, index=5)
    j5 = pandapipes.create_junction(net, 1, 293.15, index=6)
    j6 = pandapipes.create_junction(net, 1, 293.15, index=7)

    pandapipes.create_ext_grids(net, [j2, j3, j5, j1, j1], p_bar=1, t_k=285.15,
                                type=["auto", "pt", "t", "pt", "tp"])
    assert np.all(net.ext_grid.type == ["pt", "pt", "t", "pt", "pt"])

    pandapipes.create_pipe_from_parameters(net, j1, j4, 0.1, 0.1)
    pandapipes.create_pipe_from_parameters(net, j2, j5, 0.1, 0.1)
    pandapipes.create_pipe_from_parameters(net, j3, j6, 0.1, 0.1)

    pandapipes.create_sink(net, j4, mdot_kg_per_s=0.1)
    pandapipes.create_sink(net, j5, mdot_kg_per_s=0.1)
    pandapipes.create_sink(net, j6, mdot_kg_per_s=0.1)
    pandapipes.create_sink(net, j2, mdot_kg_per_s=0.02)

    max_iter_hyd = 3 if use_numba else 3
    pandapipes.pipeflow(net, max_iter_hyd=max_iter_hyd, use_numba=use_numba)

    assert np.isclose(net.res_ext_grid.at[0, "mdot_kg_per_s"], -0.12, atol=1e-12, rtol=1e-12)
    assert np.isclose(net.res_ext_grid.at[1, "mdot_kg_per_s"], -0.1, atol=1e-12, rtol=1e-12)
    assert np.isnan(net.res_ext_grid.at[2, "mdot_kg_per_s"])
    assert np.isclose(net.res_ext_grid.at[3, "mdot_kg_per_s"], -0.05, atol=1e-12, rtol=1e-12)
    assert np.isclose(net.res_ext_grid.at[4, "mdot_kg_per_s"], -0.05, atol=1e-12, rtol=1e-12)


@pytest.mark.parametrize("use_numba", [True, False])
def test_p_type(use_numba):
    """

    :return:
    :rtype:
    """
    net = pandapipes.create_empty_network("net")
    d = 75e-3
    pandapipes.create_junction(net, pn_bar=5, tfluid_k=293.15)
    pandapipes.create_junction(net, pn_bar=5, tfluid_k=293.15)
    pandapipes.create_pipe_from_parameters(net, 0, 1, 10, diameter_m=d, k_mm=0.1, sections=1)
    pandapipes.create_ext_grid(net, 0, p_bar=5, t_k=285.15, type="p")
    pandapipes.create_sink(net, 1, mdot_kg_per_s=1)
    pandapipes.create_fluid_from_lib(net, name="water")

    max_iter_hyd = 3 if use_numba else 3
    pandapipes.pipeflow(net, stop_condition="tol", max_iter_hyd=max_iter_hyd, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4, tol_m=1e-4,
                        use_numba=use_numba)

    data = pd.read_csv(os.path.join(data_path, "ext_grid_p.csv"),
                       sep=';', header=0, keep_default_na=False)
    p_comp = data["p"]
    p_pandapipes = net.res_junction["p_bar"][0]

    p_diff = np.abs(1 - p_pandapipes / p_comp.loc[0])

    assert np.all(p_diff < 0.01)

@pytest.mark.parametrize("use_numba", [True, False])
def test_t_type_single_pipe(use_numba):
    """

    :return:
    :rtype:
    """
    net = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=283)
    j1 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=283)
    pandapipes.create_ext_grid(net, j0, 5, 645, type="pt")
    pandapipes.create_sink(net, j1, 1)
    pandapipes.create_pipe_from_parameters(net, j0, j1, 6, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)

    pandapipes.create_fluid_from_lib(net, "water", overwrite=True)
    max_iter_hyd = 3 if use_numba else 3
    max_iter_therm = 6 if use_numba else 6
    pandapipes.pipeflow(net, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, mode='sequential', use_numba=use_numba)

    temp = net.res_junction.t_k.values

    net2 = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=283)
    j1 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=283)
    pandapipes.create_ext_grid(net2, j0, 5, 645, type="p")
    pandapipes.create_ext_grid(net2, j1, 100, 327.765863, type="t")
    pandapipes.create_sink(net2, j1, 1)

    pandapipes.create_pipe_from_parameters(net2, j0, j1, 6, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)
    pandapipes.create_fluid_from_lib(net2, "water", overwrite=True)
    max_iter_hyd = 3 if use_numba else 3
    max_iter_therm = 12 if use_numba else 12
    pandapipes.pipeflow(net2, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4, tol_m=1e-4,
                        mode='sequential', use_numba=use_numba)

    temp2 = net2.res_junction.t_k.values

    temp_diff = np.abs(1 - temp / temp2)

    assert np.all(temp_diff < 0.01)


@pytest.mark.parametrize("use_numba", [True, False])
def test_t_type_tee(use_numba):
    """

    :return:
    :rtype:
    """
    net = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    j1 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    j2 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    j3 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    pandapipes.create_ext_grid(net, j0, 5, 645, type="p")
    pandapipes.create_sink(net, j2, 1)
    pandapipes.create_sink(net, j3, 1)
    pandapipes.create_ext_grid(net, j2, 5, 310, type="t")

    pandapipes.create_pipe_from_parameters(net, j0, j1, 6, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j1, j2, 2.5, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j1, j3, 2.5, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)

    pandapipes.create_fluid_from_lib(net, "water", overwrite=True)

    max_iter_hyd = 4 if use_numba else 4
    max_iter_therm = 5 if use_numba else 5
    pandapipes.pipeflow(net, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, mode='sequential', use_numba=use_numba)

    temp = net.res_junction.t_k.values

    net2 = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j1 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j2 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j3 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    pandapipes.create_ext_grid(net2, j0, 5, 380.445, type="pt")
    pandapipes.create_sink(net2, j2, 1)
    pandapipes.create_sink(net2, j3, 1)

    pandapipes.create_pipe_from_parameters(net2, j0, j1, 6, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j1, j2, 2.5, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j1, j3, 2.5, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)

    pandapipes.create_fluid_from_lib(net2, "water", overwrite=True)
    pandapipes.pipeflow(net2, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4, tol_m=1e-4,
                        mode='sequential', use_numba=use_numba)
    temp2 = net2.res_junction.t_k.values

    temp_diff = np.abs(1 - temp / temp2)

    assert np.all(temp_diff < 0.01)


@pytest.mark.parametrize("use_numba", [True, False])
def test_t_type_tee_2zu_2ab(use_numba):
    """

    :return:
    :rtype:
    """
    net = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    j1 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    j2 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    j3 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    j4 = pandapipes.create_junction(net, pn_bar=5, tfluid_k=300)
    pandapipes.create_ext_grid(net, j0, 5, 645, type="p")
    pandapipes.create_ext_grid(net, j1, 5, 645, type="p")
    pandapipes.create_sink(net, j3, 1)
    pandapipes.create_sink(net, j4, 1)
    pandapipes.create_ext_grid(net, j1, 5, 645, type="t")
    pandapipes.create_ext_grid(net, j0, 5, 645, type="t")

    pandapipes.create_pipe_from_parameters(net, j0, j2, 6, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j1, j2, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j2, j3, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j2, j4, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_fluid_from_lib(net, "water", overwrite=True)
    max_iter_hyd = 4 if use_numba else 4
    max_iter_therm = 8 if use_numba else 8
    pandapipes.pipeflow(net, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, mode='sequential', use_numba=use_numba)

    temp = net.res_junction.t_k.values

    net2 = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j1 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j2 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j3 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j4 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    pandapipes.create_ext_grid(net2, j0, 5, 645, type="pt")
    pandapipes.create_ext_grid(net2, j1, 5, 645, type="pt")
    pandapipes.create_sink(net2, j3, 1)
    pandapipes.create_sink(net2, j4, 1)

    pandapipes.create_pipe_from_parameters(net2, j0, j2, 6, diameter_m=d, k_mm=.1, sections=1,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j1, j2, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j2, j3, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j2, j4, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)

    pandapipes.create_fluid_from_lib(net2, "water", overwrite=True)
    pandapipes.pipeflow(net2, stop_condition="tol", max_iter_hyd=max_iter_hyd, max_iter_therm=max_iter_therm,
                        friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, mode='sequential', use_numba=use_numba)

    temp2 = net2.res_junction.t_k.values

    temp_diff = np.abs(1 - temp / temp2)

    assert np.all(temp_diff < 0.01)

@pytest.mark.parametrize("use_numba", [True, False])
def test_t_type_tee_2zu_2ab2(use_numba):
    """

    :return:
    :rtype:
    """
    net = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    j1 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    j2 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    j3 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    j4 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    pandapipes.create_ext_grid(net, j0, 5, 645, type="p")
    pandapipes.create_ext_grid(net, j1, 5, 645, type="p")
    pandapipes.create_sink(net, j3, 1)
    pandapipes.create_sink(net, j4, 1)
    pandapipes.create_ext_grid(net, j0, 5, 645, type="t")
    pandapipes.create_ext_grid(net, j4, 5, 382.485897, type="t")

    pandapipes.create_pipe_from_parameters(net, j0, j2, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j1, j2, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j2, j3, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j2, j4, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_fluid_from_lib(net, "water", overwrite=True)
    max_iter_hyd = 3 if use_numba else 3
    max_iter_therm = 8 if use_numba else 8
    pandapipes.pipeflow(net, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, mode='sequential', use_numba=use_numba)

    temp = net.res_junction.t_k.values

    net2 = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j1 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j2 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j3 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j4 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    pandapipes.create_ext_grid(net2, j0, 5, 645, type="pt")
    pandapipes.create_ext_grid(net2, j1, 5, 645, type="pt")
    pandapipes.create_sink(net2, j3, 1)
    pandapipes.create_sink(net2, j4, 1)

    pandapipes.create_pipe_from_parameters(net2, j0, j2, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j1, j2, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j2, j3, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j2, j4, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)

    pandapipes.create_fluid_from_lib(net2, "water", overwrite=True)
    pandapipes.pipeflow(net2, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, mode='sequential', use_numba=use_numba)

    temp2 = net2.res_junction.t_k.values

    temp_diff = np.abs(1 - temp / temp2)

    assert np.all(temp_diff < 0.01)

@pytest.mark.parametrize("use_numba", [True, False])
def test_t_type_tee_2zu_2ab3(use_numba):
    """

    :return:
    :rtype:
    """
    net = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    j1 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    j2 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    j3 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    j4 = pandapipes.create_junction(net, pn_bar=3, tfluid_k=300)
    pandapipes.create_ext_grid(net, j0, 5, 645, type="p")
    pandapipes.create_ext_grid(net, j2, 5, 645, type="p")
    pandapipes.create_sink(net, j3, 1)
    pandapipes.create_sink(net, j4, 1)
    pandapipes.create_ext_grid(net, j2, 5, 645, type="t")
    pandapipes.create_ext_grid(net, j4, 5, 382.485897, type="t")

    pandapipes.create_pipe_from_parameters(net, j0, j1, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j2, j1, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j1, j3, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net, j1, j4, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)

    pandapipes.create_fluid_from_lib(net, "water", overwrite=True)

    max_iter_hyd = 3 if use_numba else 3
    max_iter_therm = 8 if use_numba else 8
    pandapipes.pipeflow(net, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, mode='sequential', use_numba=use_numba)

    temp = net.res_junction.t_k.values

    net2 = pandapipes.create_empty_network("net")
    d = 75e-3

    j0 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j1 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j2 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j3 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    j4 = pandapipes.create_junction(net2, pn_bar=5, tfluid_k=300)
    pandapipes.create_ext_grid(net2, j0, 5, 645, type="pt")
    pandapipes.create_ext_grid(net2, j2, 5, 645, type="pt")
    pandapipes.create_sink(net2, j3, 1)
    pandapipes.create_sink(net2, j4, 1)

    pandapipes.create_pipe_from_parameters(net2, j0, j1, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j2, j1, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j1, j3, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)
    pandapipes.create_pipe_from_parameters(net2, j1, j4, 2.5, diameter_m=d, k_mm=.1, sections=5,
                                           u_w_per_m2k=5)

    pandapipes.create_fluid_from_lib(net2, "water", overwrite=True)
    pandapipes.pipeflow(net2, stop_condition="tol", max_iter_hyd=max_iter_hyd,
                        max_iter_therm=max_iter_therm, friction_model="nikuradse",
                        transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, mode='sequential', use_numba=use_numba)

    temp2 = net2.res_junction.t_k.values

    temp_diff = np.abs(1 - temp / temp2)

    assert np.all(temp_diff < 0.01)


if __name__ == '__main__':
    pytest.main([r'pandapipes/test/api/test_components/test_ext_grid.py'])
