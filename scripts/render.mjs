// Fills {{PLACEHOLDERS}} in an email template. No dependencies (Node 18+).
//
//   CLI preview:  node scripts/render.mjs --preview
//   In your server: import { renderEmail } from "./scripts/render.mjs";
//
// renderEmail() REFUSES to render if a placeholder is left unfilled or if the
// action link is not an https URL, so a dummy "#" link can never be sent.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const escapeAttr = (v) =>
  String(v).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export function renderEmail(templateName, vars, { allowSampleLink = false } = {}) {
  const html = readFileSync(join(ROOT, "emails", `${templateName}.html`), "utf8");
  const link = vars.VERIFICATION_LINK ?? vars.RESET_LINK;
  const base = vars.ASSET_BASE_URL;

  if (!allowSampleLink) {
    let u;
    try { u = new URL(link); } catch { throw new Error("Action link is missing or not a valid URL"); }
    if (u.protocol !== "https:") throw new Error("Action link must be https");
  }
  if (!base || !/^https:\/\//.test(base)) throw new Error("ASSET_BASE_URL must be an https URL");

  const out = html.replace(/\{\{([A-Z_]+)\}\}/g, (_, key) => {
    if (!(key in vars)) throw new Error(`Missing value for {{${key}}}`);
    return escapeAttr(vars[key]);
  });
  return out;
}

// Plain-text alternative (no HTML escaping; same https/placeholder guards).
export function renderText(templateName, vars, { allowSampleLink = false } = {}) {
  const txt = readFileSync(join(ROOT, "emails", `${templateName}.txt`), "utf8");
  const link = vars.VERIFICATION_LINK ?? vars.RESET_LINK;
  if (!allowSampleLink) {
    let u;
    try { u = new URL(link); } catch { throw new Error("Action link is missing or not a valid URL"); }
    if (u.protocol !== "https:") throw new Error("Action link must be https");
  }
  return txt.replace(/\{\{([A-Z_]+)\}\}/g, (_, key) => {
    if (!(key in vars)) throw new Error(`Missing value for {{${key}}}`);
    return String(vars[key]);
  });
}

// Convenience: both parts to hand to your email provider as { html, text }.
export function renderEmailParts(templateName, vars, opts) {
  return { html: renderEmail(templateName, vars, opts), text: renderText(templateName, vars, opts) };
}

// ---- local preview build (sample values only; NOT for sending) ----
if (process.argv.includes("--preview")) {
  mkdirSync(join(ROOT, "preview"), { recursive: true });
  const sample = "https://example.com/__/auth/action?mode=SAMPLE&oobCode=PREVIEW_ONLY";
  const jobs = [
    ["verify-email", { VERIFICATION_LINK: sample }],
    ["reset-password", { RESET_LINK: sample }],
  ];
  for (const [name, v] of jobs) {
    // Preview loads images from the local assets folder instead of a CDN.
    const html = renderEmail(name, { ...v, ASSET_BASE_URL: "https://placeholder.invalid" }, { allowSampleLink: true })
      .replaceAll("https://placeholder.invalid", "../emails/assets");
    writeFileSync(join(ROOT, "preview", `${name}.rendered.html`), html);
    writeFileSync(join(ROOT, "preview", `${name}.rendered.txt`), renderText(name, { ...v }, { allowSampleLink: true }));
    console.log("wrote preview/" + name + ".rendered.html + .txt");
  }
}
