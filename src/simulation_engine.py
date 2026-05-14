import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .pcb import PCB, ProcessState
from .cpu import CPU, ExecutionResult
from .syscall_handler import SyscallHandler
from .instruction import Instruction


@dataclass
class TickRecord:
    t: int
    running: Optional[str]          # nome do processo em execução, ou None se ocioso
    instruction: Optional[str]       # str(instr) executada neste tick
    states: Dict[str, str]           # snapshot {nome: estado} de todos os processos após o tick
    events: List[str] = field(default_factory=list)  # eventos ocorridos no tick (chegada, preempção, etc.)


class SimulationEngine:
    def __init__(self, pcbs: List[PCB], max_time: int = 100):
        self.all_pcbs = pcbs
        self.max_time = max_time
        self.cpu = CPU()
        self.syscall = SyscallHandler()

        # processos que ainda nao chegaram
        self._pending: List[PCB] = sorted(pcbs, key=lambda p: p.arrival_time)
        # fila de prontos: min-heap por (deadline, id)
        self._ready: list = []
        self._blocked: List[PCB] = []
        self._running: Optional[PCB] = None

        # log legado (texto)
        self.gantt: List[str] = []
        self.events: List[str] = []
        self.deadline_misses: List[Tuple[str, int]] = []

        # registros estruturados por tick (usados pelo gantt_renderer)
        self.tick_records: List[TickRecord] = []

        # acumuladores para o tick em andamento
        self._tick_events: List[str] = []
        self._tick_instruction: Optional[str] = None
        self._tick_running_name: Optional[str] = None

    # ------------------------------------------------------------------
    def run(self):
        t = 0
        while t < self.max_time and not self._all_done():
            self._tick(t)
            t += 1
        self._print_report(t)

    # ------------------------------------------------------------------
    def _tick(self, t: int):
        self._tick_events = []
        self._tick_instruction = None
        self._tick_running_name = None

        # 1. Verificar chegadas
        self._check_arrivals(t)

        # 2. Verificar reativacoes periodicas (processos FINALIZADOS no periodo anterior)
        self._check_periodic_reactivations(t)

        # 3. Decrementar timers de bloqueio e desbloquear
        self._update_blocked(t)

        # 4. Escolher proxima tarefa (EDF)
        self._schedule(t)

        # 5. Executar 1 instrucao
        if self._running is not None:
            self._execute(t)
        else:
            self.gantt.append("--")
            self._log(t, "CPU ociosa")
            print(f"t={t:3d} | CPU ociosa")

        # 6. Verificar deadline miss APOS execucao
        self._check_deadline_misses(t)

        # 7. Registrar snapshot do tick
        states = {p.name: p.state.value for p in self.all_pcbs}
        self.tick_records.append(TickRecord(
            t=t,
            running=self._tick_running_name,
            instruction=self._tick_instruction,
            states=states,
            events=list(self._tick_events),
        ))

    # ------------------------------------------------------------------
    def _check_arrivals(self, t: int):
        arrived = []
        remaining = []
        for p in self._pending:
            if p.arrival_time <= t:
                p.state = ProcessState.PRONTO
                heapq.heappush(self._ready, p)
                self._log(t, f"arrival:{p.name} (deadline={p.absolute_deadline})")
                arrived.append(p)
            else:
                remaining.append(p)
        self._pending = remaining

    def _check_periodic_reactivations(self, t: int):
        for p in self.all_pcbs:
            if p.state not in (ProcessState.FINALIZADO, ProcessState.BLOQUEADO):
                continue
            # offset % period == 0 detecta o início de cada novo período do processo
            offset = t - p.arrival_time
            if offset > 0 and offset % p.period == 0:
                if p.state == ProcessState.BLOQUEADO:
                    self._blocked = [b for b in self._blocked if b is not p]
                p.reset_for_new_period(t)
                heapq.heappush(self._ready, p)
                self._log(t, f"reactivation:{p.name} (deadline={p.absolute_deadline})")

    def _update_blocked(self, t: int):
        still_blocked = []
        for p in self._blocked:
            p.block_timer -= 1
            if p.block_timer <= 0:
                p.state = ProcessState.PRONTO
                heapq.heappush(self._ready, p)
                self._log(t, f"unblock:{p.name}")
            else:
                still_blocked.append(p)
        self._blocked = still_blocked

    def _check_deadline_misses(self, t: int):
        for p in self.all_pcbs:
            if p.state in (ProcessState.PRONTO, ProcessState.BLOQUEADO, ProcessState.EXECUTANDO):
                if t == p.absolute_deadline and p.remaining_ci > 0:
                    p.deadline_misses += 1
                    self.deadline_misses.append((p.name, t))
                    self._log(t, f"deadline_miss:{p.name}")
                    print(f"  *** DEADLINE MISS: {p.name} no instante t={t} ***")

    def _schedule(self, t: int):
        if not self._ready:
            return

        best = self._ready[0]

        if self._running is None:
            self._running = heapq.heappop(self._ready)
            self._running.state = ProcessState.EXECUTANDO
            return

        if best.absolute_deadline < self._running.absolute_deadline:
            preempted = self._running.name
            self._running.state = ProcessState.PRONTO
            heapq.heappush(self._ready, self._running)
            self._running = heapq.heappop(self._ready)
            self._running.state = ProcessState.EXECUTANDO
            self._log(t, f"preemption:{self._running.name} preempts {preempted}")

    def _execute(self, t: int):
        p = self._running
        instr_str = str(p.program.instructions[p.pc]) if p.pc < len(p.program.instructions) else "?"
        self.gantt.append(p.name)
        self._tick_running_name = p.name
        self._tick_instruction = instr_str

        result = self.cpu.execute_one(p)
        # HALT significa PC fora do range — nenhuma instrução foi executada, então não desconta Ci
        if result != ExecutionResult.HALT:
            p.remaining_ci -= 1

        others = [q for q in self.all_pcbs if q is not p
                  and q.state != ProcessState.FINALIZADO]
        others_str = " | ".join(f"{q.name}:{q.state.value}" for q in others)
        print(f"t={t:3d} | [{p.name}: EXECUTANDO] {instr_str:<20} | {others_str}")

        if result == ExecutionResult.SYSCALL:
            msg = self.syscall.handle(p, t)
            if msg:
                print(f"       {msg}")
            if p.state == ProcessState.BLOQUEADO:
                self._blocked.append(p)
                self._log(t, f"io_block:{p.name} (timer={p.block_timer})")
            elif p.state == ProcessState.TERMINADO:
                self._log(t, f"halt:{p.name}")
            self._running = None

        elif result == ExecutionResult.HALT or p.remaining_ci <= 0:
            if result != ExecutionResult.SYSCALL:
                p.state = ProcessState.FINALIZADO
                p.periods_completed += 1
                self._log(t, f"period_end:{p.name} (period {p.periods_completed})")
            self._running = None

    # ------------------------------------------------------------------
    def _all_done(self) -> bool:
        # Só encerra quando todas as filas estão vazias E todos os processos estão TERMINADO.
        # FINALIZADO não conta: o processo ainda vai reiniciar no próximo período.
        if self._pending or self._ready or self._blocked or self._running is not None:
            return False
        return all(p.state == ProcessState.TERMINADO for p in self.all_pcbs)

    def _log(self, t: int, msg: str):
        self.events.append(f"t={t}: {msg}")
        self._tick_events.append(msg)

    def _print_report(self, total_time: int):
        print("\n" + "=" * 60)
        print("RELATORIO FINAL")
        print("=" * 60)

        print("\nTimeline (Gantt):")
        slots = " ".join(f"{s:>4}" for s in range(len(self.gantt)))
        vals  = " ".join(f"{s:>4}" for s in self.gantt)
        print("  t: " + slots)
        print("     " + vals)

        print("\nResumo por processo:")
        for p in self.all_pcbs:
            print(f"  {p.name}: {p.periods_completed} periodo(s) completo(s), "
                  f"{p.deadline_misses} deadline(s) perdido(s)")

        if self.deadline_misses:
            print("\nDeadlines perdidos:")
            for name, t in self.deadline_misses:
                print(f"  DEADLINE MISS: {name} no instante t={t}")
        else:
            print("\nNenhum deadline perdido.")
