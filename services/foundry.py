"""Foundry IQ adapter: async client with local JSON fallback.

This module provides a minimal `FoundryClient` that prefers a live
Foundry IQ HTTP endpoint but can fall back to a local mock JSON file
for development and integration testing.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import httpx


class FoundryClient:
    def __init__(self, *, base_url: Optional[str] = None, api_key: Optional[str] = None,
                 use_mock: Optional[bool] = None, mock_path: Optional[str] = None):
        self.base_url = base_url or os.getenv("FOUNDRY_IQ_URL")
        self.api_key = api_key or os.getenv("FOUNDRY_API_KEY")
        env_use_mock = os.getenv("FOUNDRY_USE_MOCK")
        
        if use_mock is None:
            self.use_mock = (env_use_mock or "true").lower() in ("1", "true", "yes")
        else:
            self.use_mock = use_mock
            
        self.mock_path = mock_path or os.getenv("FOUNDRY_MOCK_PATH") or "data/foundry_mock.json"

    async def _fetch_remote(self, path: str, params: Optional[Dict[str, str]] = None) -> Any:
        if not self.base_url or not self.api_key:
            raise RuntimeError("Foundry IQ base URL or API key not configured")
        
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_rule(self, rule_id: str) -> Dict[str, Any]:
        """Retrieve a single rule by id from Foundry IQ or the local mock."""
        if self.use_mock:
            return self._load_mock_rule(rule_id)
        return await self._fetch_remote(f"rules/{rule_id}")

    async def search_rules(self, query: str) -> List[Dict[str, Any]]:
        """Search rules by query. Returns a list of matching rule dicts."""
        if self.use_mock:
            return self._load_mock_search(query)
            
        payload = await self._fetch_remote("rules/search", params={"q": query})
        
        # Assume remote returns a `results` list
        if isinstance(payload, dict) and "results" in payload:
            return payload["results"]
        if isinstance(payload, list):
            return payload
        return []

    def _load_mock(self) -> Dict[str, Any]:
        try:
            with open(self.mock_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return {"rules": []}

    def _load_mock_rule(self, rule_id: str) -> Dict[str, Any]:
        data = self._load_mock()
        for r in data.get("rules", []):
            if r.get("id") == rule_id:
                return r
        raise KeyError(f"Rule not found in mock: {rule_id}")

    def _load_mock_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Simulates semantic RAG retrieval by returning mock policies.
        Relies on the strict Evaluator class to determine actual compliance matching.
        """
        data = self._load_mock()
        rules = data.get("rules", [])
        
        # Simulate an intelligent retrieval by filtering out completely irrelevant rules,
        # or returning the standard set for the Evaluator to process.
        query_tokens = set(word.lower() for word in query.split() if len(word) > 4)
        retrieved_rules = []
        
        for rule in rules:
            rule_text = (rule.get("title", "") + " " + rule.get("text", "")).lower()
            # If there is any significant vocabulary overlap, "retrieve" it
            if any(token in rule_text for token in query_tokens):
                retrieved_rules.append(rule)
                
        # Fallback: if vocabulary is too distinct, return all mock rules
        # to guarantee the Evaluator has data to parse.
        return retrieved_rules if retrieved_rules else rules