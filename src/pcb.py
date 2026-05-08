from enum import Enum, auto
from typing import List, Optional
from .program import Program


class ProcessState(Enum):
    PRONTO = "PRONTO"
    EXECUTANDO = "EXECUTANDO"
    BLOQUEADO = "BLOQUEADO"
    FINALIZADO = "FINALIZADO"   # periodo concluido; aguarda reativacao
    TERMINADO = "TERMINADO"     # encerrado por SYSCALL 0; nao sera reativado


class PCB:
    _next_id = 1

    def __init__(self, name: str, program: Program,
                 arrival_time: int, period: int, computation_time: int):
        self.id = PCB._next_id
        PCB._next_id += 1

        self.name = name
        self.program = program
        self.state = ProcessState.PRONTO

        # registradores salvos (contexto)
        self.acc: int = 0
        self.pc: int = 0

        # memoria de dados propria (copia independente por periodo)
        self.data_memory: List[int] = program.fresh_data_memory()

        # parametros EDF
        self.arrival_time = arrival_time
        self.period = period                       # Pi
        self.computation_time = computation_time   # Ci total
        self.remaining_ci = computation_time       # instrucoes restantes no periodo
        self.absolute_deadline = arrival_time + period

        # bloqueio I/O
        self.block_timer: int = 0
        self.syscall_code: Optional[int] = None

        # historico para relatorio
        self.deadline_misses: int = 0
        self.periods_completed: int = 0

    # ------------------------------------------------------------------
    def save_context(self):
        pass  # acc e pc ja estao no PCB; metodo existe por simetria

    def restore_context(self):
        pass  # idem

    def reset_for_new_period(self, current_time: int):
        self.pc = 0
        self.acc = 0
        self.remaining_ci = self.computation_time
        self.data_memory = self.program.fresh_data_memory()
        self.absolute_deadline = current_time + self.period
        self.state = ProcessState.PRONTO

    def __lt__(self, other: "PCB"):
        # PriorityQueue usa < ; menor deadline = maior prioridade
        return self.absolute_deadline < other.absolute_deadline

    def __repr__(self):
        return (f"PCB({self.name}, state={self.state.value}, "
                f"deadline={self.absolute_deadline}, ci_rem={self.remaining_ci})")
