; Cenario: desvios condicionais com BRPOS e BRNEG
; Classifica 'valor': +1 (positivo), -1 (negativo), 0 (zero)
; Com valor=7 => output=1 | valor=-5 => output=-1 | valor=0 => output=0
; Instrucoes executadas: 8 (positivo/negativo) ou 9 (zero)
; CI sugerido: 9  |  Pi sugerido: 15
; Util para: demonstrar BRPOS/BRNEG, preempcao entre tarefas curtas

.data
valor 7
resultado 0
.enddata

.code
LOAD valor
BRPOS positivo
BRNEG negativo
; chegou aqui: valor e zero
LOAD #0
STORE resultado
BRANY fim
positivo:
LOAD #1
STORE resultado
BRANY fim
negativo:
LOAD #-1
STORE resultado
fim:
LOAD resultado
SYSCALL 1
SYSCALL 0
.endcode
