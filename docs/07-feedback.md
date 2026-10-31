# Feedback das respostas

Cada resposta oferece “Ajudou” e “Não ajudou”, com comentário opcional de até
500 caracteres. O envio é explícito: preencher um comentário ou abrir o formulário
não salva nada. Um agradecimento confirma a gravação; falhas permitem tentar de novo.

O banco SQLite local padrão é `outputs/feedback.sqlite3`, ignorado pelo Git.
`NEXOPY_FEEDBACK_PATH` permite escolher outro caminho gravável antes de iniciar a
aplicação. A gravação usa transações e um identificador aleatório único por resposta
para impedir duplicação em reenvios. A mesma resposta não aceita edição posterior;
limpar a conversa remove a interface, mas não apaga avaliações já enviadas.

## Dados gravados

- Identificador aleatório da resposta e horário UTC do envio.
- Voto e comentário voluntário.
- IDs das fontes recuperadas, modo utilizado e ação (responder, recusar, esclarecer).

O feedback não copia perguntas, respostas, nomes ou identificadores de conta. O
comentário livre pode conter dados fornecidos pelo usuário; a interface pede que
não sejam incluídos dados pessoais ou chaves. Não há envio a serviços externos,
análise automática ou exclusão automática dos registros.

## Persistência e limites

Os registros ficam no disco da instância. Reinicializações ou novas instâncias
podem perder os dados se o provedor não preservar esse diretório. Para uso público
com várias instâncias, será necessário escolher armazenamento persistente e uma
política de retenção antes de tratar este recurso como coleta centralizada.

Os responsáveis pela implantação podem consultar o SQLite local para agrupar
votos por fonte ou modo. Os comentários devem permanecer privados; não devem ser
incluídos em commits, capturas, relatórios públicos ou artefatos do CI.
