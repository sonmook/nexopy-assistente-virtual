# 4. Avaliação e Métricas

## Objetivo

Avaliar se o NexoPy recupera o conteúdo correto e se recusa respostas fora do
escopo.

## Conjunto de testes

O arquivo `tests/casos_avaliacao.json` contém perguntas sobre:

- Python;
- Pandas;
- automação;
- erros;
- Git;
- inteligência artificial;
- pergunta fora do escopo.

## Métricas

### Assertividade de recuperação

Percentual de perguntas em que a primeira fonte recuperada corresponde ao item
esperado.

### Taxa de respostas seguras

Percentual de casos em que o assistente responde com contexto ou recusa quando
não há contexto.

### Recusa correta

Mede se perguntas fora do escopo não recebem respostas inventadas.

### Confiança média

Média da similaridade da primeira fonte recuperada.

## Executar avaliação

```bash
python scripts/evaluate.py
```

Os resultados são salvos em:

```text
outputs/avaliacao_detalhada.csv
outputs/metricas.json
```

## Resultado da avaliação inicial

A primeira avaliação automatizada, com 20 perguntas, alcançou:

- 20 acertos de recuperação;
- 100% de assertividade;
- 100% de respostas seguras;
- recusa correta da pergunta fora do escopo.

## Critérios iniciais

- Assertividade de recuperação: pelo menos 85%;
- Respostas seguras: pelo menos 95%;
- Recusa correta em todas as perguntas fora do escopo;
- Nenhuma resposta baseada em fonte inexistente.
