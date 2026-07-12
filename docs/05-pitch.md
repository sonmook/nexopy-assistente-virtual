# 5. Pitch do Projeto

## Roteiro de aproximadamente 3 minutos

Muitas pessoas começam a estudar Python, mas encontram dificuldades para
interpretar erros, organizar os conteúdos e saber qual deve ser o próximo passo.

Para apoiar esse processo, desenvolvi o NexoPy, um assistente virtual voltado
para estudos em Python, Pandas, automação de dados, Git e fundamentos de
inteligência artificial.

O NexoPy possui uma base de conhecimento organizada em JSON. Quando uma pessoa
faz uma pergunta, o sistema utiliza processamento de linguagem natural com
TF-IDF e similaridade de cosseno para encontrar os conteúdos mais relevantes.

Quando encontra contexto suficiente, ele produz uma explicação simples, mostra
um exemplo e recomenda um próximo passo. Quando não encontra informação,
informa sua limitação em vez de inventar uma resposta.

A aplicação possui uma interface de conversa desenvolvida em Streamlit. Ela
também pode utilizar o Gemini de forma opcional para deixar as respostas mais
naturais, mantendo a base local como fonte e como modo de segurança.

O projeto inclui testes, métricas de assertividade, documentação dos prompts,
estratégia anti-alucinação e um conjunto de perguntas de avaliação.

O principal valor do NexoPy é transformar dúvidas técnicas em orientações
curtas, rastreáveis e adequadas para iniciantes. Como evolução futura, a base
pode receber novos conteúdos, exercícios personalizados e acompanhamento da
trilha de estudos.
