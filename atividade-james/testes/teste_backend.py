import io
import json
import unittest
from email.message import Message
from unittest.mock import patch

from sentiment_backend.api import Handler
from sentiment_backend.classico import analisar
from sentiment_backend.llm import ErroLLM, Gemini
from sentiment_backend.servico import EntradaInvalida, analisar_lote


class FalsoLLM:
    chave = "teste"

    def analisar(self, texto):
        if "falha" in texto:
            raise ErroLLM("falha simulada")
        return {"sentimento": "positivo", "justificativa": "teste", "modelo": "falso"}


class RespostaFalsa:
    def __init__(self, dados):
        self.dados = dados

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        return json.dumps(self.dados).encode("utf-8")


class BackendTestes(unittest.TestCase):
    def test_classico_negacao_e_misto(self):
        self.assertEqual(analisar("Não gostei, é ruim.")["sentimento"], "negativo")
        self.assertEqual(analisar("Não é ruim.")["sentimento"], "positivo")
        self.assertEqual(analisar("Bom, mas caro.")["sentimento"], "neutro")

    def test_validacao(self):
        with self.assertRaises(EntradaInvalida):
            analisar_lote({"modo": "classico", "mensagens": [{"texto": " "}]})
        with self.assertRaises(EntradaInvalida):
            analisar_lote({"modo": "classico", "mensagens": [{"id": "x", "texto": "bom"}, {"id": "x", "texto": "ruim"}]})
        with self.assertRaises(EntradaInvalida):
            analisar_lote({"modo": [], "mensagens": [{"texto": "bom"}]})
        with self.assertRaises(EntradaInvalida):
            analisar_lote({"modo": "classico", "mensagens": [{"texto": "bom", "referencia": []}]})

    def test_relatorio_comparativo_e_acuracia(self):
        resposta = analisar_lote({"modo": "comparar", "mensagens": [
            {"texto": "Produto excelente", "referencia": "positivo"},
            {"texto": "Produto ruim", "referencia": "negativo"},
            {"texto": "falha técnica", "referencia": "negativo"},
        ]}, FalsoLLM())
        self.assertEqual(resposta["resumo"]["comparacao"], {
            "pares_validos": 2, "concordancias": 1, "discordancias": 1, "taxa_concordancia": 0.5,
        })
        self.assertEqual(resposta["resumo"]["llm"]["falhas"], 1)
        self.assertEqual(resposta["resumo"]["classico"]["acuracia_referencias"], {"amostra": 3, "valor": 1.0})

    def test_satisfacao_por_produto(self):
        resposta = analisar_lote({"modo": "classico", "mensagens": [
            {"produto": "Fone", "texto": "Excelente"},
            {"produto": "Fone", "texto": "Ruim"},
            {"produto": "Mouse", "texto": "Bom"},
        ]})
        self.assertEqual(resposta["resumo"]["por_produto"]["Fone"]["classico"]["satisfacao_percentual"], 50.0)
        self.assertEqual(resposta["resumo"]["por_produto"]["Mouse"]["classico"]["satisfacao_percentual"], 100.0)

    def test_gemini_json_e_validacao(self):
        dados = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": '{"sentimento":"positivo","justificativa":"elogio"}'}]}}]}
        with patch("sentiment_backend.llm.request.urlopen", return_value=RespostaFalsa(dados)) as abrir:
            resultado = Gemini("chave-falsa", "gemini-teste").analisar("Muito bom")
            self.assertEqual(resultado["sentimento"], "positivo")
            requisicao = abrir.call_args.args[0]
            corpo = json.loads(requisicao.data)
            self.assertEqual(corpo["generationConfig"]["responseMimeType"], "application/json")
            self.assertIn("Exemplos few-shot", corpo["contents"][0]["parts"][0]["text"])
        dados["candidates"][0]["content"]["parts"][0]["text"] = '{"sentimento":"desconhecido","justificativa":"x"}'
        with patch("sentiment_backend.llm.request.urlopen", return_value=RespostaFalsa(dados)):
            with self.assertRaises(ErroLLM):
                Gemini("chave-falsa").analisar("texto")

    def test_http_json(self):
        def chamar(corpo):
            handler = Handler.__new__(Handler)
            handler.path = "/analisar"
            handler.headers = Message()
            handler.headers["Content-Type"] = "application/json"
            handler.headers["Content-Length"] = str(len(corpo))
            handler.rfile = io.BytesIO(corpo)
            handler.wfile = io.BytesIO()
            status = []
            handler.send_response = lambda codigo: status.append(codigo)
            handler.send_header = lambda *_: None
            handler.end_headers = lambda: None
            handler.do_POST()
            return status[0], json.loads(handler.wfile.getvalue())

        corpo = json.dumps({"modo": "classico", "mensagens": [{"texto": "Excelente!"}]}).encode()
        status, resposta = chamar(corpo)
        self.assertEqual(status, 200)
        self.assertEqual(resposta["resumo"]["classico"]["distribuicao"]["positivo"]["quantidade"], 1)
        status, _ = chamar(b"{}")
        self.assertEqual(status, 400)

    def test_recursos_do_frontend(self):
        recursos = {
            "/": ("text/html", 'id="analysis-form"', 'href="/styles.css"', 'src="/app.js"'),
            "/styles.css": ("text/css", ".skip-link"),
            "/app.js": ("text/javascript", 'fetch("/saude"', 'fetch("/analisar"'),
        }
        for caminho, (tipo, *trechos) in recursos.items():
            with self.subTest(caminho=caminho):
                handler = Handler.__new__(Handler)
                handler.path = caminho
                handler.wfile = io.BytesIO()
                status = []
                cabecalhos = {}
                handler.send_response = lambda codigo: status.append(codigo)
                handler.send_header = lambda nome, valor: cabecalhos.__setitem__(nome, valor)
                handler.end_headers = lambda: None
                handler.do_GET()
                corpo = handler.wfile.getvalue()
                self.assertEqual(status, [200])
                self.assertEqual(cabecalhos["Content-Type"], f"{tipo}; charset=utf-8")
                self.assertEqual(cabecalhos["Content-Length"], str(len(corpo)))
                self.assertEqual(cabecalhos["X-Content-Type-Options"], "nosniff")
                for trecho in trechos:
                    self.assertIn(trecho, corpo.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
