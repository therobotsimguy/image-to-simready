#!/usr/bin/env python3
"""V5 AI Agents — uses Claude and Gemini APIs for reasoning.

Multi-agent parallel calls for speed.
Reads BEHAVIOR_DEFINITIONS.md as context for the 16×15 matrix.
"""

import json
import os
import sys
import threading
import time

_DIR = os.path.dirname(os.path.abspath(__file__))
_ASSETS_DIR = os.path.dirname(_DIR)
_TOOLS_DIR = os.path.dirname(_ASSETS_DIR)
_DOCS_DIR = os.path.join(_ASSETS_DIR, "docs")


def load_api_keys():
    with open(os.path.join(_TOOLS_DIR, "api_keys.json")) as f:
        return json.load(f)


def call_claude(api_key, prompt, model="claude-opus-4-6", max_tokens=8192):
    """Call Claude API."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def call_gemini(api_key, prompt, model="gemini-3.1-pro-preview"):
    """Call Gemini API."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=[prompt],
        config=types.GenerateContentConfig(max_output_tokens=8192, temperature=0.1),
    )
    return resp.text


def parse_json(text):
    """Extract JSON from AI response."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    # Try array
    start = text.find("[")
    end = text.rfind("]") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return json.loads(text)


def load_behavior_definitions():
    """Load BEHAVIOR_DEFINITIONS.md as context for AI agents."""
    path = os.path.join(_DOCS_DIR, "BEHAVIOR_DEFINITIONS.md")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return ""


def run_parallel_agents(tasks):
    """Run multiple AI calls in parallel.

    Args:
        tasks: list of (name, callable) tuples

    Returns:
        dict of {name: result}
    """
    results = {}
    errors = {}

    def _run(name, fn):
        try:
            results[name] = fn()
        except Exception as e:
            errors[name] = str(e)

    threads = []
    for name, fn in tasks:
        t = threading.Thread(target=_run, args=(name, fn))
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=120)

    if errors:
        for name, err in errors.items():
            print(f"  Agent {name} FAILED: {err[:100]}")

    return results, errors
