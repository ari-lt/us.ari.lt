#!/usr/bin/env sh

set -u

main() {
    [ "$MARIA_USER" ] && [ "$MARIA_PASS" ]

    kill -9 $(pgrep python3) || true

    cd src
    python3 -m pip install gunicorn
    python3 -m gunicorn -b 127.0.0.1:8000 -w "$(nproc --all)" main:app &
    disown
}

main "$@"
