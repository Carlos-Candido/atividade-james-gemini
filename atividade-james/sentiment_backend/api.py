"""Servidor HTTP local da interface web e da API de sentimentos."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .llm import ErroLLM
from .servico import EntradaInvalida, analisar_lote

TAMANHO_MAXIMO = 256 * 1024
DIRETORIO_FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
RECURSOS_FRONTEND = {
    "/": ("index.html", "text/html"),
    "/styles.css": ("styles.css", "text/css"),
    "/app.js": ("app.js", "text/javascript"),
}
POLITICA_CSP = (
    "default-src 'self'; object-src 'none'; base-uri 'none'; "
    "frame-ancestors 'none'; form-action 'self'"
)


class Handler(BaseHTTPRequestHandler):
    def responder(self, status: int, dados: dict) -> None:
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self) -> None:
        recurso = RECURSOS_FRONTEND.get(self.path)
        if recurso is not None:
            nome, tipo = recurso
            try:
                corpo = (DIRETORIO_FRONTEND / nome).read_bytes()
            except OSError:
                self.responder(500, {"erro": "Não foi possível carregar o recurso"})
                return
            self.send_response(200)
            self.send_header("Content-Type", f"{tipo}; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", POLITICA_CSP)
            self.end_headers()
            self.wfile.write(corpo)
        elif self.path == "/saude":
            self.responder(200, {"status": "ok", "llm_configurado": bool(os.getenv("GEMINI_API_KEY"))})
        else:
            self.responder(404, {"erro": "Rota não encontrada"})

    def do_POST(self) -> None:
        if self.path != "/analisar":
            self.responder(404, {"erro": "Rota não encontrada"})
            return
        if self.headers.get_content_type() != "application/json":
            self.responder(415, {"erro": "Use Content-Type: application/json"})
            return
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            if not 0 < tamanho <= TAMANHO_MAXIMO:
                raise EntradaInvalida(f"Corpo deve ter entre 1 e {TAMANHO_MAXIMO} bytes")
            entrada = json.loads(self.rfile.read(tamanho).decode("utf-8"))
            self.responder(200, analisar_lote(entrada))
        except (ValueError, UnicodeDecodeError, EntradaInvalida) as exc:
            self.responder(400, {"erro": str(exc)})
        except ErroLLM as exc:
            self.responder(503, {"erro": str(exc)})


def iniciar() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    porta = int(os.getenv("PORT", "8000"))
    servidor = ThreadingHTTPServer((host, porta), Handler)
    print(f"Interface disponível em http://{host}:{servidor.server_port}/", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    iniciar()
