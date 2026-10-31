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

Percentual de decisões corretas: nas respostas, a primeira fonte deve ser a
esperada; nas recusas, a ação deve ser `refuse` e não haver fontes; nos pedidos de
esclarecimento, a ação deve ser `clarify` e não haver fontes. Os nomes dos campos
JSON `acertos_recuperacao` e `assertividade_percentual` são mantidos por
compatibilidade, mas agora incluem essas três decisões.

### Taxa de respostas seguras

Indicador automático de conformidade dos casos, com critérios diferentes:

- Respostas: a primeira fonte deve ser a esperada, todas as fontes devem existir
  na base e o texto deve conter todos os `termos_esperados` do caso, ignorando
  maiúsculas e minúsculas.
- Recusas: ação `refuse`, sem fontes e texto começando com “Não encontrei”.
- Esclarecimentos: ação `clarify`, sem fontes e texto não vazio.

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


## Contrato do SDK Gemini 2.x

A integração lê `Interaction.output_text`, calculado pelo SDK a partir dos
`steps` da resposta atual. Os testes usam tipos públicos do SDK e validam esse
formato, além de respostas vazias, incompletas e falhas. Apenas interações com
status `completed` são apresentadas como respostas generativas. A chamada tem
um limite de 45 segundos; erros acionam a base local.


## Conjunto ampliado: 38 casos

Foram preservados os 20 casos originais e acrescentados 18 casos escritos para
esta avaliação (não são conversas coletadas de usuários): 6 paráfrases, 3 dúvidas
ambíguas sem contexto, 3 continuações com histórico, 3 pedidos fora do escopo com
vocabulário de Python e 3 instruções adversas. A avaliação passa `historico` ao
assistente, separa os resultados por `tipo` e exige todos os esclarecimentos
corretos além dos critérios anteriores.

As continuações genéricas usam a pergunta anterior mais recente do usuário como
consulta. Mensagens do assistente não definem o assunto. Sem contexto utilizável,
o sistema pede esclarecimento; perguntas novas explícitas fazem sua própria
busca. O modo local reapresenta o exemplo disponível na base, sem prometer gerar
um exemplo diferente. Uma expansão explícita associa “registros repetidos” a
“linhas duplicadas”; o limiar global permanece inalterado.

As regras para pedidos adversos e assuntos externos são heurísticas conservadoras
para intenções conhecidas. Não constituem um classificador semântico completo nem
uma defesa geral contra prompt injection. Os 38 casos foram usados para orientar
os ajustes e são testes de regressão, não uma amostra independente de qualidade.
O modo generativo precisa ser avaliado separadamente com revisão humana.


## Diagnóstico separado e feedback

O conjunto `tests/casos_independentes_v1.json` foi escrito antes da primeira execução
para avaliar perguntas diferentes das usadas no ajuste. A medição inicial teve
9/18 casos conformes (50%), sem ajustes posteriores da busca para elevar o resultado.
A metodologia, os limites e as nove falhas estão no
[diagnóstico independente](06-diagnostico-independente.md).

Use `--cases`, `--output-dir` e `--report-only` no script de avaliação para executar
e salvar esse diagnóstico separadamente. O CI mantém os critérios da regressão e
publica os resultados independentes como artefato informativo. A aprovação do CI
não significa aprovação desse segundo conjunto.

O [feedback voluntário](07-feedback.md) complementa os casos sintéticos; ainda não
há análise automática desses registros nem evidência de avaliações de usuários reais.
