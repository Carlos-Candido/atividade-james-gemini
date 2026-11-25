# Sistema de Análise de Sentimentos com LLM

**Relatório técnico do frontend**

## 1. Objetivo

A interface permite analisar uma avaliação por vez em português. O usuário pode digitar um texto ou preencher o campo com **Usar exemplo**, escolher o método e clicar em **Analisar**. No modo clássico, a interface mostra o sentimento identificado, a pontuação e as evidências lexicais. No modo de comparação, mostra as duas classificações, a justificativa do Gemini e se os métodos concordam.

## 2. Implementação

| Arquivo | Função |
| --- | --- |
| `index.html` | Estrutura do formulário, seleção do método, área de resultados e mensagens de estado. |
| `styles.css` | Layout responsivo, estados dos controles e apresentação dos resultados. |
| `app.js` | Contagem e validação do texto, chamadas à API e exibição dos resultados. |

O JavaScript valida textos vazios e o limite de 5.000 caracteres. O estado da análise é anunciado por uma região com `aria-live`. Os controles do formulário ficam desabilitados durante o envio para evitar submissões duplicadas.

## 3. Integração com o backend

A pasta `frontend/` fica ao lado de `atividade-james/`. O backend Python serve o HTML em `/` e entrega o CSS e o JavaScript na mesma origem da API.

| Rota | Uso na interface |
| --- | --- |
| `GET /saude` | Consulta `llm_configurado` para decidir se a comparação pode ser selecionada. |
| `POST /analisar` | Envia o modo selecionado e uma mensagem com o texto da avaliação em JSON. |

O método clássico funciona sem chave. A comparação usa a variável `GEMINI_API_KEY` no processo do backend. Quando o Gemini falha durante a comparação, a interface exibe o resultado clássico e os detalhes da falha.

## 4. Execução local

Execute a partir da pasta `frontend/`.

```bash
cd ../atividade-james
python3 -m sentiment_backend.api
```

Abra `http://127.0.0.1:8000/`, clique em **Usar exemplo** e execute a análise no modo **Clássico**.

## 5. Verificação

A suíte do backend passou nos sete testes, incluindo a entrega do HTML, do CSS e do JavaScript. O comando `node --check app.js` confirmou a sintaxe do JavaScript.

O teste complementar executou o JavaScript com um DOM simulado e encaminhou as requisições ao manipulador HTTP do backend em memória. Foram verificados três cenários.

| Cenário | Resultado observado |
| --- | --- |
| Análise sem chave | A comparação ficou desabilitada e a análise clássica exibiu o sentimento positivo. |
| Comparação com Gemini simulado | A interface exibiu a concordância e a justificativa. |
| Falha simulada do Gemini | A interface manteve o resultado clássico e exibiu os detalhes da falha. |

A verificação no navegador ficou pendente porque o ambiente bloqueou a abertura da porta local. A chamada ao Gemini foi simulada.
