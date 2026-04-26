#!/usr/bin/with-contenv bashio
# ==============================================================================
# speedtest_loop.sh
# Runs speedtest_run.sh on the configured interval, forever.
# s6-overlay will restart this service if it exits unexpectedly.
# ==============================================================================

INTERVAL_MINUTES=$(bashio::config 'interval_minutes')
INTERVAL_SECONDS=$(( INTERVAL_MINUTES * 60 ))

bashio::log.info "Speedtest MQTT add-on started"
bashio::log.info "Running every ${INTERVAL_MINUTES} minute(s)"

while true; do
    bashio::log.info "--- Running speedtest ---"

    # Run the test; log failure but don't exit the loop
    if /usr/bin/speedtest_run.sh; then
        bashio::log.info "--- Speedtest complete. Next run in ${INTERVAL_MINUTES} minute(s) ---"
    else
        bashio::log.warning "--- Speedtest failed. Retrying in ${INTERVAL_MINUTES} minute(s) ---"
    fi

    sleep "${INTERVAL_SECONDS}"
done
