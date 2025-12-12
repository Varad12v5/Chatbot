# Dialogflow Chatbot (Weather + Marathi TTS)

Small Flask app that generates a 3‑day weather forecast and offers Marathi audio via gTTS. This repo contains the webhook and helper code used to send WhatsApp messages and make outbound calls (Twilio integration).

## Requirements
- Python 3.8+
- See `requirements.txt`

## Install

Windows example:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Credentials

The app expects API credentials to be provided via environment variables or a `credentials.txt` file (KEY=VALUE lines). Provide the following keys:

- `OPENWEATHER_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_VOICE_NUMBER` (optional)
- `TWILIO_WHATSAPP_NUMBER` (optional)

Example environment (Windows PowerShell):

```powershell
$env:OPENWEATHER_API_KEY = "your_openweather_key"
$env:TWILIO_ACCOUNT_SID = "your_twilio_sid"
$env:TWILIO_AUTH_TOKEN = "your_twilio_token"
```

Or create `credentials.txt` next to `app.py` with lines like:

```
OPENWEATHER_API_KEY=your_openweather_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
```

> Important: Do NOT commit real secret values. Add `credentials.txt` to `.gitignore` if you create it.

## Run

```powershell
python app.py
```

The app listens on port 5000 by default (`http://127.0.0.1:5000`).

## Exposing your local server with ngrok

ngrok lets you expose your local server to the public internet — useful for testing webhooks (Dialogflow, Twilio). When you run ngrok it creates a public URL that forwards requests to your local port.

1. Install ngrok: download from https://ngrok.com/download and unzip.

2. (Optional) Connect your account to get a persistent auth token:

```powershell
ngrok.exe authtoken <YOUR_NGROK_AUTHTOKEN>
```

3. Start ngrok to forward port 5000 (PowerShell):

```powershell
# expose localhost:5000
ngrok.exe http 5000
```

4. ngrok prints a public URL like `https://abcd1234.ngrok.io`. Use that as your webhook base URL. For example, set your Dialogflow/Twilio webhook to:

```
https://abcd1234.ngrok.io/weather_alert
https://abcd1234.ngrok.io/voice
```

Notes and tips:
- The free ngrok URL changes each session. If you need a stable subdomain, upgrade your ngrok plan.
- Use `ngrok http 5000 --region=in` to pick a nearby region (example: `in` for India).
- The ngrok web inspector runs at `http://127.0.0.1:4040` — use it to view request/response traffic and replay requests.
- Keep ngrok running while testing webhooks; if it stops, update webhook URLs to the new public URL.

## Security
- Never commit API keys or tokens. Use environment variables or an ignored `credentials.txt`.
- Generated audio files are stored under `static/` — you may want to add `static/*.mp3` to `.gitignore`.

## Troubleshooting
- If outbound Twilio calls fail, ensure `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are set and Twilio numbers are verified.
- If weather API calls fail, verify `OPENWEATHER_API_KEY` and check request limits.

