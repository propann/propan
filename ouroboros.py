"""Ouroboros evolution engine."""

from __future__ import annotations

import ast
import logging
import os
import time
from typing import Optional

from groq import Groq


LOGGER = logging.getLogger(__name__)
SYSTEM_PROMPT = (
    "Tu es un moteur d'évolution de code. Optimise, complexifie ou rend plus créative la "
    "fonction Python suivante. Renvoie UNIQUEMENT le code de la fonction, sans markdown."
)
MODEL_NAME = "llama3-70b-8192"


def core_entity():
    """Core entity to be evolved."""
    return {
        "status": "origin",
        "timestamp": time.time(),
        "sequence": [1, 1, 2, 3, 5, 8],
    }


class EvolutionEngine:
    """Engine responsible for evolving core_entity."""

    def __init__(self, max_retries: int = 3, cooldown_seconds: float = 1.0) -> None:
        self.max_retries = max_retries
        self.cooldown_seconds = cooldown_seconds

    def _load_source(self) -> str:
        with open(__file__, "r", encoding="utf-8") as handle:
            return handle.read()

    def _extract_core_entity(self, source: str) -> Optional[str]:
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "core_entity":
                return ast.get_source_segment(source, node)
        return None

    def _request_evolution(self, function_source: str) -> Optional[str]:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            LOGGER.error("GROQ_API_KEY is not set")
            return None
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": function_source},
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        return content.strip() if content else None

    def _validate_function(self, function_source: str) -> bool:
        try:
            parsed = ast.parse(function_source)
        except SyntaxError as exc:
            LOGGER.warning("Generated code failed to parse: %s", exc)
            return False
        if not parsed.body or not isinstance(parsed.body[0], ast.FunctionDef):
            LOGGER.warning("Generated code is not a function")
            return False
        return True

    def _backup_source(self, source: str) -> None:
        with open("ouroboros.bak", "w", encoding="utf-8") as handle:
            handle.write(source)

    def _inject_core_entity(self, source: str, new_function_source: str) -> str:
        tree = ast.parse(source)
        start = None
        end = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "core_entity":
                start = node.lineno
                end = node.end_lineno
                break
        if start is None or end is None:
            raise RuntimeError("core_entity not found for injection")
        lines = source.splitlines()
        replacement_lines = new_function_source.splitlines()
        updated_lines = lines[: start - 1] + replacement_lines + lines[end:]
        return "\n".join(updated_lines) + "\n"

    def _write_source(self, source: str) -> None:
        with open(__file__, "w", encoding="utf-8") as handle:
            handle.write(source)

    def evolve_once(self) -> bool:
        source = self._load_source()
        function_source = self._extract_core_entity(source)
        if not function_source:
            LOGGER.error("Unable to locate core_entity in source")
            return False
        mutated_source = self._request_evolution(function_source)
        if not mutated_source:
            return False
        if not self._validate_function(mutated_source):
            return False
        self._backup_source(source)
        updated_source = self._inject_core_entity(source, mutated_source)
        self._write_source(updated_source)
        return True

    def run(self) -> None:
        logging.basicConfig(level=logging.INFO)
        attempt = 0
        while attempt < self.max_retries:
            try:
                if self.evolve_once():
                    LOGGER.info("Evolution successful; restarting process.")
                    os.execv(__file__, [__file__])
                LOGGER.info("Evolution failed; retrying.")
            except Exception as exc:
                LOGGER.exception("Evolution attempt failed: %s", exc)
            attempt += 1
            time.sleep(self.cooldown_seconds)
        LOGGER.error("Max retries reached; exiting.")


if __name__ == "__main__":
    EvolutionEngine().run()
