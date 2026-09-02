#!/bin/sh
# Scheduler for the file detection on the server share.
#
# Runs `manage.py check_imports` every POLL_INTERVAL_MINUTES, forever. A plain
# loop rather than cron/supercronic: it needs no extra package in the image, it
# reads the interval straight from the same environment variable the application
# uses, and it logs to stdout — which is what a container should do.
#
# Started as its own service from the same image (see docker-compose.yml), so the
# web process stays a single process and a failing import never takes the site
# down with it.
set -eu

INTERVAL_MINUTES="${POLL_INTERVAL_MINUTES:-5}"

# Fall back on the default when the variable is missing, non-numeric or zero, so
# a typo cannot turn this into a busy loop.
case "${INTERVAL_MINUTES}" in
    ''|*[!0-9]*) INTERVAL_MINUTES=5 ;;
esac
[ "${INTERVAL_MINUTES}" -lt 1 ] && INTERVAL_MINUTES=5

INTERVAL_SECONDS=$((INTERVAL_MINUTES * 60))
echo "RMW scheduler: checking the share every ${INTERVAL_MINUTES} minute(s)."

while true; do
    if ! python manage.py check_imports; then
        # Keep polling: a share that is briefly unreachable, or one bad file,
        # must not stop the scheduler.
        echo "RMW scheduler: check_imports failed; retrying next cycle."
    fi
    sleep "${INTERVAL_SECONDS}"
done
