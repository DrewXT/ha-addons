#!/usr/bin/env python3
"""
Speedtest MQTT — Home Assistant Add-on
Runs Ookla speedtest CLI and publishes results to MQTT.
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Logging — bashio-style prefix so HA log viewer colours it correctly
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Config — read from /data/options.json (populated by HA Supervisor)
# ---------------------------------------------------------------------------
OPTIONS_PATH = "/data/options.json"


def load_options() -> dict:
    try:
        with open(OPTIONS_PATH) as f:
            return json.load(f)
    except Exception as e:
        log.error("Failed to read options: %s", e)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Speedtest
# ---------------------------------------------------------------------------
def run_speedtest(server_id: int) -> dict | None:
    """Run speedtest CLI and return parsed JSON, or None on failure."""
    cmd = [
        "speedtest",
        "--format=json",
        "--accept-license",
        "--accept-gdpr",
        f"--server-id={server_id}",
    ]
    log.info("Running: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        log.error("Speedtest timed out after 120 seconds")
        return None
    except FileNotFoundError:
        log.error("speedtest binary not found — check Dockerfile")
        return None

    # Log stderr for debugging (Ookla sometimes writes progress there)
    if result.stderr.strip():
        log.debug("speedtest stderr: %s", result.stderr.strip())

    if result.returncode != 0:
        log.error(
            "speedtest exited with code %d. stdout: %r  stderr: %r",
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip(),
        )
        return None

    stdout = result.stdout.strip()
    if not stdout:
        log.error("speedtest returned empty output")
        return None

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        log.error("Failed to parse speedtest JSON: %s — raw output: %r", e, stdout)
        return None


def parse_result(data: dict) -> dict:
    """Extract and convert fields from the raw speedtest JSON."""
    # Bandwidth is in bytes/sec — convert to Mbps
    download_mbps = round(data["download"]["bandwidth"] * 8 / 1_000_000, 2)
    upload_mbps   = round(data["upload"]["bandwidth"]   * 8 / 1_000_000, 2)
    ping_ms        = round(data["ping"]["latency"],  3)
    jitter_ms      = round(data["ping"]["jitter"],   3)

    return {
        "state": data["result"]["url"],
        "attributes": {
            "time_run":  data["timestamp"],
            "ping":      ping_ms,
            "jitter":    jitter_ms,
            "download":  download_mbps,
            "upload":    upload_mbps,
            "server":    data["server"]["name"],
            "location":  data["server"]["location"],
            "isp":       data["isp"],
        },
    }


def error_payload(reason: str) -> dict:
    return {
        "state": "error",
        "attributes": {
            "time_run": datetime.now(timezone.utc).isoformat(),
            "error": reason,
        },
    }


# ---------------------------------------------------------------------------
# MQTT
# ---------------------------------------------------------------------------
def publish(opts: dict, payload: dict) -> bool:
    """Publish payload to MQTT. Returns True on success."""
    broker   = opts["mqtt_broker"]
    port     = int(opts["mqtt_port"])
    topic    = opts["mqtt_topic"]
    username = opts.get("mqtt_user", "")
    password = opts.get("mqtt_password", "")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    if username:
        client.username_pw_set(username, password or None)

    # Collect connection errors via callback
    connect_error: list[str] = []

    def on_connect(c, userdata, flags, reason_code, properties):
        if reason_code != 0:
            connect_error.append(f"MQTT connect failed: reason={reason_code}")

    client.on_connect = on_connect

    try:
        client.connect(broker, port, keepalive=10)
        client.loop_start()
        time.sleep(1)  # allow on_connect to fire

        if connect_error:
            log.error(connect_error[0])
            return False

        msg_info = client.publish(
            topic,
            json.dumps(payload),
            qos=1,
            retain=True,
        )
        msg_info.wait_for_publish(timeout=10)

        if msg_info.is_published():
            log.info("Published to %s:%d %s", broker, port, topic)
            return True
        else:
            log.error("Publish timed out or failed")
            return False

    except Exception as e:
        log.error("MQTT error: %s", e)
        return False
    finally:
        client.loop_stop()
        client.disconnect()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main() -> None:
    opts = load_options()
    server_id        = int(opts.get("server_id", 15134))
    interval_minutes = int(opts.get("interval_minutes", 60))
    interval_seconds = interval_minutes * 60

    log.info("Speedtest MQTT add-on started")
    log.info("Server ID: %d  |  Interval: %d minute(s)", server_id, interval_minutes)

    while True:
        log.info("--- Running speedtest ---")

        raw = run_speedtest(server_id)

        if raw is not None:
            try:
                payload = parse_result(raw)
                attrs = payload["attributes"]
                log.info(
                    "Download: %.2f Mbps  Upload: %.2f Mbps  Ping: %.3f ms",
                    attrs["download"], attrs["upload"], attrs["ping"],
                )
                log.info("Result URL: %s", payload["state"])
            except (KeyError, TypeError) as e:
                log.error("Unexpected speedtest result structure: %s — data: %r", e, raw)
                payload = error_payload(f"Unexpected result structure: {e}")
        else:
            payload = error_payload("Speedtest execution failed — check logs above")

        publish(opts, payload)

        log.info("--- Next run in %d minute(s) ---", interval_minutes)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
