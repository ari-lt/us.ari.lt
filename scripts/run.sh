#!/usr/bin/env sh

set -eu

main() {
    [ "$MARIA_USER" ] && [ "$MARIA_PASS" ]

    cd src
    python3 -m pip install gunicorn
    python3 -m gunicorn -b 127.0.0.1:8000 main:app
}

main "$@"

