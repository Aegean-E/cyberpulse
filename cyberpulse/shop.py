"""Black market cyberdeck upgrades and exploit vendor for CyberPulse."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from cyberpulse.models import CyberDeck


@dataclass
class ShopItem:
    item_id: str
    name: str
    description: str
    cost: int
    category: str  # "hardware" or "exploit"
    max_level: int = 1


CATALOG: Dict[str, ShopItem] = {
    "overclock_cpu": ShopItem(
        item_id="overclock_cpu",
        name="CPU Overclock Module",
        description="+2 Max CPU Cycles (current max capacity increased)",
        cost=150,
        category="hardware",
        max_level=3,
    ),
    "expand_ram": ShopItem(
        item_id="expand_ram",
        name="Hyper-Threaded RAM Array",
        description="+32MB High-Speed System Memory",
        cost=200,
        category="hardware",
        max_level=3,
    ),
    "ice_dampener": ShopItem(
        item_id="ice_dampener",
        name="Subnet ICE Dampener",
        description="Passively reduces trace accumulation rate by 20%",
        cost=250,
        category="hardware",
        max_level=3,
    ),
    "logic_bomb": ShopItem(
        item_id="logic_bomb",
        name="Logic Bomb Exploit Chip",
        description="Injects corrupted memory registers into target node",
        cost=300,
        category="exploit",
        max_level=1,
    ),
    "ghost_protocol": ShopItem(
        item_id="ghost_protocol",
        name="Ghost Protocol Exploit Chip",
        description="Masks active neural link from surveillance subnets",
        cost=350,
        category="exploit",
        max_level=1,
    ),
}


class BlackMarketShop:
    """Manages purchasing of cyberdeck hardware upgrades and exploit chips."""

    def __init__(self, catalog: Optional[Dict[str, ShopItem]] = None):
        self.catalog = catalog or CATALOG

    def list_available(self, deck: CyberDeck) -> List[Dict[str, Any]]:
        """List all shop items and current upgrade status."""
        items = []
        for item_id, item in self.catalog.items():
            if item.item_id == "overclock_cpu":
                cur_lvl = deck.overclock_level
            elif item.item_id == "expand_ram":
                cur_lvl = deck.ram_boost_level
            elif item.item_id == "ice_dampener":
                cur_lvl = deck.ice_dampener_level
            else:
                cur_lvl = 1 if item_id in deck.exploits else 0

            can_buy = deck.cryptocreds >= item.cost and cur_lvl < item.max_level
            items.append({
                "item_id": item.item_id,
                "name": item.name,
                "description": item.description,
                "cost": item.cost,
                "current_level": cur_lvl,
                "max_level": item.max_level,
                "can_buy": can_buy,
            })
        return items

    def purchase(self, deck: CyberDeck, item_id: str) -> Tuple[bool, str]:
        """Attempt to buy an item and apply its stat bonuses to deck."""
        if item_id not in self.catalog:
            return False, f"Unknown black market item '{item_id}'."

        item = self.catalog[item_id]
        if deck.cryptocreds < item.cost:
            return False, f"Insufficient funds: need {item.cost} CryptoCreds (have {deck.cryptocreds})."

        if item.item_id == "overclock_cpu":
            if deck.overclock_level >= item.max_level:
                return False, "CPU Overclock already at maximum level."
            deck.cryptocreds -= item.cost
            deck.overclock_level += 1
            deck.max_cpu += 2
            deck.cpu_cycles += 2
            return True, f"🛠️ Installed {item.name}! Max CPU is now {deck.max_cpu}."

        if item.item_id == "expand_ram":
            if deck.ram_boost_level >= item.max_level:
                return False, "RAM Array already at maximum level."
            deck.cryptocreds -= item.cost
            deck.ram_boost_level += 1
            deck.max_ram += 32
            deck.ram_mb += 32
            return True, f"🛠️ Installed {item.name}! Max RAM is now {deck.max_ram}MB."

        if item.item_id == "ice_dampener":
            if deck.ice_dampener_level >= item.max_level:
                return False, "ICE Dampener already at maximum level."
            deck.cryptocreds -= item.cost
            deck.ice_dampener_level += 1
            return True, f"🛠️ Installed {item.name}! Trace mitigation active (Lvl {deck.ice_dampener_level})."

        if item.category == "exploit":
            if item.item_id in deck.exploits:
                return False, f"Exploit '{item.name}' is already loaded in deck memory."
            deck.cryptocreds -= item.cost
            deck.exploits.append(item.item_id)
            return True, f"💾 Loaded {item.name} into deck firmware."

        return False, "Could not process transaction."
