# 3. Prompts do Agente

## System prompt

O prompt principal está em `src/nexopy/prompts.py`.

Ele define que o NexoPy deve:

- responder em português;
- usar apenas o contexto recuperado;
- não inventar informações;
- dizer quando não há informação suficiente;
- explicar código em etapas;
- proteger chaves e senhas;
- sugerir um próximo passo.

## Estrutura do prompt de usuário

A entrada enviada ao modelo contém:

1. contexto recuperado da base;
2. histórico recente da conversa;
3. pergunta atual;
4. instrução para responder somente com o contexto.

## Exemplo esperado

**Entrada**

> Como corrigir ModuleNotFoundError?

**Saída esperada**

> Esse erro aparece quando o Python não encontra o módulo importado. Verifique
> o nome, ative o ambiente virtual correto e instale a dependência com
> `python -m pip install nome-da-biblioteca`.

## Edge cases

### Pergunta fora do escopo

O agente informa que não encontrou conteúdo suficiente.

### API indisponível

O agente retorna automaticamente para a resposta local.

### Pergunta vazia

O agente pede que a pessoa digite uma pergunta.

### Saudação

O agente se apresenta e mostra os assuntos disponíveis.

### Pedido de segredo

O prompt proíbe solicitar ou exibir senhas, tokens e chaves.
