"""
Verify live Google Sheets connectivity using the One Piece service account.

Usage:
    cd backend
    python verify_connection.py [--spreadsheet-id <ID>]

If --spreadsheet-id is omitted, the script only verifies authentication and
lists the first 5 Drive files the service account can see.
"""

import argparse
import sys

import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = "one_piece_service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spreadsheet-id", help="Google Sheets spreadsheet ID to verify")
    args = parser.parse_args()

    # Step 1: Load credentials
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        print(f"Service account loaded: {creds.service_account_email}")
    except FileNotFoundError:
        print(f"ERROR: {SERVICE_ACCOUNT_FILE} not found.")
        print("  Make sure you're running this from the backend/ directory.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR loading credentials: {e}")
        sys.exit(1)

    # Step 2: Authenticate with Google
    try:
        gc = gspread.authorize(creds)
        print("Google authentication: OK")
    except Exception as e:
        print(f"ERROR authenticating: {e}")
        sys.exit(1)

    # Step 3: If a spreadsheet ID was provided, open and inspect it
    if args.spreadsheet_id:
        try:
            sheet = gc.open_by_key(args.spreadsheet_id)
            ws = sheet.sheet1
            header = ws.row_values(1)
            row_count = max(0, ws.row_count - 1)  # exclude header
            print(f"Connected to: {sheet.title}")
            print(f"Header row: {header}")
            print(f"Row count (data only): {row_count}")
            print("Connection OK.")
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"ERROR: Spreadsheet '{args.spreadsheet_id}' not found.")
            print("  Share the spreadsheet with the service account (Editor permission):")
            print(f"  {creds.service_account_email}")
            sys.exit(1)
        except Exception as e:
            print(f"ERROR opening spreadsheet: {e}")
            sys.exit(1)
    else:
        # Step 3 (alt): List accessible Drive files as a smoke test
        try:
            files = gc.list_spreadsheet_files()
            if files:
                print(f"Drive accessible. Spreadsheets visible to this account ({len(files)}):")
                for f in files[:5]:
                    print(f"  - {f['name']}  (id: {f['id']})")
            else:
                print("Drive accessible. No spreadsheets shared with this account yet.")
                print("  Share a sheet with the service account to use it:")
                print(f"  {creds.service_account_email}")
            print("Connection OK.")
        except Exception as e:
            print(f"ERROR listing Drive files: {e}")
            print("  Ensure Google Drive API and Google Sheets API are enabled in:")
            print("  https://console.cloud.google.com/apis/library?project=one-piece-498800")
            sys.exit(1)


if __name__ == "__main__":
    main()
