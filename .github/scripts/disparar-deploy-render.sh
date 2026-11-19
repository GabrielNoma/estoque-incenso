#!/usr/bin/env bash
# Dispara o deploy de um serviço do Render pelo deploy hook, com tentativas.
# Variáveis: RENDER_DEPLOY_HOOK_URL (o endereço do hook, vem de um secret) e NOME_SECRET (o nome do secret,
# usado só nas mensagens de erro). Nunca imprime o endereço do hook.
set -u

if [ -z "${RENDER_DEPLOY_HOOK_URL:-}" ]; then
  echo "::error title=Render Deploy Hook::Secret ${NOME_SECRET:-RENDER_DEPLOY_HOOK_URL} não configurado (Settings → Secrets → Actions)."
  exit 1
fi

MAX_TENTATIVAS=3
ESPERA=10
BODY_FILE=$(mktemp)
MOTIVO=""
BODY=""

for TENTATIVA in $(seq 1 $MAX_TENTATIVAS); do
  # curl devolve 000 quando não há resposta HTTP (DNS, timeout, TLS...)
  STATUS=$(curl -sS -o "$BODY_FILE" -w "%{http_code}" \
                --connect-timeout 10 --max-time 30 \
                -X POST "$RENDER_DEPLOY_HOOK_URL" 2>/tmp/curl_err) || true
  BODY=$(head -c 500 "$BODY_FILE")
  echo "Tentativa $TENTATIVA/$MAX_TENTATIVAS — Render Deploy Hook status: $STATUS"

  case "$STATUS" in
    2??)
      # 200 OK / 201 Created / 202 Accepted: deploy enfileirado
      echo "Deploy disparado com sucesso. Resposta: $BODY"
      echo "### Render: deploy disparado (HTTP $STATUS)" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
      exit 0
      ;;
    000)
      MOTIVO="sem resposta do Render (rede/timeout): $(cat /tmp/curl_err)"
      RETENTAVEL=1 ;;
    429)
      MOTIVO="limite de requisições do Render atingido (429 Too Many Requests)"
      RETENTAVEL=1 ;;
    5??)
      MOTIVO="erro interno do Render ($STATUS) — instabilidade do lado deles"
      RETENTAVEL=1 ;;
    401|403)
      MOTIVO="acesso negado ($STATUS) — a chave do Deploy Hook foi regenerada/revogada? Atualize o secret ${NOME_SECRET:-RENDER_DEPLOY_HOOK_URL}"
      RETENTAVEL=0 ;;
    404)
      MOTIVO="Deploy Hook não encontrado (404) — URL errada ou serviço removido no Render. Confira o secret ${NOME_SECRET:-RENDER_DEPLOY_HOOK_URL}"
      RETENTAVEL=0 ;;
    4??)
      MOTIVO="requisição rejeitada pelo Render ($STATUS)"
      RETENTAVEL=0 ;;
    *)
      MOTIVO="status inesperado ($STATUS)"
      RETENTAVEL=0 ;;
  esac

  if [ "$RETENTAVEL" = "1" ] && [ "$TENTATIVA" -lt "$MAX_TENTATIVAS" ]; then
    echo "::warning title=Render Deploy Hook::$MOTIVO — nova tentativa em ${ESPERA}s"
    sleep "$ESPERA"
    ESPERA=$((ESPERA * 2))
    continue
  fi
  break
done

echo "::error title=Render Deploy Hook falhou::$MOTIVO"
[ -n "$BODY" ] && echo "Resposta do Render: $BODY"
echo "### Render: deploy NÃO disparado — $MOTIVO" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
exit 1
