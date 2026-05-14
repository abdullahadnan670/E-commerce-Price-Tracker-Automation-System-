import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load the hidden variables from the .env file
load_dotenv()
# --- CONFIGURATION ---
# Replace this with the Gmail address you want to send emails FROM
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD") 

def send_deal_alert(recipient_email: str, product_name: str, price: str, url: str):
    """Sends an HTML email alert when a target price is hit."""
    
    msg = EmailMessage()
    msg['Subject'] = f"🚨 Deal Alert: {product_name[:30]} is now {price}!"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    # The HTML body of the email
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Your Deal is Ready! 🎉</h2>
            <p>Great news! The item you are tracking has dropped to your target price.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0;">{product_name}</h3>
                <p style="font-size: 24px; font-weight: bold; color: #28a745; margin: 10px 0;">{price}</p>
                <a href="{url}" style="background-color: #0d6efd; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Buy it now
                </a>
            </div>
            
            <p><small>You are receiving this because you tracked this item on MySemesterApp.</small></p>
        </body>
    </html>
    """
    
    msg.set_content("Your email client does not support HTML emails.", subtype='plain')
    msg.add_alternative(html_content, subtype='html')

    try:
        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            smtp.send_message(msg)
            print(f"[📧] Deal alert successfully sent to {recipient_email}")
    except Exception as e:
        print(f"[❌] Failed to send email to {recipient_email}. Error: {e}")