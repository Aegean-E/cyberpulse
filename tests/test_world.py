"""Unit tests for the living-grid world simulation module."""

import unittest

from cyberpulse.models import (
    FirewallRule,
    GameState,
    HostAntivirus,
    HostFirewall,
    Node,
    NodeStatus,
    NodeType,
    PortService,
    WorldState,
)
from cyberpulse.world import (
    AMBIENT_EVENTS,
    MARKET_CEILING,
    MARKET_FLOOR,
    adjust_alert,
    adjust_market,
    advance_clock,
    ambient_event_for,
    apply_resecure,
    clock_label,
    clock_minute_text,
    drift_market,
    format_news_item,
    market_multiplier,
    patrol_pressure,
    plan_resecures,
    record_news,
    shift_name,
    world_rng,
    world_summary,
)


def make_node(
    node_id: str = "node_x",
    node_type: str = NodeType.FIREWALL,
    security_level: int = 2,
    status: str = NodeStatus.BREACHED,
    breached_turn: int = 0,
) -> Node:
    return Node(
        node_id=node_id,
        name=f"Host {node_id}",
        node_type=node_type,
        security_level=security_level,
        status=status,
        breached_turn=breached_turn,
    )


class TestWorldClock(unittest.TestCase):
    def test_clock_text_and_shifts(self):
        self.assertEqual(clock_minute_text(0), "00:00")
        self.assertEqual(clock_minute_text(9 * 60 + 5), "09:05")
        self.assertEqual(clock_minute_text(24 * 60 + 30), "00:30")
        self.assertEqual(shift_name(2 * 60), "Late Night")
        self.assertEqual(shift_name(8 * 60), "Morning")
        self.assertEqual(shift_name(15 * 60), "Afternoon")
        self.assertEqual(shift_name(21 * 60), "Evening")

    def test_advance_clock_rolls_days(self):
        world = WorldState(minute=23 * 60 + 45, day=1)
        advance_clock(world)
        self.assertEqual(world.minute, 0)
        self.assertEqual(world.day, 2)
        advance_clock(world, turns=8)
        self.assertEqual(world.minute, 2 * 60)
        self.assertEqual(world.day, 2)

    def test_clock_label_and_summary(self):
        world = WorldState(minute=13 * 60, day=3, alert_level=42, market_index=1.125)
        self.assertEqual(clock_label(world), "Day 3 13:00 (Afternoon)")
        summary = world_summary(world)
        self.assertEqual(summary["shift"], "Afternoon")
        self.assertEqual(summary["alert_level"], 42)
        self.assertEqual(summary["market_multiplier"], 1.125)
        self.assertEqual(summary["news_count"], 0)


class TestWorldAlertAndMarket(unittest.TestCase):
    def test_alert_clamps(self):
        world = WorldState(alert_level=95)
        self.assertEqual(adjust_alert(world, 20), 100)
        self.assertEqual(adjust_alert(world, -500), 0)

    def test_market_bounds_and_multiplier(self):
        world = WorldState(market_index=1.0)
        self.assertEqual(adjust_market(world, 10.0), MARKET_CEILING)
        self.assertEqual(adjust_market(world, -10.0), MARKET_FLOOR)
        self.assertEqual(market_multiplier(world), MARKET_FLOOR)

    def test_market_drift_is_bounded_and_deterministic(self):
        first = WorldState(alert_level=100)
        second = WorldState(alert_level=100)
        for tick in range(25):
            drift_market(first, world_rng(7, tick, "drift"))
            drift_market(second, world_rng(7, tick, "drift"))
        self.assertEqual(first.market_index, second.market_index)
        self.assertGreaterEqual(first.market_index, MARKET_FLOOR)
        self.assertLessEqual(first.market_index, MARKET_CEILING)

    def test_patrol_pressure_thresholds(self):
        self.assertEqual(patrol_pressure(WorldState(alert_level=10)), 0)
        self.assertEqual(patrol_pressure(WorldState(alert_level=50)), 1)
        self.assertEqual(patrol_pressure(WorldState(alert_level=99)), 2)


class TestNewsFeed(unittest.TestCase):
    def test_record_news_formats_and_trims(self):
        world = WorldState(minute=7 * 60 + 30, day=2)
        for index in range(80):
            record_news(world, index, "GridWire", f"headline {index}")
        self.assertEqual(len(world.news), 60)
        self.assertEqual(world.news[0].headline, "headline 20")
        last = world.news[-1]
        self.assertEqual(format_news_item(last), "[Day 2 07:30] GridWire: headline 79")


class TestAmbientEvents(unittest.TestCase):
    def test_quiet_turn_when_cooling_down(self):
        self.assertIsNone(ambient_event_for(seed=1, tick=5, alert_level=10, turns_since_event=0))

    def test_low_alert_never_picks_negative_events(self):
        picked = {
            event.key
            for tick in range(90)
            if (event := ambient_event_for(seed=3, tick=tick, alert_level=10, turns_since_event=99)) is not None
        }
        negative = {e.key for e in AMBIENT_EVENTS if e.tone == "negative"}
        self.assertFalse(picked & negative)

    def test_high_alert_can_pick_negative_events(self):
        picked = {
            event.key
            for tick in range(120)
            if (event := ambient_event_for(seed=11, tick=tick, alert_level=95, turns_since_event=99)) is not None
        }
        negative = {e.key for e in AMBIENT_EVENTS if e.tone == "negative"}
        self.assertTrue(picked & negative)

    def test_event_roll_is_deterministic(self):
        first = ambient_event_for(seed=42, tick=17, alert_level=60, turns_since_event=9)
        second = ambient_event_for(seed=42, tick=17, alert_level=60, turns_since_event=9)
        self.assertEqual(first, second)


class TestGridResponse(unittest.TestCase):
    def test_no_resecure_below_alert_threshold(self):
        nodes = {"a": make_node("a", breached_turn=0)}
        self.assertEqual(plan_resecures(5, 50, 20, nodes, "safe"), [])

    def test_recent_breach_and_current_node_are_exempt(self):
        recent = {"a": make_node("a", breached_turn=48)}
        self.assertEqual(plan_resecures(5, 50, 99, recent, "safe"), [])

        ready = {"a": make_node("a", breached_turn=0)}
        self.assertEqual(plan_resecures(5, 50, 99, ready, "a"), [])

    def test_core_is_never_resecured(self):
        core = {core_id: make_node(core_id, node_type=NodeType.CENTRAL_CORE, security_level=5, breached_turn=0)
                for core_id in ("node_core",)}
        self.assertEqual(plan_resecures(5, 50, 100, core, "safe"), [])

    def test_high_alert_eventually_resecures_and_is_deterministic(self):
        nodes = {
            "node_a": make_node("node_a", security_level=3, breached_turn=0),
            "node_b": make_node("node_b", security_level=1, breached_turn=0),
        }
        first = [plan_resecures(9, tick, 100, nodes, "safe") for tick in range(40)]
        second = [plan_resecures(9, tick, 100, nodes, "safe") for tick in range(40)]
        self.assertEqual(first, second)
        self.assertTrue(any(first), "expected at least one re-secure across 40 hot ticks")
        for picks in first:
            self.assertLessEqual(len(picks), 1)
            for node_id in picks:
                self.assertIn(node_id, nodes)

    def test_apply_resecure_restores_defenses(self):
        node = make_node("node_a", breached_turn=4)
        node.logs_cleared = True
        node.ports = [PortService(port=22, service="ssh", version="OpenSSH 7.2", breached=True)]
        node.firewall = HostFirewall(rules=[FirewallRule(rule_id="r1", port=22, bypassed=True)])
        node.firewall.tampered = True
        node.antivirus = HostAntivirus(alert_level=80, evaded=True)

        message = apply_resecure(node)

        self.assertEqual(node.status, NodeStatus.DISCOVERED)
        self.assertFalse(node.ports[0].breached)
        self.assertFalse(node.logs_cleared)
        self.assertFalse(node.firewall.tampered)
        self.assertFalse(node.firewall.rules[0].bypassed)
        self.assertEqual(node.antivirus.alert_level, 0)
        self.assertFalse(node.antivirus.evaded)
        self.assertIn("re-secured", message)


class TestWorldPersistence(unittest.TestCase):
    def test_world_state_roundtrip(self):
        world = WorldState(minute=555, day=4, alert_level=66, market_index=1.07, resecured_count=2)
        record_news(world, 3, "NetWatch", "Host re-secured", tone="alert")
        restored = WorldState.from_dict(world.to_dict())
        self.assertEqual(restored.alert_level, 66)
        self.assertEqual(restored.day, 4)
        self.assertEqual(restored.minute, 555)
        self.assertEqual(restored.news[0].headline, "Host re-secured")

    def test_legacy_save_without_world_gets_defaults(self):
        legacy = {
            "seed": 42,
            "current_node_id": "node_gateway",
            "trace_percent": 12,
        }
        state = GameState.from_dict(legacy)
        self.assertEqual(state.trace_percent, 12)
        self.assertEqual(state.world.alert_level, 10)
        self.assertEqual(state.world.day, 1)

    def test_game_state_roundtrip_keeps_world(self):
        state = GameState(seed=7, current_node_id="node_gateway")
        state.world.alert_level = 71
        record_news(state.world, 12, "GridWire", "Grid under pressure")
        restored = GameState.from_dict(state.to_dict())
        self.assertEqual(restored.world.alert_level, 71)
        self.assertEqual(len(restored.world.news), 1)


if __name__ == "__main__":
    unittest.main()
