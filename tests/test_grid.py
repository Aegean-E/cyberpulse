"""Integration tests for living-grid simulation wired into the game engine."""

import unittest

from cyberpulse.engine import GameEngine
from cyberpulse.models import NodeStatus
from cyberpulse.world import MARKET_CEILING, MARKET_FLOOR


class TestGridIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(seed=5)

    def test_advance_turn_moves_clock_daemons_and_market(self):
        world = self.engine.state.world
        start_minute, start_day, start_turns = world.minute, world.day, self.engine.state.turns_elapsed

        self.engine.advance_turn()

        self.assertEqual(self.engine.state.turns_elapsed, start_turns + 1)
        self.assertEqual(world.minute, (start_minute + 15) % (24 * 60))
        self.assertEqual(world.day, start_day + ((start_minute + 15) // (24 * 60)))
        self.assertGreaterEqual(world.market_index, MARKET_FLOOR)
        self.assertLessEqual(world.market_index, MARKET_CEILING)

    def test_lay_low_advances_time_and_recovers_cpu(self):
        self.engine.state.world.alert_level = 0
        self.engine.state.world.turns_since_event = -50
        self.engine.deck.cpu_cycles = 0
        start_minute = self.engine.state.world.minute
        start_turns = self.engine.state.turns_elapsed

        ok, message = self.engine.lay_low(2)

        self.assertTrue(ok)
        self.assertEqual(self.engine.state.turns_elapsed, start_turns + 2)
        self.assertEqual(self.engine.state.world.minute, (start_minute + 30) % (24 * 60))
        self.assertEqual(self.engine.deck.cpu_cycles, 2)
        self.assertIn("LAY LOW", message)
        self.assertIn("2 turn", message)
        self.assertIn("CPU +2", message)

    def test_lay_low_rejects_invalid_input_and_terminal_runs(self):
        for bad in (0, 4, -1, "later"):
            ok, message = self.engine.lay_low(bad)
            self.assertFalse(ok, bad)
            self.assertIn("Lay low", message)

        for flag in ("is_game_over", "is_jacked_out", "is_victory"):
            engine = GameEngine(seed=5)
            engine.state.world.turns_since_event = -50
            setattr(engine.state, flag, True)
            start_turns = engine.state.turns_elapsed
            ok, message = engine.lay_low(1)
            self.assertFalse(ok, flag)
            self.assertIn("Cannot lay low", message)
            self.assertEqual(engine.state.turns_elapsed, start_turns)

    def test_tick_world_shift_changes_alert_decay(self):
        night = GameEngine(seed=11)
        morning = GameEngine(seed=11)
        for engine, minute in ((night, 2 * 60), (morning, 8 * 60)):
            engine.state.world.alert_level = 50
            engine.state.trace_percent = 20
            engine.state.world.turns_since_event = -50
            engine.state.world.minute = minute

        for _ in range(3):
            night.state.world.minute = 2 * 60
            morning.state.world.minute = 8 * 60
            night.tick_world()
            morning.tick_world()

        self.assertLess(night.state.world.alert_level, morning.state.world.alert_level)

    def test_breach_raises_alert_and_publishes_news(self):
        alert_before = self.engine.state.world.alert_level

        ok, _ = self.engine.complete_breach("node_proxy_a")

        self.assertTrue(ok)
        self.assertGreater(self.engine.state.world.alert_level, alert_before)
        headlines = " ".join(item.headline for item in self.engine.state.world.news)
        self.assertIn("Breach detected", headlines)

    def test_trace_thresholds_publish_news(self):
        self.engine.add_trace(55)
        self.engine.add_trace(30)

        headlines = " ".join(item.headline for item in self.engine.state.world.news)
        self.assertIn("50% NetWatch trace threshold", headlines)
        self.assertIn("80% trace", headlines)

    def test_patrol_pressure_adds_trace_at_high_alert(self):
        self.engine.state.world.alert_level = 90
        self.engine.state.trace_percent = 0

        self.engine.advance_turn()

        self.assertGreaterEqual(self.engine.state.trace_percent, 2)
        self.assertTrue(any("NETWATCH PATROL" in message for message in self.engine.state.message_log))

    def test_ambient_grid_events_fire_and_publish(self):
        self.engine.state.world.alert_level = 95
        self.engine.state.world.turns_since_event = 99
        event_messages = []

        for _ in range(60):
            self.engine.state.trace_percent = 0
            messages = self.engine.tick_world()
            event_messages.extend(m for m in messages if "[GRID EVENT]" in m)
            if event_messages:
                break

        self.assertTrue(event_messages, "expected an ambient grid event across hot ticks")
        self.assertTrue(any("[GRID EVENT]" in message for message in self.engine.state.message_log))
        self.assertGreaterEqual(len(self.engine.state.world.news), 1)

    def test_grid_resecures_host_and_recalls_daemons(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.deck.cpu_cycles = 6
        self.engine.deploy_daemon("192.168.1.10", "keylogger")
        node = self.engine.nodes["node_proxy_a"]
        node.breached_turn = 0
        self.engine.state.world.alert_level = 100

        resecured = False
        for _ in range(60):
            self.engine.state.trace_percent = 0
            self.engine.state.world.alert_level = 100
            self.engine.advance_turn()
            if node.status == NodeStatus.DISCOVERED:
                resecured = True
                break

        self.assertTrue(resecured, "expected the grid to re-secure the breached host")
        self.assertGreaterEqual(self.engine.state.world.resecured_count, 1)
        self.assertEqual(self.engine.deck.active_daemons, [])
        self.assertTrue(any("GRID RESPONSE" in message for message in self.engine.state.message_log))

    def test_rebreach_after_resecure_pays_nothing(self):
        self.engine.complete_breach("node_proxy_a")
        node = self.engine.nodes["node_proxy_a"]
        unbanked = self.engine.state.unbanked_creds
        combo = self.engine.state.combo_streak
        quest = self.engine._find_quest("q_gateway")
        quest_progress = quest.progress

        node.status = NodeStatus.DISCOVERED
        ok, msg = self.engine.complete_breach("node_proxy_a")

        self.assertTrue(ok)
        self.assertIn("No fresh data", msg)
        self.assertEqual(self.engine.state.unbanked_creds, unbanked)
        self.assertEqual(self.engine.state.combo_streak, combo)
        self.assertEqual(quest.progress, quest_progress)

    def test_world_summary_and_news_feed_shapes(self):
        self.engine.complete_breach("node_proxy_a")

        summary = self.engine.world_summary()

        self.assertIn("clock", summary)
        self.assertIn("alert_level", summary)
        self.assertIn("market_multiplier", summary)
        self.assertTrue(summary["news"])
        self.assertIn("headline", summary["news"][0])

    def test_hunter_deployment_on_alert_threshold(self):
        self.engine.state.world.alert_level = 75
        self.assertEqual(len(self.engine.state.world.hunters), 0)

        self.engine.advance_turn()

        self.assertEqual(len(self.engine.state.world.hunters), 1)
        hunter = self.engine.state.world.hunters[0]
        self.assertEqual(hunter.status, "hunting")
        self.assertTrue(any("NETWATCH HUNTER" in m for m in self.engine.state.message_log))

    def test_hunter_advances_and_intercepts_player(self):
        self.engine.state.world.alert_level = 70
        self.engine.advance_turn()
        hunter = self.engine.state.world.hunters[0]

        # Place hunter in adjacent node to player
        curr_node = self.engine.get_current_node()
        adj_id = curr_node.connected_ids[0]
        hunter.current_node_id = adj_id
        hunter.status = "hunting"
        trace_before = self.engine.state.trace_percent
        self.engine.deck.cpu_cycles = 5

        # Advancing turn should move hunter into current_node_id and intercept!
        self.engine.advance_turn()

        self.assertEqual(hunter.status, "intercepted")
        self.assertEqual(hunter.current_node_id, curr_node.node_id)
        self.assertGreaterEqual(self.engine.state.trace_percent, trace_before + 15)
        self.assertEqual(self.engine.deck.cpu_cycles, 3)  # drained by 2
        self.assertTrue(any("NETWATCH CLASH" in m for m in self.engine.state.message_log))

    def test_hunter_scrambled_by_spoof_and_wipe(self):
        self.engine.state.world.alert_level = 70
        self.engine.advance_turn()
        hunter = self.engine.state.world.hunters[0]
        self.assertEqual(hunter.confused_turns, 0)

        self.engine.deck.cpu_cycles = 5
        self.engine.state.trace_percent = 50
        ok, _ = self.engine.spoof_ip()
        self.assertTrue(ok)
        self.assertGreater(hunter.confused_turns, 0)

    def test_counter_hunter_with_logic_bomb(self):
        self.engine.state.world.alert_level = 70
        self.engine.advance_turn()
        hunter = self.engine.state.world.hunters[0]
        self.engine.deck.exploits.append("logic_bomb")

        ok, msg = self.engine.counter_hunter(method="logic_bomb")
        self.assertTrue(ok)
        self.assertEqual(hunter.status, "neutralized")
        self.assertNotIn("logic_bomb", self.engine.deck.exploits)
        self.assertIn("neutralized", msg.lower())

    def test_counter_hunter_with_ghost_protocol(self):
        self.engine.state.world.alert_level = 70
        self.engine.advance_turn()
        hunter = self.engine.state.world.hunters[0]
        self.engine.deck.exploits.append("ghost_protocol")

        ok, msg = self.engine.counter_hunter(method="ghost_protocol")
        self.assertTrue(ok)
        self.assertGreater(hunter.confused_turns, 0)
        self.assertNotIn("ghost_protocol", self.engine.deck.exploits)
        self.assertIn("ghost_protocol", msg.lower())


if __name__ == "__main__":
    unittest.main()
