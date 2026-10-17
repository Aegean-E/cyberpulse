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

    def test_network_simulation_topology(self):
        nodes = generate_network(seed=42)
        for node in nodes.values():
            self.assertTrue(node.ip_address.count(".") == 3, f"{node.node_id} has invalid IP")
            self.assertTrue(len(node.hostname) > 0, f"{node.node_id} has empty hostname")
            self.assertTrue(len(node.ports) >= 1, f"{node.node_id} has no open ports")
            self.assertTrue(len(node.filesystem) >= 1, f"{node.node_id} has empty filesystem")

        # Specific node checks
        vault = nodes["node_vault_1"]
        self.assertEqual(vault.ip_address, "10.0.4.15")
        self.assertTrue(any(p.port == 3306 for p in vault.ports))
        self.assertTrue(any(f.path == "/data/corporate_slush_fund.csv" and f.is_target_data for f in vault.filesystem))

        proxy_a = nodes["node_proxy_a"]
        self.assertEqual(proxy_a.ip_address, "192.168.1.10")
        self.assertTrue(any(p.port == 21 and p.vulnerable for p in proxy_a.ports))


if __name__ == "__main__":
    unittest.main()
