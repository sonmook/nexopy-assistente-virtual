# Correções da auditoria

## Respostas e conteúdo

Ambientes virtuais agora possuem exemplos separados para Linux/macOS (bash/zsh)
e Windows (PowerShell). Uma plataforma explícita na pergunta ou continuação seleciona
o exemplo correspondente. Sem plataforma explícita, as alternativas são identificadas.
A base de listas inclui índice -1 para o último elemento de listas não vazias e a
diferença entre listas mutáveis e tuplas imutáveis. Comparações não cobertas podem
pedir esclarecimento; a cobertura continua limitada e heurística.

## Dados enviados ao Gemini

A interface informa que a pergunta atual e a base recuperada são enviados ao Google.
O histórico bruto, incluindo perguntas recusadas e respostas anteriores, não é
encaminhado. Continuações usam o título do assunto recuperado localmente e a nova
pergunta. Isto reduz o contexto disponível para continuações muito específicas.
Não envie informações pessoais ou credenciais na pergunta atual. `store=False`
solicita que a interação não seja persistida para continuação no serviço; isso não
constitui garantia de ausência de logs ou retenção pelo provedor.
O prompt instrui o modelo a tratar entradas como dados, mas não garante proteção
completa contra prompt injection.

## Limites de consumo

| Variável | Padrão | Efeito |
| --- | ---: | --- |
| `MAX_QUESTION_CHARS` | 4000 | Rejeita perguntas maiores antes da busca e da API. |
| `MAX_PROMPT_CHARS` | 20000 | Acima disso, utiliza resposta local. |
| `GEMINI_MAX_OUTPUT_TOKENS` | 1024 | Limite de saída enviado ao SDK. |
| `GEMINI_REQUESTS_PER_MINUTE` | 10 | Tentativas numa janela móvel de 60 segundos. |
| `GEMINI_REQUESTS_PER_DAY` | 100 | Tentativas numa janela móvel de 24 horas. |

As configurações aceitam somente inteiros positivos. Reservas são atômicas e
compartilhadas por todas as sessões que usam o assistente em cache no mesmo
processo Streamlit. Falhas do provedor também consomem a cota. Ao atingir o limite,
o assistente responde pela base local e informa a indisponibilidade generativa.
O chat mantém até 40 mensagens na sessão para limitar seu crescimento.

As cotas ficam em memória: reiniciar, limpar o cache ou criar outro processo/objeto
reinicia os contadores. Não representam um teto financeiro nem uma cota por usuário.
Uma implantação pública com várias réplicas precisa de contador compartilhado,
autenticação e orçamento no provedor. Os limites não substituem esses controles.

## Avaliação

`termos_proibidos` complementa os termos esperados: uma resposta que contenha um
comando incompatível pode reprovar mesmo quando a fonte e os termos positivos
estiverem corretos. A métrica legada `seguranca_percentual` mede conformidade nos
casos, não uma garantia geral de segurança ou correção semântica.

Os casos de `tests/casos_auditoria.json` são regressões conhecidas, incluídas no CI.
Futuras medições independentes devem usar perguntas novas, não utilizadas para
ajustar regras ou conteúdo. A integração real com o provedor requer conectividade;
respostas simuladas não comprovam disponibilidade do serviço.
