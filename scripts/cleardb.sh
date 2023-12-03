#!/usr/bin/env sh

set -eu

main() {
    echo 'clearing database'

    mariadb --user="$MARIA_USER" --password="$MARIA_PASS" --host=127.0.0.1 main <<EOF
START TRANSACTION;
DROP TABLE app;
DROP TABLE user;
DROP TABLE counter;
COMMIT;
EOF
}

main "$@"

