import sys
import argparse
from src.config import PORT_A, PORT_B, LOSS_RATE
from src.chat import Chat


def parse_args():
    parser = argparse.ArgumentParser(description="Chat SR sobre UDP")
    parser.add_argument("terminal", choices=["A", "B", "a", "b"],
                        help="Terminal: A (5000->5001) ou B (5001->5000)")
    parser.add_argument("--loss", type=float, default=LOSS_RATE,
                        help=f"Taxa de perda (padrao: {LOSS_RATE})")
    parser.add_argument("--no-loss", action="store_true",
                        help="Desativar perda simulada")
    parser.add_argument("--debug", action="store_true",
                        help="Logging DEBUG")
    return parser.parse_args()


def main():
    args = parse_args()
    terminal = args.terminal.upper()

    if terminal == "A":
        local_port, remote_port, name = PORT_A, PORT_B, "Alice"
    else:
        local_port, remote_port, name = PORT_B, PORT_A, "Bob"

    loss_rate = 0.0 if args.no_loss else args.loss
    log_level = "DEBUG" if args.debug else "INFO"

    chat = Chat(name=name, local_port=local_port, remote_port=remote_port,
                loss_rate=loss_rate, simulate_loss=not args.no_loss,
                log_level=log_level)
    try:
        chat.start()
    except KeyboardInterrupt:
        chat.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
