#!/usr/bin/env sh

set -eu

main() {
    if [ "$(id -u)" != 0 ]; then
        echo 'run me as root' >&2
        exit 1
    fi

    cp res/nginx.conf /etc/nginx/nginx.conf
    systemctl enable --now nginx
}

main "$@"
