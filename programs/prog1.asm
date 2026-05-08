.data
counter 5
result 0
.enddata

.code
loop:
LOAD counter
BRZERO fim
SUB #1
STORE counter
LOAD result
ADD #10
STORE result
BRANY loop
fim:
LOAD result
SYSCALL 1
SYSCALL 0
.endcode
