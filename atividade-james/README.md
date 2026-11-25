# Backend de análise de sentimentos

Aplicação web e API HTTP em Python 3.10+ para classificar textos em **positivo**, **neutro** ou **negativo**. Compara uma baseline clássica de PLN lexical com Gemini usando prompt few-shot e saída JSON estruturada. A interface e a API são servidas pelo mesmo processo, com a biblioteca padrão do Python.

A pasta `frontend/` fica ao lado de `atividade-james/`, dentro da pasta que contém os dois componentes. Preserve essa estrutura ao copiar o projeto.

## Executar

Execute o comando dentro de `atividade-james/`.

```powershell
python -m sentiment_backend.api
```

O servidor escuta em `127.0.0.1:8000` por padrão. Abra **http://127.0.0.1:8000/** no navegador, digite uma avaliação ou clique em **Usar exemplo**, escolha o método e clique em **Analisar**. A interface analisa um texto por vez. Para enviar um lote, use `POST /analisar` com `application/json` (até 256 KiB). A interface consulta `GET /saude` para habilitar a comparação com Gemini quando a chave está configurada.

Se a porta 8000 já estiver ocupada por uma execução anterior, encerre o processo antigo ou escolha outra porta antes de iniciar:

```powershell
$env:PORT = "8765"
python -m sentiment_backend.api
```

Nesse caso, abra **http://127.0.0.1:8765/**.

Para os modos `llm` e `comparar`, configure a chave do Gemini no ambiente antes de iniciar:

```powershell
$env:GEMINI_API_KEY = "sua-chave"
$env:GEMINI_MODEL = "gemini-3.8-flash"  # opcional
python -m sentiment_backend.api
```

Não grave a chave no código ou em arquivos versionados. Para usar só o método clássico, nenhuma chave ou conexão externa é necessária.

## Enviar JSON

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/analisar -Method Post `
  -ContentType 'application/json; charset=utf-8' `
  -InFile .\exemplos\avaliacoes.json
```

O exemplo usa `modo: "classico"` para funcionar sem chave. Troque para `"comparar"` quando configurar o Gemini. Estrutura:

```json
{
  "modo": "comparar",
  "mensagens": [
    {"id": "1", "produto": "Fone", "texto": "Som excelente", "referencia": "positivo"},
    {"id": "2", "produto": "Fone", "texto": "Chegou quebrado"}
  ]
}
```

- `modo`: `classico`, `llm` ou `comparar` (padrão).
- `mensagens`: 1 a 100 itens no modo clássico; 1 a 20 nos modos com LLM.
- `texto`: obrigatório, 1 a 5000 caracteres não vazios.
- `id`: opcional, único no lote; gerado pela posição quando ausente.
- `produto`: opcional, até 120 caracteres, devolvido no resultado.
- `referencia`: opcional; rótulo humano para calcular acurácia na amostra rotulada.

A resposta inclui resultados por texto, distribuição de sentimentos, percentual positivo (indicador simples de satisfação), resumo por produto quando `produto` é enviado, falhas do LLM, concordância entre métodos e acurácia apenas quando há referências humanas. Se uma chamada ao Gemini falhar, o item mantém o resultado clássico e registra o erro, sem substituir a saída do LLM silenciosamente.

## Testes

```powershell
python -m unittest discover -s testes -v
```

Os testes usam um LLM falso e verificam o manipulador HTTP sem abrir uma conexão de rede. **Não comprovam qualidade real do Gemini**: para isso é preciso uma chave válida, execução real e um conjunto de avaliações rotuladas independentemente.

## Limitações

A baseline usa léxico pequeno e regras simples de negação; pode errar ironia, gírias, contexto e sentimentos mistos. O percentual positivo não mede satisfação calibrada. O LLM pode falhar, custar por chamada e tratar dados conforme as políticas do provedor. A API liga apenas ao host local por padrão; antes de exposição pública, adicionar autenticação, controle de taxa, observabilidade e política de retenção de dados.
