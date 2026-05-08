import random
from typing import Optional
from .pcb import PCB, ProcessState


class SyscallHandler:
    def handle(self, pcb: PCB, current_time: int) -> Optional[str]:
        """
        Processa a syscall do PCB. Retorna mensagem de output (se houver).
        Altera o estado do PCB para BLOQUEADO (syscall 1/2) ou FINALIZADO (syscall 0).
        """
        code = pcb.syscall_code
        msg = None

        if code == 0:
            pcb.state = ProcessState.TERMINADO
            pcb.periods_completed += 1

        elif code == 1:
            msg = f"[OUTPUT t={current_time}] {pcb.name}: {pcb.acc}"
            pcb.state = ProcessState.BLOQUEADO
            pcb.block_timer = random.randint(1, 3)

        elif code == 2:
            try:
                value = int(input(f"[INPUT t={current_time}] {pcb.name} aguarda leitura: "))
            except (ValueError, EOFError):
                value = 0
            pcb.acc = value
            pcb.state = ProcessState.BLOQUEADO
            pcb.block_timer = random.randint(1, 3)

        pcb.syscall_code = None
        return msg
