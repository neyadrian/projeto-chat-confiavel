import sys
from src.chat import Chat
from src.config import PORT_A, PORT_B


def main():
    print()
    print("  Escolha o terminal:")
    print("  [1] Terminal A (porta local={}, remota={})".format(PORT_A, PORT_B))
    print("  [2] Terminal B (porta local={}, remota={})".format(PORT_B, PORT_A))
    print()

    choice = input("  Opcao (1 ou 2): ").strip()

    if choice == "1":
        name, local, remote = "Alice", PORT_A, PORT_B
    elif choice == "2":
        name, local, remote = "Bob", PORT_B, PORT_A
    else:
        print("  Opcao invalida.")
        sys.exit(1)

    chat = Chat(name=name, local_port=local, remote_port=remote)
    chat.start()


if __name__ == "__main__":
    main()
