import json, os
import requests

with open("check_result.json") as f:
    result = json.load(f)

subject = result.get("email_subject", "AI Act 标准变化通知")
body_text = result.get("email_body", "") or "这是一封测试邮件，监控脚本运行正常。"

# 把纯文本正文转成 HTML（保留换行和加粗）
def text_to_html(text: str) -> str:
    lines = text.split("\n")
    html_lines = []
    for line in lines:
        if not line.strip():
            html_lines.append("<br>")
            continue
        # 把 **粗体** 转成 <strong>
        import re
        line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
        # 把 # 标题转成 <h2> / <h1>
        if line.startswith("## "):
            line = f"<h2>{line[3:]}</h2>"
        elif line.startswith("# "):
            line = f"<h1>{line[2:]}</h1>"
        elif line.startswith("---"):
            line = "<hr>"
        elif line.startswith("- "):
            line = f"<li>{line[2:]}</li>"
        else:
            line = f"<p>{line}</p>"
        html_lines.append(line)
    return "\n".join(html_lines)

html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 15px;
    line-height: 1.7;
    color: #1a1a1a;
    background: #f5f5f5;
    margin: 0;
    padding: 0;
  }}
  .wrapper {{
    max-width: 640px;
    margin: 32px auto;
    background: #ffffff;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }}
  .header {{
    background: #1a56db;
    color: #ffffff;
    padding: 28px 32px;
  }}
  .header h1 {{
    margin: 0;
    font-size: 20px;
    font-weight: 600;
    letter-spacing: -0.3px;
  }}
  .header p {{
    margin: 6px 0 0;
    font-size: 13px;
    opacity: 0.85;
  }}
  .content {{
    padding: 28px 32px;
  }}
  h1 {{ font-size: 20px; color: #1a56db; margin: 0 0 16px; }}
  h2 {{
    font-size: 15px;
    font-weight: 600;
    color: #374151;
    margin: 24px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e5e7eb;
  }}
  p {{ margin: 4px 0; }}
  li {{
    margin: 6px 0;
    padding: 8px 12px;
    background: #f9fafb;
    border-left: 3px solid #1a56db;
    border-radius: 0 4px 4px 0;
    list-style: none;
  }}
  hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }}
  strong {{ color: #111827; }}
  .footer {{
    padding: 16px 32px;
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
    font-size: 12px;
    color: #9ca3af;
    text-align: center;
  }}
  .footer a {{ color: #1a56db; text-decoration: none; }}
</style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>🔔 EU AI Act 协调标准监控</h1>
      <p>ai-act-standards.com 状态变化通知</p>
    </div>
    <div class="content">
      {text_to_html(body_text)}
    </div>
    <div class="footer">
      此邮件由 GitHub Actions 自动发送，每6小时检查一次 ·
      <a href="https://ai-act-standards.com/">查看完整标准地图</a>
    </div>
  </div>
</body>
</html>"""

payload = {
    "from": "AI Act Monitor <onboarding@resend.dev>",
    "to": os.environ["NOTIFY_EMAIL"].split(","),
    "subject": subject,
    "html": html_body,
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
