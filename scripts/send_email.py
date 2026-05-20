import json, os
import requests

with open("check_result.json") as f:
    result = json.load(f)

subject = result.get("email_subject", "AI Act 标准变化通知")
body_text = result.get("email_body", "") or "这是一封测试邮件，监控脚本运行正常。"

payload = {
    "from": "AI Act Monitor <onboarding@resend.dev>",
    "to": os.environ["NOTIFY_EMAIL"].split(","),
    "subject": subject,
    "text": body_text,
}

headers = {
    "Authorization": "Bearer " + os.environ["RESEND_API_KEY"],
    "Content-Type": "application/json",
}

response = requests.post(
    "https://api.resend.com/emails",
    headers=headers,
    json=payload,
)

print(response.status_code)
print(response.text)

if response.status_code != 200:
    raise Exception(f"Failed to send email: {response.text}")
