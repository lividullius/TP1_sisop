from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class AddressingMode(Enum):
    # IMMEDIATE: operando é valor literal (ADD #5)
    # DIRECT:    operando é variável; CPU lê da memória de dados do processo (ADD x)
    IMMEDIATE = auto()
    DIRECT = auto()


@dataclass
class Instruction:
    """
    Instrução já parseada e pronta para execução.
    Labels de salto (ex: BRANY loop) são resolvidos para índice numérico
    na segunda passagem do parser — a CPU usa o número diretamente como novo PC.
    """
    mnemonic: str
    operand: Optional[str] = None
    mode: AddressingMode = AddressingMode.DIRECT

    def __str__(self):
        # Reconstrói a instrução legível para o log do Gantt
        if self.operand is None:
            return self.mnemonic
        prefix = "#" if self.mode == AddressingMode.IMMEDIATE else ""
        return f"{self.mnemonic} {prefix}{self.operand}"
