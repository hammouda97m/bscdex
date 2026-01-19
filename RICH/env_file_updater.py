import json
import re


def update_env_with_json_wallets(json_file_path, env_file_path):
    """
    Updates the .env file with wallet data from the JSON file.
    Preserves all other content including comments and Telegram settings.
    """

    # Read the JSON file
    with open(json_file_path, 'r') as f:
        wallets_data = json.load(f)

    # Read the .env file
    with open(env_file_path, 'r') as f:
        env_content = f.read()

    # Update each wallet's private key and address
    for i, wallet in enumerate(wallets_data, 1):
        private_key = wallet['private_key']
        address = wallet['address']

        # Update private key using regex
        private_key_pattern = f'PRIVATE_KEY_{i}=.*'
        private_key_replacement = f'PRIVATE_KEY_{i}={private_key}'
        env_content = re.sub(private_key_pattern, private_key_replacement, env_content)

        # Update wallet address using regex
        wallet_address_pattern = f'WALLET_ADDRESS_{i}=.*'
        wallet_address_replacement = f'WALLET_ADDRESS_{i}={address}'
        env_content = re.sub(wallet_address_pattern, wallet_address_replacement, env_content)

    # Write the updated content back to the .env file
    with open(env_file_path, 'w') as f:
        f.write(env_content)

    print(f"Successfully updated {len(wallets_data)} wallets in the .env file!")


def preview_changes(json_file_path, env_file_path):
    """
    Preview what changes will be made without actually updating the file.
    """

    # Read the JSON file
    with open(json_file_path, 'r') as f:
        wallets_data = json.load(f)

    print("Preview of changes that will be made:")
    print("=" * 50)

    for i, wallet in enumerate(wallets_data, 1):
        print(f"Bot {i} Wallet:")
        print(f"  PRIVATE_KEY_{i}={wallet['private_key']}")
        print(f"  WALLET_ADDRESS_{i}={wallet['address']}")
        print()


# Example usage
if __name__ == "__main__":
    json_file = "created_wallets.json"
    env_file = ".env"

    # Preview changes first
    print("Previewing changes...")
    preview_changes(json_file, env_file)

    # Ask for confirmation
    confirm = input("Do you want to proceed with updating the .env file? (y/n): ")

    if confirm.lower() == 'y':
        # Create a backup of the original .env file
        import shutil

        shutil.copy(env_file, f"{env_file}.backup")
        print(f"Backup created: {env_file}.backup")

        # Update the .env file
        update_env_with_json_wallets(json_file, env_file)
    else:
        print("Operation cancelled.")