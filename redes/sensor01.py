import socket
import sys
import struct
import threading
import time

# --- Constantes ---
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5007
BUFFER_SIZE = 1024  # Tamanho do buffer para receber dados

# --- Variáveis Globais ---
# Socket TCP para comunicação Unicast com o servidor
server_socket = None
# Socket UDP para receber mensagens Multicast
multicast_socket = None
# Flag para controlar o loop de envio de dados
running_send_loop = True

# --- Funções de Comunicação ---

def receive_multicast_firmware():
    """
    Recebe pacotes de firmware enviados via multicast.
    """
    global multicast_socket
    try:
        multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        multicast_socket.bind(('', MULTICAST_PORT))  # Escuta em todas as interfaces na porta multicast

        # Junta-se ao grupo multicast
        mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
        multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        print(f"\n[MULTICAST] Entrou no grupo multicast: {MULTICAST_GROUP}:{MULTICAST_PORT}")
        while True:
            data, addr = multicast_socket.recvfrom(BUFFER_SIZE)
            print(f"[MULTICAST RECEBIDO] De {addr[0]}:{addr[1]}: '{data.decode().strip()}'")
    except socket.error as e:
        print(f"[ERRO MULTICAST] Falha ao configurar o socket multicast ou receber dados: {e}")
    except Exception as e:
        print(f"[ERRO MULTICAST] Um erro inesperado ocorreu na recepção multicast: {e}")
    finally:
        if multicast_socket:
            multicast_socket.close()
            print("[MULTICAST] Socket multicast encerrado.")

def send_sensor_data(sensor_id):
    """
    Permite ao usuário digitar e enviar dados para o servidor.
    """
    global running_send_loop
    print(f"\n[CLIENTE] Pronto para enviar dados. Digite 'sair' para encerrar.")
    while running_send_loop:
        try:
            user_input = input("[VOCÊ] Digite o texto para enviar: ").strip()

            if user_input.lower() == 'sair':
                print("[CLIENTE] Comando 'sair' recebido. Encerrando envio de dados.")
                running_send_loop = False
                break
            
            if not user_input:
                print("[CLIENTE] Entrada vazia. Nada para enviar.")
                continue

            data_to_send = user_input.encode('utf-8')
            bytes_sent = server_socket.send(data_to_send)
            print(f"[CLIENTE ENVIADO] '{user_input}' ({bytes_sent} bytes)")

        except ConnectionResetError:
            print("[ERRO TCP] O servidor fechou a conexão abruptamente.")
            running_send_loop = False
            break
        except BrokenPipeError:
            print("[ERRO TCP] A conexão com o servidor foi quebrada.")
            running_send_loop = False
            break
        except Exception as e:
            print(f"[ERRO TCP] Um erro inesperado ocorreu durante o envio de dados: {e}")
            running_send_loop = False
            break
    
    print("[CLIENTE] Loop de envio de dados encerrado.")


# --- Função Principal ---
def main():
    """
    Função principal para configurar e executar o cliente sensor.
    """
    global server_socket, multicast_socket, running_send_loop

    server_ip = input('Entre com o IP do servidor: ')
    try:
        server_port = int(input('Entre com a porta do servidor: '))
    except ValueError:
        print("[ERRO] Porta inválida. Por favor, digite um número inteiro.")
        sys.exit(1)
    sensor_id = input('Entre com o ID do sensor: ').strip()

    print(f"\n--- Informações do Cliente Sensor ---")
    print(f"ID do Sensor: {sensor_id}")
    print(f"Servidor: {server_ip}:{server_port}")
    print(f"Grupo Multicast: {MULTICAST_GROUP}:{MULTICAST_PORT}")
    print(f"------------------------------------")

    # 1. Configurar Conexão TCP (Unicast) com o Servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print(f"[CLIENTE] Tentando conectar ao servidor em {server_ip}:{server_port}...")
        server_socket.connect((server_ip, server_port))
        print(f"[CLIENTE CONECTADO] Conectado com sucesso ao servidor.")
        
        # Envia o ID do sensor imediatamente após a conexão
        server_socket.send(sensor_id.encode('utf-8'))
        print(f"[CLIENTE] ID '{sensor_id}' enviado ao servidor.")

    except socket.error as e:
        print(f"[ERRO DE CONEXÃO] Não foi possível conectar ao servidor: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO INESPERADO] Ocorreu um erro ao conectar: {e}")
        sys.exit(1)

    # 2. Iniciar Thread para Receber Firmware Multicast
    multicast_thread = threading.Thread(target=receive_multicast_firmware)
    multicast_thread.daemon = True  # Permite que o programa principal saia mesmo que a thread esteja rodando
    multicast_thread.start()

    # 3. Iniciar Loop de Envio de Dados do Sensor (na thread principal)
    try:
        send_sensor_data(sensor_id) # Esta função contém o loop de input do usuário
    except KeyboardInterrupt:
        print("\n[CLIENTE] Interrupção por teclado (CTRL+C). Encerrando o cliente.")
        running_send_loop = False
    except Exception as e:
        print(f"[ERRO PRINCIPAL] Ocorreu um erro no loop principal do cliente: {e}")
        running_send_loop = False
    finally:
        # Limpeza de recursos
        if server_socket:
            print("[CLIENTE] Fechando socket TCP do servidor...")
            server_socket.close()
        if multicast_socket: # Embora a thread multicast tenha seu próprio finally, é bom garantir
            multicast_socket.close()
        print("[CLIENTE] Cliente encerrado com sucesso.")
        sys.exit(0) # Garante que o programa saia completamente

if __name__ == "__main__":
    main()