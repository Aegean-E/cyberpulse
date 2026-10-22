"""Unit tests for the living-grid world simulation module."""

import unittest

from cyberpulse.models import (
    FirewallRule,
    GameState,
    HostAntivirus,
    HostFirewall,
    NetWatchHunter,
    Node,
    NodeStatus,
    NodeType,
    PortService,
    WorldState,
)
from cyberpulse.world import (
    ALERT_TIERS,
    AMBIENT_EVENTS,
    HUNTER_ALERT_THRESHOLD,
    MARKET_CEILING,
    MARKET_FLOOR,
    SHIFT_PROFILES,
    adjust_alert,
    adjust_market,
    advance_clock,
    alert_tier,
    ambient_event_for,
    apply_resecure,
    apply_social_shift,
    calculate_distance,
    clock_label,
    clock_minute_text,
    deploy_hunter,
    drift_market,
    find_shortest_path,
    format_news_item,
    market_multiplier,
    neutralize_hunter,
    patrol_pressure,
    plan_resecures,
    record_news,
    shift_effect_text,
    shift_name,
    shift_profile,
    step_hunter,
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


class TestShiftProfiles(unittest.TestCase):
    def test_shift_profile_boundaries(self):
        cases = (
            (0, "late_night", "Late Night"),
            (5 * 60 + 59, "late_night", "Late Night"),
            (6 * 60, "morning", "Morning"),
            (11 * 60 + 59, "morning", "Morning"),
            (12 * 60, "afternoon", "Afternoon"),
            (17 * 60 + 59, "afternoon", "Afternoon"),
            (18 * 60, "evening", "Evening"),
            (23 * 60 + 59, "evening", "Evening"),
        )
        for minute, key, label in cases:
            profile = shift_profile(minute)
            self.assertEqual(profile.key, key, minute)
            self.assertEqual(profile.label, label, minute)
            self.assertEqual(shift_name(minute), label, minute)
            self.assertIs(profile, SHIFT_PROFILES[key])

    def test_shift_modifiers_create_distinct_tradeoffs(self):
        night = shift_profile(2 * 60)
        morning = shift_profile(8 * 60)
        afternoon = shift_profile(13 * 60)
        evening = shift_profile(20 * 60)

        self.assertGreater(night.market_bias, 0)
        self.assertGreater(night.alert_decay_bonus, 0)
        self.assertLess(night.resecure_chance_delta, 0)
        self.assertGreater(night.hunter_threshold_delta, 0)

        self.assertLess(morning.market_bias, 0)
        self.assertGreater(morning.resecure_chance_delta, afternoon.resecure_chance_delta)
        self.assertLess(afternoon.hunter_threshold_delta, morning.hunter_threshold_delta)
        self.assertGreater(evening.alert_decay_bonus, 0)

    def test_shift_effect_text_is_human_readable(self):
        text = shift_effect_text(shift_profile(2 * 60))
        self.assertIn("market +5%", text)
        self.assertIn("re-secure -10%", text)
        self.assertIn(f"hunters at {HUNTER_ALERT_THRESHOLD + 10}%+", text)
        self.assertIn("alert decay +1/turn", text)

    def test_shift_profiles_carry_social_deltas(self):
        self.assertAlmostEqual(SHIFT_PROFILES["late_night"].social_delta, -0.15)
        self.assertAlmostEqual(SHIFT_PROFILES["morning"].social_delta, 0.10)
        self.assertAlmostEqual(SHIFT_PROFILES["afternoon"].social_delta, 0.0)
        self.assertAlmostEqual(SHIFT_PROFILES["evening"].social_delta, 0.05)

    def test_shift_effect_text_documents_social_surface(self):
        text = shift_effect_text(shift_profile(2 * 60))
        self.assertIn("social", text)

    def test_apply_social_shift_clamps_and_modifies(self):
        self.assertAlmostEqual(apply_social_shift(0.75, 2 * 60), 0.60)  # late night -0.15
        self.assertAlmostEqual(apply_social_shift(0.75, 8 * 60), 0.85)  # morning +0.10
        self.assertAlmostEqual(apply_social_shift(0.02, 2 * 60), 0.05)  # floor
        self.assertAlmostEqual(apply_social_shift(0.99, 8 * 60), 0.95)  # ceiling

    def test_world_summary_documents_the_shift(self):
        summary = world_summary(WorldState(minute=20 * 60))
        self.assertEqual(summary["shift_key"], "evening")
        self.assertEqual(summary["shift_tagline"], SHIFT_PROFILES["evening"].tagline)
        self.assertEqual(
            summary["shift_modifiers"]["hunter_threshold"],
            HUNTER_ALERT_THRESHOLD + SHIFT_PROFILES["evening"].hunter_threshold_delta,
        )
        self.assertIn("re-secure", summary["shift_effect"])

    def test_alert_tier_boundaries(self):
        self.assertEqual(alert_tier(0), "GREEN")
        self.assertEqual(alert_tier(29), "GREEN")
        self.assertEqual(alert_tier(30), "AMBER")
        self.assertEqual(alert_tier(54), "AMBER")
        self.assertEqual(alert_tier(55), "RED")
        self.assertEqual(alert_tier(74), "RED")
        self.assertEqual(alert_tier(75), "BLACK")
        self.assertEqual(alert_tier(100), "BLACK")
        self.assertEqual(alert_tier(-5), "GREEN")
        self.assertEqual(alert_tier(150), "BLACK")

    def test_world_summary_includes_alert_tier(self):
        summary = world_summary(WorldState(alert_level=62))
        self.assertEqual(summary["alert_tier"], "RED")

        summary_black = world_summary(WorldState(alert_level=90))
        self.assertEqual(summary_black["alert_tier"], "BLACK")

    def test_alert_tiers_are_ordered_and_unique(self):
        thresholds = [bound for bound, _ in ALERT_TIERS]
        labels = [label for _, label in ALERT_TIERS]
        self.assertEqual(thresholds, sorted(thresholds))
        self.assertEqual(len(set(labels)), len(labels))
        self.assertIn("GREEN", labels)



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

    def test_market_drift_shift_bias_moves_the_target(self):
        neutral = WorldState(alert_level=10, market_index=1.0)
        marked_up = WorldState(alert_level=10, market_index=1.0)
        for tick in range(60):
            drift_market(neutral, world_rng(3, tick, "drift"))
            drift_market(marked_up, world_rng(3, tick, "drift"), bias=0.20)
        self.assertGreater(marked_up.market_index, neutral.market_index)
        self.assertLessEqual(marked_up.market_index, MARKET_CEILING)

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

    def test_resecure_chance_delta_changes_response_rate(self):
        nodes = {
            "node_a": make_node("node_a", security_level=1, breached_turn=0),
            "node_b": make_node("node_b", security_level=1, breached_turn=0),
        }
        slow = sum(
            1 for tick in range(80) if plan_resecures(11, tick, 100, nodes, "safe", chance_delta=-0.09)
        )
        fast = sum(
            1 for tick in range(80) if plan_resecures(11, tick, 100, nodes, "safe", chance_delta=0.09)
        )
        self.assertGreater(fast, slow)

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


class TestNetWatchHunterSimulation(unittest.TestCase):
    def setUp(self):
        # Build a small network: n1 - n2 - n3 - n4, and n_core - n2
        self.nodes = {
            "n1": Node("n1", "Host 1", NodeType.GATEWAY, 1, NodeStatus.BREACHED, connected_ids=["n2"]),
            "n2": Node("n2", "Host 2", NodeType.FIREWALL, 2, NodeStatus.DISCOVERED, connected_ids=["n1", "n3", "n_core"]),
            "n3": Node("n3", "Host 3", NodeType.DATA_VAULT, 3, NodeStatus.LOCKED, connected_ids=["n2", "n4"]),
            "n4": Node("n4", "Host 4", NodeType.ICE_DEFENSE, 4, NodeStatus.LOCKED, connected_ids=["n3"]),
            "n_core": Node("n_core", "Nexus Core", NodeType.CENTRAL_CORE, 5, NodeStatus.LOCKED, connected_ids=["n2"]),
            "n_iso": Node("n_iso", "Airgap Host", NodeType.GATEWAY, 1, NodeStatus.LOCKED, connected_ids=[]),
        }

    def test_hunter_model_roundtrip(self):
        h = NetWatchHunter(
            hunter_id="h1",
            name="Aegis-9",
            current_node_id="n_core",
            status="hunting",
            turns_active=3,
            target_node_id="n1",
            confused_turns=1,
        )
        data = h.to_dict()
        restored = NetWatchHunter.from_dict(data)
        self.assertEqual(restored.hunter_id, "h1")
        self.assertEqual(restored.name, "Aegis-9")
        self.assertEqual(restored.current_node_id, "n_core")
        self.assertEqual(restored.status, "hunting")
        self.assertEqual(restored.turns_active, 3)
        self.assertEqual(restored.confused_turns, 1)

    def test_world_state_with_hunters_roundtrip(self):
        world = WorldState(alert_level=75)
        h = NetWatchHunter(hunter_id="h_alpha", current_node_id="n_core")
        world.hunters.append(h)
        data = world.to_dict()
        restored = WorldState.from_dict(data)
        self.assertEqual(len(restored.hunters), 1)
        self.assertEqual(restored.hunters[0].hunter_id, "h_alpha")
        self.assertEqual(restored.hunters[0].current_node_id, "n_core")

    def test_find_shortest_path_and_distance(self):
        path = find_shortest_path(self.nodes, "n1", "n4")
        self.assertEqual(path, ["n1", "n2", "n3", "n4"])
        self.assertEqual(calculate_distance(self.nodes, "n1", "n4"), 3)

        # Same node
        self.assertEqual(find_shortest_path(self.nodes, "n1", "n1"), ["n1"])
        self.assertEqual(calculate_distance(self.nodes, "n1", "n1"), 0)

        # Isolated unreachable node
        self.assertEqual(find_shortest_path(self.nodes, "n1", "n_iso"), [])
        self.assertEqual(calculate_distance(self.nodes, "n1", "n_iso"), -1)

    def test_deploy_hunter_threshold(self):
        world = WorldState(alert_level=40)
        deployed = deploy_hunter(world, self.nodes, tick=5)
        self.assertIsNone(deployed)
        self.assertEqual(len(world.hunters), 0)

        # At alert >= 60
        world.alert_level = 65
        deployed = deploy_hunter(world, self.nodes, tick=6)
        self.assertIsNotNone(deployed)
        self.assertEqual(deployed.current_node_id, "n_core")
        self.assertEqual(len(world.hunters), 1)
        self.assertEqual(deployed.status, "hunting")
        self.assertIn("deployed", world.news[-1].headline.lower())

        # No duplicate deployment while active
        dup = deploy_hunter(world, self.nodes, tick=7)
        self.assertIsNone(dup)
        self.assertEqual(len(world.hunters), 1)

        # An intercepted hunter still holds the sector: do not stack a second clamp.
        world.hunters[0].status = "intercepted"
        clamped = deploy_hunter(world, self.nodes, tick=8)
        self.assertIsNone(clamped)
        self.assertEqual(len(world.hunters), 1)

    def test_deploy_hunter_threshold_follows_the_shift(self):
        night = WorldState(alert_level=65, minute=2 * 60)
        self.assertIsNone(deploy_hunter(night, self.nodes, tick=1))
        self.assertEqual(night.hunters, [])

        night.alert_level = 70
        self.assertIsNotNone(deploy_hunter(night, self.nodes, tick=2))

        afternoon = WorldState(alert_level=55, minute=13 * 60)
        self.assertIsNotNone(deploy_hunter(afternoon, self.nodes, tick=1))

        morning = WorldState(alert_level=60, minute=8 * 60)
        self.assertIsNotNone(deploy_hunter(morning, self.nodes, tick=1))

    def test_step_hunter_moves_and_intercepts(self):
        rng = world_rng(42, 1, "test")
        hunter = NetWatchHunter("h1", current_node_id="n_core", status="hunting")

        # Player at n1. Shortest path from n_core to n1: n_core -> n2 -> n1.
        res1 = step_hunter(hunter, self.nodes, player_node_id="n1", rng=rng)
        self.assertEqual(res1["action"], "moved")
        self.assertEqual(hunter.current_node_id, "n2")
        self.assertEqual(hunter.turns_active, 1)

        # Step 2: moves into player node n1 -> interception!
        res2 = step_hunter(hunter, self.nodes, player_node_id="n1", rng=rng)
        self.assertEqual(res2["action"], "intercepted")
        self.assertEqual(hunter.current_node_id, "n1")
        self.assertEqual(hunter.status, "intercepted")

    def test_step_hunter_confused(self):
        rng = world_rng(42, 1, "test")
        hunter = NetWatchHunter("h1", current_node_id="n2", status="hunting", confused_turns=2)
        res = step_hunter(hunter, self.nodes, player_node_id="n4", rng=rng)
        self.assertEqual(res["action"], "confused")
        self.assertEqual(hunter.confused_turns, 1)

    def test_neutralize_hunter(self):
        hunter = NetWatchHunter("h1", status="hunting")
        msg = neutralize_hunter(hunter, "logic_bomb")
        self.assertEqual(hunter.status, "neutralized")
        self.assertIn("neutralized", msg.lower())


if __name__ == "__main__":
    unittest.main()
