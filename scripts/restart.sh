#!/usr/bin/env sh

main() {
    [ "$1" ] && pkill -f python
    pkill -f dendrite

    systemctl restart nginx
    systemctl restart forgejo

    su matrix -c 'cd ~/dendrite/ && git pull && ~/go/bin/dendrite --config dendrite.yaml & disown'
    [ "$1" ] && su mau -c 'cd ~/maubot/ && source ./bin/activate && pip install --upgrade maubot && python3 -m maubot & disown'
    [ "$1" ] && su us -c 'cd ~/us.ari.lt/ && source maria.env && source ./venv/bin/activate && git pull && pip install --upgrade -r requirements.txt && ./scripts/run.sh & disown'
    [ "$1" ] && su voe -c 'cd ~/vim-or-emacs.ari.lt/ && source ./venv/bin/activate && git pull && pip install --upgrade -r requirements.txt && ./scripts/run.sh & disown'
    [ "$1" ] && su searxng -c 'cd /usr/local/searxng/searxng-src && git pull && pip install --break-system-packages --user -r requirements.txt && SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml python3 searx/webapp.py & disown'
}

main
