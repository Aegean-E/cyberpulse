"""Procedural cyberspace network generator with deterministic topology."""

import random
from typing import Dict

from cyberpulse.models import (
    EmployeeProfile,
    FirewallPolicy,
    FirewallRule,
    HostAntivirus,
    HostFirewall,
    Node,
    NodeStatus,
    NodeType,
    PortService,
    SecurityAwarenessLevel,
    VirtualFile,
)


def generate_network(seed: int) -> Dict[str, Node]:
    """Generate a deterministic cyberspace infiltration network grid from seed."""
    rng = random.Random(seed)

    nodes: Dict[str, Node] = {
        "node_gateway": Node(
            node_id="node_gateway",
            name="External Border Gateway",
            node_type=NodeType.GATEWAY,
            security_level=1,
            status=NodeStatus.BREACHED,  # Player starts here
            connected_ids=["node_proxy_a", "node_proxy_b"],
            trace_rate=5,
            credits_reward=0,
            puzzle_type=None,
            ip_address="192.168.1.1",
            hostname="gw.omninet.internal",
            ports=[
                PortService(port=80, service="http", version="OmniWeb Portal v2.1", vulnerable=False, breached=True),
            ],
            filesystem=[
                VirtualFile(path="/etc/hosts", size_kb=1, content="192.168.1.1 gw.omninet\n192.168.1.10 alpha.internal\n192.168.1.20 beta.internal"),
                VirtualFile(path="/var/log/syslog", size_kb=4, content="[INFO] Border gateway routing active"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_gw_1", port=80, action="ALLOW")]),
            antivirus=None,
            employees=[
                EmployeeProfile(name="Leo Gates", role="Gate Operator", email="lgates@omninet.internal", awareness_level=SecurityAwarenessLevel.NAIVE, leaked_credential="gw_bypass_token=GW-991"),
            ],
        ),
        "node_proxy_a": Node(
            node_id="node_proxy_a",
            name="Subnet Router Alpha",
            node_type=NodeType.FIREWALL,
            security_level=1,
            status=NodeStatus.DISCOVERED,
            connected_ids=["node_gateway", "node_vault_1", "node_ice_perimeter"],
            trace_rate=10,
            credits_reward=50,
            data_payload="System architecture specs",
            puzzle_type="frequency",
            ip_address="192.168.1.10",
            hostname="alpha.internal",
            ports=[
                PortService(port=21, service="ftp", version="vsftpd 2.3.4", vulnerable=True, exploit_tool="ftp_bounce"),
            ],
            filesystem=[
                VirtualFile(path="/home/admin/network_map.txt", size_kb=12, content="Subnet topology routing table:\n10.0.4.15 vault.corp.finance\n172.16.1.99 blackice.defense.core", value_creds=50, is_target_data=True),
                VirtualFile(path="/var/log/auth.log", size_kb=3, content="Accepted publickey for admin from 192.168.1.1"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_a_1", port=21, action="ALLOW")]),
            antivirus=HostAntivirus(name="DefenderBasic", version="v1.2", alert_level=0, heuristic_sensitivity=2),
            employees=[
                EmployeeProfile(name="Alice Vance", role="Junior SysAdmin", email="avance@alpha.internal", awareness_level=SecurityAwarenessLevel.STANDARD, leaked_credential="ftp_admin_pass=V4nce_2026"),
            ],
        ),
        "node_proxy_b": Node(
            node_id="node_proxy_b",
            name="Subnet Router Beta",
            node_type=NodeType.FIREWALL,
            security_level=2,
            status=NodeStatus.DISCOVERED,
            connected_ids=["node_gateway", "node_vault_2", "node_ice_perimeter"],
            trace_rate=15,
            credits_reward=75,
            data_payload="Admin credential fragment",
            puzzle_type="buffer",
            ip_address="192.168.1.20",
            hostname="beta.internal",
            ports=[
                PortService(port=22, service="ssh", version="OpenSSH 7.2p2", vulnerable=True, exploit_tool="ssh_overflow"),
            ],
            filesystem=[
                VirtualFile(path="/home/secops/credentials.bak", size_kb=8, content="vault_access_token=VAULT-8842-X\nrnd_token=RND-9921-Z", value_creds=75, is_target_data=True),
                VirtualFile(path="/var/log/secure", size_kb=5, content="Failed password for invalid user root"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_b_1", port=22, action="BLOCK")]),
            antivirus=HostAntivirus(name="SentinelCore EDR", version="v3.0", alert_level=10, heuristic_sensitivity=3),
            employees=[
                EmployeeProfile(name="Marcus Cole", role="SecOps Analyst", email="mcole@beta.internal", awareness_level=SecurityAwarenessLevel.STANDARD, leaked_credential="ssh_firewall_rule_override=RULE_ALLOW_22"),
            ],
        ),
        "node_vault_1": Node(
            node_id="node_vault_1",
            name="Financial Ledger Vault",
            node_type=NodeType.DATA_VAULT,
            security_level=2,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_a"],
            trace_rate=15,
            credits_reward=250,
            data_payload="Corporate slush fund transaction logs",
            puzzle_type="hash",
            ip_address="10.0.4.15",
            hostname="vault.corp.finance",
            ports=[
                PortService(port=3306, service="mysql", version="MariaDB 10.3", vulnerable=True, exploit_tool="sql_inject"),
            ],
            filesystem=[
                VirtualFile(path="/data/corporate_slush_fund.csv", size_kb=64, content="EXEC_ID,AMOUNT,ROUTING\nCEO_OFFSHORE,$4200000,CAYMAN_SUB_99\nCFO_RESERVE,$1850000,ZURICH_NODE_12", value_creds=250, is_target_data=True),
                VirtualFile(path="/var/log/mysql.log", size_kb=16, content="Query: SELECT * FROM offshore_accounts"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_v1_1", port=3306, action="BLOCK")]),
            antivirus=HostAntivirus(name="CyberShield Corp", version="v4.0", alert_level=15, heuristic_sensitivity=4),
            employees=[
                EmployeeProfile(name="Diana Prince", role="Chief Financial Officer", email="dprince@corp.finance", awareness_level=SecurityAwarenessLevel.PARANOID, leaked_credential="vault_db_root_auth=CFO_PRINCE_SECRET"),
            ],
        ),
        "node_vault_2": Node(
            node_id="node_vault_2",
            name="Research & Prototype Archive",
            node_type=NodeType.DATA_VAULT,
            security_level=3,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_b"],
            trace_rate=20,
            credits_reward=350,
            data_payload="Classified Neural Interface schematic",
            puzzle_type="buffer",
            ip_address="10.0.4.50",
            hostname="rnd.prototype.archive",
            ports=[
                PortService(port=8080, service="http", version="Prototype Dev API v1.0", vulnerable=True, exploit_tool="web_shell"),
            ],
            filesystem=[
                VirtualFile(path="/research/neural_interface.blueprint", size_kb=128, content="PROJECT CHIMERA: Direct cortex neural override matrix firmware specifications", value_creds=350, is_target_data=True),
                VirtualFile(path="/var/log/audit.log", size_kb=8, content="Checkout: Neural schematic rev 4.2"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_v2_1", port=8080, action="BLOCK")]),
            antivirus=HostAntivirus(name="AegisAI Sentinel", version="v5.1", alert_level=20, heuristic_sensitivity=4),
            employees=[
                EmployeeProfile(name="Dr. Victor Stone", role="Lead AI Architect", email="vstone@rnd.prototype", awareness_level=SecurityAwarenessLevel.PARANOID, leaked_credential="chimera_debug_key=NEURAL_OVERRIDE_42"),
            ],
        ),
        "node_ice_perimeter": Node(
            node_id="node_ice_perimeter",
            name="Black ICE Defense Cluster",
            node_type=NodeType.ICE_DEFENSE,
            security_level=4,
            status=NodeStatus.LOCKED,
            connected_ids=["node_proxy_a", "node_proxy_b", "node_central_core"],
            trace_rate=30,
            credits_reward=150,
            data_payload="Root clearance security token",
            puzzle_type="frequency",
            ip_address="172.16.1.99",
            hostname="blackice.defense.core",
            ports=[
                PortService(port=443, service="https", version="Sentinel ICE Gateway v4", vulnerable=True, exploit_tool="zero_day_ice"),
            ],
            filesystem=[
                VirtualFile(path="/sys/root_clearance.key", size_kb=2, content="ROOT_CLEARANCE_KEY: OMEGA-ACCESS-CLEARANCE-LEVEL-5", value_creds=150, is_target_data=True),
                VirtualFile(path="/var/log/ice_trace.log", size_kb=12, content="Intruder signature detected on perimeter"),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_ice_1", port=443, action="BLOCK")]),
            antivirus=HostAntivirus(name="BlackICE Autonomous Hunter", version="v9.0", alert_level=30, heuristic_sensitivity=5),
            employees=[
                EmployeeProfile(name="Agent Smith", role="ICE Commander", email="smith@blackice.defense", awareness_level=SecurityAwarenessLevel.PARANOID, leaked_credential="ice_core_override=OMEGA_ZERO_CLEAR"),
            ],
        ),
        "node_central_core": Node(
            node_id="node_central_core",
            name="Nexus Central Supercore",
            node_type=NodeType.CENTRAL_CORE,
            security_level=5,
            status=NodeStatus.LOCKED,
            connected_ids=["node_ice_perimeter"],
            trace_rate=40,
            credits_reward=1000,
            data_payload="PROJECT OMEGA: Master AI Decryption Keys",
            puzzle_type="hash",
            ip_address="172.16.80.1",
            hostname="nexus.master.supercore",
            ports=[
                PortService(port=8888, service="tcp", version="Project Omega AI Core v1.0", vulnerable=True, exploit_tool="neural_exploit"),
            ],
            filesystem=[
                VirtualFile(path="/core/master_ai_keys.enc", size_kb=256, content="PROJECT OMEGA: Master AI Decryption Keys & Autonomous Model Weights", value_creds=1000, is_target_data=True),
                VirtualFile(path="/var/log/kernel.log", size_kb=32, content="Supercore kernel online. Decryption matrix active."),
            ],
            firewall=HostFirewall(rules=[FirewallRule(rule_id="fw_core_1", port=8888, action="BLOCK")]),
            antivirus=HostAntivirus(name="Omega Sentinel AI", version="v10.0", alert_level=40, heuristic_sensitivity=5),
            employees=[
                EmployeeProfile(name="Root Executive", role="Master AI Controller", email="nexus@omega.supercore", awareness_level=SecurityAwarenessLevel.PARANOID, leaked_credential="root_master_key=SUPERCORE_DECRYPT_ALL"),
            ],
        ),
    }

    return nodes
