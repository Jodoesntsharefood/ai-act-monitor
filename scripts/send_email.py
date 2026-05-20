import json, os, re
import requests

with open("check_result.json") as f:
    result = json.load(f)

subject = result.get("email_subject", "AI Act 标准变化通知")
body_text = result.get("email_body", "") or "这是一封测试邮件，监控脚本运行正常。"

# 纯文本转简单 HTML，保留结构
def text_to_html(text):
    lines = text.split("\n")
    html = []
    for line in lines:
        line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
        if not line.strip():
            html.append("<br>")
        elif line.startswith("# "):
            html.append(f"<h2>{line[2:]}</h2>")
        elif line.startswith("## "):
            html.append(f"<h3>{line[3:]}</h3>")
        elif line.startswith("---"):
            html.append("<hr>")
        elif line.startswith("- "):
            html.append(f"<p>• {line[2:]}</p>")
        else:
            html.append(f"<p>{line}</p>")
    return "\n".join(html)

html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 14px; color: #000; background: #fff; padding: 24px; }}
  h2 {{ font-size: 18px; }}
  h3 {{ font-size: 15px; margin-top: 20px; }}
  p {{ margin: 4px 0; line-height: 1.6; }}
  hr {{ border: none; border-top: 1px solid #ccc; margin: 16px 0; }}
</style>
</head>
<body>
{text_to_html(body_text)}
<hr>
<p><a href="https://ai-act-standards.com/">查看完整标准地图</a></p>
</body>
</html>"""

payload = {
    "from": "AI Act Monitor <onboarding@resend.dev>",
    "to": os.environ["NOTIFY_EMAIL"].split(","),
    "subject": subject,
    "html": html_body,
}

response = requests.post(
    "https://api.resend.com/emails",
    headers={
        "Authorization": "Bearer " + os.environ["RESEND_API_KEY"],
        "Content-Type": "application/json",
    },
    json=payload,
)

print(response.status_code)
print(response.text)

if response.status_code != 200:
    raise Exception(f"Failed to send email: {response.text}")
