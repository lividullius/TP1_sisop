from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class AddressingMode(Enum):
    IMMEDIATE = auto()  # #valor  -> usa o valor literal
    DIRECT = auto()     # variavel -> usa o conteudo da memoria


@dataclass
class Instruction:
    mnemonic: str
    operand: Optional[str] = None
    mode: AddressingMode = AddressingMode.DIRECT

    def __str__(self):
        if self.operand is None:
            return self.mnemonic
        prefix = "#" if self.mode == AddressingMode.IMMEDIATE else ""
        return f"{self.mnemonic} {prefix}{self.operand}"
