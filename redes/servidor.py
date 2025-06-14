# servidor.py (VERSÃO COMENTADA)

# -----------------------------------------------------------------------------
# 1. IMPORTAÇÃO DAS BIBLIOTECAS
# -----------------------------------------------------------------------------
# 'socket' é a biblioteca principal para comunicação de rede (criar servidores, clientes, etc.).
import socket
# 'sys' permite interagir com o sistema, neste caso, para encerrar o programa com sys.exit().
import sys
# 'threading' é a biblioteca que nos permite executar múltiplas tarefas ao mesmo tempo (multithreading).
# Essencial para que o servidor possa aceitar novos clientes enquanto lida com os já conectados.
import threading

# -----------------------------------------------------------------------------
# 2. DECLARAÇÃO DAS VARIÁVEIS GLOBAIS
# -----------------------------------------------------------------------------
# Variáveis globais são acessíveis por todas as funções do programa.

# Esta lista vazia vai armazenar os objetos de conexão de cada cliente que se conectar.
# É o nosso "catálogo" de clientes ativos.
clientes_conectados = []

# O 'Lock' (ou "trava") é um mecanismo de segurança. Como várias threads (tarefas)
# podem tentar adicionar ou remover clientes da lista 'clientes_conectados' ao mesmo tempo,
# o Lock garante que apenas uma thread possa modificar a lista por vez, evitando erros e corrupção de dados.
clientes_lock = threading.Lock()

# O 'Event' é um dos mecanismos de sincronização mais simples. Funciona como um sinalizador
# ou um portão de largada. Ele pode estar em dois estados: "esperando" ou "liberado".
# Vamos usá-lo para fazer o programa principal esperar até que o número certo de clientes se conecte.
evento_pronto_para_iniciar = threading.Event()


# -----------------------------------------------------------------------------
# 3. FUNÇÃO PARA GERENCIAR CADA CLIENTE INDIVIDUALMENTE
# -----------------------------------------------------------------------------
# Esta função será executada em uma thread separada para CADA cliente que se conectar.
def lidar_com_cliente(conn, addr, num_necessarios):
    # 'conn' é o objeto de conexão com o cliente (por onde enviamos/recebemos dados).
    # 'addr' contém o endereço IP e a porta do cliente.
    # 'num_necessarios' é o número de clientes que esperamos.
    print(f"[NOVO CLIENTE] Dispositivo conectado em: {addr}")
    
    # O bloco 'with clientes_lock:' adquire a trava antes de executar o código dentro dele
    # e a libera automaticamente no final. Isso garante exclusividade na manipulação da lista.
    with clientes_lock:
        # Adiciona o objeto de conexão do novo cliente à nossa lista global.
        clientes_conectados.append(conn)
        # Pega o número atual de clientes na lista.
        num_atual = len(clientes_conectados)
        # Exibe um status para o administrador do servidor.
        print(f"[STATUS] Clientes conectados: {num_atual}/{num_necessarios}")
        
        # Esta é a verificação principal da nossa lógica de espera.
        # Se o número atual de clientes for igual ao número que precisamos...
        # E (and) o nosso "sinalizador" de evento ainda não tiver sido disparado...
        if num_atual == num_necessarios and not evento_pronto_para_iniciar.is_set():
            # Imprime uma mensagem clara de que a condição foi atingida.
            print("\n" + "="*40)
            print("[CONDIÇÃO ATINGIDA] Número necessário de clientes conectado!")
            print("[MODO DE TRANSMISSÃO ATIVADO]")
            print("="*40 + "\n")
            # Dispara o sinal! Qualquer thread que estava esperando por este evento (`.wait()`)
            # será agora liberada para continuar sua execução.
            evento_pronto_para_iniciar.set()

    # O bloco 'try...finally' é usado para garantir que a limpeza seja feita.
    try:
        # Este loop infinito serve para manter a conexão com o cliente viva.
        # A linha conn.recv(1024) é bloqueante: ela pausa a execução desta thread
        # até que o cliente envie algum dado ou a conexão seja fechada.
        while True:
            data = conn.recv(1024)
            # Se 'recv' retornar vazio (not data), significa que o cliente desconectou.
            if not data:
                # Quebramos o loop para encerrar a função e a thread.
                break 
    finally:
        # O bloco 'finally' SEMPRE é executado, não importa como o 'try' terminou
        # (seja por um 'break' ou por um erro).
        print(f"[CLIENTE DESCONECTADO] Dispositivo em {addr} encerrou.")
        # Novamente, usamos a trava para remover o cliente da lista com segurança.
        with clientes_lock:
            if conn in clientes_conectados:
                clientes_conectados.remove(conn)
        # Fecha a conexão com este cliente para liberar os recursos de rede.
        conn.close()


# -----------------------------------------------------------------------------
# 4. FUNÇÃO PARA ACEITAR NOVAS CONEXÕES
# -----------------------------------------------------------------------------
# Esta função também roda em sua própria thread. Seu único trabalho é esperar por
# novas conexões e iniciar uma nova thread 'lidar_com_cliente' para cada uma.
def iniciar_escuta_de_clientes(servidor_socket, num_necessarios):
    try:
        # Loop infinito para aceitar conexões continuamente.
        while True:
            # A linha .accept() é bloqueante. Ela pausa esta thread até que um
            # novo cliente tente se conectar. Quando isso acontece, ela retorna
            # o objeto de conexão ('conn') e o endereço ('addr') do cliente.
            conn, addr = servidor_socket.accept()
            
            # Cria uma nova thread. O alvo ('target') é a nossa função que gerencia
            # clientes, e os argumentos ('args') são os dados que essa função precisa.
            thread_cliente = threading.Thread(target=lidar_com_cliente, args=(conn, addr, num_necessarios))
            # Inicia a execução da nova thread. O programa agora continua a executar
            # o loop para aceitar o próximo cliente, enquanto a nova thread começa
            # a lidar com o cliente que acabou de se conectar.
            thread_cliente.start()
    except OSError:
        # Este erro pode ocorrer se fecharmos o servidor_socket enquanto .accept()
        # está esperando. Apenas ignoramos para um desligamento limpo.
        pass


# -----------------------------------------------------------------------------
# 5. BLOCO DE EXECUÇÃO PRINCIPAL
# -----------------------------------------------------------------------------
# O código dentro deste 'if' só é executado quando o arquivo é rodado diretamente
# (e não quando é importado por outro arquivo).
if __name__ == "__main__":
    HOST = ''  # String vazia significa que o servidor vai escutar em todas as interfaces de rede disponíveis.
    PORTA = 65432  # Uma porta não privilegiada para a conexão.

    # -- Parte 1: Pergunta ao usuário e configura o ambiente --
    try:
        # Pede ao administrador para definir a condição de início.
        num_clientes_necessarios = int(input("Quantos clientes precisam se conectar para iniciar as atualizações? "))
        # Validação simples para garantir que o número seja positivo.
        if num_clientes_necessarios <= 0:
            print("O número deve ser maior que zero.")
            sys.exit() # Encerra o programa.
    except ValueError:
        # Se o usuário digitar algo que não é um número.
        print("Entrada inválida. Por favor, digite um número.")
        sys.exit()

    # -- Parte 2: Configuração do Socket do Servidor --
    # Cria o objeto de socket principal. AF_INET para IPv4, SOCK_STREAM para TCP.
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Esta opção permite que o programa reutilize um endereço de porta imediatamente
    # após ser fechado, evitando o erro "Address already in use".
    servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Associa (bind) o socket ao endereço (HOST) e à porta (PORTA).
        servidor_socket.bind((HOST, PORTA))
        # Coloca o socket em modo de escuta, pronto para aceitar até 10 conexões na fila.
        servidor_socket.listen(10)
        
        # Pega o nome e o IP da máquina local para exibir uma mensagem informativa.
        hostname = socket.gethostname()
        host_ip = socket.gethostbyname(hostname)
        print(f"\n[INFO] Servidor iniciado!")
        print(f"[INFO] Escutando em {host_ip}:{PORTA}")

        # -- Parte 3: Início das Threads e Sincronização --
        # Cria a thread que vai ficar escutando por novos clientes.
        # Passamos os argumentos que a função 'iniciar_escuta_de_clientes' precisa.
        # 'daemon=True' significa que esta thread será encerrada automaticamente se o programa principal fechar.
        thread_escuta = threading.Thread(
            target=iniciar_escuta_de_clientes, 
            args=(servidor_socket, num_clientes_necessarios), 
            daemon=True
        )
        thread_escuta.start() # Inicia a thread de escuta.

        # ESTA É A PARTE CRÍTICA DA SINCRONIZAÇÃO:
        print(f"\n[AGUARDANDO] Servidor esperando por {num_clientes_necessarios} cliente(s) para liberar a transmissão...")
        # A execução do programa principal PAUSA nesta linha. Ele só continuará
        # quando a outra thread (lidar_com_cliente) chamar `evento_pronto_para_iniciar.set()`.
        evento_pronto_para_iniciar.wait()

        # -- Parte 4: Loop de Transmissão (após ser liberado) --
        print("[CONTROLE] Digite uma mensagem para enviar a todos e pressione Enter.")
        # Loop infinito para que o administrador possa enviar múltiplas mensagens.
        while True:
            mensagem = input()
            # Se o administrador pressionar Enter sem digitar nada, apenas continua o loop.
            if not mensagem:
                continue

            # Usa a trava para acessar a lista de clientes com segurança.
            with clientes_lock:
                # Se não houver clientes (todos podem ter desconectado), avisa.
                if not clientes_conectados:
                    print("[AVISO] Nenhuma dispositivo conectado para receber a atualização.")
                    continue
                
                print(f"[ENVIO] Enviando '{mensagem}' para {len(clientes_conectados)} dispositivo(s)...")
                # Cria uma cópia da lista. Isso é uma boa prática para evitar problemas
                # se um cliente desconectar e a lista for modificada enquanto estamos no meio do loop 'for'.
                clientes_a_enviar = list(clientes_conectados)

            # Itera sobre a cópia da lista para enviar a mensagem.
            for cliente_conn in clientes_a_enviar:
                try:
                    # Envia a mensagem. `.encode('utf-8')` converte a string para bytes.
                    cliente_conn.sendall(mensagem.encode('utf-8'))
                except Exception:
                    # Se houver um erro ao enviar (ex: cliente desconectou bruscamente),
                    # apenas ignoramos. A função 'lidar_com_cliente' já trata da remoção da lista.
                    pass

    # -- Parte 5: Tratamento de Encerramento --
    # Este bloco captura o comando Ctrl+C no terminal para um desligamento gracioso.
    except (KeyboardInterrupt, EOFError):
        print("\n[INFO] Desligando o servidor...")
    # Captura outros possíveis erros de rede.
    except OSError as e:
        print(f"[ERRO] Falha crítica no servidor: {e}")
    finally:
        # O bloco 'finally' garante que o socket principal seja fechado, liberando a porta.
        servidor_socket.close()