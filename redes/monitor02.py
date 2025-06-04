import socket
import sys
import threading
import time

#--------------------------------------------------------------
def TrataSensores(s):
    while True:
        data, addr = s.recvfrom(1024)
        sensor_id = data.decode().strip()
        
        if sensor_id not in SENSORES:
            SENSORES[sensor_id] = addr
            print(f'sensor {sensor_id} registrado com endereço {addr}')
        else:
            print(f'sensor {sensor_id} enviou mensagem')

#--------------------------------------------------------------
def envia_atualizacoes(s):
    seq = 1
    while True:
        msg = f"ATUALIZAÇÃO {seq}"
        print(f'Enviando "{msg}" para {len(SENSORES)} sensores')
        for sensor_id, addr in SENSORES.items():
            try:
                s.sendto(msg.encode(), addr)
            except Exception as e:
                print(f'Erro ao enviar para {sensor_id} {addr}: {e}')
        seq += 1
        time.sleep(10)

#--------------------------------------------------------------
def envia_atualizacao_manual(s):
    while True:
        msg = input('Digite a atualização para enviar (ou "sair" para encerrar): ').strip()
        if msg.lower() == 'sair':
            print('Encerrando envio manual')
            break
        if msg:
            print(f'Enviando atualização manual: "{msg}" para {len(SENSORES)} sensores')
            for sensor_id, addr in SENSORES.items():
                try:
                    s.sendto(msg.encode(), addr)
                except Exception as e:
                    print(f'Erro ao enviar para {sensor_id} {addr}: {e}')

#--------------------------------------------------------------
# PROGRAMA PRINCIPAL

HOST = ''
SENSORES = {}

PORTA = int(input('Entre com a porta do servidor UDP: '))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    s.bind((HOST, PORTA))
except Exception as e:
    print('# erro de bind:', e)
    sys.exit()

hostname = socket.gethostname()
hostip = socket.gethostbyname(hostname)
print('host: {} ip: {}'.format(hostname, hostip))
print('Aguardando mensagens UDP na porta', PORTA)

t1 = threading.Thread(target=TrataSensores, args=(s,))
t1.daemon = True
t1.start()

t2 = threading.Thread(target=envia_atualizacoes, args=(s,))
t2.daemon = True
t2.start()

t3 = threading.Thread(target=envia_atualizacao_manual, args=(s,))
t3.daemon = True
t3.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('Servidor encerrado pelo usuário')
    s.close()
