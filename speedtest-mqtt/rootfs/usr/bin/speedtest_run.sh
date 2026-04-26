#!/usr/bin/with-contenv bashio
# ==============================================================================
# speedtest_run.sh
# Runs a single speedtest and publishes results to MQTT
# ==============================================================================

# Load config from HA options
MQTT_BROKER=$(bashio::config 'mqtt_broker')
MQTT_PORT=$(bashio::config 'mqtt_port')
MQTT_USER=$(bashio::config 'mqtt_user')
MQTT_PASSWORD=$(bashio::config 'mqtt_password')
MQTT_TOPIC=$(bashio::config 'mqtt_topic')
SERVER_ID=$(bashio::config 'server_id')

bashio::log.info "Starting speedtest against server ID: ${SERVER_ID}"

# Run speedtest, capturing both stdout and stderr
if ! speedtest_result=$(speedtest --format=json --accept-license --server-id="${SERVER_ID}" 2>&1); then
    bashio::log.error "Speedtest failed: ${speedtest_result}"

    # Publish an error state to MQTT so HA reflects the failure
    error_payload=$(jq -n \
        --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{
            state: "error",
            attributes: {
                time_run: $ts,
                error: "Speedtest execution failed"
            }
        }')

    mosquitto_pub \
        -h "${MQTT_BROKER}" \
        -p "${MQTT_PORT}" \
        ${MQTT_USER:+-u "${MQTT_USER}"} \
        ${MQTT_PASSWORD:+-P "${MQTT_PASSWORD}"} \
        -t "${MQTT_TOPIC}" \
        -m "${error_payload}" \
        -r

    exit 1
fi

bashio::log.debug "Raw result: ${speedtest_result}"

# Parse fields from JSON output
download_bps=$(echo "${speedtest_result}" | jq '.download.bandwidth')
upload_bps=$(echo "${speedtest_result}"   | jq '.upload.bandwidth')
ping_ms=$(echo "${speedtest_result}"      | jq '.ping.latency')
jitter_ms=$(echo "${speedtest_result}"    | jq '.ping.jitter')
result_url=$(echo "${speedtest_result}"   | jq -r '.result.url')
timestamp=$(echo "${speedtest_result}"    | jq -r '.timestamp')
server_name=$(echo "${speedtest_result}"  | jq -r '.server.name')
server_location=$(echo "${speedtest_result}" | jq -r '.server.location')
isp=$(echo "${speedtest_result}"          | jq -r '.isp')

# Convert bandwidth: bytes/sec → Mbps (2 decimal places)
download_mbps=$(awk "BEGIN {printf \"%.2f\", ${download_bps} * 8 / 1000000}")
upload_mbps=$(awk   "BEGIN {printf \"%.2f\", ${upload_bps}   * 8 / 1000000}")
ping_fmt=$(printf   "%.3f" "${ping_ms}")
jitter_fmt=$(printf "%.3f" "${jitter_ms}")

bashio::log.info "Download: ${download_mbps} Mbps | Upload: ${upload_mbps} Mbps | Ping: ${ping_fmt} ms"
bashio::log.info "Result URL: ${result_url}"

# Build the MQTT payload using jq for safe JSON construction
payload=$(jq -n \
    --arg state "${result_url}" \
    --arg time_run "${timestamp}" \
    --arg ping "${ping_fmt}" \
    --arg jitter "${jitter_fmt}" \
    --arg download "${download_mbps}" \
    --arg upload "${upload_mbps}" \
    --arg server "${server_name}" \
    --arg location "${server_location}" \
    --arg isp "${isp}" \
    '{
        state: $state,
        attributes: {
            time_run:  $time_run,
            ping:      ($ping      | tonumber),
            jitter:    ($jitter    | tonumber),
            download:  ($download  | tonumber),
            upload:    ($upload    | tonumber),
            server:    $server,
            location:  $location,
            isp:       $isp
        }
    }')

bashio::log.debug "Publishing payload: ${payload}"

# Build mosquitto_pub arguments conditionally (avoid empty -u/-P flags)
MOSQ_ARGS=(-h "${MQTT_BROKER}" -p "${MQTT_PORT}" -t "${MQTT_TOPIC}" -m "${payload}" -r)
[[ -n "${MQTT_USER}"     ]] && MOSQ_ARGS+=(-u "${MQTT_USER}")
[[ -n "${MQTT_PASSWORD}" ]] && MOSQ_ARGS+=(-P "${MQTT_PASSWORD}")

if mosquitto_pub "${MOSQ_ARGS[@]}"; then
    bashio::log.info "Results published to MQTT topic: ${MQTT_TOPIC}"
else
    bashio::log.error "Failed to publish to MQTT broker: ${MQTT_BROKER}:${MQTT_PORT}"
    exit 1
fi
