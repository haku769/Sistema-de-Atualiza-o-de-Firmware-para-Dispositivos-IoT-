import socket
import sys
import threading
import time

# --- Constantes ---
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5007
UNICAST_PORT_PROMPT = 'Por favor, digite a porta do servidor: '
BUFFER_SIZE = 1024  # Tamanho do buffer aumentado para recebimento de dados

# --- Variáveis Globais ---
CONNECTED_SENSORS = {}  # Armazena as conexões dos sensores: {id_sensor: objeto_socket}
multicast_socket = None


# --- Função Multicast ---
def send_firmware_updates():
    """
    Envia mensagens simuladas de atualização de firmware para um grupo multicast.
    """
    global multicast_socket
    try:
        multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Define o Time-to-Live (TTL) para pacotes multicast como 1,
        # limitando-os ao segmento de rede local.
        multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)

        packet_number = 1
        print(f"\n--- Iniciando Multicast de Atualização de Firmware (Grupo: {MULTICAST_GROUP}, Porta: {MULTICAST_PORT}) ---")
        while True:
            message = f"Pacote de Atualização de Firmware: {packet_number}"
            multicast_socket.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
            print(f"[MULTICAST] Enviado: '{message}'")
            time.sleep(2)  # Simula um atraso entre os pacotes
            packet_number += 1
    except Exception as e:
        print(f"[ERRO] Erro no envio multicast: {e}")
    finally:
        if multicast_socket:
            multicast_socket.close()


# --- Função de Tratamento de Sensor ---
def handle_sensor_connection(connection, address):
    """
    Lida com a comunicação com um cliente sensor conectado.
    Cada conexão de sensor é executada em sua própria thread.
    """
    print(f"\n--- Nova Conexão de Sensor de {address[0]}:{address[1]} ---")
    sensor_id = None
    try:
        # Espera-se que o sensor envie seu ID ao se conectar
        sensor_id = connection.recv(10).decode().strip()
        CONNECTED_SENSORS[sensor_id] = connection
        print(f"[SENSOR CONECTADO] Sensor '{sensor_id}' registrado de {connection.getpeername()}")

        while True:
            data = connection.recv(BUFFER_SIZE).decode().strip()
            if not data:
                print(f"[SENSOR DESCONECTADO] Sensor '{sensor_id}' em {connection.getpeername()} desconectou.")
                break
            print(f"[DADOS DO SENSOR] Sensor '{sensor_id}' enviou: '{data}'")

    except ConnectionResetError:
        print(f"[SENSOR DESCONECTADO] Sensor '{sensor_id}' em {address} fechou a conexão abruptamente.")
    except Exception as e:
        print(f"[ERRO] Erro ao lidar com o sensor {sensor_id if sensor_id else address}: {e}")
    finally:
        if sensor_id in CONNECTED_SENSORS:
            del CONNECTED_SENSORS[sensor_id]
        connection.close()
        print(f"--- Conexão com {address[0]}:{address[1]} encerrada ---")


# --- Programa Principal ---
def main():
    """
    Função principal para configurar e executar o servidor.
    """
    host = ''  # Escuta em todas as interfaces disponíveis
    server_port = 0

    try:
        server_port = int(input(UNICAST_PORT_PROMPT))
    except ValueError:
        print("[ERRO] Número de porta inválido. Por favor, digite um número inteiro.")
        sys.exit(1)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permite reutilizar o endereço

    try:
        server_socket.bind((host, server_port))
    except socket.error as e:
        print(f"[ERRO] Falha ao vincular (bind): {e}")
        sys.exit(1)

    hostname = socket.gethostname()
    host_ip = socket.gethostbyname(hostname)
    print(f"\n--- Informações do Servidor ---")
    print(f"Nome do Host: {hostname}")
    print(f"Endereço IP: {host_ip}")
    print(f"Escutando na porta: {server_port}")
    print(f"------------------------------")

    server_socket.listen(5)  # Escuta por até 5 conexões pendentes
    print("Aguardando conexões de entrada...")

    clients_connected_count = 0
    multicast_thread_started = False

    try:
        while True:
            connection, address = server_socket.accept()
            clients_connected_count += 1
            print(f"\n[SERVIDOR] Conexão aceita de: {address[0]}:{address[1]} (Total de conexões: {clients_connected_count})")

            # Cria uma nova thread para lidar com a conexão do sensor
            sensor_thread = threading.Thread(target=handle_sensor_connection, args=(connection, address,))
            sensor_thread.daemon = True  # Permite que o programa principal saia mesmo que as threads estejam em execução
            sensor_thread.start()

            # Inicia o multicast apenas após o primeiro cliente se conectar (ou ajuste conforme necessário)
            if clients_connected_count == 1 and not multicast_thread_started:
                multicast_thread = threading.Thread(target=send_firmware_updates)
                multicast_thread.daemon = True
                multicast_thread.start()
                multicast_thread_started = True

    except KeyboardInterrupt:
        print("\n[SERVIDOR] O servidor está sendo encerrado...")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado no loop principal: {e}")
    finally:
        for sensor_id, conn in list(CONNECTED_SENSORS.items()): # Usa list() para iterar sobre uma cópia
            try:
                conn.close()
                print(f"Conexão encerrada para o sensor: {sensor_id}")
            except Exception as e:
                print(f"Erro ao encerrar a conexão para o sensor {sensor_id}: {e}")
        if multicast_socket:
            multicast_socket.close()
        server_socket.close()
        print("[SERVIDOR] Servidor parado com sucesso.")

if __name__ == "__main__":
    main()