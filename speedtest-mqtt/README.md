# Speedtest MQTT — Home Assistant Add-on

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Supports aarch64](https://img.shields.io/badge/aarch64-yes-green)
![Supports amd64](https://img.shields.io/badge/amd64-yes-green)
![Supports armhf](https://img.shields.io/badge/armhf-yes-green)
![Supports armv7](https://img.shields.io/badge/armv7-yes-green)

Runs periodic internet speedtests via the Ookla Speedtest CLI and publishes
structured results to your MQTT broker, ready for use as Home Assistant sensors.

---

## Installation

1. Add this repository to Home Assistant:

   [![Add repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FYOUR_USERNAME%2Fha-addons)

   Or manually: **Settings → Add-ons → Add-on Store → ⋮ → Repositories** → add `https://github.com/YOUR_USERNAME/ha-addons`

2. Install **Speedtest MQTT** from the store.
3. Configure options (see below).
4. Click **Start**.

---

## Configuration

| Option             | Default            | Description                                          |
|--------------------|--------------------|------------------------------------------------------|
| `mqtt_broker`      | `core-mosquitto`   | Hostname or IP of your MQTT broker                   |
| `mqtt_port`        | `1883`             | MQTT port                                            |
| `mqtt_user`        | *(empty)*          | MQTT username — leave blank if auth is disabled      |
| `mqtt_password`    | *(empty)*          | MQTT password — leave blank if auth is disabled      |
| `mqtt_topic`       | `speedtest/result` | Topic to publish results on                          |
| `server_id`        | `15134`            | Ookla server ID (see [Finding a server](#finding-a-server-id)) |
| `interval_minutes` | `60`               | How often to run the speedtest                       |

Example `options` block in the add-on UI:

```yaml
mqtt_broker: core-mosquitto
mqtt_port: 1883
mqtt_user: ""
mqtt_password: ""
mqtt_topic: speedtest/result
server_id: 15134
interval_minutes: 60
```

---

## MQTT Payload

Results are published as a **retained** JSON message so HA always has the last
known value after a restart:

```json
{
  "state": "https://www.speedtest.net/result/c/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "attributes": {
    "time_run":  "2026-04-27T10:00:00Z",
    "ping":      12.345,
    "jitter":    1.234,
    "download":  95.42,
    "upload":    18.76,
    "server":    "Aussie Broadband",
    "location":  "Brisbane",
    "isp":       "Aussie Broadband"
  }
}
```

On failure, `state` is set to `"error"` so automations can alert you.

---

## Home Assistant Sensors

Add the following to your `configuration.yaml` (or an included file):

```yaml
mqtt:
  sensor:
    - name: "Speedtest Result URL"
      state_topic: "speedtest/result"
      value_template: "{{ value_json.state }}"
      icon: mdi:speedometer

    - name: "Speedtest Download"
      state_topic: "speedtest/result"
      value_template: "{{ value_json.attributes.download }}"
      unit_of_measurement: "Mbps"
      device_class: data_rate
      icon: mdi:download-network

    - name: "Speedtest Upload"
      state_topic: "speedtest/result"
      value_template: "{{ value_json.attributes.upload }}"
      unit_of_measurement: "Mbps"
      device_class: data_rate
      icon: mdi:upload-network

    - name: "Speedtest Ping"
      state_topic: "speedtest/result"
      value_template: "{{ value_json.attributes.ping }}"
      unit_of_measurement: "ms"
      icon: mdi:lan-pending

    - name: "Speedtest Jitter"
      state_topic: "speedtest/result"
      value_template: "{{ value_json.attributes.jitter }}"
      unit_of_measurement: "ms"
      icon: mdi:sine-wave

    - name: "Speedtest Server"
      state_topic: "speedtest/result"
      value_template: "{{ value_json.attributes.server }}"
      icon: mdi:server-network

    - name: "Speedtest ISP"
      state_topic: "speedtest/result"
      value_template: "{{ value_json.attributes.isp }}"
      icon: mdi:web

    - name: "Speedtest Last Run"
      state_topic: "speedtest/result"
      value_template: "{{ value_json.attributes.time_run }}"
      device_class: timestamp
      icon: mdi:clock-check
```

Reload your MQTT configuration (or restart HA) after saving.

---

## Finding a Server ID

Run the following on any machine with the Speedtest CLI installed to list
nearby servers:

```bash
speedtest --servers
```

Pick a server geographically close to you and paste its **ID** into the add-on
configuration. The default (`15134`) is a Brisbane, AU server.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No data in HA sensors | Check the **Log** tab in the add-on for errors |
| `speedtest` fails intermittently | Try a different `server_id` |
| MQTT publish fails | Confirm broker hostname, port, and credentials; use `core-mosquitto` for the built-in Mosquitto add-on |
| Sensors show `unknown` after HA restart | Ensure `-r` (retain) flag is working — check broker logs |

---

## Changelog

### 1.0.0
- Initial release
- Configurable interval, broker, topic, and server ID
- Publishes download, upload, ping, jitter, server, ISP, and result URL
- Error state published to MQTT on test failure
