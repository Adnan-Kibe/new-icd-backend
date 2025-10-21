import os
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr
from jinja2 import Template
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "DiagnoXis Support Team")

conf = ConnectionConfig(
    MAIL_USERNAME=EMAIL_HOST_USER,
    MAIL_PASSWORD=EMAIL_HOST_PASSWORD,
    MAIL_FROM=EMAIL_HOST_USER,
    MAIL_FROM_NAME=EMAIL_FROM_NAME,
    MAIL_PORT=EMAIL_PORT,
    MAIL_SERVER=EMAIL_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" style="margin: 0; padding: 0;">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Your One-Time Password (OTP)</title>
  </head>
  <body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: Arial, sans-serif;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f4f4; padding: 30px 0;">
      <tr>
        <td align="center">
          <table width="500" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
            <tr>
              <td style="background-color: #84cc16; color: #ffffff; text-align: center; padding: 20px 0;">
                <h1 style="margin: 0; font-size: 22px;">Your Verification Code</h1>
              </td>
            </tr>
            <tr>
              <td style="padding: 30px; text-align: center;">
                <p style="font-size: 16px; color: #333333; margin-bottom: 20px;">
                  Hello, your One-Time Password (OTP) is:
                </p>
                <p style="font-size: 36px; font-weight: bold; color: #84cc16; margin: 10px 0;">
                  {{ otp_code }}
                </p>
                <p style="font-size: 15px; color: #555555; margin-top: 20px;">
                  This code will expire in <strong>10 minutes</strong>.<br />
                  Please do not share this code with anyone.
                </p>
              </td>
            </tr>
            <tr>
              <td style="background-color: #e5e7eb; text-align: center; padding: 15px;">
                <p style="font-size: 12px; color: #6b7280; margin: 0;">
                  If you did not request this code, please ignore this email.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

def validate_email_content(email: EmailStr) -> bool:
    """Validate email for basic security (checks for XSS or injection)"""
    if not email:
        return False

    # Convert to lowercase for safer matching
    email_clean = email.lower()

    # Basic XSS / injection prevention patterns
    dangerous_patterns = ['<script', 'javascript:', 'onclick=', 'onerror=', '"', "'", ';', '--']

    # Check if any dangerous pattern appears in the email
    return not any(pattern in email_clean for pattern in dangerous_patterns)

async def send_otp_email(recipient: EmailStr, otp_code: str):
    """Send a One-Time Password (OTP) email to the user"""
    # Validate email structure and content
    if not validate_email_content(recipient):
        raise ValueError("Invalid or unsafe email address provided")

    # Render the email HTML template with Jinja2
    template = Template(EMAIL_TEMPLATE)
    html_content = template.render(otp_code=otp_code)

    # Prepare message
    message = MessageSchema(
        subject="Your OTP Code – DiagnoXis",
        recipients=[recipient],
        body=html_content,
        subtype="html",
    )

    # Send email
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        return {"status": "success", "message": f"OTP sent successfully to {recipient}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import asyncio

    async def main():
        try:
            response = await send_otp_email(recipient="charity.k.mutembei@gmail.com", otp_code="458796")
            print(response)
        except Exception as e:
            print(f"❌ Failed to send email: {e}")

    asyncio.run(main())