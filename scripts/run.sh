#!/usr/bin/env sh

set -u

main() {
    [ "$MARIA_USER" ] && [ "$MARIA_PASS" ]

    kill -9 $(pgrep python3) || true
    kill -9 $(pgrep memcached) || true

    cd src
    python3 -m pip install gunicorn
    memcached -m 1024 &
    sleep 5
    python3 -m gunicorn -b 127.0.0.1:8000 -w "$(nproc --all)" main:app &
    disown
}

main "$@"
