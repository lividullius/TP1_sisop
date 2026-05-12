from typing import List, Tuple
from .instruction import Instruction, AddressingMode
from .program import Program


class ParseError(Exception):
    pass


class Parser:
    """
    Duas passadas:
      1a: mapeia labels -> indice de instrucao; coleta variaveis de .data
      2a: resolve referencias a labels nos operandos de salto
    """

    MNEMONICS_WITH_OPERAND = {
        "LOAD", "STORE", "ADD", "SUB", "MULT", "DIV",
        "BRANY", "BRPOS", "BRZERO", "BRNEG",
    }

    def parse(self, filepath: str) -> Program:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        name = filepath.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        code_lines, data_lines = self._split_sections(lines)

        data_map, initial_data = self._parse_data(data_lines)
        instructions, label_map = self._first_pass(code_lines)
        self._second_pass(instructions, label_map)

        prog = Program(name=name, instructions=instructions,
                       data_map=data_map, initial_data=initial_data)
        return prog

    # ------------------------------------------------------------------
    def _split_sections(self, lines):
        code_lines, data_lines = [], []
        in_code = in_data = False
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith(";"):
                continue
            low = line.lower()
            if low == ".code":
                in_code, in_data = True, False
            elif low == ".endcode":
                in_code = False
            elif low == ".data":
                in_data, in_code = True, False
            elif low == ".enddata":
                in_data = False
            elif in_code:
                code_lines.append(line)
            elif in_data:
                data_lines.append(line)
        return code_lines, data_lines

    def _parse_data(self, data_lines) -> Tuple[dict, list]:
        data_map: dict = {}
        initial_data: list = []
        for line in data_lines:
            # formato: nome_var valor_inicial
            parts = line.split()
            if len(parts) != 2:
                raise ParseError(f"Linha de dados invalida: '{line}'")
            var_name, val_str = parts
            data_map[var_name] = len(initial_data)
            initial_data.append(int(val_str))
        return data_map, initial_data

    def _first_pass(self, code_lines) -> Tuple[List[Instruction], dict]:
        instructions: List[Instruction] = []
        label_map: dict = {}
        for line in code_lines:
            # remove comentario inline
            line = line.split(";")[0].strip()
            if not line:
                continue
            # label?
            if line.endswith(":"):
                label_map[line[:-1]] = len(instructions)
                continue
            # label colada a instrucao: "ponto1: LOAD x"
            if ":" in line:
                label_part, rest = line.split(":", 1)
                label_map[label_part.strip()] = len(instructions)
                line = rest.strip()
                if not line:
                    continue

            instr = self._parse_instruction(line)
            instructions.append(instr)
        return instructions, label_map

    def _second_pass(self, instructions: List[Instruction], label_map: dict):
        jump_mnemonics = {"BRANY", "BRPOS", "BRZERO", "BRNEG"}
        for instr in instructions:
            if instr.mnemonic in jump_mnemonics and instr.operand in label_map:
                instr.operand = str(label_map[instr.operand])

    def _parse_instruction(self, line: str) -> Instruction:
        parts = line.split(None, 1)
        mnemonic = parts[0].upper()

        if mnemonic == "SYSCALL":
            operand = parts[1].strip() if len(parts) > 1 else None
            return Instruction(mnemonic=mnemonic, operand=operand,
                               mode=AddressingMode.DIRECT)

        if mnemonic not in self.MNEMONICS_WITH_OPERAND:
            raise ParseError(f"Mnemonico desconhecido: '{mnemonic}'")

        if len(parts) < 2:
            raise ParseError(f"Instrucao '{mnemonic}' requer operando")

        raw_operand = parts[1].strip()
        if raw_operand.startswith("#"):
            return Instruction(mnemonic=mnemonic, operand=raw_operand[1:],
                               mode=AddressingMode.IMMEDIATE)
        return Instruction(mnemonic=mnemonic, operand=raw_operand,
                           mode=AddressingMode.DIRECT)
