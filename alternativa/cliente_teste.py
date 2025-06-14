# cliente.py (VERSÃO COM ESTADO E SINCRONIZAÇÃO)

import socket
import sys
import threading
import os

# Nome do arquivo que guardará o estado do cliente
ARQUIVO_ESTADO = 'estado_cliente.txt'

def carregar_ultimo_id():
    """Lê o arquivo de estado para saber qual foi a última mensagem recebida."""
    if not os.path.exists(ARQUIVO_ESTADO):
        return 0 # Se não há histórico, começa do zero.
    try:
        with open(ARQUIVO_ESTADO, 'r') as f:
            return int(f.read().strip())
    except (ValueError, IOError):
        return 0

def salvar_ultimo_id(ultimo_id):
    """Salva o ID da última mensagem recebida no arquivo de estado."""
    try:
        with open(ARQUIVO_ESTADO, 'w') as f:
            f.write(str(ultimo_id))
    except IOError as e:
        print(f"[ERRO] Não foi possível salvar o estado: {e}")

def receber_mensagens(sock):
    """Recebe mensagens, as exibe e salva o ID da última recebida."""
    while True:
        try:
            dados = sock.recv(1024)
            if not dados:
                print("\n[INFO] O servidor encerrou a conexão.")
                break
            
            mensagem_completa = dados.decode('utf-8')
            # O formato esperado é "ID:TEXTO"
            partes = mensagem_completa.split(':', 1)
            if len(partes) == 2:
                id_msg, texto_msg = partes
                print(f"\n>> ID {id_msg}: {texto_msg}")
                # Salva o ID desta mensagem como o último recebido.
                salvar_ultimo_id(int(id_msg))
            
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            break

def iniciar_cliente():
    """Função principal que gerencia a conexão, sincronização e input."""
    HOST = input("Digite o IP do servidor (padrão: 127.0.0.1): ") or "127.0.0.1"
    PORTA = 65432

    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print(f"Tentando conectar a {HOST}:{PORTA}...")
        cliente_socket.connect((HOST, PORTA))
        print("[CONECTADO] Conexão estabelecida.")
        
        # 1. CARREGA O ESTADO E ENVIA A MENSAGEM DE SINCRONIZAÇÃO
        ultimo_id_visto = carregar_ultimo_id()
        mensagem_sync = f"SYNC:{ultimo_id_visto}"
        cliente_socket.sendall(mensagem_sync.encode('utf-8'))
        print(f"[SINCRONIZANDO] Solicitando atualizações a partir do ID {ultimo_id_visto+1}...")

        # 2. INICIA A THREAD PARA RECEBER MENSAGENS (INCLUINDO AS PERDIDAS)
        thread_recebimento = threading.Thread(target=receber_mensagens, args=(cliente_socket,), daemon=True)
        thread_recebimento.start()

        print('[CONTROLE] Digite "sair" a qualquer momento para desconectar.')
        
        # 3. THREAD PRINCIPAL FICA NO LOOP DE INPUT
        while True:
            comando = input()
            if comando.lower() == 'sair':
                break
        
    except ConnectionRefusedError:
        print("[ERRO] Conexão recusada.")
    except KeyboardInterrupt:
        print("\n[INFO] Encerrando o cliente.")
    finally:
        print("[INFO] Desconectando...")
        cliente_socket.close()

if __name__ == "__main__":
    iniciar_cliente()