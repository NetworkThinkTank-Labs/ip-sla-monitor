#!/usr/bin/env python3
"""
IP SLA Monitor - Main Monitoring Script
========================================
Collects IP SLA metrics from Cisco DNA Center, enriches them with
NetBox device metadata, and generates performance reports.

Usage:
    python ip_sla_monitor.py              # continuous monitoring loop
        python ip_sla_monitor.py --once       # single collection cycle
            python ip_sla_monitor.py --config .env  # custom config path

            Author : NetworkThinkTank
            License: MIT
            """

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from dnac_integration import DNACClient
from netbox_integration import NetBoxClient

# Logging
logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
      datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ip-sla-monitor")

# Thresholds and defaults
DEFAULT_POLL_INTERVAL = 300
DEFAULT_LATENCY_THRESHOLD = 100
DEFAULT_JITTER_THRESHOLD = 30
DEFAULT_PACKET_LOSS_THRESHOLD = 1.0
DEFAULT_OUTPUT_DIR = "./output"


def load_config(config_path=None):
      """Load configuration from .env file and environment variables."""
      if config_path:
                load_dotenv(config_path)
else:
        load_dotenv()

    return {
              "dnac_host": os.getenv("DNAC_HOST", "https://sandboxdnac.cisco.com"),
              "dnac_username": os.getenv("DNAC_USERNAME", "devnetuser"),
              "dnac_password": os.getenv("DNAC_PASSWORD", "Cisco123!"),
              "dnac_verify_ssl": os.getenv("DNAC_VERIFY_SSL", "False").lower() == "true",
              "netbox_url": os.getenv("NETBOX_URL", "https://netbox.example.com"),
              "netbox_token": os.getenv("NETBOX_TOKEN", ""),
              "netbox_verify_ssl": os.getenv("NETBOX_VERIFY_SSL", "True").lower() == "true",
              "poll_interval": int(os.getenv("POLL_INTERVAL", DEFAULT_POLL_INTERVAL)),
              "latency_threshold": float(os.getenv("LATENCY_THRESHOLD_MS", DEFAULT_LATENCY_THRESHOLD)),
              "jitter_threshold": float(os.getenv("JITTER_THRESHOLD_MS", DEFAULT_JITTER_THRESHOLD)),
              "packet_loss_threshold": float(os.getenv("PACKET_LOSS_THRESHOLD_PCT", DEFAULT_PACKET_LOSS_THRESHOLD)),
              "output_dir": os.getenv("OUTPUT_DIR", DEFAULT_OUTPUT_DIR),
    }


def evaluate_thresholds(operation, config):
      """Return 'OK' or 'ALERT' based on configured thresholds."""
      if operation.get("avg_latency_ms", 0) > config["latency_threshold"]:
                return "ALERT"
            if operation.get("jitter_ms", 0) > config["jitter_threshold"]:
                      return "ALERT"
                  if operation.get("packet_loss_pct", 0) > config["packet_loss_threshold"]:
                            return "ALERT"
                        return "OK"


def collect_and_enrich(dnac, netbox, config):
      """Run a single collection cycle and return the report dict."""
    logger.info("Starting collection cycle...")

    # 1. Authenticate with DNA Center
    dnac.authenticate()

    # 2. Retrieve network devices from DNA Center
    devices = dnac.get_network_devices()
    logger.info("Retrieved %d devices from DNA Center", len(devices))

    # 3. Retrieve IP SLA data from DNA Center
    sla_data = dnac.get_ip_sla_operations()
    logger.info("Retrieved %d IP SLA operations", len(sla_data))

    # 4. Enrich with NetBox metadata
    enriched_operations = []
    for sla in sla_data:
              source_hostname = sla.get("source_device", "")
              nb_device = netbox.get_device_by_name(source_hostname)

        operation = {
                      "sla_id": sla.get("sla_id"),
                      "source_device": source_hostname,
                      "destination": sla.get("destination"),
                      "type": sla.get("type", "icmp-echo"),
                      "latest_rtt_ms": sla.get("latest_rtt_ms", 0),
                      "avg_latency_ms": sla.get("avg_latency_ms", 0),
                      "jitter_ms": sla.get("jitter_ms", 0),
                      "packet_loss_pct": sla.get("packet_loss_pct", 0.0),
                      "netbox_site": nb_device.get("site", "Unknown") if nb_device else "Unknown",
                      "netbox_role": nb_device.get("role", "Unknown") if nb_device else "Unknown",
        }
        operation["status"] = evaluate_thresholds(operation, config)
        enriched_operations.append(operation)

    # 5. Build summary
    total = len(enriched_operations)
    passing = sum(1 for op in enriched_operations if op["status"] == "OK")
    failing = total - passing
    avg_latency = (
              sum(op["avg_latency_ms"] for op in enriched_operations) / total
              if total else 0
    )

    report = {
              "report_timestamp": datetime.now(timezone.utc).isoformat(),
              "source": "DNA Center + NetBox",
              "summary": {
                            "total_operations": total,
                            "passing": passing,
                            "failing": failing,
                            "avg_latency_ms" round(avg_latency, 2),
              },
              "operations": enriched_operations,
    }

    # 6. Log alerts
    for op in enriched_operations:
              if op["status"] == "ALERT":
                            logger.warning(
                                              "ALERT - SLA %s on %s -> %s | latency=%sms jitter=%sms loss=%s%%",
                                              op["sla_id"], op["source_device"], op["destination"],
                                              op["avg_latency_ms"], op["jitter_ms"], op["packet_loss_pct"],
                            )

          logger.info(
                    "Collection complete - %d total, %d passing, %d failing",
                    total, passing, failing,
          )
    return report


def save_report(report, output_dir):
      """Persist the report as JSON and CSV."""
      Path(output_dir).mkdir(parents=True, exist_ok=True)

    json_path = os.path.join(output_dir, "ip_sla_report.json")
    csv_path = os.path.join(output_dir, "ip_sla_report.csv")

    # JSON
    with open(json_path, "w", encoding="utf-8") as fh:
              json.dump(report, fh, indent=2)
          logger.info("JSON report saved -> %s", json_path)

    # CSV
    if report["operations"]:
              fieldnames = list(report["operations"][0].keys())
              with open(csv_path, "w", newline="", encoding="utf-8") as fh:
                            writer = csv.DictWriter(fh, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(report["operations"])
                        logger.info("CSV report saved -> %s", csv_path)


def main():
      parser = argparse.ArgumentParser(description="IP SLA Monitor")
    parser.add_argument("--once", action="store_true", help="Run a single collection cycle")
    parser.add_argument("--config", type=str, default=None, help="Path to .env config file")
    args = parser.parse_args()

    config = load_config(args.config)

    dnac = DNACClient(
              host=config["dnac_host"],
              username=config["dnac_username"],
              password=config["dnac_password"],
              verify=config["dnac_verify_ssl"],
    )
    netbox = NetBoxClient(
              url=config["netbox_url"],
              token=config["netbox_token"],
              verify=config["netbox_verify_ssl"],
    )

    if args.once:
              report = collect_and_enrich(dnac, netbox, config)
        save_report(report, config["output_dir"])
        return

    # Continuous monitoring loop
    logger.info("Starting continuous monitoring (poll every %ds)...", config["poll_interval"])
    try:
              while True:
                            report = collect_and_enrich(dnac, netbox, config)
                            save_report(report, config["output_dir"])
                            logger.info("Sleeping %ds until next cycle...", config["poll_interval"])
                            time.sleep(config["poll_interval"])
except KeyboardInterrupt:
        logger.info("Monitoring stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
      main()
