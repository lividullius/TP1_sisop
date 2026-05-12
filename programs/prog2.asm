; Cenario: operacao simples sem loop — ADD com imediato
; Calcula x + 5  =>  10 + 5 = 15
; Instrucoes executadas: 5  |  CI sugerido: 5  |  Pi sugerido: 8
; Util para: tarefa minima, boa para combinar com tarefas longas e forcar preempcao

.data
x 10
.enddata

.code
LOAD x
ADD #5
STORE x
SYSCALL 1
SYSCALL 0
.endcode
