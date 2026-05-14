from enum import Enum, auto
from typing import TYPE_CHECKING

from .instruction import AddressingMode

if TYPE_CHECKING:
    from .pcb import PCB


class ExecutionResult(Enum):
    NORMAL = auto()
    SYSCALL = auto()
    HALT = auto()        # fim das instrucoes (PC fora do range)


class CPU:
    """
    Executa UMA instrucao do processo apontado pelo PCB.
    Lê/escreve acc, pc e data_memory diretamente no PCB.
    """

    def execute_one(self, pcb: "PCB") -> ExecutionResult:
        prog = pcb.program
        if pcb.pc >= len(prog.instructions):
            return ExecutionResult.HALT

        instr = prog.instructions[pcb.pc]
        m = instr.mnemonic

        if m == "SYSCALL":
            pcb.syscall_code = int(instr.operand) if instr.operand is not None else 0
            pcb.pc += 1
            return ExecutionResult.SYSCALL

        if m == "LOAD":
            pcb.acc = self._resolve(instr, pcb)
            pcb.pc += 1

        elif m == "STORE":
            if instr.mode == AddressingMode.IMMEDIATE:
                raise ValueError(f"Processo {pcb.name}: STORE nao suporta modo imediato (PC={pcb.pc})")
            idx = self._mem_index(instr, pcb)
            pcb.data_memory[idx] = pcb.acc
            pcb.pc += 1

        elif m == "ADD":
            pcb.acc += self._resolve(instr, pcb)
            pcb.pc += 1

        elif m == "SUB":
            pcb.acc -= self._resolve(instr, pcb)
            pcb.pc += 1

        elif m == "MULT":
            pcb.acc *= self._resolve(instr, pcb)
            pcb.pc += 1

        elif m == "DIV":
            divisor = self._resolve(instr, pcb)
            if divisor == 0:
                raise ZeroDivisionError(f"Processo {pcb.name}: divisao por zero em PC={pcb.pc}")
            pcb.acc //= divisor  # divisão inteira; mantém acc como int
            pcb.pc += 1

        # Saltos: o parser já resolveu labels para índice numérico na 2ª passagem,
        # então instr.operand é sempre um índice inteiro de instrução.
        elif m == "BRANY":
            pcb.pc = int(instr.operand)

        elif m == "BRPOS":
            pcb.pc = int(instr.operand) if pcb.acc > 0 else pcb.pc + 1

        elif m == "BRZERO":
            pcb.pc = int(instr.operand) if pcb.acc == 0 else pcb.pc + 1

        elif m == "BRNEG":
            pcb.pc = int(instr.operand) if pcb.acc < 0 else pcb.pc + 1

        else:
            raise ValueError(f"Instrucao desconhecida: {m}")

        return ExecutionResult.NORMAL

    # ------------------------------------------------------------------
    def _resolve(self, instr, pcb: "PCB") -> int:
        """Retorna o valor efetivo do operando: literal (#n) ou conteúdo da posição de memória."""
        if instr.mode == AddressingMode.IMMEDIATE:
            return int(instr.operand)
        return pcb.data_memory[self._mem_index(instr, pcb)]

    def _mem_index(self, instr, pcb: "PCB") -> int:
        """Converte o operando para índice em data_memory.
        Se for nome de variável (ex: 'x'), busca o índice em data_map; caso contrário usa o número diretamente."""
        operand = instr.operand
        data_map = pcb.program.data_map
        if operand in data_map:
            return data_map[operand]
        return int(operand)
