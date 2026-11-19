# Passo a passo: o bot no WhatsApp com número real, rodando no seu computador

Objetivo: o cliente manda o pedido para o seu número, o bot devolve a lista com `ok ou não?`, e após o
`ok` devolve o Excel como documento no próprio WhatsApp. O app continua rodando no seu Mac.

> A API da Meta muda de tempos em tempos (versões, nomes de telas, regras de cobrança). Use este
> roteiro como mapa e confira cada passo na documentação oficial: *WhatsApp Business Platform → Cloud API*.

## Como funciona (visão geral)

```text
Cliente (WhatsApp) → Meta → túnel HTTPS → seu Mac (POST /whatsapp) → Conversa.responder
Cliente (WhatsApp) ← Meta ← API Graph  ←  texto da lista / arquivo .xlsx
```

1. A Meta chama o seu servidor em `POST /whatsapp` quando chega mensagem.
2. O servidor responde `200` na hora e processa em segundo plano (o modelo leva alguns segundos e a
   Meta reenvia a notificação se demorar).
3. O servidor chama o motor que já existe, `Conversa.responder(telefone, texto)`, e devolve a resposta
   pela API Graph: texto para a lista; para o `ok`, sobe o `.xlsx` como mídia e envia como documento.

## Parte A: contas e número (você faz, uns 30 a 60 minutos; a verificação do negócio pode levar dias)

1. **Conta no Meta Business** (business.facebook.com). Use o e-mail da empresa.
2. **App no Meta for Developers** (developers.facebook.com → *Meus apps* → *Criar app* → tipo
   *Empresa*), vinculado ao seu Meta Business. Adicione o produto **WhatsApp**.
3. **Comece pelo número de teste** que a Meta dá na tela *API Setup*: ele tem um `Phone number ID` e
   deixa você cadastrar até cerca de 5 números de destino (os seus e de 2 ou 3 clientes de confiança).
   Isso valida tudo sem tocar no número real.
4. **Depois, o número real**, em *API Setup → Adicionar número de telefone*:
   - O número **não pode estar ativo no app WhatsApp comum** nem no WhatsApp Business app, a menos que
     você use o modo de coexistência (o app Business e a API no mesmo número; confira na documentação
     se está disponível para o seu país). Se o número está no celular da empresa, decida: migrar de vez
     para a API (o celular deixa de usá-lo) ou usar um número novo só para o bot.
   - A Meta confirma o número por SMS ou ligação e aprova o **nome de exibição**.
   - Pode pedir **forma de pagamento**. Conversas iniciadas pelo cliente costumam ser as mais baratas
     ou gratuitas; confira a tabela de preços atual.
5. **Verificação do negócio** (documentos da empresa, CNPJ): peça cedo, em paralelo. Sem ela os limites
   são baixos, mas para um bot que só responde clientes que escrevem primeiro costuma bastar no começo.
6. **Anote** (guarde só no `.env`, nunca no repositório): `Phone number ID`, **App Secret** (em
   *Configurações do app → Básico*) e um **token permanente**.
   - Token permanente: Business Settings → *Usuários do sistema* → crie um usuário de sistema, dê acesso
     ao app e à conta do WhatsApp, e gere o token com as permissões `whatsapp_business_messaging` e
     `whatsapp_business_management`. O token de teste da tela *API Setup* expira em cerca de 24 horas.
   - Escolha também um **token de verificação** qualquer (uma frase longa e aleatória sua).

## Parte B: expor o app local na internet (túnel)

A Meta só chama endereços HTTPS públicos; o seu Mac é local, então use um túnel.

1. Instale uma ferramenta de túnel: Cloudflare Tunnel (`brew install cloudflared`) ou ngrok.
2. Com o app no ar na porta 8000, abra o túnel:

   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```

   Ele imprime um endereço `https://algo.trycloudflare.com`. **Esse endereço muda a cada vez** que o
   túnel é reiniciado, e a Meta precisa ser avisada. Para um endereço fixo, use um túnel nomeado
   (Cloudflare, com um domínio seu) ou um domínio fixo do ngrok.
3. Mantenha o Mac **acordado e conectado** enquanto o bot deve responder (as configurações de energia do
   macOS ou `caffeinate -d` ajudam). Se o Mac dormir ou o túnel cair, o cliente fica sem resposta.

> **Atualização (feature 006):** em produção o bot exige chave de API em todas as rotas, menos `/saude`. A rota
> `/whatsapp` será a única rota pública além dela (protegida pela assinatura da Meta). Veja `docs/contrato-api.md`
> e `docs/producao-render.md`. O adaptador do WhatsApp é uma feature futura (a numeração mudou).

## Parte C: o que construir no código (adaptador do WhatsApp)

Esta é a próxima feature. Peça: *"rode o SDD da feature 005, adaptador do WhatsApp"* e ela será
especificada, planejada e implementada com testes primeiro. O conteúdo previsto:

1. **`GET /whatsapp`** (verificação): devolve o `hub.challenge` quando `hub.verify_token` é igual ao seu
   token de verificação.
2. **`POST /whatsapp`** (mensagens):
   - valida o cabeçalho `X-Hub-Signature-256` (HMAC SHA-256 do corpo com o App Secret); sem assinatura
     válida, `403`;
   - responde `200` imediatamente e processa em segundo plano;
   - lê `entry[].changes[].value.messages[]` (`id`, `from`, `type`, `text.body`);
   - **ignora mensagens repetidas** pelo `id` (tabela nova no banco), porque a Meta reenvia;
   - mensagem que não é texto (áudio, imagem...) recebe uma frase curta e neutra pedindo para escrever
     o pedido;
   - normaliza o número (`from`) e chama `Conversa.responder(telefone, texto)`.
3. **Envio**, pela API Graph (`POST /{PHONE_NUMBER_ID}/messages`, com o token):
   - texto: `{"messaging_product": "whatsapp", "to": "...", "type": "text", "text": {"body": "..."}}`;
   - planilha: subir o arquivo em `/{PHONE_NUMBER_ID}/media` e enviar uma mensagem do tipo `document`
     com o `id` da mídia e o nome `pedido-N.xlsx`.
4. **Variáveis novas no `.env`**: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_APP_SECRET`,
   `WHATSAPP_VERIFY_TOKEN`. Nunca no repositório, nunca em logs.
5. **O que já está pronto e protege o bot**: o limite de mensagens por minuto e de tamanho, o limite de
   1000 dz por produto, a mensagem tratada como dado e a memória silenciosa de apelidos.
6. **Testes** sem internet: um servidor falso da Meta (como o servidor falso de chat e embeddings que já
   existe) para a verificação, a assinatura, as mensagens repetidas, o envio de texto e de documento.

## Parte D: ligar tudo, na ordem

1. Suba o banco, o Ollama e o app (os três comandos do README do projeto):

   ```bash
   docker compose up -d db
   ```

   ```bash
   ollama serve
   ```

   ```bash
   set -a && source .env && set +a && uv run python -m pedido
   ```

2. Abra o túnel (Parte B) e copie o endereço `https://...`.
3. Na Meta: *WhatsApp → Configuração → Webhook*: *URL de callback* = `https://SEU-ENDERECO/whatsapp`,
   *Token de verificação* = o seu. Clique em *Verificar e salvar*. Assine o campo **`messages`**.
4. **Teste 1, número de teste**: do seu celular (cadastrado como destino), mande para o número de teste:
   `2 dz abre caminho e meia duzia de arruda`. Deve chegar a lista com `ok ou não?`. Responda `ok` e
   confira se o Excel chega como documento.
5. **Teste 2, mensagens ruins**: áudio, texto enorme, 25 mensagens seguidas, `5000 dz de ogum`, `não`,
   outro pedido no meio. As respostas devem ser as frases neutras já definidas.
6. **Troque para o número real** (Parte A, passo 4): atualize `WHATSAPP_PHONE_NUMBER_ID` e o token no
   `.env`, reinicie o app e repita os testes 1 e 2 com 2 ou 3 clientes de confiança.
7. **Observe por alguns dias**: anote as mensagens que o bot errou. Veja os apelidos aprendidos com
   `uv run python scripts/apelidos.py` e desative os errados com `--desativar ID`.

## Cuidados importantes

- **Janela de 24 horas**: o bot só responde livremente enquanto o cliente falou nas últimas 24 horas,
  o que cobre o fluxo pedido → `ok`. Depois disso a Meta exige mensagens-modelo aprovadas.
- **O túnel expõe o seu Mac**: por isso a assinatura do webhook é obrigatória e as rotas de teste
  (`/api/mensagem` e a página) não devem ficar abertas pelo túnel. A feature 005 deve publicar só
  `/whatsapp` pelo túnel (ou proteger o resto).
- **Privacidade (LGPD)**: o bot guarda telefone e pedidos no seu banco. Avise os clientes e defina por
  quanto tempo guardar.
- **Modelo local**: o `qwen2.5:14b` às vezes erra números (ex.: leu `1000 dz` como `100 dz`). O cliente
  vê a lista e confere antes do `ok`, mas para uso real vale um modelo maior ou o Claude
  (`LLM_PROVIDER=anthropic`).
- **Para uso diário**: um Mac que dorme não serve. Quando o bot estiver estável, leve o app para um
  servidor sempre ligado (com HTTPS fixo), um Postgres gerenciado e um modelo hospedado.
- **Porta do banco**: o banco do bot usa a porta **5434**; a 5433 é do seu `estoque-incenso-db`.

## Checklist rápido

- [ ] Conta Meta Business e app com o produto WhatsApp
- [ ] Número de teste funcionando com 1 a 3 destinos cadastrados
- [ ] Token permanente, App Secret, `Phone number ID` e token de verificação guardados no `.env`
- [ ] Túnel HTTPS e Mac configurado para não dormir
- [ ] Feature 005 implementada e testada (webhook, assinatura, repetidas, envio de texto e documento)
- [ ] Webhook verificado na Meta e campo `messages` assinado
- [ ] Teste completo: pedido → lista → `ok` → Excel no WhatsApp
- [ ] Número real adicionado, nome de exibição aprovado, testes repetidos
- [ ] Verificação do negócio solicitada
