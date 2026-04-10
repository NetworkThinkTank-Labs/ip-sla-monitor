#!/usr/bin/env python3
"""
NetBox Integration Module
==========================
Provides a client class to interact with the NetBox REST API for
retrieving device metadata, site information, and IP address details
to enrich IP SLA monitoring data.

Author : NetworkThinkTank
License: MIT
"""

import logging
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("ip-sla-monitor.netbox")


class NetBoxClient:
      """Lightweight wrapper around the NetBox REST API."""

    def __init__(self, url, token, verify=True):
              self.url = url.rstrip("/")
              self.token = token
              self.verify = verify
              self.session = requests.Session()
              self.session.headers.update({
                  "Authorization": f"Token {self.token}",
                  "Content-Type": "application/json",
                  "Accept": "application/json",
              })
              self.session.verify = self.verify
              self._device_cache = {}

    def get_device_by_name(self, name):
              """Look up a device in NetBox by hostname. Returns simplified dict."""
              if name in self._device_cache:
                            return self._device_cache[name]

              url = f"{self.url}/api/dcim/devices/"
              params = {"name": name}

        try:
                      resp = self.session.get(url, params=params)
                      resp.raise_for_status()
                      results = resp.json().get("results", [])
except requests.RequestException as exc:
              logger.warning("NetBox lookup failed for '%s': %s", name, exc)
              return self._demo_device(name)

        if not results:
                      logger.debug("Device '%s' not found in NetBox - using demo data", name)
                      device = self._demo_device(name)
else:
              raw = results[0]
              device = {
                  "name": raw.get("name"),
                  "site": raw.get("site", {}).get("name", "Unknown"),
                  "role": raw.get("device_role", {}).get("name", "Unknown"),
                  "platform": (raw.get("platform") or {}).get("name", "Unknown"),
                  "status": raw.get("status", {}).get("value", "unknown"),
                  "primary_ip": (raw.get("primary_ip") or {}).get("address", "N/A"),
                  "serial": raw.get("serial", "N/A"),
              }

        self._device_cache[name] = device
        return device

    def get_all_devices(self):
              """Retrieve all devices from NetBox (paginated)."""
              url = f"{self.url}/api/dcim/devices/"
              devices = []
              params = {"limit": 50, "offset": 0}

        while True:
                      try:
                                        resp = self.session.get(url, params=params)
                                        resp.raise_for_status()
                                        data = resp.json()
except requests.RequestException as exc:
                logger.error("Failed to fetch devices from NetBox: %s", exc)
                break

            devices.extend(data.get("results", []))
            if data.get("next") is None:
                              break
                          params["offset"] += params["limit"]

        logger.info("Retrieved %d devices from NetBox", len(devices))
        return devices

    def get_site_by_name(self, name):
              """Look up a site in NetBox by name."""
              url = f"{self.url}/api/dcim/sites/"
              params = {"name": name}
              try:
                            resp = self.session.get(url, params=params)
                            resp.raise_for_status()
                            results = resp.json().get("results", [])
except requests.RequestException as exc:
            logger.warning("NetBox site lookup failed for '%s': %s", name, exc)
            return None
        return results[0] if results else None

    def get_ip_address(self, address):
              """Look up an IP address in NetBox IPAM."""
        url = f"{self.url}/api/ipam/ip-addresses/"
        params = {"address": address}
        try:
                      resp = self.session.get(url, params=params)
                      resp.raise_for_status()
                      results = resp.json().get("results", [])
except requests.RequestException as exc:
            logger.warning("NetBox IP lookup failed for '%s': %s", address, exc)
            return None
        return results[0] if results else None

    @staticmethod
    def _demo_device(name):
              """Return sample device metadata when NetBox is unavailable."""
        demo_map = {
                      "core-rtr-01": {"name": "core-rtr-01", "site": "HQ-DC1",
                                                      "role": "core-router", "platform": "Cisco IOS-XE",
                                                      "status": "active", "primary_ip": "10.0.0.1/32", "serial": "FDO2201A0B1"},
                      "branch-rtr-01": {"name": "branch-rtr-01", "site": "Branch-NYC",
                                                        "role": "branch-router", "platform": "Cisco IOS-XE",
                                                        "status": "active", "primary_ip": "10.10.0.1/32", "serial": "FDO2201A0C2"},
                      "dist-sw-01": {"name": "dist-sw-01", "site": "HQ-DC1",
                                                     "role": "distribution-switch", "platform": "Cisco IOS-XE",
                                                     "status": "active", "primary_ip": "10.0.1.1/32", "serial": "FDO2201A0D3"},
                      "edge-rtr-01": {"name": "edge-rtr-01", "site": "HQ-DC1",
                                                      "role": "edge-router", "platform": "Cisco IOS-XR",
                                                      "status": "active", "primary_ip": "10.0.2.1/32", "serial": "FDO2201A0E4"},
                      "wan-rtr-01": {"name": "wan-rtr-01", "site": "Branch-LAX",
                                                     "role": "wan-router", "platform": "Cisco IOS-XE",
                                                     "status": "active", "primary_ip": "10.20.0.1/32", "serial": "FDO2201A0F5"},
                      "dc-spine-01": {"name": "dc-spine-01", "site": "HQ-DC1",
                                                      "role": "dc-spine", "platform": "Cisco NX-OS",
                                                      "status": "active", "primary_ip": "10.0.100.1/32",  "serial": "FDO2201A0G6"},
        }
        return demo_map.get(name, {
                      "name": name, "site": "Unknown", "role": "Unknown",
                      "platform": "Unknown", "status": "unknown",
                      "primary_ip": "N/A", "serial": "N/A",
        })


if __name__ == "__main__":
      import os
    from dotenv import load_dotenv
    load_dotenv()

    client = NetBoxClient(
              url=os.getenv("NETBOX_URL", "https://netbox.example.com"),
              token=os.getenv("NETBOX_TOKEN", ""),
    )

    sample_devices = ["core-rtr-01", "branch-rtr-01", "dist-sw-01",
                                             "edge-rtr-01", "wan-rtr-01", "dc-spine-01"]

    print("\n--- NetBox Device Lookup ---")
    for hostname in sample_devices:
              dev = client.get_device_by_name(hostname)
        if dev:
                      print(f"  {dev['name']:20s}  Site={dev['site']:15s}  Role={dev['role']}")
else:
            print(f"  {hostname:20s}  NOT FOUND")
