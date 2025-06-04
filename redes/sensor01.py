import socket
import sys

server_ip = input('Entre com o IP do servidor: ')
server_port = int(input('Entre com a porta do servidor: '))
sensor_id = input('Entre com o ID do sensor: ')

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# envia o ID do sensor para registrar no servidor
s.sendto(sensor_id.encode(), (server_ip, server_port))

print('Esperando atualizações do servidor...')

while True:
    try:
        data, addr = s.recvfrom(1024)
        print(f'Recebido do servidor: {data.decode()}')
    except KeyboardInterrupt:
        print('\nCliente encerrado pelo usuário')
        break
