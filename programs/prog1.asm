; Cenario: loop com acumulador usando BRZERO e BRANY
; Conta regressivamente de 5 ate 0, somando 10 a cada iteracao
; Resultado esperado: 5 * 10 = 50
; Instrucoes executadas: 45  |  CI sugerido: 45  |  Pi sugerido: 60
; Util para: demonstrar loop com BRZERO, acumulador, tarefa CPU-bound longa

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
