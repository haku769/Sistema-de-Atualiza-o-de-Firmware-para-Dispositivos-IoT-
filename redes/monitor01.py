import socket
import sys
import threading

#--------------------------------------------------------------
# FUNÇÕES
def TrataSensor(conn, addr):
    while True:
        data = conn.recv(1000)
        print('sensor em ', addr, 'enviou ', data)

        if not data:
            break

    conn.close()
    print('sensor em', addr, 'encerrou')

#--------------------------------------------------------------
# PROGRAMA PRINCIPAL
HOST = ''               # ANY_IP = todos os IPs do HOST
SENSORES={}     # lista de sensores conectados
CONSOLE=None  # conexao com o console remoto

PORTA = int(input('Entre com a porta do servidor: '))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((HOST, PORTA))
except:
   print('# erro de bind')
   sys.exit()
hostname = socket.gethostname()
hostip = socket.gethostbyname(hostname)
print('host: {} ip: {}'.format(hostname, hostip))

s.listen(2)
print('aguardando conexoes em ', PORTA)

#--------------------------------------------------------------
# LOOP para tratar clientes

while True:
    conn, addr = s.accept()
    print('recebi uma conexao de ', addr)
    TrataSensor(conn, addr)
    # print('o cliente encerrou')
    conn.close()
#--------------------------------------------------------------

print('o servidor encerrou')
s.close()