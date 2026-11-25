"""Validação, orquestração e métricas do lote."""

from collections import Counter

from . import classico
from .llm import ErroLLM, Gemini, ROTULOS


class EntradaInvalida(ValueError):
    pass


def validar(dados: object) -> tuple[list[dict], str]:
    if not isinstance(dados, dict):
        raise EntradaInvalida("O corpo deve ser um objeto JSON")
    modo = dados.get("modo", "comparar")
    if not isinstance(modo, str) or modo not in {"classico", "llm", "comparar"}:
        raise EntradaInvalida("modo deve ser classico, llm ou comparar")
    mensagens = dados.get("mensagens")
    limite = 100 if modo == "classico" else 20
    if not isinstance(mensagens, list) or not 1 <= len(mensagens) <= limite:
        raise EntradaInvalida(f"mensagens deve conter entre 1 e {limite} itens")
    ids = set()
    validadas = []
    for indice, item in enumerate(mensagens, 1):
        if not isinstance(item, dict):
            raise EntradaInvalida(f"mensagem {indice} deve ser um objeto")
        item = dict(item)
        item.setdefault("id", str(indice))
        if not isinstance(item["id"], str) or not 1 <= len(item["id"]) <= 80 or item["id"] in ids:
            raise EntradaInvalida(f"id inválido ou duplicado na mensagem {indice}")
        ids.add(item["id"])
        if not isinstance(item.get("texto"), str) or not item["texto"].strip() or len(item["texto"]) > 5000:
            raise EntradaInvalida(f"texto da mensagem {indice} deve ter entre 1 e 5000 caracteres")
        if "produto" in item and (not isinstance(item["produto"], str) or len(item["produto"]) > 120):
            raise EntradaInvalida(f"produto inválido na mensagem {indice}")
        if "referencia" in item and (not isinstance(item["referencia"], str) or item["referencia"] not in ROTULOS):
            raise EntradaInvalida(f"referencia inválida na mensagem {indice}")
        validadas.append(item)
    return validadas, modo


def _distribuicao(rotulos: list[str]) -> dict:
    contagem = Counter(rotulos)
    total = len(rotulos)
    return {
        nome: {"quantidade": contagem[nome], "percentual": round(100 * contagem[nome] / total, 2) if total else 0.0}
        for nome in ("positivo", "neutro", "negativo")
    }


def analisar_lote(dados: object, llm: Gemini | None = None) -> dict:
    mensagens, modo = validar(dados)
    if modo != "classico" and not (llm or Gemini()).chave:
        raise ErroLLM("GEMINI_API_KEY não configurada; use modo classico ou configure a chave")
    llm = llm or Gemini()
    resultados = []
    for item in mensagens:
        resultado = {"id": item["id"], "texto": item["texto"]}
        if "produto" in item:
            resultado["produto"] = item["produto"]
        if "referencia" in item:
            resultado["referencia"] = item["referencia"]
        if modo in {"classico", "comparar"}:
            resultado["classico"] = classico.analisar(item["texto"])
        if modo in {"llm", "comparar"}:
            try:
                resultado["llm"] = llm.analisar(item["texto"])
            except ErroLLM as exc:
                resultado["llm"] = {"erro": str(exc)}
        if modo == "comparar":
            resultado["concordam"] = (
                resultado["classico"]["sentimento"] == resultado["llm"].get("sentimento")
                if "sentimento" in resultado["llm"] else None
            )
        resultados.append(resultado)

    resumo = {"total": len(resultados)}
    for metodo in ("classico", "llm"):
        if modo in {metodo, "comparar"}:
            validos = [r[metodo]["sentimento"] for r in resultados if "sentimento" in r[metodo]]
            resumo[metodo] = {
                "analisados": len(validos),
                "falhas": len(resultados) - len(validos),
                "distribuicao": _distribuicao(validos),
                "satisfacao_percentual": round(100 * validos.count("positivo") / len(validos), 2) if validos else None,
            }
            rotulados = [r for r in resultados if "referencia" in r and "sentimento" in r[metodo]]
            if rotulados:
                resumo[metodo]["acuracia_referencias"] = {
                    "amostra": len(rotulados),
                    "valor": round(sum(r[metodo]["sentimento"] == r["referencia"] for r in rotulados) / len(rotulados), 4),
                }
    if modo == "comparar":
        comparaveis = [r for r in resultados if r["concordam"] is not None]
        resumo["comparacao"] = {
            "pares_validos": len(comparaveis),
            "concordancias": sum(r["concordam"] for r in comparaveis),
            "discordancias": sum(not r["concordam"] for r in comparaveis),
            "taxa_concordancia": round(sum(r["concordam"] for r in comparaveis) / len(comparaveis), 4) if comparaveis else None,
        }
    produtos = sorted({r["produto"] for r in resultados if r.get("produto")})
    if produtos:
        resumo["por_produto"] = {}
        for produto in produtos:
            itens = [r for r in resultados if r.get("produto") == produto]
            dados_produto = {"total": len(itens)}
            for metodo in ("classico", "llm"):
                if modo in {metodo, "comparar"}:
                    validos = [r[metodo]["sentimento"] for r in itens if "sentimento" in r[metodo]]
                    dados_produto[metodo] = {
                        "analisados": len(validos),
                        "distribuicao": _distribuicao(validos),
                        "satisfacao_percentual": round(100 * validos.count("positivo") / len(validos), 2) if validos else None,
                    }
            resumo["por_produto"][produto] = dados_produto
    return {"modo": modo, "resultados": resultados, "resumo": resumo}
