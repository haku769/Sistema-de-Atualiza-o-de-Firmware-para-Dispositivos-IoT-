# servidor.py (VERSÃO COM HISTÓRICO E SINCRONIZAÇÃO)

import socket
import sys
import threading

# --- Globais ---
# Lista de clientes para transmissão em tempo real
clientes_conectados = []
clientes_lock = threading.Lock()

# Novas globais para o histórico de mensagens
historico_mensagens = []
proximo_id_mensagem = 1
historico_lock = threading.Lock() # Trava para o histórico

def lidar_com_cliente(conn, addr):
    """
    Gerencia um cliente: primeiro sincroniza, depois adiciona para tempo real.
    """
    print(f"[NOVA CONEXÃO] Dispositivo em {addr}. Aguardando sincronização...")
    
    try:
        # 1. ESPERA A MENSAGEM DE SINCRONIZAÇÃO DO CLIENTE
        # Ex: "SYNC:15"
        sync_request = conn.recv(1024).decode('utf-8')
        
        ultimo_id_cliente = 0
        if sync_request.startswith('SYNC:'):
            ultimo_id_cliente = int(sync_request.split(':')[1])
        
        print(f"[SINCRONIZAÇÃO] Cliente {addr} solicitou atualizações a partir do ID: {ultimo_id_cliente}.")

        # 2. ENVIA AS MENSAGENS PERDIDAS
        with historico_lock:
            # Filtra o histórico para pegar apenas as mensagens que o cliente não tem.
            mensagens_a_enviar = [msg for msg in historico_mensagens if msg['id'] > ultimo_id_cliente]

        if mensagens_a_enviar:
            print(f"[SINCRONIZAÇÃO] Enviando {len(mensagens_a_enviar)} mensagem(ns) perdida(s) para {addr}.")
            for msg in mensagens_a_enviar:
                # Formata a mensagem com ID e texto para envio.
                mensagem_formatada = f"{msg['id']}:{msg['texto']}"
                conn.sendall(mensagem_formatada.encode('utf-8'))
                # Pequena pausa para garantir que o cliente consiga processar
                threading.sleep(0.05)

        # 3. ADICIONA O CLIENTE À LISTA DE TRANSMISSÃO EM TEMPO REAL
        print(f"[CONECTADO] Cliente {addr} sincronizado e agora recebendo atualizações em tempo real.")
        with clientes_lock:
            clientes_conectados.append(conn)

        # 4. MANTÉM A CONEXÃO E ESPERA POR DESCONEXÃO
        while True:
            data = conn.recv(1024)
            if not data:
                break
                
    except (ConnectionResetError, BrokenPipeError):
        pass # Apenas ignora, o finally cuidará da limpeza
    finally:
        print(f"[CLIENTE DESCONECTADO] Dispositivo em {addr} encerrou.")
        with clientes_lock:
            if conn in clientes_conectados:
                clientes_conectados.remove(conn)
        conn.close()

def iniciar_escuta_de_clientes(servidor_socket):
    try:
        while True:
            conn, addr = servidor_socket.accept()
            thread_cliente = threading.Thread(target=lidar_com_cliente, args=(conn, addr), daemon=True)
            thread_cliente.start()
    except OSError:
        pass

# --- PROGRAMA PRINCIPAL ---
if __name__ == "__main__":
    HOST = ''
    PORTA = 65432

    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        servidor_socket.bind((HOST, PORTA))
        servidor_socket.listen(10)
        
        print(f"\n[INFO] Servidor com Histórico iniciado na porta {PORTA}")

        thread_escuta = threading.Thread(target=iniciar_escuta_de_clientes, args=(servidor_socket,), daemon=True)
        thread_escuta.start()

        print("[CONTROLE] Digite uma mensagem para enviar e pressione Enter.")
        
        while True:
            mensagem_texto = input()
            if not mensagem_texto:
                continue

            # CRIA E ARMAZENA A NOVA MENSAGEM NO HISTÓRICO
            with historico_lock:
                nova_mensagem = {'id': proximo_id_mensagem, 'texto': mensagem_texto}
                historico_mensagens.append(nova_mensagem)
                proximo_id_mensagem += 1

            # ENVIA A MENSAGEM EM TEMPO REAL PARA OS CLIENTES JÁ CONECTADOS
            with clientes_lock:
                if not clientes_conectados:
                    print("[AVISO] Mensagem armazenada. Nenhum cliente conectado para receber em tempo real.")
                else:
                    print(f"[ENVIO] Enviando ID {nova_mensagem['id']} para {len(clientes_conectados)} dispositivo(s)...")
                    mensagem_formatada = f"{nova_mensagem['id']}:{nova_mensagem['texto']}"
                    clientes_a_enviar = list(clientes_conectados)

            for cliente_conn in clientes_a_enviar:
                try:
                    cliente_conn.sendall(mensagem_formatada.encode('utf-8'))
                except Exception:
                    pass

    except (KeyboardInterrupt, EOFError):
        print("\n[INFO] Desligando o servidor...")
    finally:
        servidor_socket.close()