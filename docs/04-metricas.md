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

Indicador automático de conformidade dos casos, com critérios diferentes:

- Respostas: a primeira fonte deve ser a esperada, todas as fontes devem existir
  na base e o texto deve conter todos os `termos_esperados` do caso, ignorando
  maiúsculas e minúsculas.
- Recusas: não devem apresentar fontes e devem começar com “Não encontrei”.

A presença de termos não comprova correção semântica, ausência de alucinações ou
segurança geral. Esta métrica serve para regressão do conjunto documentado.
Respostas generativas precisam também de avaliação humana. Os termos são
curados nos casos de teste, não extraídos automaticamente das respostas.

### Recusa correta

Mede se os casos marcados fora do escopo são recusados sem fontes.

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


## Validação contínua

O CI executa os testes, a checagem estática `ruff check --isolated --select E9,F .`
e `python scripts/evaluate.py`. O script retorna erro quando a recuperação fica
abaixo de 85%, a conformidade (“respostas seguras”) abaixo de 95% ou qualquer caso
de recusa recebe fontes. Conjuntos vazios e casos de resposta sem termos esperados
são erros de configuração.

Os testes do Gemini usam objetos do SDK e simulam respostas válidas, vazias,
falhas do provedor e inicialização indisponível, sem chave de API ou chamadas
externas. Um teste Streamlit verifica a interação local com o chat. Isso não
valida disponibilidade, acesso ou comportamento real do serviço Gemini.

Cada resposta registra o modo efetivamente utilizado e a interface o exibe junto
ao conteúdo. A indicação na barra lateral representa o provedor configurado.
