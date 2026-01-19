import json
import csv
from web3 import Web3
import pandas as pd
from datetime import datetime
import time

# Your setup
web3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/bsc/74fd72ea607c37d8ef3729331054abb623de16b02e93a0fc8625c35434b3cb6f"))
contract_address = "0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA"

# Load ABI
with open('prediction_abi.json', 'r') as f:
    contract_abi = json.load(f)

# Create contract instance
contract = web3.eth.contract(address=contract_address, abi=contract_abi)


def get_current_epoch():
    """Get the current epoch number"""
    try:
        return contract.functions.currentEpoch().call()
    except Exception as e:
        print(f"Error getting current epoch: {e}")
        return None


def get_round_data(epoch):
    """Get round data for a specific epoch"""
    try:
        # Get round info
        round_data = contract.functions.rounds(epoch).call()

        # Extract round data (structure may vary based on contract)
        # Typical structure: [epoch, startTimestamp, lockTimestamp, closeTimestamp, lockPrice, closePrice, lockOracleId, closeOracleId, totalAmount, bullAmount, bearAmount, rewardBaseCalAmount, rewardAmount, oracleCalled]

        return {
            'epoch': epoch,
            'start_timestamp': round_data[1],
            'lock_timestamp': round_data[2],
            'close_timestamp': round_data[3],
            'lock_price': round_data[4],
            'close_price': round_data[5],
            'total_amount': round_data[8],
            'bull_amount': round_data[9],
            'bear_amount': round_data[10],
            'reward_base_cal_amount': round_data[11],
            'reward_amount': round_data[12],
            'oracle_called': round_data[13]
        }
    except Exception as e:
        print(f"Error getting round data for epoch {epoch}: {e}")
        return None


def calculate_winner_and_multipliers(round_data):
    """Determine winner and calculate payout multipliers"""
    if not round_data:
        return None, None, None

    lock_price = round_data['lock_price'] / 10 ** 8  # Assuming 8 decimals
    close_price = round_data['close_price'] / 10 ** 8

    # Determine winner
    if close_price > lock_price:
        winner = 'bull'
    elif close_price < lock_price:
        winner = 'bear'
    else:
        winner = 'tie'

    # Calculate multipliers
    total_amount = round_data['total_amount'] / 10 ** 18  # Convert from wei
    bull_amount = round_data['bull_amount'] / 10 ** 18
    bear_amount = round_data['bear_amount'] / 10 ** 18

    # Calculate payout multipliers (how much winners get per unit bet)
    bull_multiplier = total_amount / bull_amount if bull_amount > 0 else 0
    bear_multiplier = total_amount / bear_amount if bear_amount > 0 else 0

    return winner, bull_multiplier, bear_multiplier


def scrape_prediction_data(start_epoch=None, end_epoch=None, num_epochs=None):
    """
    Scrape prediction data for specified epoch range

    Parameters:
    - start_epoch: Starting epoch number (if None, calculated from num_epochs)
    - end_epoch: Ending epoch number (if None, uses current epoch)
    - num_epochs: Number of epochs to scrape backwards from current (used if start_epoch is None)
    """

    print("Getting current epoch...")
    current_epoch = get_current_epoch()
    if not current_epoch:
        print("Failed to get current epoch")
        return

    print(f"Current epoch: {current_epoch}")

    # Determine epoch range
    if end_epoch is None:
        end_epoch = current_epoch

    if start_epoch is None:
        if num_epochs is None:
            num_epochs = 100000  # Default value
        start_epoch = max(1, end_epoch - num_epochs)

    # Validate epoch range
    if start_epoch > end_epoch:
        print(f"Error: start_epoch ({start_epoch}) cannot be greater than end_epoch ({end_epoch})")
        return

    if start_epoch < 1:
        start_epoch = 1
        print(f"Warning: start_epoch adjusted to 1 (minimum epoch)")

    if end_epoch > current_epoch:
        end_epoch = current_epoch
        print(f"Warning: end_epoch adjusted to current epoch ({current_epoch})")

    total_epochs = end_epoch - start_epoch + 1
    print(f"Scraping from epoch {start_epoch} to {end_epoch} ({total_epochs} epochs)")

    # Prepare data storage
    data = []

    # Loop through epochs
    for epoch in range(start_epoch, end_epoch + 1):
        if epoch % 100 == 0:
            progress = epoch - start_epoch + 1
            print(f"Processing epoch {epoch} ({progress}/{total_epochs})")

        # Get round data
        round_data = get_round_data(epoch)
        if not round_data:
            continue

        # Skip if round is not finished
        if not round_data['oracle_called']:
            continue

        # Calculate winner and multipliers
        winner, bull_multiplier, bear_multiplier = calculate_winner_and_multipliers(round_data)

        # Prepare record
        record = {
            'epoch': epoch,
            'timestamp': datetime.fromtimestamp(round_data['close_timestamp']).isoformat(),
            'price_locked': round_data['lock_price'] / 10 ** 8,
            'price_closed': round_data['close_price'] / 10 ** 8,
            'price_change': (round_data['close_price'] - round_data['lock_price']) / 10 ** 8,
            'price_change_percent': ((round_data['close_price'] - round_data['lock_price']) / round_data[
                'lock_price']) * 100,
            'total_bets_amount': round_data['total_amount'] / 10 ** 18,
            'bull_bets_amount': round_data['bull_amount'] / 10 ** 18,
            'bear_bets_amount': round_data['bear_amount'] / 10 ** 18,
            'bull_multiplier': bull_multiplier,
            'bear_multiplier': bear_multiplier,
            'winner': winner,
            'duration_seconds': round_data['close_timestamp'] - round_data['lock_timestamp']
        }

        data.append(record)

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    return data


def save_data(data, format='both', filename_prefix="pancakeswap_prediction_data"):
    """Save data to JSON and/or CSV format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format in ['json', 'both']:
        json_filename = f"{filename_prefix}_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data saved to {json_filename}")

    if format in ['csv', 'both']:
        csv_filename = f"{filename_prefix}_{timestamp}.csv"
        if data:
            df = pd.DataFrame(data)
            df.to_csv(csv_filename, index=False)
            print(f"Data saved to {csv_filename}")
            print(f"Data shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")


def main():
    """Main execution function with user input for epoch ranges"""
    print("Starting PancakeSwap Prediction Data Scraper...")
    print(f"Web3 connected: {web3.is_connected()}")

    if not web3.is_connected():
        print("Error: Cannot connect to BSC network")
        return

    # Get current epoch for reference
    current_epoch = get_current_epoch()
    if current_epoch:
        print(f"Current epoch: {current_epoch}")

    print("\nChoose scraping method:")
    print("1. Specific epoch range (start to end)")
    print("2. Last N epochs from current")
    print("3. From specific epoch to current")
    print("4. Last N epochs before specific epoch")

    try:
        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            start_epoch = int(input("Enter start epoch: "))
            end_epoch = int(input("Enter end epoch: "))
            data = scrape_prediction_data(start_epoch=start_epoch, end_epoch=end_epoch)

        elif choice == "2":
            num_epochs = int(input("Enter number of epochs to scrape backwards: "))
            data = scrape_prediction_data(num_epochs=num_epochs)

        elif choice == "3":
            start_epoch = int(input("Enter start epoch: "))
            data = scrape_prediction_data(start_epoch=start_epoch)

        elif choice == "4":
            end_epoch = int(input("Enter end epoch: "))
            num_epochs = int(input("Enter number of epochs to scrape backwards from that epoch: "))
            data = scrape_prediction_data(end_epoch=end_epoch, num_epochs=num_epochs)

        else:
            print("Invalid choice. Using default: last 1000 epochs")
            data = scrape_prediction_data(num_epochs=1000)

    except ValueError:
        print("Invalid input. Using default: last 1000 epochs")
        data = scrape_prediction_data(num_epochs=1000)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return

    if data:
        print(f"Successfully scraped {len(data)} records")

        # Ask for save format preference
        print("\nChoose save format:")
        print("1. CSV only")
        print("2. JSON only")
        print("3. Both CSV and JSON")

        try:
            format_choice = input("Enter your choice (1-3, default=3): ").strip()
            if format_choice == "1":
                save_format = "csv"
            elif format_choice == "2":
                save_format = "json"
            else:
                save_format = "both"
        except:
            save_format = "both"

        # Save data
        save_data(data, format=save_format)

        # Print sample data
        print("\nSample data:")
        for i, record in enumerate(data[:3]):
            print(f"Record {i + 1}: {record}")

        # Print basic statistics
        df = pd.DataFrame(data)
        print(f"\nBasic Statistics:")
        print(f"Total records: {len(df)}")
        print(f"Epoch range: {df['epoch'].min()} to {df['epoch'].max()}")
        print(f"Bull wins: {len(df[df['winner'] == 'bull'])} ({len(df[df['winner'] == 'bull']) / len(df) * 100:.1f}%)")
        print(f"Bear wins: {len(df[df['winner'] == 'bear'])} ({len(df[df['winner'] == 'bear']) / len(df) * 100:.1f}%)")
        print(f"Ties: {len(df[df['winner'] == 'tie'])} ({len(df[df['winner'] == 'tie']) / len(df) * 100:.1f}%)")
        print(f"Average price change: {df['price_change_percent'].mean():.4f}%")
        print(f"Average total bet amount: {df['total_bets_amount'].mean():.4f} BNB")
        print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

    else:
        print("No data scraped")


if __name__ == "__main__":
    main()