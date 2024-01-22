#!/usr/bin/env sh

set -e

main() {
    pkill -f dendrite
    systemctl restart nginx
    systemctl restart forgejo
    su matrix -c 'cd ~/dendrite/ && ~/go/bin/dendrite --config dendrite.yaml >/dev/null 2>/dev/null & disown'
}

main "$@"

