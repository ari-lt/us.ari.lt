#!/usr/bin/env sh

set -u

main() {
    [ "$MARIA_USER" ] && [ "$MARIA_PASS" ]

    kill -9 $(pgrep memcached) || true

    memcached -m 1024 &
    sleep 5
    python3 src/main.py
}

main "$@"
