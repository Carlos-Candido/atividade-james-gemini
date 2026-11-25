"""Baseline de PLN lexical, transparente e sem dependências externas."""

import re
import unicodedata

POSITIVAS = {
    # Satisfação e opinião
    "adoro", "adorei", "amei", "amar", "agradavel", "aprovado",
    "aprovada", "bom", "boa", "bons", "boas", "excelente",
    "fantastico", "fantastica", "feliz", "gostei", "gosto",
    "incrivel", "maravilhoso", "maravilhosa", "otimo", "otima",
    "perfeito", "perfeita", "satisfeito", "satisfeita",
    "satisfatorio", "satisfatoria", "surpreendente", "sensacional",
    "espetacular", "impressionante", "excepcional", "extraordinario",
    "superou", "surpreendeu", "encantado", "encantada",
    "impecavel", "admiravel", "esplendido", "magnifico",

    # Qualidade e durabilidade
    "qualidade", "resistente", "duravel", "robusto", "robusta",
    "reforcado", "reforcada", "confiavel", "original",
    "autentico", "autentica", "premium", "superior",
    "caprichado", "caprichada", "conservado", "conservada",
    "intacto", "intacta", "firme", "solido", "solida",

    # Funcionamento e desempenho
    "funciona", "funcionou", "funcionando", "funcional",
    "eficiente", "eficaz", "rapido", "rapida", "agil",
    "preciso", "precisa", "potente", "estavel",
    "silencioso", "silenciosa", "fluido", "fluida",
    "responsivo", "responsiva", "desempenho", "produtivo",

    # Usabilidade e conforto
    "pratico", "pratica", "facil", "simples", "intuitivo",
    "intuitiva", "confortavel", "macio", "macia",
    "ergonomico", "ergonomica", "ajustavel", "versatil",
    "util", "leve", "compacto", "compacta", "conveniente",

    # Aparência e acabamento
    "lindo", "linda", "bonito", "bonita", "elegante",
    "estiloso", "estilosa", "moderno", "moderna",
    "sofisticado", "sofisticada", "charmoso", "charmosa",

    # Preço e custo-benefício
    "barato", "barata", "acessivel", "economico", "economica",
    "vantajoso", "vantajosa", "compensa", "compensou",
    "vale", "justo", "justa",

    # Atendimento e entrega
    "atencioso", "atenciosa", "educado", "educada",
    "prestativo", "prestativa", "cordial", "gentil",
    "pontual", "cuidadoso", "cuidadosa", "honesto",
    "honesta", "competente", "profissional", "resolvido",
    "resolvida", "solucionado", "solucionada",

    # Recomendação
    "recomendo", "recomendado", "recomendada",
    "indicaria", "recompraria", "parabens",

    # Linguagem informal
    "top", "topzera", "show", "brabo", "braba",
    "massa", "bacana", "legal", "maneiro", "maneira",
    "otimismo", "perfeicao", "excelencia", "sensacional",
    "incriveis", "otimos", "otimas", "maravilha",
}

NEGATIVAS = {
    # Insatisfação e opinião
    "ruim", "horrivel", "pessimo", "pessima", "terrivel",
    "decepcao", "decepcionante", "decepcionado", "decepcionada",
    "insatisfeito", "insatisfeita", "insatisfatorio",
    "insatisfatoria", "arrependido", "arrependida",
    "arrependimento", "frustrante", "frustrado", "frustrada",
    "lamentavel", "ridiculo", "ridicula", "absurdo",
    "inaceitavel", "desagradavel", "irritante", "detestei",
    "odiei", "horroroso", "horrorosa", "mediocre",
    "desastroso", "desastrosa", "lastimavel",

    # Qualidade e durabilidade
    "defeito", "defeituoso", "defeituosa", "quebrado",
    "quebrada", "fragil", "fraco", "fraca", "falsificado",
    "falsificada", "falso", "falsa", "pirata",
    "danificado", "danificada", "arranhado", "arranhada",
    "amassado", "amassada", "rasgado", "rasgada",
    "desgastado", "desgastada", "enferrujado", "enferrujada",
    "descascando", "descolando", "desbotado", "desbotada",
    "vazando", "vazamento", "rachado", "rachada",
    "trincado", "trincada", "solto", "solta",
    "malfeito", "malfeita", "descartavel", "inferior",

    # Funcionamento e desempenho
    "erro", "falha", "falhou", "falhando", "problema",
    "problemas", "trava", "travou", "travando",
    "lento", "lenta", "lentidao", "bug", "bugado",
    "bugada", "instavel", "inutil", "ineficiente",
    "ineficaz", "inoperante", "incompativel",
    "impreciso", "imprecisa", "desliga", "desligando",
    "superaquece", "superaquecimento", "queimou",
    "parou", "estragou", "quebrou", "barulhento",
    "barulhenta", "ruidoso", "ruidosa", "desconecta",
    "descarregando", "descarregou",

    # Usabilidade e conforto
    "dificil", "complicado", "complicada", "desconfortavel",
    "incomodo", "incomoda", "apertado", "apertada",
    "pesado", "pesada", "confuso", "confusa",
    "desajeitado", "desajeitada", "impraticavel",
    "inutilizavel", "inadequado", "inadequada",

    # Aparência
    "feio", "feia", "horroroso", "horrorosa",
    "manchado", "manchada", "sujo", "suja",
    "deformado", "deformada", "desalinhado", "desalinhada",

    # Preço e custo-benefício
    "caro", "cara", "carissimo", "carissima",
    "abusivo", "abusiva", "prejuizo", "desperdicio",
    "superfaturado", "superfaturada", "injusto", "injusta",

    # Entrega e embalagem
    "atrasado", "atrasada", "atraso", "demora",
    "demorado", "demorada", "extraviado", "extraviada",
    "extravio", "violado", "violada", "incompleto",
    "incompleta", "faltando", "avariado", "avariada",
    "vencido", "vencida",

    # Atendimento e pós-venda
    "grosseiro", "grosseira", "arrogante", "descaso",
    "desrespeito", "desrespeitoso", "desrespeitosa",
    "incompetente", "desonesto", "desonesta",
    "enganoso", "enganosa", "enganado", "enganada",
    "fraude", "golpe", "mentira", "enganacao",
    "reembolso", "devolucao", "reclamacao",
    "cancelamento", "cancelado", "cancelada",
    "negligencia", "omissao", "abandono",

    # Linguagem informal
    "lixo", "porcaria", "merda", "bosta", "horrivel",
    "furada", "bomba", "porcariazinha", "tranqueira",
    "vagabundo", "vagabunda", "zoado", "zoada",
    "podre", "tosco", "tosca", "mequetrefe",
}

NEGACOES = {
    "nao", "nunca", "jamais", "nem", "sem",
    "nenhum", "nenhuma", "nada", "tampouco",
    "ninguem", "negativo",

    # Abreviações informais
    "n", "nn", "naum", "nunca",
}

INTENSIFICADORES = {
    "muito", "muita", "muitos", "muitas",
    "super", "extremamente", "bastante",
    "demais", "totalmente", "completamente",
    "absurdamente", "excessivamente", "altamente",
    "incrivelmente", "surpreendentemente",
    "imensamente", "realmente", "verdadeiramente",
    "especialmente", "profundamente",
    "consideravelmente", "particularmente",
    "exageradamente", "hiper", "mega", "ultra",
    "absolutamente", "extremo",

    # Abreviações informais
    "mt", "mto", "mta", "dms",
}


def normalizar(palavra: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", palavra.lower())
        if not unicodedata.combining(c)
    )


def analisar(texto: str) -> dict:
    """Pontua palavras de opinião, invertendo polaridade sob negação próxima."""
    pontuacao = 0.0
    evidencias = []
    # Pontuação delimita o alcance aproximado da negação.
    for trecho in re.split(r"[,.!?;:]", texto):
        tokens = [normalizar(t) for t in re.findall(r"[^\W_]+", trecho, re.UNICODE)]
        for indice, token in enumerate(tokens):
            polaridade = 1 if token in POSITIVAS else -1 if token in NEGATIVAS else 0
            if not polaridade:
                continue
            contexto = tokens[max(0, indice - 3):indice]
            # Cada negação troca o sinal. Isto é uma aproximação, não análise sintática.
            if sum(p in NEGACOES for p in contexto) % 2:
                polaridade *= -1
            peso = 1.5 if contexto and contexto[-1] in INTENSIFICADORES else 1.0
            pontuacao += polaridade * peso
            evidencias.append(token)
    sentimento = "positivo" if pontuacao > 0 else "negativo" if pontuacao < 0 else "neutro"
    return {
        "sentimento": sentimento,
        "pontuacao": round(pontuacao, 2),
        "evidencias": evidencias,
        "metodo": "lexico_com_negacao",
    }
