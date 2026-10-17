# Paw QUIZ – email templates

Table-based HTML with inline CSS, built for email clients. Two templates:

| File | Purpose | Placeholders |
|---|---|---|
| `emails/verify-email.html` + `.txt` | Verify email address | `{{VERIFICATION_LINK}}`, `{{ASSET_BASE_URL}}` |
| `emails/reset-password.html` + `.txt` | Reset password | `{{RESET_LINK}}`, `{{ASSET_BASE_URL}}` |

> The reset-password **copy is my own wording** (you only specified the verify email). Edit it freely.

## Preview locally

```bash
node scripts/render.mjs --preview     # fills sample values into preview/*.rendered.html
open preview/index.html               # or just double-click it
```

`preview/index.html` has toggles for Verify / Reset and Mobile (390) / Tablet / Desktop widths.
The preview uses a **sample link that goes nowhere** – it exists only so the button renders.

## Layout tests

```bash
pip install playwright && playwright install chromium
python3 scripts/layout-test.py        # screenshots land in test-output/
```

This checks both templates in headless Chromium at 360, 390, 768 and 1280 px:
no horizontal scroll, card fits the viewport and is ≤ 600 px, all images load,
button is ≥ 44 px tall. **This tests layout in Chromium only – not real email clients** (see "Not yet tested").

## Host the images

Email clients load images from public URLs. `localhost`, `file://` and base64 `data:` images
do not work reliably (Gmail strips data URIs).

1. Upload the two files in `emails/assets/` to any public **HTTPS** location
   (Firebase Hosting, Cloud Storage public bucket, S3/CloudFront, your own domain):
   - `paw-quiz-mascot.jpg`
   - `hero-cat.jpg`
2. Pass the folder URL as `ASSET_BASE_URL`, e.g. `https://yourdomain.com/email-assets`
   (no trailing slash). Keep file names unchanged, and don't edit them in place once emails are
   sent – old emails keep pointing at those URLs.

Firebase Hosting example: put the files in `public/email-assets/`, run `firebase deploy --only hosting`.

## About the image files

- **Mascot** (`paw-quiz-mascot.jpg`): your orange-and-white cat from the clean file, trimmed of the
  black strip at its bottom edge and scaled down. Not redrawn.
- **Hero cat** (`hero-cat.jpg`): the image you attached as the official hero. Kept at full size
  (1080 px wide) with its original aspect ratio, not redrawn. The only change from your file is that
  the 9 black pixel rows at the bottom edge (a screenshot artifact, rows 1088-1096) are removed so no
  black line shows in the email. Your untouched file is in `emails/assets/originals/hero-cat-original.jpg`.
  **Note:** this file is byte-identical to the file used for the logo (the orange tabby cat with a
  pink envelope), so the logo and hero show the same cat. It is *not* the flat orange cat from the
  reference screenshot. To swap in a different image later: `python3 scripts/set-hero.py /path/to/file`.
- Neither image has a transparent background; both sit on white, which matches the card.

## Firebase integration (what is required to send real emails)

Firebase's built-in verification/reset emails only allow limited template edits in the console,
so custom HTML means **you send the email yourself**, using a link Firebase generates:

```
Your server ──(Firebase Admin SDK)──> generateEmailVerificationLink(email, actionCodeSettings)
            ──> fill template via renderEmail() ──> email provider API ──> user's inbox
```

You need:

1. **A server/Cloud Function** with Firebase Admin credentials (service account). These stay on the
   server – never in client code, the repo, or these templates.
2. **An email provider** (Resend, SendGrid, Postmark, Amazon SES, or your own SMTP) with its API key
   in server environment variables / Secret Manager, and a **verified sending domain**
   (SPF, DKIM, DMARC) – otherwise mail will land in spam.
3. **An action-link destination.** Set `actionCodeSettings.url` to a page in your app, and make sure
   its domain is in Firebase Console → Authentication → Settings → Authorized domains.
   The generated link opens Firebase's hosted action handler (or your custom one, if you configured it).
4. **Authorization on the endpoint** that triggers sending (e.g. require the signed-in user's ID token),
   and rate limiting, so it can't be used to spam arbitrary addresses.

Sketch (**untested illustration, not production code**):

```js
import { getAuth } from "firebase-admin/auth";
import { renderEmail } from "./scripts/render.mjs";

const link = await getAuth().generateEmailVerificationLink(email, {
  url: "https://yourapp.com/login?verified=1",
});
const html = renderEmail("verify-email", {
  VERIFICATION_LINK: link,
  ASSET_BASE_URL: process.env.EMAIL_ASSET_BASE_URL,
});
// await yourProvider.send({ to: email, subject: "Verify your Paw QUIZ email", html, text: "..." });
// Password reset: generatePasswordResetLink(email, ...) + renderEmail("reset-password", { RESET_LINK, ... })
```

`renderEmail()` throws if the link is missing or not `https`, or if any placeholder is left unfilled,
so a dummy link can't be sent by accident. It also HTML-escapes the values it inserts.

Every email also has a **plain-text alternative** (`emails/verify-email.txt`, `emails/reset-password.txt`).
Send both parts (multipart/alternative) - improves deliverability and accessibility:

```js
import { renderEmailParts } from "./scripts/render.mjs";
const { html, text } = renderEmailParts("verify-email", { VERIFICATION_LINK: link, ASSET_BASE_URL: base });
```

## Not yet tested

- **No email has been sent.** Delivery, Firebase link generation and provider setup are not configured here.
- **Real email clients** (Gmail, Apple Mail, Outlook desktop/web, Yahoo, dark mode) have not been tested.
  The Outlook button uses a VML fallback written to the standard pattern but **unverified** –
  test with Litmus / Email on Acid or send to real inboxes before launch.
- The 🐾 in the heading is a text emoji, so its look varies by device.

## Files

```
emails/verify-email.html/.txt, reset-password.html/.txt
emails/assets/paw-quiz-mascot.jpg, hero-cat.jpg
preview/index.html (+ generated *.rendered.html)
scripts/render.mjs, layout-test.py, set-hero.py
test-output/  screenshots + results.json
```
