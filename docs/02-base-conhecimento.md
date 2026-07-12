# 2. Base de Conhecimento

## Arquivo principal

A base está em:

```text
data/conhecimentos.json
```

Cada registro possui:

- identificador;
- categoria;
- título;
- perguntas relacionadas;
- palavras-chave;
- resposta;
- exemplo;
- próximo passo.

## Categorias

- Fundamentos de Python;
- Pandas;
- Automação;
- Erros comuns;
- Ambiente de desenvolvimento;
- Organização de projetos;
- Git e GitHub;
- Inteligência Artificial;
- Trilha de estudos;
- Exercícios.

## Estratégia de recuperação

O sistema transforma a base e a pergunta em vetores TF-IDF. Depois calcula a
similaridade de cosseno e seleciona os conteúdos mais próximos.

A resposta só é produzida quando a melhor correspondência supera o limite
definido por `MIN_SIMILARITY`.

## Manutenção da base

Novos registros devem:

1. possuir um `id` único;
2. responder a uma dúvida específica;
3. usar linguagem simples;
4. incluir exemplo pequeno quando possível;
5. indicar um próximo passo;
6. ser testados com uma pergunta em `tests/casos_avaliacao.json`.

## Limitações

A base inicial não pretende cobrir toda a linguagem Python. Ela prioriza dúvidas
recorrentes de pessoas iniciantes e pode ser ampliada gradualmente.
