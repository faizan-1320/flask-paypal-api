from flask import Blueprint,request,jsonify
import vonage
import os

sms_bp = Blueprint("sms", __name__)


@sms_bp.post("/send-message")
def send_message():
    client = vonage.Client(key=os.environ['SMS_API_KEY'], secret=os.environ['SMS_API_SECRET'])
    sms = vonage.Sms(client)
    data = request.json
    if not data.get("mobile_number"):
        return jsonify({"error":"Please Enter Mobile Number"}),400
    responseData = sms.send_message(
        {
            "from": "Vonage APIs",
            "to": data.get("mobile_number"),
            "text": "A text message sent using the Nexmo SMS API",
        }
    )


    if responseData["messages"][0]["status"] == "0":
        print("Message sent successfully.")
    else:
        print(
            f"Message failed with error: {responseData['messages'][0]['error-text']}")
