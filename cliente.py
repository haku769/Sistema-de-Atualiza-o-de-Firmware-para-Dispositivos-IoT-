# cliente.py (VERSÃO COM OPÇÃO DE SAIR)

import socket
import sys
import threading

def receber_mensagens(sock):
    """
    Esta função roda em uma thread separada.
    Seu único trabalho é receber mensagens do servidor e imprimi-las.
    """
    while True:
        try:
            # Fica bloqueado aqui até que uma mensagem chegue ou a conexão seja fechada.
            dados = sock.recv(1024)
            # Se 'dados' estiver vazio, o servidor encerrou a conexão.
            if not dados:
                print("\n[INFO] O servidor encerrou a conexão.")
                break
            
            # Decodifica a mensagem e a exibe para o usuário.
            # O '\n' no início garante que a mensagem apareça em uma nova linha,
            # sem interferir com o que o usuário possa estar digitando.
            print(f"\n>> ATUALIZAÇÃO RECEBIDA: {dados.decode('utf-8')}")

        except (ConnectionResetError, ConnectionAbortedError, OSError):
            # Estes erros acontecem se a conexão for fechada (pelo próprio cliente ou pelo servidor).
            # Apenas saímos do loop para encerrar a thread.
            break

def iniciar_cliente():
    """
    Função principal que configura a conexão e gerencia o input do usuário.
    """
    HOST = input("Digite o IP do servidor (padrão: 127.0.0.1): ") or "127.0.0.1"
    PORTA = 65432  # A mesma porta usada pelo servidor

    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print(f"Tentando conectar a {HOST}:{PORTA}...")
        cliente_socket.connect((HOST, PORTA))
        print("[CONECTADO] Conexão estabelecida com o servidor.")
        
        # Inicia a thread que vai ficar escutando as mensagens do servidor.
        # `daemon=True` garante que esta thread não impeça o programa de fechar.
        thread_recebimento = threading.Thread(target=receber_mensagens, args=(cliente_socket,), daemon=True)
        thread_recebimento.start()

        print('[CONTROLE] Digite "sair" a qualquer momento e pressione Enter para desconectar.')

        # A thread principal agora fica neste loop, esperando pelo comando do usuário.
        while True:
            comando = input()
            # Se o comando for "sair" (ignorando maiúsculas/minúsculas)...
            if comando.lower() == 'sair':
                # ...quebramos o loop para iniciar o processo de encerramento.
                break
        
    except ConnectionRefusedError:
        print("[ERRO] Conexão recusada. Verifique se o servidor está no ar e o IP está correto.")
    except KeyboardInterrupt:
        # Permite fechar com Ctrl+C
        print("\n[INFO] Encerrando o cliente.")
    finally:
        # Este bloco é executado sempre que o programa está prestes a fechar.
        print("[INFO] Desconectando...")
        # Fecha o socket, o que também fará com que a thread de recebimento pare.
        cliente_socket.close()

if __name__ == "__main__":
    iniciar_cliente()