# type: ignore
import os
import pytz
import time
import smtplib
import requests
import threading
from flask import Flask
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

load_dotenv()

USER_EMAIL = os.getenv("USER_EMAIL")
PASSWORD = os.getenv("PASSWORD")
EMAIL = os.getenv("EMAIL")
CODE = os.getenv("CODE")
URL = os.getenv("URL")

# Ensure all environment variables are loaded
if not all([USER_EMAIL, PASSWORD, EMAIL, CODE, URL]):
    raise ValueError(
        "Missing required environment variables. Please check your .env file."
    )


# Function to monitor the website
def monitor_website(url, user_code, email_id):
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")

        if not table:
            return "No table found on the webpage."

        rows = table.find_all("tr")[1:]  # Skip the header row
        current_date = datetime.now().strftime("%d/%m/%Y")  # Format: DD/MM/YYYY

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:  # Ensure there are enough columns
                program_code = cells[1].text.strip()  # 2nd column: Program Code
                result_date = cells[3].text.strip()  # 4th column: Result Date

                if program_code == user_code and result_date == current_date:
                    send_email(
                        email_id,
                        "Website Update Detected",
                        f"The following update was detected:\n\nProgram Code: {program_code}\nResult Date: {result_date}",
                    )
                    return "Website update detected successfully."

        return "No new changes detected."

    except requests.exceptions.RequestException as e:
        return f"Error with the request: {e}"
    except Exception as e:
        return f"Error: {e}"


# Function to send an email
def send_email(to_email, subject, body):
    try:
        sender_email = USER_EMAIL
        sender_password = PASSWORD

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")


# Function to calculate sleep time based on Indian time
def get_sleep_time():
    india_tz = pytz.timezone("Asia/Kolkata")  # IST timezone
    india_time = datetime.now(india_tz)

    if 7 <= india_time.hour < 19:  # Between 7 AM and 7 PM
        return 600  # 10 minutes
    else:
        return 39600  # 30 minutes


# Background task for monitoring
def background_monitoring():
    while True:
        print("Monitoring started...")
        print(monitor_website(URL, CODE, EMAIL))
        sleep_time = get_sleep_time()
        print(f"Sleeping for {sleep_time // 60} minutes...")
        time.sleep(sleep_time)


# Flask endpoint
@app.route("/")
def index():
    return "Web Monitor is running. Check the logs for monitoring updates."


if __name__ == "__main__":
    # Start the background monitoring thread
    monitoring_thread = threading.Thread(target=background_monitoring, daemon=True)
    monitoring_thread.start()

    # Start the Waitress server
    from waitress import serve

    print("Starting server with Waitress...")
    serve(app, host="0.0.0.0", port=8000)
