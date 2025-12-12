from flask import Flask, request, jsonify, send_from_directory
import requests
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from collections import defaultdict
import os
from gtts import gTTS # Free Google TTS

app = Flask(__name__)

OPENWEATHER_API_KEY = ""
account_sid = ""
auth_token = ""
twilio_voice_number = ""
twilio_whatsapp_number = ""
client = Client(account_sid, auth_token)

# --- Generate Marathi Audio using gTTS (with file reuse) ---
def generate_marathi_audio(text, filename="marathi_weather.mp3"):
    # Remove emojis before generating audio
    clean_text = text.replace("🌾", "").replace("🌱", "").replace("🌻", "")
    
    # Check if file already exists - REUSE if available
    os.makedirs("static", exist_ok=True)
    filepath = os.path.join("static", filename)
    
    if not os.path.exists(filepath):
        print(f"Generating new audio file: {filepath}")
        tts = gTTS(text=clean_text, lang="mr")
        tts.save(filepath)
        print(f"✅ Generated audio: {filepath}")
    else:
        print(f"✅ Reusing existing audio: {filepath}")
    
    return f"/audio/{filename}"

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory("static", filename)

# --- Pre-generate Marathi audio at startup ---
def pregenerate_marathi_audio():
    city = "Aurangabad"  # Default city
    try:
        print("🚀 Pre-generating Marathi audio for Aurangabad at startup...")
        forecast_voice, _, _ = build_forecast(city, "mr")
        generate_marathi_audio(forecast_voice)
        print("✅ Marathi audio pre-generation complete!")
    except Exception as e:
        print(f"❌ Failed to pre-generate Marathi audio: {e}")

# --- Weather + Crop Tips Generator ---
def build_forecast(city, language="en"):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    # Translation dictionary for weather conditions (lowercase keys)
    condition_translations = {
        "clear sky": {"hi": "साफ आसमान", "mr": "स्वच्छ आकाश"},
        "few clouds": {"hi": "थोड़े बादल", "mr": "थोडेसे ढग"},
        "scattered clouds": {"hi": "बिखरे बादल", "mr": "विखुरलेले ढग"},
        "broken clouds": {"hi": "टूटे हुए बादल", "mr": "तुटलेले ढग"},
        "overcast clouds": {"hi": "घने बादल", "mr": "दाट ढग"},
        "shower rain": {"hi": "बौछार बारिश", "mr": "धारा पाऊस"},
        "light rain": {"hi": "हल्की बारिश", "mr": "हलका पाऊस"},
        "moderate rain": {"hi": "मध्यम बारिश", "mr": "मध्यम पाऊस"},
        "heavy intensity rain": {"hi": "तेज़ बारिश", "mr": "जोरदार पाऊस"},
        "rain": {"hi": "बारिश", "mr": "पाऊस"},
        "thunderstorm": {"hi": "आंधी-तूफान", "mr": "वादळ"},
        "snow": {"hi": "बर्फबारी", "mr": "हिमवर्षाव"},
        "mist": {"hi": "कोहरा", "mr": "धुके"},
        "haze": {"hi": "धुंध", "mr": "धूसरता"},
        "fog": {"hi": "कोहरा", "mr": "धुके"},
        "drizzle": {"hi": "फुहार", "mr": "रिमझिम"}
    }

    forecast_by_day = defaultdict(list)
    for entry in data["list"][:24]: # next 3 days
        date = entry["dt_txt"].split(" ")[0]
        temp = entry["main"]["temp"]
        # normalize to lowercase to match dictionary keys
        condition = entry["weather"][0]["description"].lower()
        pop = entry.get("pop", 0) * 100

        # Translate condition for Hindi/Marathi if available
        if language in ["hi", "mr"]:
            translated = condition_translations.get(condition, {}).get(language)
            if translated:
                condition = translated

        forecast_by_day[date].append((temp, condition, pop))

    forecast_details = []
    for date, values in forecast_by_day.items():
        avg_temp = sum(v[0] for v in values) / len(values)
        avg_pop = sum(v[2] for v in values) / len(values)
        # Most frequent condition of the day
        condition = max(set(v[1] for v in values), key=[v[1] for v in values].count)
        forecast_details.append((date, condition, avg_temp, avg_pop))

    if language == "hi":
        forecast_voice = f"{city} के लिए आगामी 3 दिनों का मौसम पूर्वानुमान:\n"
        forecast_whatsapp = f"*{city} के लिए आगामी 3 दिनों का मौसम पूर्वानुमान:*\n"
        for date, condition, avg_temp, avg_pop in forecast_details:
            forecast_voice += f"{date}: {condition}, औसत तापमान {avg_temp:.1f}°C, वर्षा संभावना {avg_pop:.0f}%\n"
            forecast_whatsapp += f"{date}: {condition}, औसत तापमान {avg_temp:.1f}°C, वर्षा संभावना {avg_pop:.0f}%\n"

        crop_tips_voice = (
            "अब हम आपको फसल के रखरखाव पर सलाह देते हैं। "
            "अनाज: जड़ आरंभ और फूल आने पर सिंचाई करें। "
            "दलहन: पाले से बचाव हेतु हल्की सिंचाई करें। "
            "तिलहन: फूल आने पर मिट्टी में नमी बनाए रखें।"
        )
        crop_tips_whatsapp = (
            "*अब हम आपको फसल के रखरखाव पर सलाह देते हैं।*\n\n"
            "🌾 अनाज:\n- जड़ आरंभ और फूल आने पर सिंचाई करें।\n"
            "🌱 दलहन:\n- पाले से बचाव हेतु हल्की सिंचाई करें।\n"
            "🌻 तिलहन:\n- फूल आने पर मिट्टी में नमी बनाए रखें।"
        )

        return forecast_voice + "\n" + crop_tips_voice, forecast_whatsapp + "\n" + crop_tips_whatsapp, "hi-IN"

    elif language == "mr":
        forecast_voice = f"{city} साठी पुढील ३ दिवसांचा हवामान अंदाज:\n"
        forecast_whatsapp = f"*{city} साठी पुढील ३ दिवसांचा हवामान अंदाज:*\n"
        for date, condition, avg_temp, avg_pop in forecast_details:
            forecast_voice += f"{date}: {condition}, सरासरी तापमान {avg_temp:.1f}°C, पावसाची शक्यता {avg_pop:.0f}%\n"
            forecast_whatsapp += f"{date}: {condition}, सरासरी तापमान {avg_temp:.1f}°C, पावसाची शक्यता {avg_pop:.0f}%\n"

        crop_tips_voice = (
            "आता आम्ही तुम्हाला पिकांच्या देखभालीबद्दल सल्ला देतो. "
            "धान्य: मुळांच्या वाढीच्या वेळी सिंचन करा. "
            "कडधान्य: थंडीपासून बचावासाठी हलके सिंचन करा. "
            "तेलबिया: फुलांच्या वेळी जमिनीत ओलावा ठेवा."
        )
        crop_tips_whatsapp = (
            "*आता आम्ही तुम्हाला पिकांच्या देखभालीबद्दल सल्ला देतो.*\n\n"
            "🌾 धान्य:\n- मुळांच्या वाढीच्या वेळी सिंचन करा.\n"
            "🌱 कडधान्य:\n- थंडीपासून बचावासाठी हलके सिंचन करा.\n"
            "🌻 तेलबिया:\n- फुलांच्या वेळी जमिनीत ओलावा ठेवा."
        )

        return forecast_voice + "\n" + crop_tips_voice, forecast_whatsapp + "\n" + crop_tips_whatsapp, "mr-IN"

    else:
        forecast_voice = f"Weather forecast for {city} (next 3 days):\n"
        forecast_whatsapp = f"*Weather forecast for {city} (next 3 days):*\n"
        for date, condition, avg_temp, avg_pop in forecast_details:
            forecast_voice += f"{date}: {condition}, Avg Temp {avg_temp:.1f}°C, Rain chance {avg_pop:.0f}%\n"
            forecast_whatsapp += f"{date}: {condition}, Avg Temp {avg_temp:.1f}°C, Rain chance {avg_pop:.0f}%\n"

        crop_tips_voice = (
            "Now we will give you advice on crop maintaining. "
            "Cereals: Irrigate at crown root initiation. "
            "Pulses: Protect from frost with light irrigation. "
            "Oilseeds: Maintain soil moisture at flowering."
        )
        crop_tips_whatsapp = (
            "*Now we will give you advice on crop maintaining.*\n\n"
            "🌾 Cereals:\n- Irrigate at crown root initiation.\n"
            "🌱 Pulses:\n- Protect from frost with light irrigation.\n"
            "🌻 Oilseeds:\n- Maintain soil moisture at flowering."
        )

        return forecast_voice + "\n" + crop_tips_voice, forecast_whatsapp + "\n" + crop_tips_whatsapp, "en-IN"

# --- RUN PRE-GENERATION at startup ---
pregenerate_marathi_audio()

# --- Initial Greeting Route ---
@app.route("/voice", methods=["GET", "POST"])
def voice():
    resp = VoiceResponse()
    gather = Gather(num_digits=1, action="/handle-language", method="POST", language="hi-IN")
    gather.say("यह कॉल XYZ कंपनी से है, आपको मौसम की जानकारी देने के लिए। अंग्रेज़ी के लिए 1 दबाएँ, हिंदी के लिए 2 दबाएँ, मराठी के लिए 3 दबाएँ।", language="hi-IN")
    resp.append(gather)
    resp.redirect("/voice") # repeat if no input
    return str(resp)

# --- Handle Language Choice ---
@app.route("/handle-language", methods=["POST"])
def handle_language():
    digits = request.values.get("Digits", None)
    city = "Aurangabad" # can be dynamic later
    resp = VoiceResponse()

    if digits == "1":
        forecast_voice, forecast_whatsapp, twilio_lang = build_forecast(city, "en")
        resp.say(forecast_voice, language=twilio_lang)
    elif digits == "2":
        forecast_voice, forecast_whatsapp, twilio_lang = build_forecast(city, "hi")
        resp.say(forecast_voice, language=twilio_lang)
    elif digits == "3":
        forecast_voice, forecast_whatsapp, twilio_lang = build_forecast(city, "mr")
        audio_path = generate_marathi_audio(forecast_voice)
        resp.play(request.url_root + audio_path.lstrip("/"))
    else:
        resp.say("अमान्य विकल्प। कृपया फिर से प्रयास करें।", language="hi-IN")
        resp.redirect("/voice")

    return str(resp)

# --- WhatsApp Alert + Automatic Call ---
@app.route("/weather_alert", methods=["POST"])
def weather_alert():
    try:
        req_data = request.get_json(silent=True)
        language = req_data.get("sessionInfo", {}).get("parameters", {}).get("language", "en")
        city = req_data.get("sessionInfo", {}).get("parameters", {}).get("city", "Aurangabad")

        forecast_voice, forecast_whatsapp, twilio_lang = build_forecast(city, language)

        # Pre-generate audio for Marathi if requested (for next call)
        if language == "mr":
            safe_city = city.replace(" ", "_").lower()  # Make filename safe
            generate_marathi_audio(forecast_voice, filename=f"marathi_weather_{safe_city}.mp3")

        farmer_numbers = [""] # Example numbers. These numbers much be verified in Twilio sandbox first
        for number in farmer_numbers:
            # WhatsApp message
            client.messages.create(
                from_=twilio_whatsapp_number,
                body=forecast_whatsapp,
                to=f"whatsapp:{number}"
            )

            # Automatic outbound call
            call = client.calls.create(
                url=request.url_root + "voice", # points to /voice route
                to=number,
                from_=twilio_voice_number
            )
            print("Call SID:", call.sid)

        return jsonify({
            "fulfillment_response": {
                "messages": [
                    {"text": {"text": [forecast_whatsapp]}}
                ]
            }
        })

    except Exception as e:
        return jsonify({
            "fulfillment_response": {
                "messages": [
                    {"text": {"text": [f"Error occurred: {str(e)}"]}}
                ]
            }
        }), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
