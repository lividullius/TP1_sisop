# TP1 Sistemas Operacionais — Simulador EDF

Simulador de escalonamento **EDF (Earliest Deadline First)** com interpretador de assembly hipotético, desenvolvido em Python para a disciplina de Sistemas Operacionais da PUCRS.

---

## Visão geral

O simulador executa múltiplos processos periódicos em tempo discreto. A cada tick, o escalonador EDF escolhe o processo com menor deadline absoluto. Processos são preemptíveis e reativados automaticamente a cada novo período.

---

## Estrutura de arquivos

```
TP1_sisop/
├── main.py                   # Ponto de entrada; coleta parâmetros e inicia simulação
├── programs/
│   ├── prog1.asm             # Programa exemplo: loop com contador e output
│   └── prog2.asm             # Programa exemplo: operação simples com output
└── src/
    ├── instruction.py        # Dataclass Instruction + enum AddressingMode (#imediato / direto)
    ├── program.py            # Dataclass Program: lista de instruções + mapa de variáveis
    ├── parser.py             # Parser dois-passos: lê .asm, resolve labels, retorna Program
    ├── cpu.py                # CPU: executa uma instrução por tick, retorna ExecutionResult
    ├── pcb.py                # PCB: contexto de processo (acc, pc, memória, estado EDF)
    ├── syscall_handler.py    # Trata SYSCALLs 0 (termina), 1 (output/bloqueia), 2 (input/bloqueia)
    └── simulation_engine.py  # Motor principal: loop de ticks, fila EDF, relatório Gantt
```

### Descrição de cada módulo

| Arquivo | Responsabilidade |
|---|---|
| `instruction.py` | Define `Instruction` (mnemônico, operando, modo de endereçamento) |
| `program.py` | Agrupa instruções e memória de dados inicial de um programa |
| `parser.py` | Lê arquivos `.asm`, resolve labels em dois passos, retorna `Program` |
| `cpu.py` | Interpreta e executa uma instrução por vez sobre o estado do `PCB` |
| `pcb.py` | Armazena o contexto completo do processo (registradores, deadline, estado) |
| `syscall_handler.py` | Processa chamadas de sistema: encerramento, I/O com bloqueio temporário |
| `simulation_engine.py` | Orquestra ticks, fila de prontos (min-heap por deadline), preempção e relatório |

---

## Linguagem Assembly suportada

Os programas são escritos em arquivos `.asm` com duas seções:

```asm
.data
  nome_variavel valor_inicial
.enddata

.code
  ; instruções
.endcode
```

### Instruções disponíveis

| Instrução | Descrição |
|---|---|
| `LOAD x` / `LOAD #v` | Carrega valor no acumulador (direto ou imediato) |
| `STORE x` | Salva acumulador na variável `x` |
| `ADD x` / `ADD #v` | Acumulador += valor |
| `SUB x` / `SUB #v` | Acumulador -= valor |
| `MULT x` / `MULT #v` | Acumulador *= valor |
| `DIV x` / `DIV #v` | Acumulador //= valor |
| `BRANY label` | Salto incondicional |
| `BRPOS label` | Salto se acumulador > 0 |
| `BRZERO label` | Salto se acumulador == 0 |
| `BRNEG label` | Salto se acumulador < 0 |
| `SYSCALL 0` | Encerra o processo |
| `SYSCALL 1` | Imprime acumulador e bloqueia por 1–3 ticks |
| `SYSCALL 2` | Lê valor do usuário e bloqueia por 1–3 ticks |

---

## Como rodar

**Pré-requisito:** Python 3.10+

```bash
python main.py
```

O programa pede interativamente:

1. Número de tarefas a carregar
2. Para cada tarefa:
   - Caminho do arquivo `.asm` (ex: `programs/prog1.asm`)
   - Nome da tarefa (ex: `T1`)
   - Arrival time — instante de chegada (padrão: `0`)
   - **Ci** — número de instruções executadas por período
   - **Pi** — duração do período
3. Tempo máximo de simulação (padrão: `50`)

### Exemplo de execução

```
Quantas tarefas deseja carregar? 2

--- Tarefa 1 ---
  Caminho do arquivo .asm: programs/prog1.asm
  Nome da tarefa: T1
  Arrival time (padrao 0): 0
  Ci — instrucoes por periodo: 4
  Pi — periodo: 8

--- Tarefa 2 ---
  Caminho do arquivo .asm: programs/prog2.asm
  Nome da tarefa: T2
  Arrival time (padrao 0): 0
  Ci — instrucoes por periodo: 2
  Pi — periodo: 5

Tempo maximo de simulacao (padrao 50): 20
```

### Saída

- Linha por tick mostrando processo em execução, instrução e estado dos demais
- Avisos de **deadline miss** durante a simulação
- Relatório final com timeline Gantt, períodos completados e deadlines perdidos por processo
