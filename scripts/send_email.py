import json, os, urllib.request, urllib.error

with open("check_result.json") as f:
    result = json.load(f)

subject = result.get("email_subject", "AI Act 标准变化通知")
body_text = result.get("email_body", "")

payload = json.dumps({
    "from": "AI Act Monitor <onboarding@resend.dev>",
    "to": [os.environ["TO_EMAILS"]],
    "subject": subject,
    "text": body_text,
}).encode()

req = urllib.request.Request(
    "https://api.resend.com/emails",
    data=payload,
    headers={
        "Authorization": "Bearer " + os.environ["RESEND_API_KEY"],
        "Content-Type": "application/json",
    },
)
try:
    with urllib.request.urlopen(req) as resp:
        print("Email sent:", resp.read().decode())
except urllib.error.HTTPError as e:
    print("Failed:", e.code, e.read().decode())
    raise
print("Sending to:", os.environ["NOTIFY_EMAIL"])
print("API Key prefix:", os.environ["RESEND_API_KEY"][:8])  # 只打印前8位
