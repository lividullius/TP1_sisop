; Cenario: duplo bloqueio de I/O — SYSCALL 2 (leitura) e SYSCALL 1 (escrita)
; Le um numero pelo terminal, multiplica por 3 e exibe
; Ex: usuario digita 5 => output = 15
; Instrucoes executadas: 6  |  CI sugerido: 6  |  Pi sugerido: 15
; ATENCAO: o simulador solicitara digitacao ao executar SYSCALL 2
; Util para: demonstrar dois bloqueios de I/O no mesmo periodo,
;            rescheduling EDF enquanto processo aguarda entrada

.data
entrada 0
.enddata

.code
SYSCALL 2
STORE entrada
LOAD entrada
MULT #3
SYSCALL 1
SYSCALL 0
.endcode
