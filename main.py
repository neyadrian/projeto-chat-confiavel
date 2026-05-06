import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from chat_node import ChatNode

def main():
    print("=== Chat Selective Repeat (UDP) ===")
    
    my_port = int(input("Qual porta VOCÊ quer usar? (ex: 5000): "))
    peer_port = int(input("Qual a porta do DESTINO? (ex: 5001): "))
    
    node = ChatNode(my_ip="127.0.0.1", my_port=my_port, peer_ip="127.0.0.1", peer_port=peer_port)
    
    print("\n[+] Nó iniciado! Você pode começar a digitar as mensagens.")
    print("[+] Digite 'sair' para encerrar o chat.\n")
    
    try:
        while True:
            msg = input()
            
            if msg.lower().strip() == 'sair':
                break
                
            if msg.strip():
                node.send_chat_message(msg)
                
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    finally:
        print("Encerrando o nó...")
        node.stop()

if __name__ == "__main__":
    main()