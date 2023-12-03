#!/usr/bin/env sh

set -eu

main() {
    if [ "$(id -u)" != 0 ]; then
        echo 'run me as root' >&2
        exit 1
    fi

    apt install certbot python3-certbot-nginx
    certbot --nginx
    certbot renew --dry-run
}

main "$@"
