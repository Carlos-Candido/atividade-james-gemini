# Como executar o frontend

Requisito: Python 3.10 ou superior. O backend serve a interface da pasta `frontend/` no mesmo processo que atende a API.

## Iniciar a aplicação

Abra um terminal na pasta `atividade-james/` e execute:

```bash
python3 -m sentiment_backend.api
```

No Windows, use `python -m sentiment_backend.api` se o comando `python3` estiver indisponível.

Abra [http://127.0.0.1:8000/](http://127.0.0.1:8000/) no navegador. Clique em **Usar exemplo**, selecione **Clássico** e clique em **Analisar**. O exemplo deve retornar o sentimento **Positivo**. Para parar o servidor, pressione **Ctrl+C**.

## Habilitar a comparação com Gemini

No Bash, dentro de `atividade-james/`, informe a chave quando solicitado e inicie o servidor novamente.

```bash
read -rsp 'Chave do Gemini: ' GEMINI_API_KEY
printf '\n'
export GEMINI_API_KEY
python3 -m sentiment_backend.api
```

Recarregue a página e selecione **Comparar**.

## Rodar os testes

Em outro terminal, dentro de `atividade-james/`, execute:

```bash
python3 -m unittest discover -s testes -v
```
