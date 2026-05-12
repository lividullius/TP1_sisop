import heapq
from typing import List, Optional, Tuple

from .pcb import PCB, ProcessState
from .cpu import CPU, ExecutionResult
from .syscall_handler import SyscallHandler
from .instruction import Instruction


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

        # log
        self.gantt: List[str] = []           # slot por tick
        self.events: List[str] = []          # mensagens de texto
        self.deadline_misses: List[Tuple[str, int]] = []

    # ------------------------------------------------------------------
    def run(self):
        t = 0
        while t < self.max_time and not self._all_done():
            self._tick(t)
            t += 1
        self._print_report(t)

    # ------------------------------------------------------------------
    def _tick(self, t: int):
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

        # 6. Verificar deadline miss APOS execucao: evita falso positivo quando
        #    a ultima instrucao executa exatamente no tick do deadline
        self._check_deadline_misses(t)

    # ------------------------------------------------------------------
    def _check_arrivals(self, t: int):
        arrived = []
        remaining = []
        for p in self._pending:
            if p.arrival_time <= t:
                p.state = ProcessState.PRONTO
                heapq.heappush(self._ready, p)
                self._log(t, f"{p.name} chegou (deadline={p.absolute_deadline})")
                arrived.append(p)
            else:
                remaining.append(p)
        self._pending = remaining

    def _check_periodic_reactivations(self, t: int):
        for p in self.all_pcbs:
            if p.state not in (ProcessState.FINALIZADO, ProcessState.BLOQUEADO):
                continue
            # proximo periodo comeca quando t == arrival_time + k*period
            offset = t - p.arrival_time
            if offset > 0 and offset % p.period == 0:
                if p.state == ProcessState.BLOQUEADO:
                    # remove da lista de bloqueados antes de resetar
                    self._blocked = [b for b in self._blocked if b is not p]
                p.reset_for_new_period(t)
                heapq.heappush(self._ready, p)
                self._log(t, f"{p.name} reativado (novo deadline={p.absolute_deadline})")

    def _update_blocked(self, t: int):
        still_blocked = []
        for p in self._blocked:
            p.block_timer -= 1
            if p.block_timer <= 0:
                p.state = ProcessState.PRONTO
                heapq.heappush(self._ready, p)
                self._log(t, f"{p.name} desbloqueado")
            else:
                still_blocked.append(p)
        self._blocked = still_blocked

    def _check_deadline_misses(self, t: int):
        for p in self.all_pcbs:
            if p.state in (ProcessState.PRONTO, ProcessState.BLOQUEADO, ProcessState.EXECUTANDO):
                if t == p.absolute_deadline and p.remaining_ci > 0:
                    p.deadline_misses += 1
                    self.deadline_misses.append((p.name, t))
                    print(f"  *** DEADLINE MISS: {p.name} no instante t={t} ***")

    def _schedule(self, t: int):
        if not self._ready:
            # sem candidatos; manter running ou ficar ocioso
            return

        best = self._ready[0]  # menor deadline

        if self._running is None:
            self._running = heapq.heappop(self._ready)
            self._running.state = ProcessState.EXECUTANDO
            return

        # preempcao: candidato tem deadline MENOR que o atual
        if best.absolute_deadline < self._running.absolute_deadline:
            # salvar contexto do atual e colocar de volta na fila
            self._running.state = ProcessState.PRONTO
            heapq.heappush(self._ready, self._running)
            self._running = heapq.heappop(self._ready)
            self._running.state = ProcessState.EXECUTANDO
            self._log(t, f"Preempcao: {self._running.name} assume")

    def _execute(self, t: int):
        p = self._running
        instr_str = str(p.program.instructions[p.pc]) if p.pc < len(p.program.instructions) else "?"
        self.gantt.append(p.name)

        result = self.cpu.execute_one(p)
        if result != ExecutionResult.HALT:
            p.remaining_ci -= 1

        # log da linha
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
            self._running = None

        elif result == ExecutionResult.HALT or p.remaining_ci <= 0:
            if result != ExecutionResult.SYSCALL:
                p.state = ProcessState.FINALIZADO
                p.periods_completed += 1
                self._log(t, f"{p.name} completou periodo {p.periods_completed}")
            self._running = None

    # ------------------------------------------------------------------
    def _all_done(self) -> bool:
        if self._pending or self._ready or self._blocked or self._running is not None:
            return False
        # processos FINALIZADO ainda podem ser reativados no proximo periodo
        return all(p.state == ProcessState.TERMINADO for p in self.all_pcbs)

    def _log(self, t: int, msg: str):
        self.events.append(f"t={t}: {msg}")

    def _print_report(self, total_time: int):
        print("\n" + "=" * 60)
        print("RELATORIO FINAL")
        print("=" * 60)

        # Gantt
        print("\nTimeline (Gantt):")
        slots = " ".join(f"{s:>4}" for s in range(len(self.gantt)))
        vals  = " ".join(f"{s:>4}" for s in self.gantt)
        print("  t: " + slots)
        print("     " + vals)

        # Resumo por processo
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
