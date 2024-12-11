import requests
from solana.rpc.api import Client
import time
from solders.pubkey import Pubkey
from httpx import HTTPStatusError

# Initialize Solana client
solana_client = Client("https://api.mainnet-beta.solana.com")

# Wallet address to monitor
#PROM
wallet_address = "9ky2EiBoyXmhzC6H1KVPyQiUKpSyENLh7WxCEQA48WYj"

# Telegram bot token and chat ID
bot_token = '7668068869:AAH9wQrbxSdNlNlu6m1xa2zQWUtBE1p6aYM'
chat_id = '-1002329806079'

# DeFi Program IDs
defi_program_ids = [
    '9xQeWvG816bUx9EPf4V5thG2pHf7k5k9t3d4y5k4k4k4',  # Serum
    'EhhTK9k4k4k4k4k4k4k4k4k4k4k4k4k4k4k4k4k4k4k4k4'   # Raydium
]

# Function to get the latest transactions
def get_latest_transactions(wallet_address):
    pubkey = Pubkey.from_string(wallet_address)
    response = solana_client.get_signatures_for_address(pubkey)
    return response

# Store the latest transaction signature
latest_signature = get_latest_transactions(wallet_address).value[0].signature
# latest_signature = get_latest_transactions(wallet_address)

# print(len(latest_signature.value))


def check_new_transactions():
    global latest_signature
    transactions = get_latest_transactions(wallet_address).value
    new_transactions = []
    
    for tx in transactions:
        if tx.signature == latest_signature:
            break
        new_transactions.append(tx)
    
    if new_transactions:
        latest_signature = new_transactions[0].signature
    
    return new_transactions

def is_defi_transaction(transaction):
    print("-------")
    print(transaction)
    print("-------")

    tx_details = solana_client.confirm_transaction(transaction.signature)
    for instruction in tx_details['result']['transaction']['message']['instructions']:
        if instruction['programId'] in defi_program_ids:
            return True
    return False

def send_notification(transaction):
    message = f"New DeFi transaction detected: {transaction.signature}"
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=data)
    print(f"Notification sent: {response.json()}")

# Periodically check for new transactions and send notifications
while True:
    try:
        new_transactions = check_new_transactions()
        if new_transactions:
            print("New potential transactions detected")
            for tx in new_transactions:
                print(f"New transaction detected: {tx.signature}")
                send_notification(tx)
        time.sleep(60)  # Check every 60 seconds
    except HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get('Retry-After', 60))
            print(f"Rate limit hit. Pausing for {retry_after} seconds.")
            time.sleep(retry_after)
        else:
            print(f"An error occurred: {e}")
            time.sleep(60)  # Pause for 1 minute before retrying
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        time.sleep(60)  # Pause for 1 minute before retrying