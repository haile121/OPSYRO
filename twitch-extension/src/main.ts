/// <reference types="vite/client" />
import "./style.css";

interface TwitchAuth { token: string; userId: string; channelId: string; clientId: string; }
interface TwitchExtension { onAuthorized(callback: (auth: TwitchAuth) => void): void; }
declare global { interface Window { Twitch?: { ext?: TwitchExtension }; } }


const root = document.querySelector<HTMLElement>("#app")!;
const apiUrl = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");
let extensionToken = "";
let sessionToken = "";
let participantKey = sessionStorage.getItem("opsyro-extension-participant") || crypto.randomUUID();
sessionStorage.setItem("opsyro-extension-participant", participantKey);

function escapeHtml(value: string) { return value.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!); }
function showMessage(message: string) { root.innerHTML = `<section class="notice"><a class="brand" href="#">◢ OPSYRO</a><p>${escapeHtml(message)}</p><small>Audience curiosity, made visible.</small></section>`; }
function showForm(title: string) {
  root.innerHTML = `<header><a class="brand" href="#">◢ OPSYRO</a><span class="live"><i></i> LIVE SESSION</span></header><section class="intro"><p class="eyebrow">WHAT CAUGHT YOUR ATTENTION?</p><h1>${escapeHtml(title)}</h1><p>Tap the part of the experience you want to understand.</p></section><button class="media" type="button" aria-label="Select the area that caught your attention"><span class="crosshair"></span><small>Tap to mark a region</small></button><fieldset><legend>What kind of signal?</legend><div class="choices"><button type="button" aria-pressed="true" data-intent="curious">Curious</button><button type="button" aria-pressed="false" data-intent="confused">Unclear</button><button type="button" aria-pressed="false" data-intent="question">Ask a question</button></div></fieldset><label class="question-label" for="question">Ask a question <span>optional</span></label><textarea id="question" rows="2" maxlength="240" placeholder="What would you like to understand?"></textarea><button id="submit" class="submit">Send signal</button><p id="status" class="status" role="status">Your signal is shared without your Twitch username.</p>`;
  const media = root.querySelector<HTMLButtonElement>(".media")!;
  let x = .5, y = .5, selected = false;
  media.addEventListener("click", (event) => { const rect = media.getBoundingClientRect(); x = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width)); y = Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height)); selected = true; const marker = media.querySelector<HTMLElement>(".crosshair")!; marker.style.left = `${x * 100}%`; marker.style.top = `${y * 100}%`; marker.classList.add("selected"); media.querySelector("small")!.textContent = "Region selected"; });
  let intent = "curious";
  root.querySelectorAll<HTMLButtonElement>("[data-intent]").forEach((button) => button.addEventListener("click", () => { intent = button.dataset.intent || "curious"; root.querySelectorAll("[data-intent]").forEach((node) => node.setAttribute("aria-pressed", String(node === button))); }));
  root.querySelector<HTMLButtonElement>("#submit")!.addEventListener("click", async () => {
    const send = root.querySelector<HTMLButtonElement>("#submit")!;
    const status = root.querySelector<HTMLElement>("#status")!;
    send.disabled = true; status.textContent = "Sending…";
    try {
      const response = await fetch(`${apiUrl}/api/signals/`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_token: sessionToken, participant_key: participantKey, idempotency_key: crypto.randomUUID(), region_x: x.toFixed(4), region_y: y.toFixed(4), region_key: selected ? `extension-${Math.floor(x * 10)}-${Math.floor(y * 10)}` : "extension-general", intent, question: root.querySelector<HTMLTextAreaElement>("#question")!.value.trim() }) });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || "The signal could not be saved.");
      showMessage("Your signal was saved. Thanks for helping make this moment clearer.");
    } catch (error) { status.textContent = error instanceof Error ? error.message : "The signal could not be saved."; send.disabled = false; }
  });
}

async function authorize(auth: TwitchAuth) {
  extensionToken = auth.token;
  try {
    const response = await fetch(`${apiUrl}/api/twitch/extension/session/`, { method: "POST", headers: { "X-Twitch-Extension-Jwt": extensionToken } });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "No live OPSYRO session is configured for this channel.");
    const firstAuthorization = !sessionToken;
    sessionToken = body.session_token;
    if (firstAuthorization) showForm(body.title);
  } catch (error) { showMessage(error instanceof Error ? error.message : "Twitch authorization could not be checked."); }
}

if (window.Twitch?.ext) window.Twitch.ext.onAuthorized(authorize);
else showMessage("This viewer panel must be opened inside a configured Twitch Extension. For local preview, use the OPSYRO demo site.");




