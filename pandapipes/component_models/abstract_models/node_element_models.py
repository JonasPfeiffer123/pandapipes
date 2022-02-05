# Copyright (c) 2020-2021 by Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel, and University of Kassel. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from pandapipes.component_models.abstract_models.base_component import Component

try:
    import pplog as logging
except ImportError:
    import logging

logger = logging.getLogger(__name__)


class NodeElementComponent(Component):
    """

    """

    @classmethod
    def create_pit_node_entries(cls, net, node_pit):
        """
        Function that creates pit node entries.

        :param net: The pandapipes network
        :type net: pandapipesNet
        :param node_pit:
        :type node_pit:
        :return: No Output.
        """
        raise NotImplementedError

    @classmethod
    def get_connected_node_type(cls):
        raise NotImplementedError
