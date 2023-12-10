#!/usr/bin/env sh

set -eux

main() {
    if [ "$(id -u)" != 0 ]; then
        echo 'run me as root' >&2
        exit 1
    fi

    cc scripts/dbsize.c -s -Ofast -o dbsize
    strip dbsize
    chown root:root dbsize
    install -o root -Dm4111 ./dbsize /usr/bin/dbsize

    rm -f dbsize
}

main "$@"

