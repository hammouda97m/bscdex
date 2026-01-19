import json
import csv
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import pandas as pd
from datetime import datetime
import time

# Your setup
web3 = Web3(Web3.HTTPProvider("https://bsc-mainnet.nodereal.io/v1/1e56d5b614aa4f88a999fe5d002236d1"))
contract_address = "0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA"

web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

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


def get_bet_data(epoch, user_address):
    """Get bet data for a specific user in a specific epoch"""
    try:
        # This function assumes there's a method to get individual bet data
        # The exact method name may vary depending on the contract
        bet_info = contract.functions.ledger(epoch, user_address).call()

        # Typical structure: [position, amount, claimed]
        # position: 0 = Bull, 1 = Bear
        return {
            'position': bet_info[0],  # 0 for Bull, 1 for Bear
            'amount': bet_info[1],
            'claimed': bet_info[2]
        }
    except Exception as e:
        # This is expected for users who didn't bet in this epoch
        return None


def get_epoch_events(epoch, from_block=None, to_block=None):
    """Get betting events for a specific epoch"""
    try:
        # If no block range provided, try to get recent blocks
        if from_block is None or to_block is None:
            current_block = web3.eth.block_number
            from_block = max(1, current_block - 1000)  # Look back 1000 blocks
            to_block = current_block

        # Define event filters - use from_block and to_block (with underscores)
        bet_bull_filter = contract.events.BetBull.create_filter(
            from_block=from_block,
            to_block=to_block,
            argument_filters={'epoch': epoch}
        )

        bet_bear_filter = contract.events.BetBear.create_filter(
            from_block=from_block,
            to_block=to_block,
            argument_filters={'epoch': epoch}
        )

        # Get events
        bull_events = bet_bull_filter.get_all_entries()
        bear_events = bet_bear_filter.get_all_entries()

        return bull_events, bear_events

    except Exception as e:
        print(f"Error getting events for epoch {epoch}: {e}")
        return [], []


def get_top_bets_from_events(bull_events, bear_events, top_n=3):
    """Extract top bets from events"""
    bull_bets = []
    bear_bets = []

    # Process bull events
    for event in bull_events:
        bet_data = {
            'user': event['args']['sender'],
            'amount': event['args']['amount'] / 10 ** 18,  # Convert from wei
            'block_number': event['blockNumber'],
            'transaction_hash': event['transactionHash'].hex()
        }
        bull_bets.append(bet_data)

    # Process bear events
    for event in bear_events:
        bet_data = {
            'user': event['args']['sender'],
            'amount': event['args']['amount'] / 10 ** 18,  # Convert from wei
            'block_number': event['blockNumber'],
            'transaction_hash': event['transactionHash'].hex()
        }
        bear_bets.append(bet_data)

    # Sort by amount and get top N
    bull_bets.sort(key=lambda x: x['amount'], reverse=True)
    bear_bets.sort(key=lambda x: x['amount'], reverse=True)

    return bull_bets[:top_n], bear_bets[:top_n]


def get_block_range_for_epoch(epoch):
    """
    Estimate block range for an epoch based on timestamps
    This is a rough estimation - you may need to adjust based on actual block times
    """
    try:
        round_data = get_round_data(epoch)
        if not round_data:
            return None, None

        start_time = round_data['start_timestamp']
        lock_time = round_data['lock_timestamp']

        # BSC average block time is ~3 seconds
        # Estimate blocks by getting current block and working backwards
        current_block = web3.eth.block_number
        current_timestamp = web3.eth.get_block(current_block)['timestamp']

        # Rough estimation of blocks
        time_diff_start = current_timestamp - start_time
        time_diff_lock = current_timestamp - lock_time

        blocks_back_start = int(time_diff_start / 3)  # 3 seconds per block
        blocks_back_lock = int(time_diff_lock / 3)

        from_block = max(1, current_block - blocks_back_start - 2000)  # Add buffer
        to_block = max(1, current_block - blocks_back_lock + 2000)  # Add buffer

        return from_block, to_block

    except Exception as e:
        print(f"Error estimating block range for epoch {epoch}: {e}")
        return None, None


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


def scrape_prediction_data(start_epoch=None, end_epoch=None, num_epochs=None, include_top_bets=True):
    """
    Scrape prediction data for specified epoch range

    Parameters:
    - start_epoch: Starting epoch number (if None, calculated from num_epochs)
    - end_epoch: Ending epoch number (if None, uses current epoch)
    - num_epochs: Number of epochs to scrape backwards from current (used if start_epoch is None)
    - include_top_bets: Whether to include top 3 bets for each side
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

    if include_top_bets:
        print("Note: Including top bets will significantly slow down the scraping process")

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

        # Prepare basic record
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

        # Get top bets if requested
        if include_top_bets:
            try:
                from_block, to_block = get_block_range_for_epoch(epoch)
                if from_block and to_block:
                    bull_events, bear_events = get_epoch_events(epoch, from_block, to_block)
                    top_bull_bets, top_bear_bets = get_top_bets_from_events(bull_events, bear_events)

                    # Add top bets to record
                    record['top_bull_bets'] = top_bull_bets
                    record['top_bear_bets'] = top_bear_bets

                    # Add summary statistics
                    record['bull_bets_count'] = len(bull_events)
                    record['bear_bets_count'] = len(bear_events)
                    record['total_bets_count'] = len(bull_events) + len(bear_events)

                    if top_bull_bets:
                        record['largest_bull_bet'] = max(bet['amount'] for bet in top_bull_bets)
                    else:
                        record['largest_bull_bet'] = 0

                    if top_bear_bets:
                        record['largest_bear_bet'] = max(bet['amount'] for bet in top_bear_bets)
                    else:
                        record['largest_bear_bet'] = 0

                else:
                    record['top_bull_bets'] = []
                    record['top_bear_bets'] = []
                    record['bull_bets_count'] = 0
                    record['bear_bets_count'] = 0
                    record['total_bets_count'] = 0
                    record['largest_bull_bet'] = 0
                    record['largest_bear_bet'] = 0

            except Exception as e:
                print(f"Error getting top bets for epoch {epoch}: {e}")
                record['top_bull_bets'] = []
                record['top_bear_bets'] = []
                record['bull_bets_count'] = 0
                record['bear_bets_count'] = 0
                record['total_bets_count'] = 0
                record['largest_bull_bet'] = 0
                record['largest_bear_bet'] = 0

        data.append(record)

        # Longer delay when getting events to avoid rate limiting
        time.sleep(1.0 if include_top_bets else 0.5)

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
            # Flatten the data for CSV (top bets as separate columns)
            flattened_data = []
            for record in data:
                flat_record = record.copy()

                # Remove complex nested data for CSV
                if 'top_bull_bets' in flat_record:
                    top_bull_bets = flat_record.pop('top_bull_bets', [])
                    top_bear_bets = flat_record.pop('top_bear_bets', [])

                    # Add top bets as separate columns
                    for i, bet in enumerate(top_bull_bets[:3]):
                        flat_record[f'bull_bet_{i + 1}_user'] = bet['user']
                        flat_record[f'bull_bet_{i + 1}_amount'] = bet['amount']
                        flat_record[f'bull_bet_{i + 1}_tx_hash'] = bet['transaction_hash']

                    for i, bet in enumerate(top_bear_bets[:3]):
                        flat_record[f'bear_bet_{i + 1}_user'] = bet['user']
                        flat_record[f'bear_bet_{i + 1}_amount'] = bet['amount']
                        flat_record[f'bear_bet_{i + 1}_tx_hash'] = bet['transaction_hash']

                flattened_data.append(flat_record)

            df = pd.DataFrame(flattened_data)
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

    # Ask if user wants to include top bets
    include_bets = input("\nInclude top 3 bets for each side? (y/n, default=y): ").strip().lower()
    include_top_bets = include_bets != 'n'

    if include_top_bets:
        print("Warning: Including top bets will significantly slow down the scraping process due to event filtering")

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
            data = scrape_prediction_data(start_epoch=start_epoch, end_epoch=end_epoch,
                                          include_top_bets=include_top_bets)

        elif choice == "2":
            num_epochs = int(input("Enter number of epochs to scrape backwards: "))
            data = scrape_prediction_data(num_epochs=num_epochs, include_top_bets=include_top_bets)

        elif choice == "3":
            start_epoch = int(input("Enter start epoch: "))
            data = scrape_prediction_data(start_epoch=start_epoch, include_top_bets=include_top_bets)

        elif choice == "4":
            end_epoch = int(input("Enter end epoch: "))
            num_epochs = int(input("Enter number of epochs to scrape backwards from that epoch: "))
            data = scrape_prediction_data(end_epoch=end_epoch, num_epochs=num_epochs, include_top_bets=include_top_bets)

        else:
            print("Invalid choice. Using default: last 1000 epochs")
            data = scrape_prediction_data(num_epochs=1000, include_top_bets=include_top_bets)

    except ValueError:
        print("Invalid input. Using default: last 1000 epochs")
        data = scrape_prediction_data(num_epochs=1000, include_top_bets=include_top_bets)
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
        for i, record in enumerate(data[:2]):  # Show fewer records due to more data
            print(f"Record {i + 1}:")
            for key, value in record.items():
                if key in ['top_bull_bets', 'top_bear_bets']:
                    print(f"  {key}: {len(value)} bets")
                    for j, bet in enumerate(value[:2]):  # Show first 2 bets
                        print(f"    Bet {j + 1}: {bet['amount']:.4f} BNB from {bet['user'][:10]}...")
                else:
                    print(f"  {key}: {value}")
            print()

        # Print enhanced statistics
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

        if include_top_bets and 'largest_bull_bet' in df.columns:
            print(f"Largest bull bet: {df['largest_bull_bet'].max():.4f} BNB")
            print(f"Largest bear bet: {df['largest_bear_bet'].max():.4f} BNB")
            print(f"Average bets per epoch: {df['total_bets_count'].mean():.1f}")

    else:
        print("No data scraped")


if __name__ == "__main__":
    main()