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
def test_heat_exchanger(use_numba):
    """

        :return:
        :rtype:
        """
    net = pandapipes.create_empty_network("net", add_stdtypes=False)

    pandapipes.create_junction(net, pn_bar=5, tfluid_k=283)
    pandapipes.create_junction(net, pn_bar=5, tfluid_k=283)
    pandapipes.create_heat_exchanger(net, 0, 1, qext_w=20000)
    pandapipes.create_ext_grid(net, 0, p_bar=5, t_k=330, type="pt")
    pandapipes.create_sink(net, 1, mdot_kg_per_s=1)

    pandapipes.create_fluid_from_lib(net, "water", overwrite=True)

    max_iter_hyd = 2 if use_numba else 2
    max_iter_therm = 4 if use_numba else 4
    pandapipes.pipeflow(net, max_iter_hyd=max_iter_hyd, max_iter_therm=max_iter_therm,
                        stop_condition="tol", friction_model="nikuradse",
                        mode='sequential', transient=False, nonlinear_method="automatic", tol_p=1e-4,
                        tol_m=1e-4, use_numba=use_numba)

    data = pd.read_csv(os.path.join(data_path, "heat_exchanger_test.csv"), sep=';',
                       header=0, keep_default_na=False)
    temp_an = data["T1"]

    t_pan = net.res_junction.t_k

    temp_diff = np.abs(1 - t_pan / temp_an)

    assert np.all(temp_diff < 0.01)
