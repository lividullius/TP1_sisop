; Cenario: tarefa PERIODICA — sem SYSCALL 0, periodo encerra pelo limite de CI
; A cada periodo: carrega valor, dobra e exibe; o BRANY reinicia o loop
; mas o CI se esgota em BRANY -> estado FINALIZADO -> reativacao automatica
; Na reativacao: acc, pc e memoria sao resetados para valores iniciais
;
; CI sugerido: 4  |  Pi sugerido: 10  |  arrival: 0  |  max_t: 35
; Output por periodo (fixo): [OUTPUT t=?] Tx: 14
; Util para: demonstrar reativacao periodica EDF (arrival + k * Pi)

.data
valor 7
.enddata

.code
inicio:
LOAD valor
MULT #2
SYSCALL 1
BRANY inicio
.endcode
