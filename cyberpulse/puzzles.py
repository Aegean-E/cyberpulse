"""Interactive and deterministic cyberpunk hacking mini-game puzzles with near-miss feedback."""

import random
from typing import List, Optional, Tuple


class FrequencyPuzzle:
    """Tuning resonance frequency puzzle with near-miss feedback mechanics."""

    def __init__(self, target_freq: float, tolerance: float = 0.5):
        self.target_freq = round(target_freq, 1)
        self.tolerance = tolerance
        self.attempts_left = 3
        self.near_miss: bool = False

    @classmethod
    def generate(cls, seed: int) -> "FrequencyPuzzle":
        rng = random.Random(seed)
        freq = rng.uniform(20.0, 99.0)
        return cls(target_freq=freq, tolerance=0.8)

    def tune(self, guess: float) -> Tuple[bool, str]:
        """Test a frequency guess with near-miss detection."""
        self.attempts_left -= 1
        diff = guess - self.target_freq
        if abs(diff) <= self.tolerance:
            self.near_miss = False
            return True, f"🎯 RESONANCE LOCKED! Frequency aligned at {guess:.1f} GHz."

        self.near_miss = abs(diff) <= (self.tolerance * 2.5)
        hint = "TOO HIGH" if diff > 0 else "TOO LOW"
        near_miss_text = " [⚡ NEAR-MISS! Resonance harmonic almost locked!]" if self.near_miss else ""

        if self.attempts_left <= 0:
            return False, f"❌ FREQUENCY LOCK FAILED! Target was {self.target_freq:.1f} GHz."
        return False, f"⚠️  Signal off: {hint}.{near_miss_text} Attempts remaining: {self.attempts_left}."


class BufferPuzzle:
    """Memory buffer sequence matching puzzle with partial alignment detection."""

    def __init__(self, matrix: List[List[str]], target_seq: List[str]):
        self.matrix = matrix
        self.target_seq = target_seq
        self.near_miss: bool = False

    @classmethod
    def generate(cls, seed: int) -> "BufferPuzzle":
        rng = random.Random(seed)
        hex_pool = ["1C", "E9", "7A", "BD", "55", "FF"]
        matrix = [[rng.choice(hex_pool) for _ in range(4)] for _ in range(4)]
        seq_len = 2
        seq = [rng.choice(matrix[r]) for r in range(seq_len)]
        return cls(matrix=matrix, target_seq=seq)

    def verify_sequence(self, player_seq: List[str]) -> Tuple[bool, str]:
        """Verify whether player's sequence matches with near-miss feedback."""
        if player_seq == self.target_seq:
            self.near_miss = False
            return True, "💾 BUFFER OVERFLOW EXPLOIT EXECUTED! Memory injected."

        self.near_miss = len(player_seq) > 0 and len(self.target_seq) > 0 and player_seq[0] == self.target_seq[0]
        near_miss_text = " [⚡ NEAR-MISS! Primary buffer block aligned!]" if self.near_miss else ""
        return False, f"❌ BUFFER CORRUPTION! Expected {self.target_seq}, received {player_seq}.{near_miss_text}"


class HashCrackPuzzle:
    """Cryptographic password / hash cracking cipher puzzle with single-letter near miss."""

    WORDS = ["NEXUS", "CYBER", "GHOST", "PULSE", "LASER", "NEONX", "PROXY", "VIPER"]

    def __init__(self, target_word: str, word_list: List[str]):
        self.target_word = target_word.upper()
        self.word_list = [w.upper() for w in word_list]
        self.attempts_left = 4
        self.near_miss: bool = False

    @classmethod
    def generate(cls, seed: int) -> "HashCrackPuzzle":
        rng = random.Random(seed)
        pool = rng.sample(cls.WORDS, 5)
        secret = rng.choice(pool)
        return cls(target_word=secret, word_list=pool)

    def guess(self, candidate: str) -> Tuple[bool, str]:
        """Evaluate a guess and return matching character count with near-miss detection."""
        self.attempts_left -= 1
        candidate = candidate.upper().strip()

        if candidate == self.target_word:
            self.near_miss = False
            return True, f"🔓 ACCESS GRANTED! Password hash cracked: '{self.target_word}'."

        matches = sum(1 for a, b in zip(candidate, self.target_word) if a == b)
        self.near_miss = matches == (len(self.target_word) - 1)
        near_miss_text = " [⚡ CRITICAL NEAR-MISS! Only 1 character off!]" if self.near_miss else ""

        if self.attempts_left <= 0:
            return False, f"🔒 TERMINAL LOCKED! Correct hash key was '{self.target_word}'."

        return False, f"⚠️  ACCESS DENIED: {matches}/{len(self.target_word)} correct letters.{near_miss_text} Attempts left: {self.attempts_left}."
