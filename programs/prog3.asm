; Cenario: operacoes aritmeticas com MULT e DIV
; Calcula (a * b) / c  =>  (6 * 7) / 2 = 21
; Instrucoes executadas: 6  |  CI sugerido: 6  |  Pi sugerido: 10
; Util para: demonstrar MULT/DIV, tarefa CPU-bound curta

.data
a 6
b 7
c 2
resultado 0
.enddata

.code
LOAD a
MULT b
DIV c
STORE resultado
SYSCALL 1
SYSCALL 0
.endcode
