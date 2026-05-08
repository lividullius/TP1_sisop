from dataclasses import dataclass, field
from typing import List, Dict
from .instruction import Instruction


@dataclass
class Program:
    name: str
    instructions: List[Instruction] = field(default_factory=list)
    # nome_variavel -> indice em data_memory
    data_map: Dict[str, int] = field(default_factory=dict)
    # valores iniciais da memoria de dados
    initial_data: List[int] = field(default_factory=list)

    def fresh_data_memory(self) -> List[int]:
        """Retorna uma copia dos dados iniciais para o processo."""
        return list(self.initial_data)
