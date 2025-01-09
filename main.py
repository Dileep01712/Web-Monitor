# type: ignore
import os
import time
import smtplib
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

USER_EMAIL = os.getenv("USER_EMAIL")
PASSWORD = os.getenv("PASSWORD")
EMAIL = os.getenv("EMAIL")
CODE = os.getenv("CODE")
URL = os.getenv("URL")

# Ensure all environment variables are loaded
if not all(
    [
        USER_EMAIL,
        PASSWORD,
        EMAIL,
        CODE,
        URL,
    ]
):
    raise ValueError(
        "Missing required environment variables. Please check your .env file."
    )


# Function to monitor the website
def monitor_website(url, user_code, email_id):
    try:
        # Fetch the website content
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract the table data (specific to the given table structure)
        table = soup.find("table")
        rows = table.find_all("tr")[1:]  # Skip the header row

        current_date = datetime.now().strftime("%d/%m/%Y")  # Format: DD/MM/YYYY

        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:  # Ensure there are enough columns
                program_code = cells[1].text.strip()  # 2nd column: Program Code
                result_date = cells[3].text.strip()  # 4th column: Result Date

                # Check for a match with the user-provided code and current date
                if program_code == user_code and result_date == current_date:
                    send_email(
                        email_id,
                        "Website Update Detected",
                        f"The following update was detected:\n\nProgram Code: {program_code}\nResult Date: {result_date}",
                    )
                    return "Website update detected successfully."
        return "No new changes detected."

    except Exception as e:
        return f"Error: {e}"


# Function to send an email
def send_email(to_email, subject, body):
    try:
        # Email configuration
        sender_email = USER_EMAIL  # Replace with your email
        sender_password = PASSWORD  # Replace with your email password

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # SMTP configuration
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")


# Main function to schedule the job every 30 minutes
if __name__ == "__main__":
    website_url = URL  # Replace with the website URL
    user_code = CODE  # Replace with the user-provided code
    recipient_email = EMAIL  # Replace with the recipient's email

    while True:
        print("I'm listening...")
        print(monitor_website(website_url, user_code, recipient_email))
        time.sleep(30)  # Sleep for 30 seconds (30 seconds)
