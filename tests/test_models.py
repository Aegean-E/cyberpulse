"""Unit tests for CyberPulse domain models."""

import unittest
from cyberpulse.models import (
    BountyContract,
    CareerProfile,
    CyberDeck,
    GameState,
    Node,
    NodeStatus,
    NodeType,
    PortService,
    RewardType,
    VirtualFile,
    apply_career_profile,
)


class TestModels(unittest.TestCase):
    def test_node_roundtrip(self):
        port = PortService(port=22, service="ssh", version="OpenSSH 7.2", vulnerable=True)
        vfile = VirtualFile(path="/etc/passwd", size_kb=2, content="root:x:0:0", value_creds=10)
        node = Node(
            node_id="n1",
            name="Proxy Server",
            node_type=NodeType.FIREWALL,
            security_level=2,
            status=NodeStatus.DISCOVERED,
            connected_ids=["n2"],
            trace_rate=15,
            credits_reward=100,
            ip_address="192.168.1.10",
            hostname="proxy.alpha",
            ports=[port],
            filesystem=[vfile],
        )
        data = node.to_dict()
        restored = Node.from_dict(data)
        self.assertEqual(restored.node_id, "n1")
        self.assertEqual(restored.node_type, NodeType.FIREWALL)
        self.assertEqual(restored.credits_reward, 100)
        self.assertEqual(restored.ip_address, "192.168.1.10")
        self.assertEqual(restored.hostname, "proxy.alpha")
        self.assertEqual(len(restored.ports), 1)
        self.assertEqual(restored.ports[0].port, 22)
        self.assertEqual(restored.ports[0].service, "ssh")
        self.assertEqual(len(restored.filesystem), 1)
        self.assertEqual(restored.filesystem[0].path, "/etc/passwd")

    def test_port_and_file_roundtrip(self):
        port = PortService(port=3306, service="mysql", version="MariaDB 10.3", vulnerable=True, exploit_tool="sql_inject")
        p_dict = port.to_dict()
        p_restored = PortService.from_dict(p_dict)
        self.assertEqual(p_restored.port, 3306)
        self.assertEqual(p_restored.exploit_tool, "sql_inject")

        vfile = VirtualFile(path="/data/secret.csv", size_kb=16, content="confidential", value_creds=200, is_target_data=True)
        f_dict = vfile.to_dict()
        f_restored = VirtualFile.from_dict(f_dict)
        self.assertEqual(f_restored.path, "/data/secret.csv")
        self.assertEqual(f_restored.value_creds, 200)
        self.assertTrue(f_restored.is_target_data)

    def test_deck_roundtrip(self):
        deck = CyberDeck(cryptocreds=500, cpu_cycles=8, ice_dampener_level=1)
        data = deck.to_dict()
        restored = CyberDeck.from_dict(data)
        self.assertEqual(restored.cryptocreds, 500)
        self.assertEqual(restored.cpu_cycles, 8)
        self.assertEqual(restored.ice_dampener_level, 1)

    def test_game_state_roundtrip(self):
        contract = BountyContract(contract_id="c1", title="Heist", target_node_type=NodeType.DATA_VAULT)
        state = GameState(
            seed=42,
            current_node_id="node_gateway",
            trace_percent=25,
            unbanked_creds=150,
            active_contract=contract,
        )
        data = state.to_dict()
        restored = GameState.from_dict(data)
        self.assertEqual(restored.seed, 42)
        self.assertEqual(restored.trace_percent, 25)
        self.assertEqual(restored.unbanked_creds, 150)
        self.assertIsNotNone(restored.active_contract)
        self.assertEqual(restored.active_contract.contract_id, "c1")

    def test_career_profile_roundtrip(self):
        profile = CareerProfile(alias="Phantom", banked_creds=1200, current_streak=3)
        data = profile.to_dict()
        restored = CareerProfile.from_dict(data)
        self.assertEqual(restored.alias, "Phantom")
        self.assertEqual(restored.banked_creds, 1200)
        self.assertEqual(restored.current_streak, 3)

    def test_apply_career_profile(self):
        deck = CyberDeck()
        profile = CareerProfile(
            banked_creds=600,
            purchased_upgrades=["overclock_cpu", "expand_ram", "ice_dampener", "logic_bomb"],
        )
        apply_career_profile(deck, profile)
        self.assertEqual(deck.cryptocreds, 600)
        self.assertEqual(deck.overclock_level, 1)
        self.assertEqual(deck.max_cpu, 12)
        self.assertEqual(deck.ram_boost_level, 1)
        self.assertEqual(deck.max_ram, 96)
        self.assertEqual(deck.ice_dampener_level, 1)
        self.assertIn("logic_bomb", deck.exploits)


if __name__ == "__main__":
    unittest.main()
