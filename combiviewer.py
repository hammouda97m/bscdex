import json
import os
import time
import math
from datetime import datetime
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_utils import event_signature_to_log_topic
from dotenv import load_dotenv, find_dotenv
import requests
import sys

# === Config ===

load_dotenv(find_dotenv())

with open("prediction_abi.json", "r") as f:
    ABI = json.load(f)
web3 = Web3(Web3.HTTPProvider("https://still-fittest-forest.bsc.quiknode.pro/2c2000a1399960609a9424b0bdd3afcec5a279e2/"))

web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

if not web3.is_connected():
    raise Exception("❌ Failed to connect to BSC")
CONTRACT_ADDRESS = Web3.to_checksum_address("0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA")

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# === Chainlink Price Feed ===
CHAINLINK_BNB_USD = Web3.to_checksum_address("0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE")
CHAINLINK_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

price_feed = web3.eth.contract(address=CHAINLINK_BNB_USD, abi=CHAINLINK_ABI)

# === Price Caching Variables ===
last_price_fetch = 0
cached_price = 0

# Topics for events
bet_bull_topic = event_signature_to_log_topic("BetBull(address,uint256,uint256)")
bet_bear_topic = event_signature_to_log_topic("BetBear(address,uint256,uint256)")

# Global variables
rounds_history = []  # Store last 24 rounds info
first_timer_print = True
last_round_close_price = 0

# Streak tracking variables
current_streak = 0
current_streak_type = None  # 'BULL' or 'BEAR'
last_notified_streak = 0  # Track last streak we notified about

# Cache file for storing rounds data
CACHE_FILE = "rounds_cache.json"

# ML INSIGHTS INTEGRATION
HOURLY_BULL_RATES = {
    0: 0.518, 1: 0.505, 2: 0.514, 3: 0.528, 4: 0.509, 5: 0.528,
    6: 0.509, 7: 0.500, 8: 0.517, 9: 0.520, 10: 0.492, 11: 0.520,
    12: 0.503, 13: 0.509, 14: 0.512, 15: 0.514, 16: 0.507, 17: 0.506,
    18: 0.514, 19: 0.511, 20: 0.515, 21: 0.529, 22: 0.524, 23: 0.504
}

FEATURE_WEIGHTS = {
    "price_volatility": 0.154,
    "bet_ratio": 0.151,
    "bear_bets_amount": 0.140,
    "bull_bets_amount": 0.140,
    "total_bets_amount": 0.132,
    "total_bet_log": 0.131,
    "hour": 0.093,
    "day_of_week": 0.058
}

BULL_WIN_BET_RATIO = 1.117  # Bulls win when bet_ratio ≈ 1.117
BEAR_WIN_BET_RATIO = 1.051  # Bears win when bet_ratio ≈ 1.051

# Store price history for volatility calculation
price_history = []


def get_24_round_summary():
    """Get 24-round summary for notifications"""
    if not rounds_history:
        return "📊 No rounds data available"
    
    # Count wins
    bull_wins = sum(1 for r in rounds_history if r['winner'] == 'BULL')
    bear_wins = sum(1 for r in rounds_history if r['winner'] == 'BEAR')
    
    # Price trend (first round open vs last round close)
    first_price = rounds_history[0]['lock_price_usdt']
    last_price = rounds_history[-1]['close_price_usdt']
    price_diff = last_price - first_price
    trend_emoji = "📈" if price_diff >= 0 else "📉"
    
    return f"📊 24-Round Summary:\n🟢 BULL: {bull_wins} | 🔴 BEAR: {bear_wins}\n{trend_emoji} Trend: ${first_price:.4f} → ${last_price:.4f} ({price_diff:+.4f})"


def get_current_price_info():
    """Get current price with direction and difference for notifications"""
    global last_round_close_price

    live_price = get_live_bnb_price()

    if last_round_close_price > 0:
        price_diff = live_price - last_round_close_price
        if price_diff > 0:
            direction_text = f"📈 +{price_diff:.4f}"
        elif price_diff < 0:
            direction_text = f"📉 {price_diff:.4f}"
        else:
            direction_text = "➡️ +0.0000"
    else:
        direction_text = "➡️ +0.0000"

    return f"💰 Current BNB: ${live_price:.4f} {direction_text}"


def get_live_bnb_price():
    """Get live BNB price from Chainlink with 10-second caching"""
    global last_price_fetch, cached_price

    current_time = time.time()

    # Return cached price if less than 10 seconds old
    if current_time - last_price_fetch < 10 and cached_price > 0:
        return cached_price

    # Fetch new price
    try:
        latest_data = price_feed.functions.latestRoundData().call()
        cached_price = latest_data[1] / 1e8  # Chainlink uses 8 decimals
        last_price_fetch = current_time
        return cached_price
    except Exception as e:
        print(f"⚠️ Price fetch error: {e}")
        return cached_price if cached_price > 0 else 0


def send_telegram_message(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ Telegram credentials not configured")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
        if not response.ok:
            print(f"⚠️ Telegram error: {response.text}")
    except Exception as e:
        print(f"⚠️ Telegram exception: {e}")


def check_streak_and_notify():
    """Check for streaks of 7+ and send Telegram notification"""
    global current_streak, current_streak_type, last_notified_streak

    if len(rounds_history) < 4:
        return

    # Get all 24 rounds to analyze streaks
    recent_rounds = rounds_history

    # Store previous values for comparison
    prev_streak_type = current_streak_type
    prev_streak = current_streak

    # Reset streak tracking
    current_streak = 1
    current_streak_type = recent_rounds[-1]['winner']

    # Count consecutive wins from the end
    for i in range(len(recent_rounds) - 2, -1, -1):
        if recent_rounds[i]['winner'] == current_streak_type:
            current_streak += 1
        else:
            break

    # Reset notification counter if streak type changed or streak broke
    if (current_streak_type != prev_streak_type or
            current_streak < prev_streak):
        last_notified_streak = 0

    # Check if we have a streak of 4+ and haven't notified for this streak yet
    if current_streak >= 7 and current_streak > last_notified_streak:
        streak_emoji = "🟢" if current_streak_type == "BULL" else "🔴"
        message = f"🚨 STREAK ALERT! 🚨\n\n{streak_emoji} {current_streak_type} STREAK: {current_streak} wins in a row!\n\n"

        # Add current price info
        message += f"{get_current_price_info()}\n\n"

        # Add 24-round summary
        message += f"{get_24_round_summary()}\n\n"

        # Add recent rounds info
        message += "📊 Last 10 rounds:\n"
        for round_info in recent_rounds[-10:]:
            winner_emoji = "🟩" if round_info['winner'] == "BULL" else "🟥"
            message += f"Round {round_info['epoch']}: {winner_emoji} {round_info['winner']} (${round_info['close_price_usdt']:.4f})\n"

        message += f"\n⚠️ Consider the streak when analyzing patterns!"

        time.sleep(3)  # 3 second delay
        send_telegram_message(message)
        last_notified_streak = current_streak
        print(f"🚨 STREAK NOTIFICATION SENT: {current_streak_type} x{current_streak}")


def check_price_movement_and_notify():
    """Check for price movements >$2.50 and send Telegram notification"""
    if len(rounds_history) < 1:
        return

    # Check the most recent round for big price movement
    latest_round = rounds_history[-1]
    price_change = abs(latest_round['price_change_usdt'])

    if price_change > 2.50:
        direction = "UP" if latest_round['price_change_usdt'] > 0 else "DOWN"
        direction_emoji = "📈" if latest_round['price_change_usdt'] > 0 else "📉"
        winner_emoji = "🟩" if latest_round['winner'] == "BULL" else "🟥"

        message = f"🚨 BIG PRICE MOVEMENT! 🚨\n\n"
        message += f"{direction_emoji} Round {latest_round['epoch']}: BNB moved {direction} by ${price_change:.4f}!\n\n"

        # Add current price info
        message += f"{get_current_price_info()}\n\n"

        # Add 24-round summary
        message += f"{get_24_round_summary()}\n\n"

        message += f"📊 Details:\n"
        message += f"Open: ${latest_round['lock_price_usdt']:.4f}\n"
        message += f"Close: ${latest_round['close_price_usdt']:.4f}\n"
        message += f"Change: {latest_round['price_change_usdt']:+.4f} USDT\n"
        message += f"Winner: {winner_emoji} {latest_round['winner']}\n\n"
        message += f"💰 Payouts: Bull {latest_round['bull_payout']:.2f}x | Bear {latest_round['bear_payout']:.2f}x"

        time.sleep(3)  # 3 second delay
        send_telegram_message(message)
        print(f"🚨 PRICE MOVEMENT NOTIFICATION SENT: ${price_change:.4f} change")


def get_max_bets_for_round(epoch, start_ts, lock_ts):
    """Get max bull and bear bets for a specific round"""
    try:
        # Get block range for this round
        def get_block_by_timestamp(target_timestamp, before=True):
            latest_block = web3.eth.block_number
            low = max(1, latest_block - 50000)  # Limit search range
            high = latest_block
            while low < high:
                mid = (low + high) // 2
                try:
                    block = web3.eth.get_block(mid)
                    block_time = block.timestamp
                    if block_time < target_timestamp:
                        low = mid + 1
                    else:
                        high = mid
                except:
                    break
            return (low - 1) if before and low > 1 else low

        start_block = get_block_by_timestamp(start_ts, before=False)
        end_block = get_block_by_timestamp(lock_ts, before=True)

        # Get bet events for this round
        bet_bull_logs = web3.eth.get_logs({
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": CONTRACT_ADDRESS,
            "topics": [bet_bull_topic]
        })
        bet_bear_logs = web3.eth.get_logs({
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": CONTRACT_ADDRESS,
            "topics": [bet_bear_topic]
        })

        # Process bull bets
        max_bull_bet = 0
        for log in bet_bull_logs:
            try:
                event = contract.events.BetBull().process_log(log)
                if event['args']['epoch'] == epoch:
                    amount_bnb = event['args']['amount'] / 1e18
                    max_bull_bet = max(max_bull_bet, amount_bnb)
            except:
                continue

        # Process bear bets
        max_bear_bet = 0
        for log in bet_bear_logs:
            try:
                event = contract.events.BetBear().process_log(log)
                if event['args']['epoch'] == epoch:
                    amount_bnb = event['args']['amount'] / 1e18
                    max_bear_bet = max(max_bear_bet, amount_bnb)
            except:
                continue

        return max_bull_bet, max_bear_bet

    except Exception as e:
        print(f"⚠️ Error getting max bets for round {epoch}: {e}")
        return 0, 0


def load_cached_rounds():
    """Load rounds data from cache file"""
    global rounds_history

    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cached_data = json.load(f)
                rounds_history = cached_data.get('rounds_history', [])
                print(f"📂 Loaded {len(rounds_history)} rounds from cache")
        else:
            print("📂 No cache file found, starting fresh")
            rounds_history = []
    except Exception as e:
        print(f"⚠️ Error loading cache: {e}")
        rounds_history = []


def save_rounds_to_cache():
    """Save rounds data to cache file"""
    try:
        cache_data = {
            'rounds_history': rounds_history,
            'last_updated': datetime.now().isoformat()
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"💾 Saved {len(rounds_history)} rounds to cache")
    except Exception as e:
        print(f"⚠️ Error saving cache: {e}")


def fetch_single_round_data(epoch):
    """Fetch data for a single round"""
    try:
        round_data = contract.functions.rounds(epoch).call()

        start_ts = round_data[1]
        lock_ts = round_data[2]
        close_ts = round_data[3]
        lock_price = round_data[4] / 1e8  # Oracle price (8 decimals) - this is already in USDT
        close_price = round_data[5] / 1e8 if round_data[5] > 0 else 0  # Oracle price in USDT
        total_amount = round_data[8] / 1e18
        bull_amount = round_data[9] / 1e18
        bear_amount = round_data[10] / 1e18

        if close_price == 0 or close_ts == 0:
            return None  # Skip incomplete rounds

        # Calculate payouts
        bull_payout = total_amount / bull_amount if bull_amount > 0 else 0
        bear_payout = total_amount / bear_amount if bear_amount > 0 else 0

        # Use oracle prices directly (they're already in USDT)
        lock_price_usdt = lock_price
        close_price_usdt = close_price
        price_change_usdt = close_price_usdt - lock_price_usdt

        # Determine winner
        winner = "BULL" if close_price > lock_price else "BEAR"

        # Fetch max bets for this round
        max_bull_bet, max_bear_bet = get_max_bets_for_round(epoch, start_ts, lock_ts)

        round_info = {
            'epoch': epoch,
            'lock_price': lock_price,
            'close_price': close_price,
            'lock_price_usdt': lock_price_usdt,
            'close_price_usdt': close_price_usdt,
            'price_change_usdt': price_change_usdt,
            'bull_payout': bull_payout,
            'bear_payout': bear_payout,
            'winner': winner,
            'total_amount': total_amount,
            'max_bull_bet': max_bull_bet,
            'max_bear_bet': max_bear_bet
        }

        return round_info

    except Exception as e:
        print(f"⚠️ Error fetching round {epoch}: {e}")
        return None


def fetch_round_history():
    """Fetch the last 24 completed rounds data with caching"""
    global rounds_history

    try:
        # Load existing cache
        load_cached_rounds()

        current_epoch = contract.functions.currentEpoch().call()
        target_epochs = list(range(current_epoch - 24, current_epoch))  # Last 24 epochs

        # Get epochs we already have cached
        cached_epochs = {round_info['epoch'] for round_info in rounds_history}

        # Find which epochs we need to fetch
        epochs_to_fetch = [epoch for epoch in target_epochs if epoch not in cached_epochs and epoch > 0]

        print(f"📊 Current epoch: {current_epoch}")
        print(f"📂 Cached rounds: {len(cached_epochs)}")
        print(f"🔄 Need to fetch: {len(epochs_to_fetch)} new rounds")

        # Fetch missing rounds
        new_rounds_fetched = 0
        for epoch in epochs_to_fetch:
            print(f"🔄 Fetching round {epoch}...")
            round_info = fetch_single_round_data(epoch)
            if round_info:
                rounds_history.append(round_info)
                new_rounds_fetched += 1

        # Sort by epoch and keep only last 24
        rounds_history.sort(key=lambda x: x['epoch'])
        rounds_history = rounds_history[-24:]  # Keep only last 24

        # Save updated cache
        if new_rounds_fetched > 0:
            save_rounds_to_cache()
            print(f"✅ Fetched {new_rounds_fetched} new rounds")

            # Check for streaks and price movements after fetching new data
            check_streak_and_notify()
            check_price_movement_and_notify()
        else:
            print("✅ All rounds up to date from cache")

        print(f"📋 Total rounds in history: {len(rounds_history)}")

    except Exception as e:
        print(f"⚠️ Error in fetch_round_history: {e}")


def display_rounds_history():
    """Display the last 24 rounds in a formatted table with summary"""
    if not rounds_history:
        print("📋 No rounds history available")
        return

    print("\n" + "=" * 140)
    print("📊 LAST 24 ROUNDS HISTORY")

    # Display current streak info
    if current_streak >= 3:
        streak_emoji = "🟢" if current_streak_type == "BULL" else "🔴"
        print(f"🔥 CURRENT STREAK: {streak_emoji} {current_streak_type} x{current_streak}")

    print("=" * 140)
    print(
        f"{'Round':<8} {'Open USDT':<12} {'Close USDT':<12} {'Change':<10} {'Bull Payout':<12} {'Bear Payout':<12} {'Max Bull':<10} {'Max Bear':<10} {'Winner':<8} {'Pool':<10}")
    print("-" * 140)

    for round_info in rounds_history:
        change_color = "📈" if round_info['price_change_usdt'] >= 0 else "📉"
        winner_emoji = "🟩" if round_info['winner'] == "BULL" else "🟥"

        print(f"{round_info['epoch']:<8} "
              f"${round_info['lock_price_usdt']:<13.4f} "
              f"${round_info['close_price_usdt']:<13.4f} "
              f"{change_color}{round_info['price_change_usdt']:+.2f}   "
              f"{round_info['bull_payout']:<11.2f}x "
              f"{round_info['bear_payout']:<11.2f}x "
              f"{round_info['max_bull_bet']:<9.3f} "
              f"{round_info['max_bear_bet']:<9.3f} "
              f"{winner_emoji}{round_info['winner']:<7} "
              f"{round_info['total_amount']:<9.3f}")

    print("=" * 140)
    
    # ADHD-FRIENDLY SUMMARY BOX
    if len(rounds_history) >= 1:
        # Count wins
        bull_wins = sum(1 for r in rounds_history if r['winner'] == 'BULL')
        bear_wins = sum(1 for r in rounds_history if r['winner'] == 'BEAR')
        
        # Price trend (first round open vs last round close)
        first_price = rounds_history[0]['lock_price_usdt']
        last_price = rounds_history[-1]['close_price_usdt']
        price_diff = last_price - first_price
        trend_emoji = "📈" if price_diff >= 0 else "📉"
        
        print("🎯 24-ROUND SUMMARY:")
        print(f"🟢 BULL: {bull_wins} wins | 🔴 BEAR: {bear_wins} wins")
        print(f"{trend_emoji} PRICE TREND: ${first_price:.4f} → ${last_price:.4f} ({price_diff:+.4f})")
        print("=" * 140)


def calculate_price_volatility():
    if len(price_history) < 10:
        return 0.0
    prices = price_history[-10:]
    mean_price = sum(prices) / len(prices)
    variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
    return math.sqrt(variance) / mean_price if mean_price > 0 else 0.0


def calculate_ml_prediction_score(bet_data):
    current_hour = datetime.now().hour
    current_day = datetime.now().weekday()
    bull_amount = bet_data["bull_amount"]
    bear_amount = bet_data["bear_amount"]
    total_amount = bet_data["total_amount"]

    if total_amount == 0:
        return 0.0

    bet_ratio = bull_amount / bear_amount if bear_amount > 0 else 2.0
    price_volatility = calculate_price_volatility()

    score = 0.0
    if bet_ratio > BULL_WIN_BET_RATIO:
        score += 0.3 * FEATURE_WEIGHTS["bet_ratio"]
    elif bet_ratio < BEAR_WIN_BET_RATIO:
        score -= 0.3 * FEATURE_WEIGHTS["bet_ratio"]

    volatility_factor = min(price_volatility * 2, 0.2)
    score += volatility_factor * FEATURE_WEIGHTS["price_volatility"]

    if total_amount > 5.0:
        score += 0.2 * FEATURE_WEIGHTS["total_bets_amount"]
    elif total_amount < 1.0:
        score -= 0.1 * FEATURE_WEIGHTS["total_bets_amount"]

    hourly_bull_rate = HOURLY_BULL_RATES.get(current_hour, 0.5)
    hour_bias = (hourly_bull_rate - 0.5) * 2
    score += hour_bias * FEATURE_WEIGHTS["hour"]

    if current_day in [5, 6]:
        score += 0.05 * FEATURE_WEIGHTS["day_of_week"]

    bull_whales = bet_data.get("bull_whales", 0)
    bear_whales = bet_data.get("bear_whales", 0)

    if bull_whales > bear_whales:
        score += 0.1
    elif bear_whales > bull_whales:
        score -= 0.1

    return max(-1.0, min(1.0, score))


def fetch_bets(start_block, end_block, current_epoch):
    """Fetch live bet data for current round"""
    try:
        bet_bull_logs = web3.eth.get_logs({
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": CONTRACT_ADDRESS,
            "topics": [bet_bull_topic]
        })
        bet_bear_logs = web3.eth.get_logs({
            "fromBlock": start_block,
            "toBlock": end_block,
            "address": CONTRACT_ADDRESS,
            "topics": [bet_bear_topic]
        })
        
        bet_bull_events = [
            contract.events.BetBull().process_log(log)
            for log in bet_bull_logs
            if contract.events.BetBull().process_log(log)['args']['epoch'] == current_epoch
        ]
        bet_bear_events = [
            contract.events.BetBear().process_log(log)
            for log in bet_bear_logs
            if contract.events.BetBear().process_log(log)['args']['epoch'] == current_epoch
        ]

        all_bets = []
        for event in bet_bull_events:
            amount_bnb = event['args']['amount'] / 1e18
            all_bets.append({
                "side": "Bull",
                "amount_bnb": amount_bnb,
                "user": event['args']['sender'],
                "epoch": event['args']['epoch']
            })
        for event in bet_bear_events:
            amount_bnb = event['args']['amount'] / 1e18
            all_bets.append({
                "side": "Bear",
                "amount_bnb": amount_bnb,
                "user": event['args']['sender'],
                "epoch": event['args']['epoch']
            })

        bull_amount = sum(bet["amount_bnb"] for bet in all_bets if bet["side"] == "Bull")
        bear_amount = sum(bet["amount_bnb"] for bet in all_bets if bet["side"] == "Bear")
        total_amount = bull_amount + bear_amount

        bull_whales = sum(1 for b in all_bets if b["side"] == "Bull" and b["amount_bnb"] >= 0.84)
        bear_whales = sum(1 for b in all_bets if b["side"] == "Bear" and b["amount_bnb"] >= 0.84)

        bull_payout = total_amount / bull_amount if bull_amount > 0 else 0
        bear_payout = total_amount / bear_amount if bear_amount > 0 else 0

        bull_percent = (bull_amount / total_amount) * 100 if total_amount > 0 else 0
        bear_percent = (bear_amount / total_amount) * 100 if total_amount > 0 else 0

        max_bet_on_bull = max([bet["amount_bnb"] for bet in all_bets if bet["side"] == "Bull"], default=0)
        max_bet_on_bear = max([bet["amount_bnb"] for bet in all_bets if bet["side"] == "Bear"], default=0)

        # Update price history (simplified - using total pool as price proxy)
        if total_amount > 0:
            price_history.append(total_amount)
            if len(price_history) > 20:
                price_history.pop(0)

        return {
            "bull_amount": bull_amount,
            "bear_amount": bear_amount,
            "total_amount": total_amount,
            "bull_payout": bull_payout,
            "bear_payout": bear_payout,
            "bull_percent": bull_percent,
            "bear_percent": bear_percent,
            "max_bet_on_bull": max_bet_on_bull,
            "max_bet_on_bear": max_bet_on_bear,
            "bull_whales": bull_whales,
            "bear_whales": bear_whales,
            "all_bets": all_bets
        }
    except Exception as e:
        # Return default values if fetching fails
        return {
            "bull_amount": 0, "bear_amount": 0, "total_amount": 0, "bull_payout": 0, "bear_payout": 0,
            "bull_percent": 0, "bear_percent": 0, "max_bet_on_bull": 0,
            "max_bet_on_bear": 0, "bull_whales": 0, "bear_whales": 0, "all_bets": []
        }


def get_block_by_timestamp(target_timestamp, before=True):
    """Get block number by timestamp"""
    try:
        latest_block = web3.eth.block_number
        low = max(1, latest_block - 50000)  # Limit search range
        high = latest_block
        while low < high:
            mid = (low + high) // 2
            try:
                block = web3.eth.get_block(mid)
                block_time = block.timestamp
                if block_time < target_timestamp:
                    low = mid + 1
                else:
                    high = mid
            except:
                break
        return (low - 1) if before and low > 1 else low
    except:
        return web3.eth.block_number


def main_loop():
    global last_round_close_price, first_timer_print

    print("⏳ Initializing viewer...")
    fetch_round_history()
    display_rounds_history()

    current_epoch = contract.functions.currentEpoch().call()
    current_round = contract.functions.rounds(current_epoch).call()
    start_ts = current_round[1]
    end_ts = current_round[2]

    if len(rounds_history) > 0:
        last_round_close_price = rounds_history[-1]['close_price_usdt']
    else:
        last_round_close_price = 0

    print(f"\n🔄 Current Epoch: {current_epoch}")
    print(f"🕒 Round ends at: {datetime.fromtimestamp(end_ts)}")

    start_block = get_block_by_timestamp(start_ts, before=False)

    first_timer_print = True

    while True:
        now = int(time.time())
        time_left = end_ts - now

        if time_left <= 0:
            print("\n🔴 ROUND ENDED - Waiting for next round...")
            break

        live_price = get_live_bnb_price()

        if last_round_close_price > 0:
            price_diff = live_price - last_round_close_price
            if price_diff > 0:
                price_direction = f"🟩 +{price_diff:.4f}"
            elif price_diff < 0:
                price_direction = f"🟥 {price_diff:.4f}"
            else:
                price_direction = "➡️ +0.0000"
        else:
            price_direction = "➡️ +0.0000"

        if time_left <= 10:
            timer_color = "🔴"
        elif time_left <= 30:
            timer_color = "🟡"
        else:
            timer_color = "🟢"

        # Only fetch bet data when time_left <= 25 to save RPC calls
        if time_left <= 25:
            try:
                latest_block = web3.eth.block_number
                bet_data = fetch_bets(start_block, latest_block, current_epoch)
                bull_percent = bet_data["bull_percent"]
                bear_percent = bet_data["bear_percent"]
                total_amount = bet_data["total_amount"]
                max_bet_on_bull = bet_data["max_bet_on_bull"]
                max_bet_on_bear = bet_data["max_bet_on_bear"]
                bull_whales = bet_data["bull_whales"]
                bear_whales = bet_data["bear_whales"]
                bet_ratio = bet_data["bull_amount"] / bet_data["bear_amount"] if bet_data["bear_amount"] > 0 else 2.0
                ml_score = calculate_ml_prediction_score(bet_data)
            except Exception:
                bull_percent = bear_percent = total_amount = max_bet_on_bull = max_bet_on_bear = 0
                bull_whales = bear_whales = 0
                bet_ratio = ml_score = 0

            # Move cursor up 2 lines if not first print, else print blank line to start
            if not first_timer_print:
                sys.stdout.write('\033[F\033[F')
            else:
                print()  # Ensure there is space for 2 lines
                first_timer_print = False

            # Print timer line and stats line
            sys.stdout.write(f"{timer_color} TIME: {time_left:.0f}s | 💰 Live BNB: ${live_price:.4f} {price_direction}{' '*40}\n")
            sys.stdout.write(f"📊 Bull: {bull_percent:.1f}% | Bear: {bear_percent:.1f}% | Ratio: {bet_ratio:.2f} | Pool: {total_amount:.4f} | Max Bull: {max_bet_on_bull:.3f} | Max Bear: {max_bet_on_bear:.3f} | Bull Whales: {bull_whales} | Bear Whales: {bear_whales} | ML: {ml_score:.3f}{' '*10}\n")
            sys.stdout.flush()
        else:
            # Only timer line
            if not first_timer_print:
                sys.stdout.write('\033[F\033[F')
            else:
                print()
                first_timer_print = False

            sys.stdout.write(f"{timer_color} TIME: {time_left:.0f}s | 💰 Live BNB: ${live_price:.4f} {price_direction}{' '*40}\n")
            sys.stdout.write(' '*120 + '\n')
            sys.stdout.flush()

        if time_left <= 0:
            break

        time.sleep(1)


if __name__ == "__main__":
    print("🚀 PANCAKESWAP PREDICTION VIEWER")
    print("👀 View-Only Mode: Monitor rounds, streaks & price movements!")
    print("📊 Live bet data: Shows ONLY in last 25 seconds (saves RPC calls)")
    print("🚨 Streak + price movement notifications enabled!")
    print("💰 Live BNB price with 10-second caching!")
    print("⏰ Telegram notifications delayed 3 seconds!")
    print("📈 24-round summary in ALL notifications!")

    while True:
        try:
            main_loop()
        except Exception as e:
            print(f"\n⚠️ Main loop error: {e}")

        print("\n⏳ Waiting 170 seconds before checking next round...\n")
        for i in range(170, 0, -1):
            print(f"\r⏳ Next round check in {i} seconds...", end="")
            time.sleep(1)