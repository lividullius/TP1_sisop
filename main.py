import sys
import os

# Garante que o diretório do script esteja no path para os imports funcionarem
# ao rodar como: python main.py
sys.path.insert(0, os.path.dirname(__file__))

from src.parser import Parser, ParseError
from src.pcb import PCB, PCB as _PCBClass
from src.simulation_engine import SimulationEngine


def input_int(prompt: str, default: int = None) -> int:
    # Lê um inteiro do usuário, repetindo até receber um valor válido.
    # Se o usuário pressionar Enter sem digitar nada e houver um valor padrão, usa o padrão.
    while True:
        raw = input(prompt).strip()
        if not raw and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            print("  Digite um numero inteiro.")


def main():
    # Cabeçalho do simulador
    print("=" * 60)
    print(" Simulador EDF — TP1 Sistemas Operacionais")
    print("=" * 60)

    parser = Parser()
    pcbs = []
    _PCBClass._next_id = 1  # reseta o contador de IDs dos processos a cada execução

    # Pergunta quantas tarefas o usuário quer carregar
    n = input_int("\nQuantas tarefas deseja carregar? ", default=1)

    # Loop para cadastrar cada tarefa
    for i in range(n):
        print(f"\n--- Tarefa {i+1} ---")

        # Lê e valida o caminho do arquivo .asm com o código da tarefa
        filepath = input("  Caminho do arquivo .asm: ").strip()
        if not os.path.isfile(filepath):
            print(f"  Arquivo nao encontrado: {filepath}")
            sys.exit(1)

        # Faz o parse do arquivo .asm, convertendo as instruções em uma estrutura interna
        try:
            prog = parser.parse(filepath)
        except ParseError as e:
            print(f"  Erro de parse: {e}")
            sys.exit(1)

        # Lê os parâmetros de escalonamento da tarefa
        name = input(f"  Nome da tarefa (ex: T{i+1}): ").strip() or f"T{i+1}"
        at   = input_int("  Arrival time (padrao 0): ", default=0)  # instante em que a tarefa chega
        ci   = input_int("  Ci — instrucoes por periodo: ")          # tempo de computação por período
        pi   = input_int("  Pi — periodo: ")                         # período da tarefa (deadline relativa)

        # Cria o PCB (Process Control Block) com todos os dados da tarefa e adiciona à lista
        pcb = PCB(name=name, program=prog, arrival_time=at,
                  period=pi, computation_time=ci)
        pcbs.append(pcb)

    # Pergunta até qual instante de tempo a simulação deve rodar
    max_t = input_int("\nTempo maximo de simulacao (padrao 50): ", default=50)

    print("\n" + "=" * 60)
    print("INICIANDO SIMULACAO")
    print("=" * 60 + "\n")

    # Cria o motor de simulação com as tarefas cadastradas e o tempo máximo,
    # depois executa o escalonador EDF
    engine = SimulationEngine(pcbs, max_time=max_t)
    engine.run()


if __name__ == "__main__":
    main()
