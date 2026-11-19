const conversa = document.getElementById("conversa");
const formulario = document.getElementById("formulario");
const campo = document.getElementById("texto");
const telefone = document.getElementById("telefone");
const enviar = document.getElementById("enviar");

function balao(classe, texto) {
  const el = document.createElement("div");
  el.className = "balao " + classe;
  el.textContent = texto;
  conversa.appendChild(el);
  conversa.scrollTop = conversa.scrollHeight;
  return el;
}

function link(el, arquivo) {
  const a = document.createElement("a");
  a.href = arquivo.url;
  a.download = arquivo.nome;
  a.textContent = window.TEXTOS.baixar + " (" + arquivo.nome + ")";
  el.appendChild(document.createElement("br"));
  el.appendChild(a);
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const texto = campo.value;
  if (!texto.trim()) return;
  balao("cliente", texto);
  campo.value = "";
  enviar.disabled = true;
  const espera = balao("bot digitando", "...");
  try {
    const resposta = await fetch("/api/mensagem", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({telefone: telefone.value, texto}),
    });
    const dados = await resposta.json();
    espera.remove();
    const el = balao("bot", dados.resposta || dados.mensagem || window.TEXTOS.semRede);
    if (dados.arquivo) link(el, dados.arquivo);
  } catch (erro) {
    espera.remove();
    balao("bot", window.TEXTOS.semRede);
  } finally {
    enviar.disabled = false;
    campo.focus();
  }
});
