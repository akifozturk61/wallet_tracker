import requests
from solana.rpc.api import Client
import time
from solders.pubkey import Pubkey
from httpx import HTTPStatusError
import json

# Initialize Solana client
solana_client = Client("https://api.mainnet-beta.solana.com")

# Wallet address to monitor
#PROM
wallet_address = "9ky2EiBoyXmhzC6H1KVPyQiUKpSyENLh7WxCEQA48WYj"

# Telegram bot token and chat ID
# bot_token = '7668068869:AAH9wQrbxSdNlNlu6m1xa2zQWUtBE1p6aYM'
# chat_id = '-1002329806079'

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

# Function to check if any mint address ends with "pump"
def check_mint_address(tzx_id):
    tzx_json = json.loads(tzx_id.to_json())
    pre_token_balances = tzx_json['result']['meta']['preTokenBalances']
    for balance in pre_token_balances:
        mint_address = balance['mint']
        if mint_address.endswith("pump"):
            return mint_address
    return None

def send_notification(transaction):
    message = ""
    # Assuming tzx_json is the JSON string of your transaction response
    # Check the mint addresses
    mint_address = check_mint_address(transaction)
    if mint_address:
        message = f"Mint address ending with 'pump' found: `{mint_address}`"
        message2 = f"/bundle {mint_address}"
    else:
        message = "No token address ending with 'pump' found, but other events have triggered."
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {'chat_id': chat_id, 'text': message, 'parse_mode': "Markdown"}
    response = requests.post(url, data=data)
    print(f"Notification sent: {response.json()}")
    time.sleep(1)
    data = {'chat_id': chat_id, 'text': message2}
    response = requests.post(url, data=data)
    print(f"Notification2 sent: {response.json()}")


# Periodically check for new transactions and send notifications
while True:
    try:
        new_transactions = check_new_transactions()
        # transactions = get_latest_transactions(wallet_address).value
        # new_transactions = solana_client.get_transaction(tx_sig=transactions[5].signature, max_supported_transaction_version=0, encoding="jsonParsed")
        # send_notification(new_transactions)
        if new_transactions:
            print("New potential transactions detected")
            for tx in new_transactions:
                tzx = solana_client.get_transaction(tx_sig=tx.signature, max_supported_transaction_version=0, encoding="jsonParsed")
                send_notification(tzx)
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