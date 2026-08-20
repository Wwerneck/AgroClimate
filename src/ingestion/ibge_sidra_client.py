from __future__ import annotations

from typing import Any

import httpx

from src.utils.exceptions import APIConnectionError

SIDRA_BASE_URL = "https://apisidra.ibge.gov.br/values"


class SidraClient:
    def __init__(self, timeout: float = 20):
        self.timeout = timeout

    def fetch_pam_temporary_crops(self, product_codes: list[str], period: str = "last 1") -> list[dict[str, Any]]:
        products = ",".join(product_codes)
        url = f"{SIDRA_BASE_URL}/t/1612/n3/all/v/214,215,216,112/c81/{products}/p/{period}"
        try:
            response = httpx.get(url, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise APIConnectionError(f"Failed to fetch IBGE SIDRA PAM data: {exc}") from exc
        if not payload:
            return []
        return payload[1:]
