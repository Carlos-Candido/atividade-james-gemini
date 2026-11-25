# Sistema de Análise de Sentimentos com LLM

**Relatório técnico da etapa de backend**

**Instituição, curso, disciplina, professor e integrantes:** a preencher pela equipe

**Data:** 23 de novembro de 2026

**Escopo:** API e processamento em Python, com página local de teste; frontend completo e apresentação pertencem a etapas futuras.

## Resumo

Foi desenvolvido um backend para receber avaliações, comentários e outras mensagens em JSON e classificá-las como positivas, neutras ou negativas. O serviço oferece uma baseline clássica de processamento de linguagem natural por léxico e regras de negação, além de integração com o modelo Gemini para classificação por LLM. O prompt inclui exemplos few-shot e pede resposta em JSON estruturado. Nos modos com ambos os métodos, a resposta mostra concordâncias e divergências por mensagem. O resumo apresenta distribuição, percentual positivo e satisfação por produto; com rótulos de referência, calcula acurácia sobre a amostra. Uma página local permite testar a API no navegador. A implementação usa apenas a biblioteca padrão do Python em execução. Sete testes automatizados passaram; a execução real do Gemini não foi aferida por falta de chave de API neste ambiente.

<!-- pagebreak -->

## 1. Introdução e problema

Comentários de clientes em comércio eletrônico têm valor para identificar defeitos, elogios e problemas de atendimento. Ler manualmente grandes volumes é lento e dificulta acompanhar a satisfação. O projeto transforma um lote de mensagens em rótulos e estatísticas que possam ser consumidos por outra aplicação ou por uma equipe de análise.

O tema escolhido é o Tema 2 do guia do projeto: análise de sentimentos com LLM e comparação com abordagens clássicas de PLN. O guia pede ao menos uma técnica de PLN, integração com modelo de linguagem, engenharia de prompts, código funcional e documentação. Esses pontos são materializados no backend. A pedido do usuário, foi acrescentada uma página local de teste; a interface completa continua para outra etapa.

O público inicial é uma equipe que queira avaliar reviews de produtos. Um cliente HTTP pode enviar `mensagens` com texto, identificador, produto e um rótulo humano opcional. O serviço devolve os resultados individuais e um resumo. A comparação por lote ajuda a localizar casos em que a abordagem lexical e o LLM divergem, como ironia, ambiguidade ou linguagem fora do léxico.

O sistema não toma decisões automáticas sobre pessoas. Os números representam classificação de textos enviados no lote, e não uma pesquisa de satisfação representativa de toda a base de clientes.

<!-- pagebreak -->

## 2. Metodologia e ferramentas

O backend foi escrito para Python 3.10 ou superior com módulos da biblioteca padrão: `http.server` para HTTP, `json` para entrada e saída, `urllib` para a chamada REST ao Gemini, `re` e `unicodedata` para tokenização e normalização, e `unittest` para testes. Não há serviço de banco de dados nem dependência de instalação para executar o servidor.

O processamento tem quatro etapas. Primeiro, valida-se a estrutura JSON, o modo, o número de mensagens, os IDs e os tamanhos dos textos. Segundo, o método lexical pontua tokens positivos e negativos. Terceiro, quando solicitado, o texto é encaminhado ao Gemini com um prompt que delimita o conteúdo do cliente como dado. Por fim, o serviço combina as classificações e calcula distribuição, satisfação por produto, taxa de concordância e acurácia para referências fornecidas.

Foram definidos três modos: `classico`, que funciona offline; `llm`, que usa apenas Gemini; e `comparar`, que usa ambos. O último é o padrão e exige a variável de ambiente `GEMINI_API_KEY`. O nome do modelo pode ser alterado por `GEMINI_MODEL`. A chave é enviada no cabeçalho HTTP ao provedor e não é gravada no projeto.

O limite é de 100 textos no modo clássico e 20 nos modos que fazem chamadas ao LLM; cada texto pode ter até 5.000 caracteres e o corpo HTTP até 256 KiB. Esses limites evitam requisições excessivas e tornam mais previsível o custo de demonstração.

<!-- pagebreak -->

## 3. Arquitetura da solução

O ponto de entrada é `sentiment_backend/api.py`. Ele oferece `GET /` para a página de teste, `GET /saude` e `POST /analisar`, responde em UTF-8 e usa códigos HTTP para sucesso, erro de entrada e ausência de configuração do LLM. A página em `pagina.html` envia o mesmo JSON da API e mostra resumo, classificações e resposta completa. A lógica de negócio está em `servico.py`; a baseline lexical está em `classico.py`; a integração REST e o prompt estão em `llm.py`. Um arquivo JSON de exemplo e testes automatizados acompanham o código.

Fluxo de dados: cliente HTTP → validação JSON → classificador clássico e/ou Gemini → consolidação por mensagem → resumo estatístico → resposta JSON. Não há persistência: o lote existe apenas durante a requisição. A API liga por padrão em `127.0.0.1:8000`, portanto é adequada para desenvolvimento local.

O contrato de entrada aceita `modo` e `mensagens`. Cada item contém `texto` obrigatório, além de `id`, `produto` e `referencia` opcionais. `referencia` deve ser `positivo`, `neutro` ou `negativo` e representa um rótulo humano externo, não uma previsão. IDs ausentes são gerados pela posição no lote. IDs duplicados e textos vazios são rejeitados.

Na resposta, cada item contém a análise por método. Em `comparar`, `concordam` é verdadeiro ou falso quando ambos produziram rótulo; torna-se nulo se o LLM falhar. O resumo informa o número de análises válidas e falhas, além da distribuição e satisfação agrupadas por produto quando esse campo é enviado. Assim, um erro externo não aparece como sentimento neutro nem altera silenciosamente os percentuais.

<!-- pagebreak -->

## 4. Técnicas de PLN e LLM

A baseline clássica usa um léxico pequeno de termos de opinião em português. O texto é separado em tokens Unicode; acentos são normalizados para facilitar correspondência. Cada palavra positiva soma um ponto e cada negativa subtrai um ponto. Intensificadores imediatamente anteriores elevam o peso para 1,5. Negação dentro das três palavras anteriores inverte o sinal. Pontuação delimita o alcance dessa regra. Soma positiva, negativa ou zero determina o rótulo.

Essa baseline foi escolhida por ser explicável, rápida e funcionar sem rede. O campo `evidencias` mostra quais palavras foram reconhecidas e `pontuacao` mostra o saldo. Ela não foi treinada em um corpus e não deve ser confundida com um modelo supervisionado de alta acurácia.

O caminho LLM chama o endpoint REST `generateContent` do Gemini. O prompt define os três rótulos, orienta a interpretação de opiniões mistas e fornece três exemplos few-shot: elogio, reclamação e relato neutro. O texto do cliente é delimitado por tags e instruções internas a esse texto devem ser ignoradas. A configuração solicita `application/json` com esquema de saída contendo `sentimento` e `justificativa`.

Após receber a resposta, o backend verifica término normal, parse JSON, rótulo pertencente ao conjunto permitido e justificativa textual. Uma resposta inválida gera erro associado ao item. O campo `justificativa` é limitado a 500 caracteres. Nenhuma confiança probabilística é anunciada, pois o modelo não fornece uma probabilidade calibrada para esse contrato.

<!-- pagebreak -->

## 5. Resultados e verificação

O exemplo em `exemplos/avaliacoes.json` contém quatro reviews fictícias com referências: elogio, reclamação, relato factual e opinião mista. No modo clássico, o backend retornou uma avaliação positiva, duas neutras e uma negativa. A parcela positiva foi 25%. A acurácia sobre as quatro referências do próprio exemplo foi 1,0. Esse valor só comprova que o fluxo e as regras acertaram os casos demonstrativos; não permite estimar desempenho em dados reais.

Os sete testes automatizados passaram. Eles cobrem negação e opinião mista no classificador clássico; validação de textos vazios e IDs repetidos; resumo de concordância, falhas e acurácia; satisfação por produto; formato do pedido Gemini e rejeição de rótulo inválido; respostas JSON do manipulador HTTP; e entrega da página HTML. A chamada ao provedor é simulada nos testes, sem custo e sem chave externa.

Para reproduzir: executar `python -m unittest discover -s testes -v`. Para testar visualmente: iniciar `python -m sentiment_backend.api` e abrir `http://127.0.0.1:8000/` no navegador. Também é possível enviar o JSON do exemplo diretamente para `POST /analisar`, conforme `README.md`. O modo `classico` funciona sem configuração. Para uma comparação real, definir `GEMINI_API_KEY` e usar `modo: "comparar"`.

Não foi realizada inferência real com Gemini neste ambiente, pois não havia uma chave do usuário disponível. Portanto, não há resultado observado de concordância entre os dois métodos nem comparação quantitativa de qualidade em um corpus independente.

<!-- pagebreak -->

## 6. Limitações e cuidados

O léxico é pequeno e pode ignorar sinônimos, gírias, erros de digitação, nomes de produto, sarcasmo e nuances de contexto. A regra de negação é aproximada e pode falhar em construções longas. Textos mistos recebem rótulo neutro quando os sinais se anulam, mesmo que o comentário contenha elogio e reclamação relevantes. A agregação por produto depende do preenchimento consistente do campo `produto`.

O LLM depende de rede, cota, disponibilidade do serviço e chave válida. Pode haver custo por chamada. Embora o esquema JSON seja solicitado ao provedor, a validação local continua necessária. O prompt contém defesa básica contra instruções dentro da avaliação, mas não oferece garantia total contra ataques de prompt injection. A qualidade das justificativas também precisa ser revisada com dados representativos.

Reviews reais podem conter nomes, contatos e outros dados pessoais. A equipe deve evitar enviar informações sensíveis ao provedor sem autorização, definir retenção adequada e considerar anonimização antes do uso. O backend atual não armazena textos nem chaves. Como a API não implementa autenticação ou limite de taxa por cliente, está configurada para escutar apenas na máquina local. Para publicação, esses controles precisam ser adicionados.

A acurácia só é calculada quando referências são fornecidas; elas devem ser produzidas por avaliadores humanos independentes. A taxa de concordância entre métodos mostra semelhança, não qual método está correto. O percentual positivo é um indicador descritivo do lote, não uma medida estatística calibrada de satisfação.

<!-- pagebreak -->

## 7. Continuidade e conclusão

O próximo passo técnico é montar um conjunto rotulado de avaliações reais ou autorizadas, com diversidade de produtos, tamanhos, gírias e opiniões mistas. Deve-se reservar um conjunto de teste separado, medir acurácia, precisão, revocação e matriz de confusão para cada método e revisar manualmente as divergências. Esse estudo permitirá ampliar o léxico ou substituí-lo por uma baseline supervisionada, caso necessário.

Depois, vale executar a comparação com uma chave Gemini válida, registrar custos e latência e testar indisponibilidade do provedor. A API poderá receber autenticação, limites por cliente e logs sem conteúdo sensível. O frontend completo, deixado para outra etapa, poderá consumir o mesmo contrato JSON e exibir filtros, gráficos e exemplos de discordância.

O guia também pede uma apresentação com demonstração e um relatório final completo da equipe. Esta entrega documenta a etapa de backend e fornece um caminho de execução local para a futura demonstração; dados institucionais e dos integrantes deverão ser preenchidos pela equipe antes de uma submissão acadêmica. O projeto já reúne uma técnica clássica de PLN, uma integração LLM, prompting few-shot, saída JSON, exemplos e testes, com as limitações explicitadas.

## Referências

Guia do Projeto – AV_FINAL – Desenvolvimento de Solução com IA. Documento fornecido pelo usuário, 18 páginas, 2026.

Google AI for Developers. *Structured outputs*. https://ai.google.dev/gemini-api/docs/structured-output. Consulta em 22 nov. 2026.

Google AI for Developers. *Generating content: Gemini API*. https://ai.google.dev/api/generate-content. Consulta em 22 nov. 2026.

Python Software Foundation. *Python Standard Library*. https://docs.python.org/3/library/. Consulta em 22 nov. 2026.
