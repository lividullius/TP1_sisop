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
│   ├── prog1.asm             # Loop regressivo com BRZERO — CPU-bound longa (Ci=45)
│   ├── prog2.asm             # Operação simples ADD imediato — tarefa mínima (Ci=5)
│   ├── prog3.asm             # Aritmética com MULT e DIV — CPU-bound curta (Ci=6)
│   ├── prog4.asm             # Desvios condicionais BRPOS/BRNEG — classificação de sinal (Ci=9)
│   ├── prog5.asm             # Duplo bloqueio I/O — SYSCALL 2 (leitura) + SYSCALL 1 (escrita)
│   └── prog6.asm             # Tarefa periódica sem SYSCALL 0 — encerra pelo limite de Ci
└── src/
    ├── instruction.py        # Dataclass Instruction + enum AddressingMode (#imediato / direto)
    ├── program.py            # Dataclass Program: lista de instruções + mapa de variáveis
    ├── parser.py             # Parser dois-passos: lê .asm, resolve labels, retorna Program
    ├── cpu.py                # CPU: executa uma instrução por tick, retorna ExecutionResult
    ├── pcb.py                # PCB: contexto de processo (acc, pc, memória, estado EDF)
    ├── syscall_handler.py    # Trata SYSCALLs 0 (termina), 1 (output/bloqueia), 2 (input/bloqueia)
    ├── simulation_engine.py  # Motor principal: loop de ticks, fila EDF, relatório Gantt
    └── gantt_renderer.py     # Gera gantt.html: gráfico interativo com estados, eventos e badges
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
| `gantt_renderer.py` | Gera `gantt.html` auto-contido com gráfico de Gantt interativo |

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

Comentários são iniciados com `;` e podem aparecer em qualquer linha.

### Instruções disponíveis

| Instrução | Descrição |
|---|---|
| `LOAD x` / `LOAD #v` | Carrega valor no acumulador (direto ou imediato) |
| `STORE x` | Salva acumulador na variável `x` (não aceita modo imediato) |
| `ADD x` / `ADD #v` | Acumulador += valor |
| `SUB x` / `SUB #v` | Acumulador -= valor |
| `MULT x` / `MULT #v` | Acumulador *= valor |
| `DIV x` / `DIV #v` | Acumulador //= valor (divisão inteira) |
| `BRANY label` | Salto incondicional |
| `BRPOS label` | Salto se acumulador > 0 |
| `BRZERO label` | Salto se acumulador == 0 |
| `BRNEG label` | Salto se acumulador < 0 |
| `SYSCALL 0` | Encerra o processo permanentemente |
| `SYSCALL 1` | Imprime acumulador e bloqueia por 1–3 ticks (I/O) |
| `SYSCALL 2` | Lê inteiro do terminal e bloqueia por 1–3 ticks (I/O) |

### Modos de endereçamento

| Sintaxe | Modo | Comportamento |
|---|---|---|
| `ADD x` | Direto | Lê o valor da variável `x` na memória de dados |
| `ADD #5` | Imediato | Usa o literal `5` diretamente |

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
   - **Pi** — duração do período (também é o deadline relativo)
3. Tempo máximo de simulação (padrão: `50`)

### Exemplo de execução

```
Quantas tarefas deseja carregar? 2

--- Tarefa 1 ---
  Caminho do arquivo .asm: programs/prog2.asm
  Nome da tarefa: T1
  Arrival time (padrao 0): 0
  Ci — instrucoes por periodo: 5
  Pi — periodo: 8

--- Tarefa 2 ---
  Caminho do arquivo .asm: programs/prog3.asm
  Nome da tarefa: T2
  Arrival time (padrao 0): 0
  Ci — instrucoes por periodo: 6
  Pi — periodo: 10

Tempo maximo de simulacao (padrao 50): 30
```

---

## Saída

### Terminal

- Uma linha por tick mostrando processo em execução, instrução e estado dos demais processos
- Avisos de **deadline miss** sinalizados durante a simulação
- Relatório final com timeline Gantt em texto, períodos completados e deadlines perdidos por processo

### Gantt HTML (`gantt.html`)

Ao final da simulação é gerado um arquivo `gantt.html` auto-contido no diretório atual. Abra no navegador para visualizar.

