# Diagnóstico v2 — novas perguntas

Foram reservados 12 casos em `tests/casos_independentes_v2.json` antes da alteração
de implementação da expansão de consultas. As expectativas foram escritas antes
da execução. O conjunto é sintético, da mesma autoria; não representa validação
externa nem perguntas coletadas de usuários reais. A exploração das três falhas de
v1 precedeu a reserva; este conjunto verifica a implementação resultante, não um
experimento cego de outra equipe.

SHA-256: `505f5b53151947fb06b4f1451420be0b61f07b00756587bef36802bb770d905f`.

## Resultado da primeira execução

**10/12 decisões corretas e casos conformes (83,33%)**, em modo local.

| Grupo | Casos conformes |
| --- | ---: |
| Paráfrases | 6/7 |
| Pedidos externos | 2/3 |
| Ambiguidade | 1/1 |
| Continuação | 1/1 |

As duas falhas foram preservadas, sem reajustar a busca após observar os resultados:

- “Como acessar a primeira posição de uma lista?” recupera `erro-indexerror`, mas
  o esperado é `python-listas`.
- “Qual o total de calorias por refeição?” responde com `exercicio-pandas`, quando
  o esperado é recusa. Não houve expansão dessa pergunta: trata-se de um falso
  positivo da recuperação original que continua presente.

A segunda falha demonstra que impedir expansões indevidas é necessário, mas não
suficiente para classificar o domínio. São problemas conhecidos após a medição;
qualquer ajuste futuro a partir deles exigirá novas perguntas para avaliar a
generalização. Os percentuais verificam IDs, ações e termos; não são uma medida
completa de segurança ou correção semântica.

## Reproduzir

```bash
python scripts/evaluate.py --cases tests/casos_independentes_v2.json --output-dir outputs/independente-v2 --report-only
```

O CI salva resultados separados como `avaliacao-independente-v2`. `--report-only`
relata as falhas sem usá-las como critério de aprovação. A regressão de 38 casos e
os testes dos 18 casos conhecidos de v1 continuam obrigatórios.


## Correção das duas falhas conhecidas

Após a primeira medição, os dois casos foram usados para orientar correções e
receberam testes de regressão com variações. A busca expande acesso normal a
posições de listas com termos de indexação, sem aplicar essa expansão quando
há indícios explícitos de erro ou posição inexistente. A classificação de intenção
recusa pedidos nutricionais, mas permite operações de programação sobre dados
de nutrição, incluindo leitura de CSV e soma de colunas em Pandas.

O resultado atual é **12/12 (100%)**. A primeira medição de 10/12 permanece acima
como histórico; os casos não foram editados. O conjunto deixou de ser independente
para medir melhorias futuras. Os testes dos 12 casos passam a ser obrigatórios,
embora a etapa de relatório no CI continue apenas informativa. As regras de intenção
são heurísticas e esse resultado não prova segurança geral ou generalização.

Antes dessas correções, foi verificada a execução do GitHub Actions para
`a9caa5c`: [Tests, execução 41247217029](https://github.com/sonmook/nexopy-assistente-virtual/actions/runs/41247217029)
terminou com `success`. Essa evidência pertence à versão anterior; o resultado
local das correções não substitui uma execução remota após seu envio.
