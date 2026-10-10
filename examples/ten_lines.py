# pip install sadasend
import os
from sadasend import SadaSend

sadasend = SadaSend(os.environ["SADASEND_API_KEY"])

result = sadasend.emails.send(
    from_="noreply@onboarding.sadasend.com",
    to="dana@example.com",
    subject="It works.",
    html="<strong>Sent from the SadaSend SDK.</strong>",
)

print(result["status"], result["id"])
