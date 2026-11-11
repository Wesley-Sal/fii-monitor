"""Roda o monitor no seu computador, sem GitHub.

- Atualiza as cotações agora e depois a cada hora (seg-sex, 10h às 18h).
- Abre a página em http://localhost:8000 no navegador.

Uso:  python iniciar.py
Para parar: feche esta janela ou aperte Ctrl+C.
"""
import functools
import http.server
import os
import threading
import time
import webbrowser
from datetime import datetime

import monitor

PASTA = os.path.dirname(os.path.abspath(__file__))
PORTA = 8000
HORA_INICIO, HORA_FIM = 10, 18  # horário local do computador
SO_DIAS_UTEIS = True


def atualizar() -> None:
    os.chdir(PASTA)  # monitor.py grava data.json na pasta atual
    agora = datetime.now().strftime("%d/%m %H:%M")
    try:
        monitor.main()
        print(f"[{agora}] cotações atualizadas")
    except Exception as e:
        print(f"[{agora}] falha ao atualizar: {e}")


def dentro_do_horario(agora: datetime) -> bool:
    if SO_DIAS_UTEIS and agora.weekday() >= 5:
        return False
    return HORA_INICIO <= agora.hour <= HORA_FIM


def agendador() -> None:
    agora = datetime.now()
    ultima_hora = (agora.date(), agora.hour)  # main() já atualizou agora
    while True:
        agora = datetime.now()
        chave = (agora.date(), agora.hour)
        if dentro_do_horario(agora) and chave != ultima_hora:
            atualizar()
            ultima_hora = chave
        time.sleep(60)


class SemLog(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main() -> None:
    atualizar()  # primeira carga, a qualquer hora
    threading.Thread(target=agendador, daemon=True).start()

    handler = functools.partial(SemLog, directory=PASTA)
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), handler)
    url = f"http://localhost:{PORTA}"
    print(f"Monitor aberto em {url}  (Ctrl+C para parar)")
    webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")


if __name__ == "__main__":
    main()
