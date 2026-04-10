#!/usr/bin/env python3
"""
DNA Center Integration Module
===============================
Provides a client class to interact with the Cisco DNA Center REST API
for retrieving network device inventory and IP SLA operation data.

Author : NetworkThinkTank
License: MIT
"""

import logging
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("ip-sla-monitor.dnac")


class DNACClient:
      """Lightweight wrapper around the Cisco DNA Center REST API."""

    def __init__(self, host, username, password, verify=False):
              self.host = host.rstrip("/")
              self.username = username
              self.password = password
              self.verify = verify
              self.token = None
              self.session = requests.Session()
              self.session.verify = self.verify

    def authenticate(self):
              """Obtain an authentication token from DNA Center."""
              url = f"{self.host}/dna/system/api/v1/auth/token"
              logger.info("Authenticating with DNA Center at %s", self.host)
              resp = self.session.post(url, auth=(self.username, self.password))
              resp.raise_for_status()
              self.token = resp.json()["Token"]
              self.session.headers.update({"X-Auth-Token": self.token})
              logger.info("Authentication successful")
              return self.token

    def get_network_devices(self):
              """Retrieve all network devices from DNA Center."""
              url = f"{self.host}/dna/intent/api/v1/network-device"
              logger.info("Fetching network devices...")
              resp = self.session.get(url)
              resp.raise_for_status()
              devices = resp.json().get("response", [])
              logger.info("Found %d network devices", len(devices))
              return devices

    def get_device_by_ip(self, ip_address):
              """Look up a single device by its management IP."""
              url = f"{self.host}/dna/intent/api/v1/network-device/ip-address/{ip_address}"
              resp = self.session.get(url)
              if resp.status_code == 200:
                            return resp.json().get("response")
                        logger.warning("Device not found for IP %s", ip_address)
        return None

    def get_device_health(self):
              """Retrieve device health scores."""
        url = f"{self.host}/dna/intent/api/v1/device-health"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json().get("response", [])

    def get_ip_sla_operations(self):
              """
                      Retrieve IP SLA operation data.
                              In production this uses the command-runner API to execute
                                      'show ip sla statistics' on each device. For demonstration
                                              we return structured sample data.
                                                      """
        logger.info("Collecting IP SLA operation data...")
        sample_sla_data = [
                      {"sla_id": 100, "source_device": "core-rtr-01", "destination": "10.1.1.1",
                                    "type": "icmp-echo", "latest_rtt_ms": 23, "avg_latency_ms": 25.4,
                                    "jitter_ms": 3.2, "packet_loss_pct": 0.0},
                      {"sla_id": 101, "source_device": "core-rtr-01", "destination": "10.2.1.1",
                                    "type": "icmp-echo", "latest_rtt_ms": 48, "avg_latency_ms": 52.1,
                                    "jitter_ms": 8.7, "packet_loss_pct": 0.5},
                      {"sla_id": 200, "source_device": "branch-rtr-01", "destination": "10.1.1.1",
                                    "type": "icmp-echo", "latest_rtt_ms": 110, "avg_latency_ms": 115.3,
                                    "jitter_ms": 35.2, "packet_loss_pct": 2.1},
                      {"sla_id": 201, "source_device": "branch-rtr-01", "destination": "10.3.1.1",
                                    "type": "udp-jitter", "latest_rtt_ms": 67, "avg_latency_ms": 72.8,
                                    "jitter_ms": 12.4, "packet_loss_pct": 0.2},
                      {"sla_id": 300, "source_device": "dist-sw-01", "destination": "10.1.1.1",
                                    "type": "icmp-echo", "latest_rtt_ms": 5, "avg_latency_ms": 6.1,
                                    "jitter_ms": 1.0, "packet_loss_pct": 0.0},
                      {"sla_id": 400, "source_device": "edge-rtr-01", "destination": "8.8.8.8",
                                    "type": "icmp-echo", "latest_rtt_ms": 32, "avg_latency_ms": 34.7,
                                    "jitter_ms": 4.5, "packet_loss_pct": 0.1},
                      {"sla_id": 500, "source_device": "wan-rtr-01", "destination": "10.1.1.1",
                                    "type": "udp-jitter", "latest_rtt_ms": 89, "avg_latency_ms": 95.0,
                                    "jitter_ms": 22.1, "packet_loss_pct": 0.8},
                      {"sla_id": 501, "source_device": "wan-rtr-01", "destination": "10.5.1.1",
                                    "type": "icmp-echo", "latest_rtt_ms": 145, "avg_latency_ms": 150.6,
                                    "jitter_ms": 40.3, "packet_loss_pct": 3.5},
                      {"sla_id": 600, "source_device": "dc-spine-01", "destination": "10.1.1.1",
                                    "type": "icmp-echo", "latest_rtt_ms": 2, "avg_latency_ms": 2.5,
                                    "jitter_ms": 0.5, "packet_loss_pct": 0.0},
        ]
        logger.info("Collected %d IP SLA operations", len(sample_sla_data))
        return sample_sla_data

    def run_command(self, device_ids, command):
              """Execute a CLI command on devices via command-runner API."""
              url = f"{self.host}/dna/intent/api/v1/network-device-poller/cli/read-request"
              payload = {
                  "commands": [command],
                  "deviceUuids": device_ids,
                  "timeout": 30,
              }
              resp = self.session.post(url, json=payload)
              resp.raise_for_status()
              return resp.json().get("response", {})


if __name__ == "__main__":
      import os
      from dotenv import load_dotenv

    load_dotenv()

    client = DNACClient(
              host=os.getenv("DNAC_HOST", "https://sandboxdnac.cisco.com"),
              username=os.getenv("DNAC_USERNAME", "devnetuser"),
              password=os.getenv("DNAC_PASSWORD", "Cisco123!"),
    )

    client.authenticate()

    print("\n--- Network Devices ---")
    for dev in client.get_network_devices()[:5]:
              print(f"  {dev.get('hostname', 'N/A'):30s}  {dev.get('managementIpAddress', 'N/A')}")

    print("\n--- IP SLA Operations ---")
    for sla in client.get_ip_sla_operations():
              print(
                            f"  SLA {sla['sla_id']:>4d}  {sla['source_device']:20s}  "
                            f"RTT={sla['latest_rtt_ms']}ms  Loss={sla['packet_loss_pct']}%"
              )
