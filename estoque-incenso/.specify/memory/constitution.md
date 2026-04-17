<!--
SYNC IMPACT REPORT
==================
Version change: [template] → 1.0.0
Modified principles: N/A (initial ratification)
Added sections:
  - Core Principles (I. Simplicidade de Uso, II. Clean Code & SOLID, III. Observabilidade de Erros)
  - Padrões de Desenvolvimento
  - Fluxo de Trabalho
  - Governance
Removed sections: N/A
Templates reviewed:
  - .specify/templates/plan-template.md ✅ aligned (Constitution Check section present)
  - .specify/templates/spec-template.md ✅ aligned (FR-005 logging requirement mirrors Principle III)
  - .specify/templates/tasks-template.md ✅ aligned (T008 error handling/logging task in Phase 2)
  - .specify/templates/commands/ ⚠️ no command files found — skip
Follow-up TODOs: none
-->

# Estoque de Incenso Constitution

## Core Principles

### I. Simplicidade de Uso

Todo código DEVE ser projetado para ser simples de usar e entender. APIs, serviços e interfaces
DEVEM expor a intenção de forma clara, com nomes de funções, variáveis e módulos que comuniquem
propósito sem necessidade de comentários explicativos. Complexidade desnecessária DEVE ser evitada;
soluções mais simples que atendam ao requisito DEVEM ser preferidas. Nenhuma abstração deve ser
introduzida antes de ser necessária (YAGNI).

**Regras não-negociáveis:**
- Nomes de variáveis, funções e classes DEVEM ser autoexplicativos
- Funções DEVEM ter responsabilidade única e ser pequenas o suficiente para caber na tela
- Abstrações e padrões de design DEVEM ser justificados por necessidade real, não antecipada
- Interfaces públicas DEVEM ser projetadas do ponto de vista do consumidor

### II. Clean Code & SOLID

Todo código DEVE seguir os princípios de Clean Code e SOLID. Cada módulo, classe ou função
DEVE ter uma única razão para mudar (Single Responsibility). Extensões de comportamento DEVEM
ser feitas por adição, não por modificação de código existente (Open/Closed). Dependências DEVEM
ser invertidas: módulos de alto nível não DEVEM depender de módulos de baixo nível diretamente
(Dependency Inversion). Código duplicado (DRY) DEVE ser eliminado.

**Regras não-negociáveis:**
- Single Responsibility: cada classe/função tem UMA responsabilidade
- Open/Closed: código aberto para extensão, fechado para modificação
- Liskov Substitution: subtipos DEVEM ser substituíveis por seus tipos base
- Interface Segregation: interfaces DEVEM ser granulares e específicas
- Dependency Inversion: depender de abstrações, não de implementações concretas
- Código duplicado DEVE ser extraído antes do terceiro uso

### III. Observabilidade de Erros

Toda feature DEVE possuir mecanismo de log ou identificação de erros. Erros DEVEM ser capturados,
registrados com contexto suficiente para diagnóstico (timestamp, operação, dados relevantes, stack
trace quando aplicável) e nunca silenciados. O sistema DEVE diferenciar níveis de severidade (INFO,
WARN, ERROR). Logs DEVEM ser estruturados para facilitar filtragem e rastreabilidade.

**Regras não-negociáveis:**
- Toda feature DEVE ter ao menos um ponto de log de erro
- Erros NUNCA podem ser capturados e descartados silenciosamente (catch vazio proibido)
- Logs DEVEM conter: timestamp, operação, mensagem descritiva e contexto relevante
- Níveis de log DEVEM ser usados corretamente: ERROR para falhas que impactam o usuário,
  WARN para situações degradadas, INFO para fluxo normal relevante
- Em ambientes de produção, stack traces completos DEVEM ser registrados no log
- Cada serviço/módulo DEVE ter identificador próprio no log para rastreabilidade

## Padrões de Desenvolvimento

Padrões técnicos obrigatórios para todas as contribuições ao projeto:

- **Estrutura de projeto**: código organizado por domínio/feature, não por tipo técnico
- **Tratamento de erros**: usar tipos/classes de erro específicos do domínio; evitar strings brutas
  como mensagens de erro em código de produção
- **Testes**: código de negócio DEVE ser testável de forma isolada; dependências externas DEVEM
  ser injetadas
- **Configuração**: valores de ambiente e configurações DEVEM ser externalizados (variáveis de
  ambiente ou arquivos de configuração); nunca hardcoded em código-fonte
- **Revisão**: todo PR DEVE verificar conformidade com os três princípios antes de aprovação

## Fluxo de Trabalho

Diretrizes para o processo de desenvolvimento:

- Features DEVEM ser desenvolvidas em branches separadas
- Cada feature DEVE ter sua especificação (`spec.md`) aprovada antes da implementação
- O plano de implementação (`plan.md`) DEVE incluir verificação dos princípios desta constituição
  na seção "Constitution Check"
- Tasks DEVEM incluir uma task de configuração de logging/error handling na fase Foundation
- Code review DEVE verificar: simplicidade de uso, aderência a SOLID/Clean Code, e presença de
  observabilidade de erros
- Commits DEVEM ser atômicos e descritivos

## Governance

Esta constituição é a autoridade suprema de qualidade do projeto. Toda decisão técnica DEVE ser
avaliada contra seus princípios. Violações DEVEM ser justificadas no plano de implementação com
a complexidade documentada na tabela de Complexity Tracking.

**Processo de emenda:**
1. Proposta documentada com motivação e impacto nos princípios existentes
2. Revisão e aprovação antes da implementação
3. Atualização do `LAST_AMENDED_DATE` e incremento de versão segundo regras semânticas
4. Propagação de alterações para templates dependentes

**Política de versionamento:**
- MAJOR: remoção ou redefinição incompatível de princípio existente
- MINOR: adição de novo princípio ou expansão material de seção existente
- PATCH: clarificações, correções de texto, refinamentos sem mudança semântica

**Revisão de conformidade**: a cada nova feature, o Constitution Check no `plan.md` serve como
gate de conformidade antes do início da implementação.

**Version**: 1.0.0 | **Ratified**: 2026-04-17 | **Last Amended**: 2026-04-17
