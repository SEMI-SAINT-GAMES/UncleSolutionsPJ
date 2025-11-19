def registration_template(username: str, code: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <h2>Welcome, {username}!</h2>
        <p>Thank you for registering.</p>
        <p>Your verification code:</p>
        <div style="font-size: 24px; font-weight: bold; color: #2b6cb0;">
            {code}
        </div>
        <br />
        <p>This code is valid for 5 minutes.</p>
    </body>
    </html>
    """

def reset_password_template(username: str, code: str) -> str:
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <h2>Password Reset Request</h2>
        <p>Hello {username},</p>
        <p>Here is your password reset code:</p>

        <div style="font-size: 24px; font-weight: bold; color: #c53030;">
            {code}
        </div>

        <br />
        <p>Use it within 5 minutes.</p>
    </body>
    </html>
    """