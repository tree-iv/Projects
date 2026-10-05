# ISS Overhead Email Alert

This program monitors the International Space Station and emails an alert when:

- the ISS is within 5 degrees of VIT Vellore (`12.934968, 79.146881`),
- it is nighttime at VIT Vellore, and
- an alert has not already been sent during the last hour.

It uses the [Open Notify ISS API](http://api.open-notify.org/iss-now.json) and the
[Sunrise-Sunset API](https://sunrise-sunset.org/api).

## Setup

```powershell
cd "D:\Computer Science\Projects\ISS Overheard Notifier"
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configure the two email addresses

Use one Gmail account as the sender. The sender account's password must be a
Gmail **app password**, not its normal password:

1. Sign in to the sender Gmail account.
2. Open [Google Account security](https://myaccount.google.com/security).
3. Turn on **2-Step Verification** if it is not already enabled.
4. Search for **App passwords**, create one named `ISS Alert`, and copy the
   generated 16-character password.
5. In PowerShell, set the sender, app password, and both recipient addresses.
   Separate the two addresses with a comma:

```powershell
$env:SMTP_EMAIL = "your-address@gmail.com"
$env:SMTP_PASSWORD = "your-gmail-app-password"
$env:ALERT_RECIPIENTS = "first-person@example.com,second-person@example.com"
```

`SMTP_EMAIL` is the account that sends the message. `ALERT_RECIPIENTS` contains
the two accounts that receive it; they can be different from the sender. A
semicolon may also be used between addresses. Keep these values in the
terminal or a secure secrets manager, and never put credentials in `main.py`
or commit them to source control.

`SMTP_HOST` and `SMTP_PORT` are optional and default to `smtp.gmail.com` and
`465`.

For example, if the two recipients are `alice@gmail.com` and
`bob@gmail.com`:

```powershell
$env:SMTP_EMAIL = "iss.sender@gmail.com"
$env:SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"
$env:ALERT_RECIPIENTS = "alice@gmail.com,bob@gmail.com"
```

The app password is used only by the sender account and is not the password of
either recipient.

## Run

```powershell
..\.venv\Scripts\python.exe main.py
```

The program checks once per minute. Stop it with `Ctrl+C`.
