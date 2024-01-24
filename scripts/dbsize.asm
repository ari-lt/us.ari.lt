format ELF64 executable 3
segment readable executable

define SYS_execve 59

_start:
    mov eax, SYS_execve
    mov edi, arg0
    mov esi, argv
    mov edx, 0
    syscall

segment readable

arg0 db "/usr/bin/du", 0
arg1 db "-csh", 0
arg2 db "/var/lib/mysql/main/", 0

argv dq arg0, arg1, arg2, 0
