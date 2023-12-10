#!/usr/bin/env sh

set -eu

main() {
    echo 'clearing database'

    mariadb --user="$MARIA_USER" --password="$MARIA_PASS" --host=127.0.0.1 main <<EOF
START TRANSACTION;
DROP TABLE app;
DROP TABLE blog_post;
DROP TABLE blog;
DROP TABLE counter;
DROP TABLE user;
COMMIT;
EOF
}

main "$@"

