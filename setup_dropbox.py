"""
Dropbox OAuth2 Setup Helper
===========================
Run this script ONCE to generate a permanent Dropbox refresh token.
After running, paste the values into config.py.

Requires:
    pip install dropbox

Usage:
    python setup_dropbox.py
"""

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

print("=" * 55)
print("  Dropbox OAuth2 Setup")
print("=" * 55)
print()
print("Before running, make sure you have:")
print("  1. Created a Dropbox app at https://www.dropbox.com/developers/apps")
print("  2. Set Access type to: Full Dropbox")
print("  3. Enabled permissions: files.content.read + files.content.write")
print("  4. Your App Key and App Secret ready")
print()

app_key    = input("Enter your Dropbox App Key:    ").strip()
app_secret = input("Enter your Dropbox App Secret: ").strip()

if not app_key or not app_secret:
    print("\n[ERROR] App Key and App Secret cannot be empty.")
    exit(1)

# Start OAuth2 flow (no redirect URL needed for desktop apps)
auth_flow = DropboxOAuth2FlowNoRedirect(
    app_key,
    app_secret,
    token_access_type="offline"   # 'offline' = gives a refresh token (permanent)
)

authorize_url = auth_flow.start()

print()
print("-" * 55)
print("STEP 1: Open this URL in your browser:")
print()
print(f"  {authorize_url}")
print()
print("STEP 2: Click 'Allow' to authorize the app.")
print("STEP 3: Copy the authorization code shown.")
print("-" * 55)
print()

auth_code = input("Paste the authorization code here: ").strip()

try:
    oauth_result = auth_flow.finish(auth_code)
except Exception as e:
    print(f"\n[ERROR] Authorization failed: {e}")
    exit(1)

refresh_token = oauth_result.refresh_token
access_token  = oauth_result.access_token

print()
print("=" * 55)
print("  SUCCESS! Copy these values into your config.py")
print("=" * 55)
print()
print(f'DROPBOX_APP_KEY       = "{app_key}"')
print(f'DROPBOX_APP_SECRET    = "{app_secret}"')
print(f'DROPBOX_REFRESH_TOKEN = "{refresh_token}"')
print()
print("The REFRESH TOKEN never expires.")
print("You do NOT need to run this script again.")
print()

# Verify the connection works
try:
    dbx = dropbox.Dropbox(
        app_key=app_key,
        app_secret=app_secret,
        oauth2_refresh_token=refresh_token
    )
    account = dbx.users_get_current_account()
    print(f"[OK] Connected as: {account.name.display_name} ({account.email})")
except Exception as e:
    print(f"[WARNING] Could not verify connection: {e}")
    print("The tokens above may still be valid - try pasting them into config.py.")
