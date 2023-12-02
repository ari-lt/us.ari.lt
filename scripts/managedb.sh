#!/usr/bin/env sh

set -eu

main() {
    exec mariadb --user="$MARIA_USER" --password="$MARIA_PASS" --host=127.0.0.1 main
}

main "$@"

