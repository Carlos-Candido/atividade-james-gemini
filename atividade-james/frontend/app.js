const form = document.querySelector("#analysis-form");
const textarea = document.querySelector("#analysis-text");
const exampleButton = document.querySelector("#use-example");
const countLabel = document.querySelector("#text-count");
const modeOptions = document.querySelector("#mode-options");
const compareMode = document.querySelector("#compare-mode");
const modeGuidance = document.querySelector("#mode-guidance");
const formError = document.querySelector("#form-error");
const analyzeButton = document.querySelector("#analyze-button");
const analyzeButtonLabel = analyzeButton.querySelector("span");
const analysisStatus = document.querySelector("#analysis-status");
const resultContent = document.querySelector("#result-content");
const analysisErrorDetails = document.querySelector("#analysis-error-details");
const analysisErrorMessage = analysisErrorDetails?.querySelector("p");

let comparisonAvailable = false;
let comparisonNotice = "Verificando disponibilidade do modelo…";
let providerName = "modelo de IA";
let healthChecking = false;
let analysisInProgress = false;
let textValidationAttempted = false;


function selectedMode() {
  return form.elements.namedItem("modo").value;
}

function codePointLength(value) {
  return Array.from(value).length;
}

function updateCharacterCount() {
  const length = codePointLength(textarea.value);
  countLabel.textContent = `${length.toLocaleString("pt-BR")} / 5.000`;
  countLabel.classList.toggle("is-over-limit", length > 5000);
  return length;
}

function setFormError(message) {
  formError.textContent = message;
  formError.hidden = !message;
  if (message) {
    textarea.setAttribute("aria-invalid", "true");
    textarea.setAttribute("aria-describedby", "text-guidance text-count form-error");
  } else {
    textarea.removeAttribute("aria-invalid");
    textarea.setAttribute("aria-describedby", "text-guidance text-count");
  }
}
function validateText(text, length) {
  if (!text.trim()) {
    setFormError("Digite um texto antes de analisar.");
    return false;
  }
  if (length > 5000) {
    setFormError("O texto ultrapassa o limite de 5.000 caracteres. Remova parte do conteúdo para continuar.");
    return false;
  }
  setFormError("");
  return true;
}

function updateModeGuidance() {
  modeGuidance.textContent = comparisonNotice || (
    selectedMode() === "comparar"
      ? `Se ${providerName} falhar, o resultado clássico continua disponível.`
      : "A análise clássica está disponível."
  );
}


async function checkHealth() {
  if (healthChecking || analysisInProgress) return;
  healthChecking = true;
  comparisonNotice = "Verificando disponibilidade do modelo…";
  comparisonAvailable = false;
  compareMode.disabled = true;
  updateModeGuidance();

  try {
    const response = await fetch("/saude", {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
      credentials: "omit",
    });
    let body;
    try {
      body = await response.json();
    } catch {
      throw new Error("Resposta inválida do backend");
    }
    if (!response.ok || !body || body.status !== "ok" || typeof body.llm_configurado !== "boolean") {
      throw new Error("Resposta inválida do backend");
    }

    providerName = body.llm_provedor === "deepseek" ? "DeepSeek" : "Gemini";
    comparisonAvailable = body.llm_configurado;
    comparisonNotice = comparisonAvailable
      ? ""
      : "A comparação não está disponível: nenhuma chave de API configurada.";
  } catch {
    comparisonAvailable = false;
    comparisonNotice = "Backend indisponível. Verifique a conexão e recarregue a página.";
  } finally {
    healthChecking = false;
    compareMode.disabled = !comparisonAvailable;
    if (!comparisonAvailable && selectedMode() === "comparar") {
      form.elements.namedItem("modo").value = "classico";
    }
    updateModeGuidance();
  }
}

function clearAnalysisErrorDetails() {
  if (!analysisErrorDetails || !analysisErrorMessage) return;
  analysisErrorDetails.hidden = true;
  analysisErrorDetails.open = false;
  analysisErrorMessage.textContent = "";
}

function showAnalysisErrorDetails(message) {
  if (!analysisErrorDetails || !analysisErrorMessage) return;
  if (typeof message !== "string" || !message.trim()) {
    clearAnalysisErrorDetails();
    return;
  }
  analysisErrorMessage.textContent = message;
  analysisErrorDetails.open = false;
  analysisErrorDetails.hidden = false;
}

function clearResults() {
  resultContent.replaceChildren();
  resultContent.classList.remove("is-comparing");
  clearAnalysisErrorDetails();
}

function setAnalysisStatus(message, state = "") {
  analysisStatus.classList.remove("is-loading", "is-success", "is-error");
  if (state) analysisStatus.classList.add(`is-${state}`);
  analysisStatus.textContent = message;
}

function isSentiment(value) {
  return value === "positivo" || value === "neutro" || value === "negativo";
}

function sentimentLabel(sentiment) {
  return sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
}

function createSentimentIndicator(sentiment) {
  const indicator = document.createElement("span");
  indicator.className = `sentiment sentiment-${sentiment}`;
  const icon = document.createElement("span");
  icon.className = "sentiment-icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = sentiment === "positivo" ? "↗" : sentiment === "negativo" ? "↘" : "−";
  indicator.append(icon, document.createTextNode(sentimentLabel(sentiment)));
  return indicator;
}

function hasLlmError(llm) {
  return typeof llm?.erro === "string" && llm.erro.length > 0;
}

function isValidResult(body, mode) {
  if (!body || typeof body !== "object" || body.modo !== mode || !Array.isArray(body.resultados) || body.resultados.length !== 1) {
    return false;
  }
  const result = body.resultados[0];
  const classic = result?.classico;
  if (!classic || !isSentiment(classic.sentimento) || !Number.isFinite(classic.pontuacao) || !Array.isArray(classic.evidencias) || !classic.evidencias.every((item) => typeof item === "string")) {
    return false;
  }
  if (mode === "comparar") {
    if (result.concordam !== true && result.concordam !== false && result.concordam !== null) return false;
    const llm = result.llm;
    if (!llm || typeof llm !== "object") return false;
    if (hasLlmError(llm)) return result.concordam === null;
    return isSentiment(llm.sentimento) && typeof llm.modelo === "string" && typeof llm.justificativa === "string" && typeof result.concordam === "boolean";
  }
  return true;
}

function appendDetail(container, label, value) {
  const term = document.createElement("dt");
  term.textContent = label;
  const description = document.createElement("dd");
  if (value instanceof Node) description.append(value);
  else description.textContent = value;
  container.append(term, description);
}

function createScore(classic) {
  const score = document.createElement("dl");
  score.className = "result-score";
  const term = document.createElement("dt");
  term.textContent = "Pontuação lexical";
  const description = document.createElement("dd");
  const value = document.createElement("strong");
  value.textContent = classic.pontuacao.toLocaleString("pt-BR");
  const note = document.createElement("p");
  note.textContent = "Pontuação do léxico, não uma probabilidade.";
  description.append(value, note);
  score.append(term, description);
  return score;
}

function createEvidenceSection(evidences, headingTag) {
  const section = document.createElement("section");
  section.className = "evidence-section";
  const heading = document.createElement(headingTag);
  heading.textContent = "Evidências do texto";
  section.append(heading);

  if (evidences.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-evidence";
    empty.textContent = "Nenhuma evidência lexical foi encontrada neste texto.";
    section.append(empty);
    return section;
  }

  const list = document.createElement("ul");
  list.className = "evidence-list";
  for (const word of evidences) {
    const item = document.createElement("li");
    item.textContent = word;
    list.append(item);
  }
  section.append(list);
  return section;
}

function createResultCard(title, sentiment) {
  const card = document.createElement("article");
  card.className = "result-card";
  const header = document.createElement("div");
  header.className = "result-card-header";
  const heading = document.createElement("h3");
  heading.textContent = title;
  header.append(heading);
  if (sentiment) header.append(createSentimentIndicator(sentiment));
  card.append(header);
  return card;
}

function createClassicComparisonCard(classic) {
  const card = createResultCard("Análise clássica", classic.sentimento);
  card.append(
    createScore(classic),
    createEvidenceSection(classic.evidencias, "h4"),
  );
  return card;
}

function createLlmComparisonCard(llm) {
  const card = createResultCard(`Análise com ${providerName}`, hasLlmError(llm) ? null : llm.sentimento);
  if (hasLlmError(llm)) {
    const error = document.createElement("p");
    error.className = "result-error";
    error.textContent = `${providerName} indisponível nesta análise.`;

    const details = document.createElement("details");
    details.className = "error-details";
    const summary = document.createElement("summary");
    summary.textContent = "Detalhes do erro";
    const message = document.createElement("p");
    message.textContent = llm.erro;
    details.append(summary, message);
    card.append(error, details);
    return card;
  }

  const details = document.createElement("dl");
  details.className = "result-details";
  if (llm.modelo.trim()) appendDetail(details, "Modelo", llm.modelo);
  appendDetail(
    details,
    "Justificativa",
    llm.justificativa.trim() ? llm.justificativa : "Justificativa não retornada.",
  );
  card.append(details);
  return card;
}

function renderResults(body, mode) {
  const result = body.resultados[0];
  const classic = result.classico;

  if (mode === "classico") {
    const hero = document.createElement("article");
    hero.className = "result-hero";
    const header = document.createElement("div");
    header.className = "result-card-header";
    const heading = document.createElement("h3");
    heading.textContent = "Sentimento identificado";
    const method = document.createElement("p");
    method.className = "result-method";
    method.textContent = "Análise clássica · Léxico";
    header.append(heading, createSentimentIndicator(classic.sentimento), method);
    hero.append(header, createScore(classic));

    resultContent.classList.remove("is-comparing");
    resultContent.replaceChildren(hero, createEvidenceSection(classic.evidencias, "h3"));
    setAnalysisStatus(
      `Análise clássica concluída: sentimento ${sentimentLabel(classic.sentimento)}.`,
      "success",
    );
    return;
  }

  const summary = document.createElement("p");
  summary.className = "result-summary";
  if (result.concordam === true) {
    summary.textContent = "Os métodos concordam";
  } else if (result.concordam === false) {
    summary.classList.add("is-different");
    summary.textContent = "Os métodos divergem";
  } else {
    summary.classList.add("is-unavailable");
    summary.textContent = "Comparação indisponível";
  }

  const comparison = document.createElement("div");
  comparison.className = "result-comparison";
  comparison.append(
    createClassicComparisonCard(classic),
    createLlmComparisonCard(result.llm),
  );
  resultContent.classList.add("is-comparing");
  resultContent.replaceChildren(summary, comparison);

  if (result.concordam === null) {
    setAnalysisStatus(`Análise clássica concluída; ${providerName} indisponível nesta análise.`, "success");
  } else {
    setAnalysisStatus(
      result.concordam
        ? "Comparação concluída. Os métodos concordam."
        : "Comparação concluída. Os métodos divergem.",
      "success",
    );
  }
}

function setBusy(busy) {
  analysisInProgress = busy;
  textarea.disabled = busy;
  exampleButton.disabled = busy;
  modeOptions.disabled = busy;
  analyzeButton.disabled = busy;
  analyzeButton.classList.toggle("is-loading", busy);
  resultContent.setAttribute("aria-busy", String(busy));
  analyzeButtonLabel.textContent = busy ? "Analisando…" : "Analisar";
}

textarea.addEventListener("input", () => {
  const length = updateCharacterCount();
  if (textValidationAttempted) validateText(textarea.value, length);
  else setFormError("");
});

form.addEventListener("change", (event) => {
  if (event.target.name === "modo") updateModeGuidance();
});

exampleButton.addEventListener("click", () => {
  textarea.value = "O produto é excelente e eu recomendo.";
  updateCharacterCount();
  setFormError("");
  textarea.focus();
});


form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (analysisInProgress) return;

  const text = textarea.value;
  const length = updateCharacterCount();
  textValidationAttempted = true;
  if (!validateText(text, length)) {
    textarea.focus();
    return;
  }

  const mode = selectedMode();
  if (mode === "comparar" && healthChecking) {
    setFormError("A disponibilidade do modelo ainda está sendo verificada. Aguarde e tente novamente.");
    return;
  }
  if (mode === "comparar" && !comparisonAvailable) {
    setFormError("A comparação não está disponível. Verifique a conexão.");
    return;
  }

  setFormError("");
  clearResults();
  setAnalysisStatus("Analisando a avaliação…", "loading");
  setBusy(true);
  try {
    let response;
    try {
      response = await fetch("/analisar", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ modo: mode, mensagens: [{ texto: text }] }),
        cache: "no-store",
        credentials: "omit",
      });
    } catch (error) {
      setAnalysisStatus(
        "Não foi possível conectar ao backend. Verifique a conexão e tente novamente.",
        "error",
      );
      showAnalysisErrorDetails(error instanceof Error ? error.message : "");
      return;
    }

    let body;
    try {
      body = await response.json();
    } catch {
      showAnalysisErrorDetails(
        response.ok ? "Resposta inválida do backend." : `Não foi possível analisar (HTTP ${response.status}).`,
      );
      setAnalysisStatus("Não foi possível concluir a análise. Tente novamente.", "error");
      return;
    }

    if (!response.ok) {
      const message = body && typeof body.erro === "string" && body.erro.trim()
        ? body.erro
        : `Não foi possível analisar (HTTP ${response.status}).`;
      showAnalysisErrorDetails(message);
      setAnalysisStatus("Não foi possível concluir a análise. Tente novamente.", "error");
      return;
    }
    if (!isValidResult(body, mode)) {
      showAnalysisErrorDetails("Resposta inválida do backend.");
      setAnalysisStatus("Não foi possível concluir a análise. Tente novamente.", "error");
      return;
    }
    renderResults(body, mode);
  } catch {
    showAnalysisErrorDetails("Não foi possível analisar o texto.");
    setAnalysisStatus("Não foi possível concluir a análise. Tente novamente.", "error");
  } finally {
    setBusy(false);
  }
});

updateCharacterCount();
updateModeGuidance();
checkHealth();
