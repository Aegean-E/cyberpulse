"""Unit tests for procedural network generation."""

import unittest
from cyberpulse.models import NodeStatus, NodeType
from cyberpulse.network import generate_network


class TestNetwork(unittest.TestCase):
    def test_network_topology(self):
        nodes = generate_network(seed=1337)
        self.assertIn("node_gateway", nodes)
        self.assertIn("node_central_core", nodes)

        # Gateway starts breached
        self.assertEqual(nodes["node_gateway"].status, NodeStatus.BREACHED)

        # Central core is security level 5
        self.assertEqual(nodes["node_central_core"].security_level, 5)
        self.assertEqual(nodes["node_central_core"].node_type, NodeType.CENTRAL_CORE)

    def test_deterministic_generation(self):
        net1 = generate_network(seed=999)
        net2 = generate_network(seed=999)
        self.assertEqual(list(net1.keys()), list(net2.keys()))
        for k in net1:
            self.assertEqual(net1[k].name, net2[k].name)
            self.assertEqual(net1[k].connected_ids, net2[k].connected_ids)


if __name__ == "__main__":
    unittest.main()
