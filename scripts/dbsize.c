#include <unistd.h>

int main(void) {
    execl("/usr/bin/du", "/usr/bin/du", "-csh", "/var/lib/mysql/main/", NULL);
}
