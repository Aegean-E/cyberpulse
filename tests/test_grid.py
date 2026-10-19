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


if __name__ == "__main__":
    unittest.main()
