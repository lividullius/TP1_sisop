import sys
import os

# permite rodar como: python main.py
sys.path.insert(0, os.path.dirname(__file__))

from src.parser import Parser, ParseError
from src.pcb import PCB, PCB as _PCBClass
from src.simulation_engine import SimulationEngine


def input_int(prompt: str, default: int = None) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            print("  Digite um numero inteiro.")


def main():
    print("=" * 60)
    print(" Simulador EDF — TP1 Sistemas Operacionais")
    print("=" * 60)

    parser = Parser()
    pcbs = []
    _PCBClass._next_id = 1  # reset ids

    n = input_int("\nQuantas tarefas deseja carregar? ", default=1)

    for i in range(n):
        print(f"\n--- Tarefa {i+1} ---")
        filepath = input("  Caminho do arquivo .asm: ").strip()
        if not os.path.isfile(filepath):
            print(f"  Arquivo nao encontrado: {filepath}")
            sys.exit(1)
        try:
            prog = parser.parse(filepath)
        except ParseError as e:
            print(f"  Erro de parse: {e}")
            sys.exit(1)

        name  = input(f"  Nome da tarefa (ex: T{i+1}): ").strip() or f"T{i+1}"
        at    = input_int("  Arrival time (padrao 0): ", default=0)
        ci    = input_int("  Ci — instrucoes por periodo: ")
        pi    = input_int("  Pi — periodo: ")

        pcb = PCB(name=name, program=prog, arrival_time=at,
                  period=pi, computation_time=ci)
        pcbs.append(pcb)

    max_t = input_int("\nTempo maximo de simulacao (padrao 50): ", default=50)

    print("\n" + "=" * 60)
    print("INICIANDO SIMULACAO")
    print("=" * 60 + "\n")

    engine = SimulationEngine(pcbs, max_time=max_t)
    engine.run()


if __name__ == "__main__":
    main()
