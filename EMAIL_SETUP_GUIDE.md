# Email Configuration Guide for E-Shop

## Current Status: ✅ Working with Console Backend

The email system is now configured to output emails to the terminal/console during development.

## What happens when you place an order:
1. Order confirmation email content will be displayed in the terminal where you run `python manage.py runserver`
2. Look for output that starts with email headers like:
   ```
   Content-Type: text/plain; charset="utf-8"
   MIME-Version: 1.0
   Subject: Order Confirmation - Order #123
   From: E-Shop <riaz35-995@diu.edu.bd>
   To: customer@example.com
   ```

## To Enable Real Email Sending (Gmail SMTP):

### Step 1: Generate Gmail App Password
1. Go to https://myaccount.google.com/apppasswords
2. Generate a new App Password for "E-Shop Django App"
3. Copy the 16-character password (e.g., "abcd efgh ijkl mnop")

### Step 2: Update Settings
In `e_shop/settings.py`, change:
```python
# Change this line:
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# To this:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# And update the password:
EMAIL_HOST_PASSWORD = 'your-16-char-app-password-here'  # Replace with App Password
```

### Step 3: Test Real Email
```bash
python manage.py shell -c "
from django.core.mail import send_mail
send_mail('Test', 'Real email test', 'riaz35-995@diu.edu.bd', ['your-email@example.com'])
"
```

## Alternative Email Backends for Development:
- **Console**: `django.core.mail.backends.console.EmailBackend` (current)
- **File**: `django.core.mail.backends.filebased.EmailBackend`
- **Memory**: `django.core.mail.backends.locmem.EmailBackend`

## Troubleshooting:
- ❌ Gmail authentication error → Need App Password
- ❌ Connection timeout → Check firewall/VPN
- ❌ Template not found → Verify `order_confirmation_email.html` exists
- ✅ Email appears in terminal → System working correctly with console backend
