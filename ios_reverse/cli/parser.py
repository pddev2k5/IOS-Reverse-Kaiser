"""
Command Parser for /ios-reverse commands.

Parses commands like:
    /ios-reverse app.ipa unpack
    /ios-reverse app.ipa dump-full
    /ios-reverse app.ipa network --depth full
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CommandError(Exception):
    """Raised when command parsing fails."""
    pass


@dataclass
class ParsedCommand:
    """Parsed command result."""
    target: str
    intent: str
    depth: str = "standard"
    output_dir: Optional[str] = None
    options: dict = field(default_factory=dict)

    def __post_init__(self):
        # Validate
        if not self.target:
            raise CommandError("Target artifact is required")
        if not self.intent:
            raise CommandError("Intent is required")


class CommandParser:
    """
    Parser for /ios-reverse commands.

    Supported formats:
        /ios-reverse <target> <intent>
        /ios-reverse <target> <intent>-<depth>
        /ios-reverse <target> <intent> --depth <depth>
        /ios-reverse <target> <intent> -o <output_dir>
        /ios-reverse <target> <intent> --output <output_dir>
    """

    # Intent aliases
    INTENT_ALIASES = {
        # unpack
        "extract": "unpack",

        # inspect
        "examine": "inspect",

        # dump
        "inventory": "dump",

        # decompile
        "disassemble": "decompile",

        # macho
        "mach-o": "macho",
        "macho": "macho",

        # objc
        "objective-c": "objc",
        "objc": "objc",

        # swift
        "swift": "swift",

        # network
        "net": "network",
        "http": "network",
        "network": "network",

        # login-flow
        "auth": "login-flow",
        "login": "login-flow",
        "login-flow": "login-flow",

        # crypto
        "crypt": "crypto",
        "encryption": "crypto",
        "crypto": "crypto",

        # anti-analysis
        "anti-tamper": "anti-analysis",
        "anti-analysis": "anti-analysis",

        # ida
        "ida-pro": "ida",
        "ida": "ida",

        # runtime
        "dynamic": "runtime",
        "runtime": "runtime",

        # report
        "report": "report",

        # full
        "all": "full",
        "complete": "full",
        "full": "full",
    }

    # Supported intents
    SUPPORTED_INTENTS = {
        "unpack", "inspect", "dump", "decompile",
        "macho", "objc", "swift",
        "network", "login-flow", "crypto",
        "anti-analysis", "ida", "runtime",
        "report", "full"
    }

    # Depth aliases
    DEPTH_ALIASES = {
        "quick": "quick",
        "q": "quick",
        "standard": "standard",
        "std": "standard",
        "s": "standard",
        "deep": "deep",
        "d": "deep",
        "full": "full",
        "f": "full",
    }

    # Supported depths
    SUPPORTED_DEPTHS = {"quick", "standard", "deep", "full"}

    # Depth for each intent
    DEFAULT_DEPTHS = {
        "unpack": "quick",
        "inspect": "quick",
        "dump": "standard",
        "decompile": "standard",
        "macho": "standard",
        "objc": "standard",
        "swift": "standard",
        "network": "standard",
        "login-flow": "standard",
        "crypto": "standard",
        "anti-analysis": "quick",
        "ida": "deep",
        "runtime": "deep",
        "report": "standard",
        "full": "full",
    }

    def parse(self, command: str) -> ParsedCommand:
        """
        Parse a command string.

        Args:
            command: The command string to parse (without /ios-reverse prefix)

        Returns:
            ParsedCommand with extracted values

        Raises:
            CommandError: If parsing fails
        """
        # Clean up command
        command = command.strip()

        # Split into tokens
        tokens = self._tokenize(command)

        if len(tokens) < 2:
            raise CommandError(
                f"Expected at least 2 arguments: <target> <intent>. "
                f"Got: {len(tokens)}"
            )

        # First token is target
        target = tokens[0]

        # Second token is intent (possibly with depth suffix)
        intent_part = tokens[1]

        # Parse intent and depth from second token
        intent, depth = self._parse_intent_depth(intent_part)

        # Remaining tokens are options
        options = self._parse_options(tokens[2:])

        # Extract output directory (from -o or --output)
        output_dir = options.pop("output", None) or options.pop("o", None)

        # Extract depth override (from --depth)
        depth_override = options.pop("depth", None)
        if depth_override:
            depth = self._normalize_depth(depth_override)

        return ParsedCommand(
            target=target,
            intent=intent,
            depth=depth,
            output_dir=output_dir,
            options=options
        )

    def _tokenize(self, command: str) -> list:
        """Tokenize command string."""
        # Handle quoted strings
        tokens = []
        current = ""
        in_quote = False
        quote_char = None

        i = 0
        while i < len(command):
            char = command[i]

            if char in ('"', "'") and not in_quote:
                in_quote = True
                quote_char = char
            elif char == quote_char and in_quote:
                in_quote = False
                quote_char = None
            elif char.isspace() and not in_quote:
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += char

            i += 1

        if current:
            tokens.append(current)

        return tokens

    def _parse_intent_depth(self, part: str) -> tuple:
        """
        Parse intent and depth from a string like 'dump-full' or 'unpack'.

        Returns:
            Tuple of (intent, depth)
        """
        # Check for depth suffix
        depth_suffixes = ["-quick", "-standard", "-deep", "-full", "-q", "-s", "-d", "-f"]

        for suffix in depth_suffixes:
            if part.lower().endswith(suffix):
                intent = part[:-len(suffix)]
                depth = self._normalize_depth(suffix[1:])  # Remove leading hyphen
                intent = self._normalize_intent(intent)
                return intent, depth

        # No suffix, use default depth
        intent = self._normalize_intent(part)
        depth = self.DEFAULT_DEPTHS.get(intent, "standard")

        return intent, depth

    def _normalize_intent(self, intent: str) -> str:
        """Normalize intent to canonical form."""
        normalized = intent.lower().strip()

        if normalized in self.INTENT_ALIASES:
            return self.INTENT_ALIASES[normalized]

        if normalized not in self.SUPPORTED_INTENTS:
            raise CommandError(
                f"Unknown intent: '{intent}'. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_INTENTS))}"
            )

        return normalized

    def _normalize_depth(self, depth: str) -> str:
        """Normalize depth to canonical form."""
        normalized = depth.lower().strip()

        if normalized in self.DEPTH_ALIASES:
            return self.DEPTH_ALIASES[normalized]

        if normalized not in self.SUPPORTED_DEPTHS:
            raise CommandError(
                f"Unknown depth: '{depth}'. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_DEPTHS))}"
            )

        return normalized

    def _parse_options(self, tokens: list) -> dict:
        """Parse options from remaining tokens."""
        options = {}
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.startswith("--"):
                # Long option
                if "=" in token:
                    key, value = token[2:].split("=", 1)
                    options[key] = value
                else:
                    key = token[2:]
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                        options[key] = tokens[i + 1]
                        i += 1
                    else:
                        options[key] = True
            elif token.startswith("-"):
                # Short option
                key = token[1:]
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    options[key] = tokens[i + 1]
                    i += 1
                else:
                    options[key] = True
            else:
                # Positional argument (should not happen here)
                pass

            i += 1

        return options


def parse_command(command: str) -> ParsedCommand:
    """
    Convenience function to parse a command.

    Args:
        command: The command string to parse

    Returns:
        ParsedCommand with extracted values
    """
    parser = CommandParser()
    return parser.parse(command)
