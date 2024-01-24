#!/usr/bin/env sh

main() {
    pkill -f python
    pkill -f dendrite

    systemctl restart nginx
    systemctl restart forgejo

    su matrix -c 'cd ~/dendrite/ && ~/go/bin/dendrite --config dendrite.yaml & disown'
    su mau -c 'cd ~/maubot/ && source ./bin/activate && python3 -m maubot & disown'
    su us -c 'cd ~/us.ari.lt/ && source maria.env && source ./venv/bin/activate && ./scripts/run.sh & disown'
    su voe -c 'cd ~/vim-or-emacs.ari.lt/ && source ./venv/bin/activate && ./scripts/run.sh & disown'
    su searxng -c 'cd /usr/local/searxng/searxng-src && SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml python3 searx/webapp.py & disown'
}

main
