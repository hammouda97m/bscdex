# RICH Multi-Bot Prediction System - Complete Documentation

```
██████╗ ██╗ ██████╗██╗  ██╗    ███████╗██╗   ██╗███████╗████████╗███████╗███╗   ███╗
██╔══██╗██║██╔════╝██║  ██║    ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝████╗ ████║
██████╔╝██║██║     ███████║    ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██╔████╔██║
██╔══██╗██║██║     ██╔══██║    ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║╚██╔╝██║
██║  ██║██║╚██████╗██║  ██║    ███████║   ██║   ███████║   ██║   ███████╗██║ ╚═╝ ██║
╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝    ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚═╝     ╚═╝
```

**Advanced Multi-Bot Prediction Betting System for PancakeSwap**
**Version:** 2.0  
**Last Updated:** January 2025  
**Author:** RICH Development Team

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Multi-Bot Coordination](#multi-bot-coordination)
4. [Core Components](#core-components)
5. [Machine Learning Engine](#machine-learning-engine)
6. [Betting Strategies](#betting-strategies)
7. [Loss Prevention System](#loss-prevention-system)
8. [Automated Claimer](#automated-claimer)
9. [Configuration & Setup](#configuration--setup)
10. [Operation Workflows](#operation-workflows)
11. [Data Structures](#data-structures)
12. [API & Integration](#api--integration)
13. [Monitoring & Analytics](#monitoring--analytics)
14. [Troubleshooting](#troubleshooting)
15. [FAQ](#faq)
16. [Appendices](#appendices)

---

## 1. Executive Summary

### 1.1 What is the RICH System?

The RICH (Rapid Intelligence Crypto Hedge) system is an advanced, multi-bot automated prediction betting platform designed for PancakeSwap's BNB/USD prediction markets. It operates **THREE IDENTICAL BETTING BOTS** simultaneously, each managing a separate wallet while sharing critical loss prevention data to minimize risk and maximize returns.

### 1.2 Key Features

- **🤖 Triple Bot Architecture**: Three identical bots (fin1, fin2, fin3) operating simultaneously
- **🧠 ML-Powered Decisions**: 8-feature machine learning model with 55% accuracy
- **📊 Real-Time Analysis**: BTC correlation tracking, price momentum, and volatility analysis
- **🛡️ Shared Loss Prevention**: Coordinated 5-round skip after any bot loses
- **💰 Automated Claiming**: Claimer bot handles all 12 wallets automatically
- **🔄 Strategy Switching**: Dynamic contrarian/consensus strategy updates
- **📈 Comprehensive Logging**: CSV bet history with 40+ data points per bet
- **⏰ Smart Timing**: Staggered bet placement to avoid detection (0min, 5min, 10min delays)

### 1.3 System Performance

- **Win Rate**: ~55% (ML model accuracy on test data)
- **Average Confidence**: HIGH (60%), MEDIUM (30%), LOW (10%)
- **Bet Frequency**: ~1 bet every 2-3 rounds per bot
- **Risk Management**: 5-round pause after loss, dynamic bet sizing (2-6% of balance)

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RICH SYSTEM ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────┘

                        ┌──────────────────────┐
                        │  PancakeSwap Smart   │
                        │  Contract (BSC)      │
                        │  0x18B2A6...49cdA    │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │   Chainlink Price Feeds     │
                    │   BNB/USD + BTC/USD         │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐        ┌────────▼────────┐        ┌───────▼────────┐
│   Bot 1        │        │   Bot 2         │        │   Bot 3        │
│   (fin1.py)    │        │   (fin2.py)     │        │   (fin3.py)    │
│   WALLET_1     │        │   WALLET_2      │        │   WALLET_3     │
│   Immediate    │        │   +5min delay   │        │   +10min delay │
└───────┬────────┘        └────────┬────────┘        └───────┬────────┘
        │                          │                          │
        └──────────────┬───────────┴──────────────┬───────────┘
                       │                          │
            ┌──────────▼──────────┐    ┌──────────▼──────────┐
            │ shared_loss_state   │    │  rounds_cache.json  │
            │      .json          │    │  (24 round history) │
            │ (Shared skip count) │    │                     │
            └──────────┬──────────┘    └─────────────────────┘
                       │
            ┌──────────▼──────────┐
            │   bet_history/      │
            │   bets.csv          │
            │   (All bets logged) │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │   claimer_bot.py    │
            │   (Every 300s)      │
            │   Handles 12 wallets│
            └─────────────────────┘

           ┌────────────────────────────────────┐
           │     Supporting Tools               │
           ├────────────────────────────────────┤
           │ • strategy_updater.py              │
           │   (Contrarian ⟷ Consensus)        │
           │ • ml_insights_updater.py           │
           │   (Update ML params from JSON)     │
           │ • ML/DG.py (Data Gathering)        │
           │ • ML/ML.py (Model Training)        │
           └────────────────────────────────────┘
```

### 2.2 Component Overview

| Component | File | Purpose | Status |
|-----------|------|---------|--------|
| Main Bot 1 | `fin1.py` | Primary betting bot, Wallet 1 | Active |
| Main Bot 2 | `fin2.py` | Secondary bot, Wallet 2, +5min delay | Active |
| Main Bot 3 | `fin3.py` | Tertiary bot, Wallet 3, +10min delay | Active |
| Claimer | `claimer_bot.py` | Claims rewards for all wallets | Active |
| Strategy Updater | `strategy_updater.py` | Switches betting strategies | Tool |
| ML Insights | `ml_insights_updater.py` | Updates ML parameters | Tool |
| Data Gatherer | `ML/DG.py` | Scrapes historical data | Tool |
| ML Trainer | `ML/ML.py` | Trains prediction models | Tool |
| Loss State | `shared_loss_state.json` | Coordinated loss prevention | Data |
| Cache | `rounds_cache.json` | 24-round history cache | Data |
| Bet Log | `bet_history/bets.csv` | Complete bet records | Data |

### 2.3 Network Configuration

```python
# BSC Mainnet Configuration
RPC_ENDPOINT = "https://bsc-mainnet.nodereal.io/v1/a16acfa17ef245b7973338fef461c447"
CONTRACT_ADDRESS = "0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA"
CHAINLINK_BNB_USD = "0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE"

# Gas Configuration
GAS_LIMIT = 200000
GAS_PRICE = 0.1 gwei  # Base price, adds dynamic pricing
```

---

## 3. Multi-Bot Coordination

### 3.1 Why Three Bots?

The system runs **three identical bots** to:

1. **Diversify Risk**: Three separate wallets mean losses are isolated
2. **Avoid Detection**: Staggered timing prevents pattern recognition
3. **Maximize Opportunities**: Different delay timings catch different market conditions
4. **Statistical Edge**: More bets = smoother variance, closer to expected value

### 3.2 Bot Differences

```python
# fin1.py - Line 26
BOT_NUMBER = 1  # Bets immediately (0 second delay)

# fin2.py - Line 26  
BOT_NUMBER = 2  # Waits 5 minutes before betting logic starts

# fin3.py - Line 26
BOT_NUMBER = 3  # Waits 10 minutes before betting logic starts
```

**All other code is IDENTICAL** - this ensures consistent strategy across all bots.

### 3.3 Timing Strategy

```
Round Start (0:00)
│
├─ Bot 1: Starts analysis immediately
│          └─ Places bet at ~35-40s mark
│
├─ Bot 2: Waits 5 minutes
│          └─ Starts analysis at 5:00
│          └─ Places bet at ~5:35-5:40 mark
│
└─ Bot 3: Waits 10 minutes
           └─ Starts analysis at 10:00
           └─ Places bet at ~10:35-10:40 mark

Round End (5:00 minutes total)
```

### 3.4 Shared Loss Prevention

All three bots share a **single loss prevention state** file:

```json
{
  "skip_rounds_remaining": 5,
  "last_loss_epoch": 418606,
  "loss_bot": "Bot3",
  "timestamp": "2025-10-05T05:39:32.699043"
}
```

**How it works:**

```
┌─────────────────────────────────────────────────────────┐
│           SHARED LOSS PREVENTION FLOW                    │
└─────────────────────────────────────────────────────────┘

Bot 1 LOSES in epoch 418606
    │
    ├─ Saves: skip_rounds_remaining = 5
    │         loss_bot = "Bot1"
    │         last_loss_epoch = 418606
    │
    ▼
All Bots Read File on Next Round
    │
    ├─ Bot 1: Sees skip = 5, SKIPS betting
    ├─ Bot 2: Sees skip = 5, SKIPS betting  
    └─ Bot 3: Sees skip = 5, SKIPS betting
    │
    ▼
Each Round Decrements skip_rounds_remaining
    │
    ├─ Round 1: skip = 4
    ├─ Round 2: skip = 3
    ├─ Round 3: skip = 2
    ├─ Round 4: skip = 1
    └─ Round 5: skip = 0 → ALL BOTS RESUME
```

**Code Implementation (fin1.py, lines 976-984):**

```python
# Load shared loss state at startup
shared_state = load_shared_loss_state()
skip_rounds_remaining = shared_state["skip_rounds_remaining"]

# Countdown at start of each round
if skip_rounds_remaining > 0:
    new_skip_count = max(0, skip_rounds_remaining - 1)
    save_shared_loss_state(new_skip_count, shared_state["last_loss_epoch"], f"Bot{BOT_NUMBER}")
```

---

## 4. Core Components

### 4.1 Main Betting Bots (fin1.py, fin2.py, fin3.py)

**File Size:** 1,204 lines each  
**Language:** Python 3.8+  
**Dependencies:** web3, requests, pandas, python-dotenv

#### 4.1.1 Key Functions

| Function | Lines | Purpose |
|----------|-------|---------|
| `main_loop()` | 972-1204 | Main betting cycle, waits for rounds |
| `enhanced_decision_logic()` | 694-819 | Core betting decision engine |
| `calculate_ml_prediction_score()` | 578-692 | ML-based scoring system |
| `fetch_bets()` | 820-913 | Collects bet data from blockchain |
| `place_bet()` | 915-970 | Executes transaction on-chain |
| `fetch_round_history()` | 442-504 | Loads last 24 rounds for analysis |
| `save_bet_snapshot_csv()` | 125-202 | Logs bet details to CSV |
| `get_live_bnb_price()` | 236-254 | Chainlink price feed with 8s cache |
| `get_btc_data()` | 258-297 | BTC 5-min tracking with 30s cache |
| `calculate_btc_influence()` | 299-323 | BTC correlation scoring (-0.4 to +0.4) |
| `should_use_streak_for_ml()` | 327-357 | Validates streak against price action |

#### 4.1.2 Global Variables

```python
# Bot Configuration
BOT_NUMBER = 1  # Changes to 2 or 3 in other files
PRIVATE_KEY = os.getenv(f"PRIVATE_KEY_{BOT_NUMBER}")
WALLET_ADDRESS = os.getenv(f"WALLET_ADDRESS_{BOT_NUMBER}")

# Blockchain Connection
web3 = Web3(Web3.HTTPProvider("https://bsc-mainnet.nodereal.io/..."))
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
price_feed = web3.eth.contract(address=CHAINLINK_BNB_USD, abi=CHAINLINK_ABI)

# State Management
bet_placed_last_round = False
last_bet_epochs = []
skip_rounds_remaining = 0
last_loss_epoch = None

# Streak Tracking
current_streak = 0
current_streak_type = None  # 'BULL' or 'BEAR'
rounds_history = []  # Last 24 rounds

# Caching
last_price_fetch = 0
cached_price = 0
last_btc_fetch = 0
cached_btc_data = {"price": 0, "change_5min": 0}
price_history = []

# Files
CACHE_FILE = "rounds_cache.json"
SHARED_LOSS_FILE = "shared_loss_state.json"
```

#### 4.1.3 ML Configuration

```python
# Updated hourly bull win rates (from 10k rounds analysis)
HOURLY_BULL_RATES = {
    0: 0.5,    1: 0.5,    2: 0.5,    3: 0.5,    4: 0.5,    5: 0.5,
    6: 0.5,    7: 0.5,    8: 0.5,    9: 0.5,    10: 0.5,   11: 0.5,
    12: 0.667, 13: 0.545, 14: 0.75,  15: 0.333, 16: 0.583, 17: 0.818,
    18: 0.5,   19: 0.364, 20: 0.5,   21: 0.5,   22: 0.5,   23: 0.5
}

# Feature importance from Random Forest model
FEATURE_WEIGHTS = {
    "bet_ratio": 0.1933,           # Most important
    "price_volatility": 0.1905,    # Second most important
    "bull_bets_amount": 0.1434,
    "bear_bets_amount": 0.1348,
    "total_bet_log": 0.1315,
    "total_bets_amount": 0.1177,
    "hour": 0.0889,
    "day_of_week": 0.0000          # Not predictive
}

# Key thresholds (from 10k rounds)
BULL_WIN_BET_RATIO = 1.043021637000436
BEAR_WIN_BET_RATIO = 0.9752999098946478
```

### 4.2 Claimer Bot (claimer_bot.py)

**File Size:** 294 lines  
**Purpose:** Automatically claims rewards for ALL wallets  
**Execution Frequency:** Every 300 seconds (5 minutes)

#### 4.2.1 Architecture

```
┌─────────────────────────────────────────────────────┐
│              CLAIMER BOT WORKFLOW                    │
└─────────────────────────────────────────────────────┘

Every 300 seconds:
    │
    ├─ Read bet_history/bets.csv
    │  └─ Filter: claimed == 'no'
    │
    ├─ For each unclaimed bet:
    │   │
    │   ├─ Check if epoch is finished (closePrice > 0)
    │   │  └─ If LIVE: Skip to next cycle
    │   │
    │   ├─ Call contract.claimable(epoch, wallet_address)
    │   │  │
    │   │  ├─ If claimable > 0: WIN!
    │   │  │  ├─ Record balance_before
    │   │  │  ├─ Execute claim transaction
    │   │  │  ├─ Record balance_after
    │   │  │  ├─ Calculate net_profit = balance_after - balance_before - original_bet
    │   │  │  ├─ Update CSV: result='win', reward_amount=net_profit
    │   │  │  ├─ Send Telegram: "💰 WIN! Net profit: X BNB"
    │   │  │  └─ Reset shared loss: skip_rounds = 0
    │   │  │
    │   │  └─ If claimable == 0: LOSS!
    │   │     ├─ Calculate loss_amount = -original_bet
    │   │     ├─ Update CSV: result='loss', reward_amount=loss_amount
    │   │     ├─ Send Telegram: "⛔ LOSS! Skip 5 rounds"
    │   │     └─ Set shared loss: skip_rounds = 5
    │   │
    │   └─ Wait 2 seconds before next claim
    │
    └─ Print summary: X processed, Y skipped
```

#### 4.2.2 Key Functions

```python
def check_and_claim_bet(bet_record):
    """
    Check and claim reward for a single bet
    Returns: {"result": "win"/"loss", "reward_amount": float, "claimed": "yes"}
    """
    epoch = int(bet_record['epoch'])
    wallet_num = int(bet_record['wallet_number'])
    
    # NEW: Skip if epoch not finished
    if not is_epoch_finished(epoch):
        return None  # Will retry next cycle
    
    # Check claimable amount
    claimable_amount = contract.functions.claimable(epoch, wallet_address).call()
    
    if claimable_amount > 0:
        # WIN: Claim and calculate net profit
        balance_before = web3.eth.get_balance(wallet_address)
        # ... execute claim transaction ...
        balance_after = web3.eth.get_balance(wallet_address)
        
        reward_bnb_real = web3.from_wei(balance_after - balance_before, 'ether')
        net_profit = float(reward_bnb_real) - float(original_bet_amount)
        
        # Reset shared loss state
        save_shared_loss_state(0, None, f"WIN_W{wallet_num}")
        
        return {"result": "win", "reward_amount": net_profit, "claimed": "yes"}
    else:
        # LOSS: Calculate loss and set shared skip
        loss_amount = -float(original_bet_amount)
        save_shared_loss_state(5, epoch, f"LOSS_W{wallet_num}")
        
        return {"result": "loss", "reward_amount": loss_amount, "claimed": "yes"}
```

#### 4.2.3 Wallet Configuration

The claimer handles **12 wallets** (configurable in `.env`):

```python
# Load all 12 wallets
WALLETS = {}
for i in range(1, 13):
    private_key = os.getenv(f"PRIVATE_KEY_{i}")
    wallet_address = os.getenv(f"WALLET_ADDRESS_{i}")
    if private_key and wallet_address:
        WALLETS[i] = {
            "private_key": private_key,
            "address": wallet_address
        }
```

Currently only **3 wallets** (Bot 1-3) are actively betting, but the claimer can handle up to 12.

### 4.3 Strategy Updater (strategy_updater.py)

**File Size:** 570 lines  
**Purpose:** Switch between Contrarian and Consensus strategies

#### 4.3.1 Strategy Comparison

| Aspect | Contrarian Strategy | Consensus Strategy |
|--------|---------------------|-------------------|
| **Whale Logic** | Bet AGAINST whale | Bet WITH whale |
| **ML Signal** | Follow directly (bull ML → bull bet) | Invert (bull ML → bear bet) |
| **Bet Ratio** | Bet against high ratios | Bet with high ratios |
| **Philosophy** | "Smart money is wrong" | "Smart money is right" |
| **Win Rate** | ~55% (historical) | ~50% (needs testing) |

#### 4.3.2 Code Differences

**Contrarian (Current Strategy):**
```python
# Priority 1: Whale logic
if whale_bet_side and skip_rounds_remaining == 0:
    if abs(ml_score) <= 0.08:
        opposite_side = "bear" if whale_bet_side == "bull" else "bull"  # AGAINST
        return opposite_side, "HIGH (Against whale - ML too weak)"
    else:
        same_side = whale_bet_side  # WITH whale when ML agrees
        return same_side, "HIGH (Follow whale - ML agrees)"

# Priority 2: Bet ratio logic
if bet_ratio > BEAR_WIN_BET_RATIO and max_bet_on_bull >= 0.7:
    payout_decision = "bear"  # Bet AGAINST bulls
elif bet_ratio < BULL_WIN_BET_RATIO and max_bet_on_bear >= 0.7:
    payout_decision = "bull"  # Bet AGAINST bears

# ML decision
if ml_score > 0.05:
    ml_decision = "bull"  # Follow ML directly
elif ml_score < -0.05:
    ml_decision = "bear"
```

**Consensus:**
```python
# Priority 1: Whale logic (FLIPPED)
if whale_bet_side and skip_rounds_remaining == 0:
    if abs(ml_score) <= 0.08:
        opposite_side = "bear" if whale_bet_side == "bear" else "bull"  # WITH
        return opposite_side, "HIGH (With whale - ML confirms)"

# Priority 2: Bet ratio logic (FLIPPED)
if bet_ratio > BEAR_WIN_BET_RATIO and max_bet_on_bull >= 0.7:
    payout_decision = "bull"  # Bet WITH bulls
elif bet_ratio < BULL_WIN_BET_RATIO and max_bet_on_bear >= 0.7:
    payout_decision = "bear"  # Bet WITH bears

# ML decision (INVERTED)
if ml_score > 0.05:
    ml_decision = "bear"  # INVERT ML
elif ml_score < -0.05:
    ml_decision = "bull"  # INVERT ML
```

#### 4.3.3 Usage

```bash
# Run interactive menu
python strategy_updater.py

Options:
1. Show current strategy for all files
2. Switch to CONTRARIAN strategy
3. Switch to CONSENSUS strategy
4. Exit

# The tool will:
# 1. Auto-detect all fin*.py files (fin1.py, fin2.py, fin3.py)
# 2. Show current strategy for each file
# 3. Allow selective or bulk updates
# 4. Create backups in backup/ folder before modifying
# 5. Validate updates after completion
```

### 4.4 ML Insights Updater (ml_insights_updater.py)

**File Size:** 364 lines  
**Purpose:** Update ML parameters from JSON analysis results

#### 4.4.1 Workflow

```
┌─────────────────────────────────────────────────────┐
│         ML INSIGHTS UPDATE WORKFLOW                  │
└─────────────────────────────────────────────────────┘

1. Train ML model (ML/ML.py) on historical data
   └─ Outputs: analysis_results.json

2. Run ml_insights_updater.py
   │
   ├─ Reads analysis_results.json
   │  └─ Contains: feature_importance, hourly_bull_rates, bet_ratios
   │
   ├─ Formats Python code sections:
   │  ├─ HOURLY_BULL_RATES = {...}
   │  ├─ FEATURE_WEIGHTS = {...}
   │  └─ BULL_WIN_BET_RATIO / BEAR_WIN_BET_RATIO
   │
   ├─ Updates all fin*.py files (fin1-fin12)
   │  ├─ Creates backups: fin1.py_backup_YYYYMMDD_HHMMSS
   │  ├─ Replaces code sections using regex
   │  └─ Validates updates
   │
   └─ Summary: X/Y files updated successfully
```

#### 4.4.2 analysis_results.json Structure

```json
{
  "model_accuracy": {
    "random_forest": 0.55,
    "logistic_regression": 0.50
  },
  "feature_importance": [
    {"feature": "bet_ratio", "importance": 0.1933},
    {"feature": "price_volatility", "importance": 0.1905},
    {"feature": "bull_bets_amount", "importance": 0.1434},
    {"feature": "bear_bets_amount", "importance": 0.1348},
    {"feature": "total_bet_log", "importance": 0.1315},
    {"feature": "total_bets_amount", "importance": 0.1177},
    {"feature": "hour", "importance": 0.0889},
    {"feature": "day_of_week", "importance": 0.0000}
  ],
  "patterns": {
    "bull_avg_bet_ratio": 1.043021637000436,
    "bear_avg_bet_ratio": 0.9752999098946478,
    "hourly_bull_rates": {
      "12": 0.6667,
      "13": 0.5455,
      "14": 0.75,
      "15": 0.3333,
      "16": 0.5833,
      "17": 0.8182,
      "18": 0.5,
      "19": 0.3636
    }
  }
}
```

#### 4.4.3 Usage

```bash
# Update all fin*.py files (fin1-fin12)
python ml_insights_updater.py

# Update specific file
python ml_insights_updater.py --single fin5.py

# Update range
python ml_insights_updater.py --range 1 3  # Updates fin1-fin3

# Help
python ml_insights_updater.py --help
```

---

## 5. Machine Learning Engine

### 5.1 ML Model Overview

The system uses a **Random Forest Classifier** with 8 features to predict round outcomes.

```
┌────────────────────────────────────────────────────┐
│        ML MODEL ARCHITECTURE                        │
└────────────────────────────────────────────────────┘

Input Features (8):
    ├─ bet_ratio (19.33% importance)
    ├─ price_volatility (19.05%)
    ├─ bull_bets_amount (14.34%)
    ├─ bear_bets_amount (13.48%)
    ├─ total_bet_log (13.15%)
    ├─ total_bets_amount (11.77%)
    ├─ hour (8.89%)
    └─ day_of_week (0.00% - not predictive)
    
         ↓
    
Random Forest Classifier
    ├─ 100 decision trees
    ├─ Trained on 10,000+ rounds
    ├─ 80/20 train/test split
    └─ Class weights: balanced
    
         ↓
    
Output: Prediction Score (-1 to +1)
    ├─ Positive = Bull bias
    ├─ Negative = Bear bias
    └─ Magnitude = Confidence
```

### 5.2 Feature Engineering

#### 5.2.1 Feature Descriptions

| Feature | Formula | Range | Importance | Description |
|---------|---------|-------|------------|-------------|
| **bet_ratio** | `bull_amount / bear_amount` | 0 to ∞ | 19.33% | Most important - indicates market sentiment |
| **price_volatility** | `rolling_std(price, 10)` | 0 to 1 | 19.05% | Recent price movement variance |
| **bull_bets_amount** | `sum(bull_bets)` | 0 to ∞ | 14.34% | Total BNB on bull side |
| **bear_bets_amount** | `sum(bear_bets)` | 0 to ∞ | 13.48% | Total BNB on bear side |
| **total_bet_log** | `log(total_amount + 1)` | 0 to ∞ | 13.15% | Pool size (log-scaled) |
| **total_bets_amount** | `bull + bear` | 0 to ∞ | 11.77% | Raw pool size |
| **hour** | `datetime.now().hour` | 0 to 23 | 8.89% | Time-based patterns |
| **day_of_week** | `datetime.now().weekday()` | 0 to 6 | 0.00% | Not predictive |

#### 5.2.2 Feature Calculation (Code)

```python
def calculate_ml_prediction_score(bet_data):
    """
    Calculate prediction score from -1 (bear) to +1 (bull)
    """
    # Extract raw data
    bull_amount = bet_data["bull_amount"]
    bear_amount = bet_data["bear_amount"]
    total_amount = bet_data["total_amount"]
    current_epoch = bet_data.get("current_epoch", 0)
    
    # Calculate features
    bet_ratio = bull_amount / bear_amount if bear_amount > 0 else 2.0
    total_bet_log = math.log(total_amount + 1)
    real_volatility = calculate_real_price_volatility()  # Rolling 10-round std
    
    # Time features
    current_hour = datetime.now().hour
    current_day = datetime.now().weekday()
    
    # Initialize score
    score = 0.0
    
    # Feature 1: Bet ratio (19.33% weight)
    if bet_ratio > BULL_WIN_BET_RATIO:  # 1.043
        score += 0.3 * FEATURE_WEIGHTS["bet_ratio"]
    elif bet_ratio < BEAR_WIN_BET_RATIO:  # 0.975
        score -= 0.3 * FEATURE_WEIGHTS["bet_ratio"]
    
    # Feature 2: Price volatility (19.05% weight)
    volatility_factor = min(real_volatility * 2, 0.2)
    score += volatility_factor * FEATURE_WEIGHTS["price_volatility"]
    
    # Feature 3-4: Pool size
    if total_amount > 5.0:
        score += 0.2 * FEATURE_WEIGHTS["total_bets_amount"]
    elif total_amount < 1.0:
        score -= 0.1 * FEATURE_WEIGHTS["total_bets_amount"]
    
    # Feature 5: Hourly patterns (8.89% weight)
    hourly_bull_rate = HOURLY_BULL_RATES.get(current_hour, 0.5)
    hour_bias = (hourly_bull_rate - 0.5) * 2  # Convert to -1 to 1
    score += hour_bias * FEATURE_WEIGHTS["hour"]
    
    # Feature 6: Day of week (0% - skipped)
    # Not used as it has no predictive power
    
    # Additional signals (not in original ML model)
    # Whale count pressure (contrarian)
    bull_whales = bet_data.get("bull_whales", 0)
    bear_whales = bet_data.get("bear_whales", 0)
    if bull_whales > bear_whales:
        score -= 0.1  # Bet against bull whales
    elif bear_whales > bull_whales:
        score += 0.1  # Bet against bear whales
    
    # BTC influence (-0.4 to +0.4)
    btc_influence = calculate_btc_influence()
    score += btc_influence
    
    # Price momentum
    momentum_score = calculate_price_momentum()
    score += momentum_score * 0.15
    
    # Big move reversal (>$2.75 USDT)
    if len(rounds_history) >= 1:
        last_move = abs(rounds_history[-1]['price_change_usdt'])
        if last_move > 2.75:
            if rounds_history[-1]['price_change_usdt'] > 0:
                score -= 0.08  # Big up → expect down
            else:
                score += 0.08  # Big down → expect up
    
    # Streak reversal (10+ streaks)
    if current_streak >= 10 and should_use_streak_for_ml(current_epoch):
        streak_bias = min(current_streak * 0.05, 0.15)
        if current_streak_type == "BULL":
            score -= streak_bias  # Expect reversal
        elif current_streak_type == "BEAR":
            score += streak_bias
    
    # Clamp to [-1, 1]
    return max(-1.0, min(1.0, score))
```

### 5.3 BTC Correlation Tracking

The system tracks **Bitcoin's 5-minute price changes** and uses them to influence predictions.

#### 5.3.1 BTC Data Collection

```python
def get_btc_data():
    """
    Get BTC price and 5-minute change with 30-second caching
    Uses Binance API (free, fast)
    """
    global last_btc_fetch, cached_btc_data
    
    # Return cached if < 30 seconds old
    if time.time() - last_btc_fetch < 30 and cached_btc_data["price"] > 0:
        return cached_btc_data
    
    try:
        # Get current price
        response = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", 
            timeout=5
        )
        data = response.json()
        current_price = float(data["lastPrice"])
        
        # Get 5-minute kline data
        kline_response = requests.get(
            "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=6",
            timeout=5
        )
        klines = kline_response.json()
        
        # Price 5 minutes ago
        price_5min_ago = float(klines[0][4])
        change_5min = ((current_price - price_5min_ago) / price_5min_ago) * 100
        
        cached_btc_data = {
            "price": current_price,
            "change_5min": change_5min
        }
        last_btc_fetch = time.time()
        return cached_btc_data
        
    except Exception as e:
        return cached_btc_data if cached_btc_data["price"] > 0 else {"price": 0, "change_5min": 0}
```

#### 5.3.2 BTC Influence Scoring

```python
def calculate_btc_influence():
    """
    Calculate BTC influence on BNB prediction
    Returns: -0.4 to +0.4
    """
    btc_data = get_btc_data()
    change_5min = btc_data["change_5min"]
    
    # 5-minute thresholds
    if change_5min > 1.5:        # Strong 5min pump (>1.5%)
        return 0.4
    elif change_5min > 0.8:      # Medium pump (0.8-1.5%)
        return 0.3
    elif change_5min > 0.3:      # Small pump (0.3-0.8%)
        return 0.2
    elif change_5min < -1.5:     # Strong dump (<-1.5%)
        return -0.4
    elif change_5min < -0.8:     # Medium dump (-1.5 to -0.8%)
        return -0.3
    elif change_5min < -0.3:     # Small dump (-0.8 to -0.3%)
        return -0.2
    else:                        # Sideways (-0.3% to +0.3%)
        return 0.0
```

**Why 5 minutes?** PancakeSwap prediction rounds are 5 minutes long, so BTC's price action during the same timeframe is highly relevant.

### 5.4 Price Volatility & Momentum

#### 5.4.1 Real Price Volatility

```python
def calculate_real_price_volatility():
    """
    Calculate volatility using real oracle prices from last 10 rounds
    """
    if len(rounds_history) < 5:
        return 0.0
    
    # Get last 10 close prices (in USDT)
    prices = [r['close_price_usdt'] for r in rounds_history[-10:]]
    
    # Calculate price changes
    changes = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
    avg_change = sum(changes) / len(changes)
    avg_price = sum(prices) / len(prices)
    
    return avg_change / avg_price if avg_price > 0 else 0.0
```

#### 5.4.2 Price Momentum

```python
def calculate_price_momentum():
    """
    Calculate if BNB is trending up or down
    Returns: -1 to +1
    """
    if len(rounds_history) < 5:
        return 0.0
    
    # Recent avg (last 3 rounds) vs older avg (rounds 5-8)
    recent_avg = sum(r['close_price_usdt'] for r in rounds_history[-3:]) / 3
    older_avg = sum(r['close_price_usdt'] for r in rounds_history[-8:-5]) / 3
    
    momentum = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
    
    # Scale to [-1, 1]
    return max(-1.0, min(1.0, momentum * 10))
```

### 5.5 Streak Validation

The system tracks **winning streaks** (consecutive bull or bear wins) and validates them against actual price movement.

#### 5.5.1 Streak Tracking

```python
# Globals
current_streak = 0          # Length of current streak
current_streak_type = None  # 'BULL' or 'BEAR'
rounds_history = []         # Last 24 rounds

# Update after fetching round history
if len(rounds_history) >= 2:
    current_streak = 1
    current_streak_type = rounds_history[-1]['winner']
    
    # Count backwards
    for i in range(len(rounds_history) - 2, -1, -1):
        if rounds_history[i]['winner'] == current_streak_type:
            current_streak += 1
        else:
            break
```

#### 5.5.2 Smart Validation

```python
def should_use_streak_for_ml(current_epoch):
    """
    Validate if streak matches current price direction
    Only matters for streaks >= 10
    """
    if current_streak < 10:
        return True  # Short streaks don't need validation
    
    try:
        # Get previous round's lock price (current round lockPrice is $0)
        previous_epoch = current_epoch - 1
        previous_round = contract.functions.rounds(previous_epoch).call()
        lock_price = previous_round[4] / 1e8
        
        # Get current live price
        live_price = get_live_bnb_price()
        price_difference = live_price - lock_price
        
        # Check if price direction matches streak
        if current_streak_type == "BULL" and price_difference > 0:
            return True  # Bull streak + price up = valid
        elif current_streak_type == "BEAR" and price_difference < 0:
            return True  # Bear streak + price down = valid
        else:
            print(f"🚫 STREAK INVALIDATED: {current_streak_type} x{current_streak} but price diff: {price_difference:+.4f}")
            return False  # Contradictory = invalid
            
    except Exception as e:
        return True  # Default to valid on error
```

**Example:**
- If there's a **Bull streak x12** but current price is **DOWN** from lock price → **INVALID**
- This prevents betting on streaks that contradict market reality

### 5.6 Model Training (ML/ML.py)

The `ML.py` script trains the Random Forest model on historical data.

#### 5.6.1 Data Preparation

```python
# Load data from DG.py (Data Gatherer)
df = pd.read_csv('pancakeswap_prediction_data_20260119_195510.csv')

# Feature engineering
df['bet_ratio'] = df['bull_bets_amount'] / (df['bear_bets_amount'] + 0.001)
df['total_bet_log'] = np.log(df['total_bets_amount'] + 1)
df['price_volatility'] = df['price_change_percent'].rolling(window=10).std().fillna(0)
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek

# Prepare features
feature_columns = ['bet_ratio', 'total_bet_log', 'price_volatility', 'hour', 
                   'day_of_week', 'bull_bets_amount', 'bear_bets_amount', 
                   'total_bets_amount']

X = df[feature_columns].fillna(0)
y = df['winner']

# Remove ties
mask = y != 'tie'
X = X[mask]
y = y[mask]

# Split 80/20
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, 
                                                     random_state=42, stratify=y)
```

#### 5.6.2 Model Training

```python
# Train Random Forest
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# Evaluate
rf_pred = rf_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_pred)
print(f"Random Forest Accuracy: {rf_accuracy:.4f}")  # ~0.55

# Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)
```

#### 5.6.3 Pattern Analysis

```python
# 1. Bet ratio patterns
bull_wins = df_no_ties[df_no_ties['winner'] == 'bull']
bear_wins = df_no_ties[df_no_ties['winner'] == 'bear']

print(f"Bull win avg bet ratio: {bull_wins['bet_ratio'].mean():.3f}")  # 1.043
print(f"Bear win avg bet ratio: {bear_wins['bet_ratio'].mean():.3f}")  # 0.975

# 2. Hourly patterns
hourly_stats = df_no_ties.groupby('hour')['winner'].apply(lambda x: (x == 'bull').mean())
# Hour 17: 0.818 bull win rate (best bull hour)
# Hour 19: 0.364 bull win rate (worst bull hour)

# 3. Bet size patterns
df_no_ties['bet_size_category'] = pd.cut(
    df_no_ties['total_bets_amount'], 
    bins=[0, 1, 5, 10, float('inf')], 
    labels=['Small', 'Medium', 'Large', 'Huge']
)
bet_size_stats = df_no_ties.groupby('bet_size_category')['winner'].apply(
    lambda x: (x == 'bull').mean()
)
```

#### 5.6.4 Output: analysis_results.json

The script saves all findings to `analysis_results.json`, which is then used by `ml_insights_updater.py` to update bot code.

---

## 6. Betting Strategies

### 6.1 Decision Priority Ladder

The `enhanced_decision_logic()` function uses a **priority system** to make betting decisions:

```
┌─────────────────────────────────────────────────────┐
│         BETTING DECISION PRIORITY LADDER             │
└─────────────────────────────────────────────────────┘

Priority 1: Whale Detection (if whale_bet_side exists)
    ├─ If skip_rounds_remaining > 0: SKIP
    ├─ If ML very weak (|ml_score| <= 0.08):
    │  └─ CONTRARIAN: Bet AGAINST whale (HIGH confidence)
    └─ If ML confident (|ml_score| > 0.08):
       └─ Bet WITH whale (HIGH confidence)

    ↓ (If no whale detected or whale logic skipped)

Priority 2: Bet Ratio + ML Consensus (if pool > 1.5 BNB AND payout diff >= 1.2)
    ├─ Calculate payout_decision based on bet_ratio + max_bets
    ├─ Calculate ml_decision based on ML score
    ├─ If BOTH AGREE:
    │  └─ Place bet (MEDIUM/HIGH confidence)
    └─ If DISAGREE or no clear edge:
       └─ SKIP

    ↓ (If no consensus)

Priority 3: Strong ML Signal (if |ml_score| > 0.2)
    └─ Follow ML directly (MEDIUM confidence)

    ↓ (If ML weak)

Priority 4: Time + Large Bet Combo (if pool > 2.0 BNB)
    ├─ Check current hour against HOURLY_BULL_RATES
    ├─ Check for large bets (>= 1.0 BNB)
    ├─ If good hour + matching ML + large bet:
    │  └─ Place bet (LOW confidence)
    └─ Otherwise: SKIP

    ↓ (If none of above)

SKIP (No edge detected)
```

### 6.2 Contrarian Strategy (Current)

```python
def enhanced_decision_logic(bet_data, ml_score):
    """
    CONTRARIAN: Bet AGAINST whales, bet ratios, and consensus
    """
    # ... extract bet_data ...
    
    # Priority 1: CONTRARIAN whale logic
    if whale_bet_side and skip_rounds_remaining == 0:
        if abs(ml_score) <= 0.08:
            # ML weak → bet AGAINST whale
            opposite_side = "bear" if whale_bet_side == "bull" else "bull"
            return opposite_side, "HIGH (Against whale - ML too weak)"
        else:
            # ML strong → bet WITH whale (ML agrees)
            same_side = whale_bet_side
            return same_side, "HIGH (Follow whale - ML agrees)"
    
    # Priority 2: Bet against bet ratio patterns
    if total_amount > 1.5 and skip_rounds_remaining == 0 and abs(bull_payout - bear_payout) >= 1.2:
        payout_decision = None
        
        # FLIPPED LOGIC
        if bet_ratio > BEAR_WIN_BET_RATIO and max_bet_on_bull >= 0.7:
            payout_decision = "bear"  # Bet AGAINST bulls
        elif bet_ratio < BULL_WIN_BET_RATIO and max_bet_on_bear >= 0.7:
            payout_decision = "bull"  # Bet AGAINST bears
        
        # ML decision (direct)
        ml_decision = None
        if ml_score > 0.05:
            ml_decision = "bull"  # Follow ML
        elif ml_score < -0.05:
            ml_decision = "bear"
        
        # Both must agree
        if payout_decision and payout_decision == ml_decision:
            # ... confidence logic ...
            return payout_decision, confidence
        else:
            return None, "SKIP (Methods disagree)"
    
    # Priority 3: Strong ML
    if abs(ml_score) > 0.2:
        decision = "bull" if ml_score > 0 else "bear"
        return decision, f"MEDIUM (Strong ML: {ml_score:.3f})"
    
    # Priority 4: Time + Large bet
    if total_amount > 2.0:
        current_hour = datetime.now().hour
        good_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate >= 0.6]
        bad_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate <= 0.4]
        
        if current_hour in good_bull_hours and ml_score > 0.15 and max_bet_on_bull >= 1.0:
            return "bull", f"LOW (Good bull hour {current_hour})"
        elif current_hour in bad_bull_hours and ml_score < -0.15 and max_bet_on_bear >= 1.0:
            return "bear", f"LOW (Bad bull hour {current_hour})"
    
    return None, f"No edge detected (ratio: {bet_ratio:.2f}, ML: {ml_score:.3f})"
```

### 6.3 Bet Sizing

```python
def place_bet(decision, current_epoch, confidence, bet_data, ml_score):
    balance_wei = web3.eth.get_balance(WALLET_ADDRESS)
    
    # Dynamic bet sizing based on confidence
    if confidence.startswith("HIGH"):
        bet_multiplier = 0.06  # 6% of balance
    elif confidence.startswith("MEDIUM"):
        bet_multiplier = 0.04  # 4% of balance
    else:  # LOW
        bet_multiplier = 0.02  # 2% of balance
    
    bet_amount_wei = int(balance_wei * bet_multiplier)
    min_bet_wei = web3.to_wei('0.001', 'ether')  # 0.001 BNB minimum
    
    if bet_amount_wei < min_bet_wei:
        bet_amount_wei = min_bet_wei
```

**Example:**
- Balance: 1 BNB
- HIGH confidence: Bet 0.06 BNB (6%)
- MEDIUM: 0.04 BNB (4%)
- LOW: 0.02 BNB (2%)

### 6.4 Skip Conditions

The bot will **SKIP betting** if:

1. **Loss prevention active**: `skip_rounds_remaining > 0`
2. **Methods disagree**: Bet ratio says bull, ML says bear
3. **No clear edge**: All signals weak or neutral
4. **ML contradicts time**: Good bull hour but ML bearish (and vice versa)
5. **Pool too small**: `total_amount < 1.5 BNB` (for Priority 2)
6. **Payout difference too small**: `abs(bull_payout - bear_payout) < 1.2` (for Priority 2)

---

## 7. Loss Prevention System

### 7.1 Shared Loss State Architecture

```
┌─────────────────────────────────────────────────────┐
│        SHARED LOSS PREVENTION WORKFLOW               │
└─────────────────────────────────────────────────────┘

File: shared_loss_state.json
{
  "skip_rounds_remaining": 5,  # Decrements each round
  "last_loss_epoch": 418606,   # Epoch where loss occurred
  "loss_bot": "Bot3",           # Which bot lost
  "timestamp": "2025-01-..."    # When loss occurred
}

┌─────────────────────────────────────────────────────┐
│  Bot 1                Bot 2                Bot 3    │
│  ┌──────┐             ┌──────┐             ┌──────┐│
│  │Round │             │Round │             │Round ││
│  │Start │             │Start │             │Start ││
│  └───┬──┘             └───┬──┘             └───┬──┘│
│      │                    │                    │   │
│      ├─ Load shared_loss_state.json ───────────┤   │
│      │                    │                    │   │
│      ├─ if skip > 0: SKIP (decrement)          │   │
│      ├────────────────────┼────────────────────┤   │
│      │                    │                    │   │
│  ┌───▼──┐             ┌───▼──┐             ┌───▼──┐│
│  │Logic │             │Logic │             │Logic ││
│  │Skip  │             │Skip  │             │Skip  ││
│  └──────┘             └──────┘             └──────┘│
│                                                     │
│  After 5 rounds: skip_rounds_remaining = 0         │
│  → ALL BOTS RESUME NORMAL OPERATION                │
└─────────────────────────────────────────────────────┘
```

### 7.2 Loss Detection (claimer_bot.py)

```python
def check_and_claim_bet(bet_record):
    epoch = int(bet_record['epoch'])
    wallet_num = int(bet_record['wallet_number'])
    
    # Check if claimable
    claimable_amount = contract.functions.claimable(epoch, wallet_address).call()
    
    if claimable_amount > 0:
        # WIN: Reset loss state
        save_shared_loss_state(0, None, f"WIN_W{wallet_num}")
        send_telegram_message(f"💰 WIN! Wallet{wallet_num} Net: {net_profit:.6f} BNB")
        
    else:
        # LOSS: Trigger 5-round skip for ALL bots
        save_shared_loss_state(5, epoch, f"LOSS_W{wallet_num}")
        send_telegram_message(f"⛔ LOSS! Wallet{wallet_num}. ALL BOTS skip 5 rounds!")
```

### 7.3 Loss State Loading (finX.py)

```python
def load_shared_loss_state():
    """Load shared loss state from file"""
    try:
        if os.path.exists(SHARED_LOSS_FILE):
            with open(SHARED_LOSS_FILE, 'r') as f:
                return json.load(f)
        else:
            return {"skip_rounds_remaining": 0, "last_loss_epoch": None, "loss_bot": None}
    except Exception as e:
        return {"skip_rounds_remaining": 0, "last_loss_epoch": None, "loss_bot": None}

def main_loop():
    global skip_rounds_remaining
    
    # Load at startup
    shared_state = load_shared_loss_state()
    skip_rounds_remaining = shared_state["skip_rounds_remaining"]
    
    # Decrement at start of each round
    if skip_rounds_remaining > 0:
        new_skip_count = max(0, skip_rounds_remaining - 1)
        save_shared_loss_state(new_skip_count, shared_state["last_loss_epoch"], f"Bot{BOT_NUMBER}")
        print(f"⚠️ LOSS PREVENTION: Skipping {new_skip_count} more rounds")
```

### 7.4 Win Recovery

When **any bot WINS**, the shared loss state is **immediately reset**:

```python
# In claimer_bot.py
if claimable_amount > 0:
    # WIN detected
    save_shared_loss_state(0, None, f"WIN_W{wallet_num}")
    # This allows ALL bots to resume betting immediately
```

**Rationale:** A win indicates the strategy is working again, so no need to continue skipping.

---

## 8. Automated Claimer

### 8.1 Claimer Architecture

```
┌─────────────────────────────────────────────────────┐
│           CLAIMER BOT 300s CYCLE                     │
└─────────────────────────────────────────────────────┘

Every 300 seconds (5 minutes):
    │
    ├─ 1. Read bet_history/bets.csv
    │   └─ Filter: claimed == 'no'
    │   └─ Result: List of unclaimed bets
    │
    ├─ 2. For each unclaimed bet:
    │   │
    │   ├─ 2a. Check if epoch is finished
    │   │   ├─ contract.rounds(epoch).call()
    │   │   ├─ closeTimestamp > 0 AND closePrice > 0?
    │   │   ├─ YES → Continue to 2b
    │   │   └─ NO → Skip (epoch still live, retry next cycle)
    │   │
    │   ├─ 2b. Check claimable amount
    │   │   ├─ contract.claimable(epoch, wallet_address).call()
    │   │   │
    │   │   ├─ If claimable > 0: WIN!
    │   │   │   ├─ Get balance_before
    │   │   │   ├─ Execute claim transaction
    │   │   │   ├─ Wait for confirmation
    │   │   │   ├─ Get balance_after
    │   │   │   ├─ Calculate: net_profit = balance_after - balance_before - original_bet
    │   │   │   ├─ Update CSV: result='win', reward_amount=net_profit, claimed='yes'
    │   │   │   ├─ Telegram: "💰 WIN! Net: X BNB"
    │   │   │   └─ Reset shared loss: skip_rounds = 0
    │   │   │
    │   │   └─ If claimable == 0: LOSS!
    │   │       ├─ Calculate: loss_amount = -original_bet
    │   │       ├─ Update CSV: result='loss', reward_amount=loss_amount, claimed='yes'
    │   │       ├─ Telegram: "⛔ LOSS! Skip 5 rounds"
    │   │       └─ Set shared loss: skip_rounds = 5
    │   │
    │   └─ Wait 2 seconds before next claim
    │
    └─ 3. Print summary
        ├─ "✅ X processed, Y skipped (live epochs)"
        └─ Wait 300 seconds for next cycle
```

### 8.2 Why Separate Claimer?

**Advantages:**
1. **Decoupled**: Main bots focus on betting, claimer handles rewards
2. **Centralized**: One process manages all wallets (up to 12)
3. **Efficient**: Runs every 5 minutes instead of constantly checking
4. **Loss Coordination**: Single point of truth for loss state management
5. **Net Profit Tracking**: Accurately calculates profit after gas fees

### 8.3 CSV Update Logic

```python
def update_bet_history(bet_record, result_data):
    """Update CSV with claim results"""
    df = pd.read_csv(BET_HISTORY_FILE)
    
    # Find the row
    mask = (df['epoch'] == bet_record['epoch']) & (df['wallet_number'] == bet_record['wallet_number'])
    
    if mask.any():
        # Update columns
        df.loc[mask, 'result'] = result_data['result']          # 'win' or 'loss'
        df.loc[mask, 'reward_amount'] = result_data['reward_amount']  # net profit or -loss
        df.loc[mask, 'claimed'] = result_data['claimed']        # 'yes'
        
        # Save back
        df.to_csv(BET_HISTORY_FILE, index=False)
```

**Before claiming:**
```csv
epoch,wallet_number,decision,claimed,result,reward_amount
418606,1,bull,no,,,
```

**After claiming (WIN):**
```csv
epoch,wallet_number,decision,claimed,result,reward_amount
418606,1,bull,yes,win,0.045123
```

**After claiming (LOSS):**
```csv
epoch,wallet_number,decision,claimed,result,reward_amount
418606,1,bull,yes,loss,-0.001000
```

### 8.4 Telegram Notifications

```python
# WIN
send_telegram_message(
    f"💰🥳💰 WIN! Wallet{wallet_num} NET PROFIT: {net_profit:.6f} BNB (Epoch {epoch})💰🥳💰"
)

# LOSS
send_telegram_message(
    f"⛔ LOSS! Wallet{wallet_num} lost in epoch {epoch}. ALL BOTS skip 5 rounds!"
)
```

---

## 9. Configuration & Setup

### 9.1 File Structure

```
RICH/
├── fin1.py                    # Main bot 1 (1,204 lines)
├── fin2.py                    # Main bot 2 (1,204 lines, BOT_NUMBER=2)
├── fin3.py                    # Main bot 3 (1,204 lines, BOT_NUMBER=3)
├── claimer_bot.py             # Automated claimer (294 lines)
├── strategy_updater.py        # Strategy switching tool (570 lines)
├── ml_insights_updater.py     # ML parameter updater (364 lines)
├── env_file_updater.py        # Wallet configuration tool
├── .env                       # Configuration file (PRIVATE KEYS!)
├── prediction_abi.json        # PancakeSwap contract ABI
├── shared_loss_state.json     # Shared loss prevention state
├── rounds_cache.json          # 24-round history cache
├── analysis_results.json      # ML training output
│
├── ML/                        # Machine learning scripts
│   ├── DG.py                  # Data gathering (scrape blockchain)
│   ├── DG2.py                 # Alternative data gatherer
│   ├── ML.py                  # Model training (Random Forest)
│   ├── ML2.py                 # Alternative model training
│   ├── prediction_abi.json    # Contract ABI (duplicate)
│   └── Result/                # ML training outputs
│
├── bet_history/               # Bet logging
│   └── bets.csv               # All bets with 40+ columns
│
└── backup/                    # Automatic backups
    ├── fin1.py.backup_...
    ├── fin2.py.backup_...
    └── ...
```

### 9.2 Environment Configuration (.env)

```bash
# Bot 1 Wallet
PRIVATE_KEY_1=0x897bc8b5a803929b10dbf0463208826d4df91eb16703e75a8b67aa87fa43df43
WALLET_ADDRESS_1=0xF17498D9B785814d723b8C895F851203Ed2B0Bb2

# Bot 2 Wallet
PRIVATE_KEY_2=0x582829832cb443e2aadbb4ca5b28960e9e0d18e9756cff3860398da5692b2b80
WALLET_ADDRESS_2=0xE03DedA5f10178DDCe5D3e4438d8429b16de486A

# Bot 3 Wallet
PRIVATE_KEY_3=0xa11fa0753470d364b28b11fe9d9a81fc8dfce83118fd12fad1450bab764934c0
WALLET_ADDRESS_3=0x110B160f51d1aB42a622eECe8239bF135072E7fB

# ... up to PRIVATE_KEY_12 / WALLET_ADDRESS_12 ...

# Telegram Bot (for notifications)
TELEGRAM_TOKEN=7571742232:AAE--fJpCB0x-E7qCNv9pRNB5X1NmMT1Stk
TELEGRAM_CHAT_ID=7959012432
```

**⚠️ SECURITY WARNING**: This file contains private keys. **NEVER** commit to public repositories!

### 9.3 Dependencies (requirements.txt)

```txt
web3==6.11.0
python-dotenv==1.0.0
requests==2.31.0
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
matplotlib==3.8.2
seaborn==0.13.0
eth-utils==2.3.1
```

Install with:
```bash
pip install -r requirements.txt
```

### 9.4 Initial Setup Steps

1. **Clone/Download** the RICH folder

2. **Create virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure wallets** in `.env`:
   - Add private keys for Bot 1-3 (minimum)
   - Add Telegram bot token and chat ID

5. **Test connection**:
```bash
python3 -c "from web3 import Web3; w3 = Web3(Web3.HTTPProvider('https://bsc-mainnet.nodereal.io/v1/a16acfa17ef245b7973338fef461c447')); print('Connected:', w3.is_connected())"
```

6. **Fund wallets**:
   - Send BNB to WALLET_ADDRESS_1, _2, _3
   - Recommended: 0.1 BNB minimum per wallet

7. **Initialize cache files**:
```bash
echo '{"skip_rounds_remaining": 0, "last_loss_epoch": null, "loss_bot": null}' > shared_loss_state.json
```

8. **Run bots** (in separate terminals):
```bash
# Terminal 1
python3 fin1.py

# Terminal 2
python3 fin2.py

# Terminal 3
python3 fin3.py

# Terminal 4
python3 claimer_bot.py
```

### 9.5 Production Deployment (Using Screen/Tmux)

```bash
# Using screen
screen -S bot1
python3 fin1.py
# Ctrl+A, D to detach

screen -S bot2
python3 fin2.py
# Ctrl+A, D

screen -S bot3
python3 fin3.py
# Ctrl+A, D

screen -S claimer
python3 claimer_bot.py
# Ctrl+A, D

# List screens
screen -ls

# Reattach
screen -r bot1
```

```bash
# Using tmux
tmux new -s rich-bots
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v

# Now you have 4 panes
# Pane 0: python3 fin1.py
# Pane 1: python3 fin2.py
# Pane 2: python3 fin3.py
# Pane 3: python3 claimer_bot.py

# Detach: Ctrl+B, D
# Reattach: tmux attach -t rich-bots
```

---

## 10. Operation Workflows

### 10.1 Complete Betting Cycle

```
┌──────────────────────────────────────────────────────────────┐
│              COMPLETE BETTING CYCLE TIMELINE                  │
└──────────────────────────────────────────────────────────────┘

Time: 0:00 - Round Starts
    │
    ├─ Contract creates new epoch
    ├─ startTimestamp set
    ├─ Bots detect new round via currentEpoch() call
    │
    ├─ Bot 1: Starts immediately
    ├─ Bot 2: Waits 5 minutes (300s delay)
    └─ Bot 3: Waits 10 minutes (600s delay)

Time: 0:00 - 0:35 - Data Collection Phase (Bot 1)
    │
    ├─ Fetch round history (24 rounds)
    ├─ Load shared loss state
    ├─ Get live BNB price (Chainlink, 8s cache)
    ├─ Get BTC data (Binance API, 30s cache)
    ├─ Calculate current streak
    ├─ Validate streak against price action
    │
    └─ LOOP: Monitor bets every 0.001 seconds
       ├─ fetch_bets() - Get all BetBull/BetBear events
       ├─ Calculate bet_ratio, pool size, payouts
       ├─ Calculate ML score (-1 to +1)
       ├─ Run enhanced_decision_logic()
       └─ Display: Bull%, Bear%, Ratio, ML score, Decision

Time: 0:35 - Bot 1 Analysis Complete
    │
    ├─ Lock analysis at 35 seconds before end
    ├─ Final ML score calculated
    ├─ Final decision made
    │
    ├─ If Decision = SKIP:
    │  └─ Print reason, wait for next round
    │
    └─ If Decision = bull/bear:
       ├─ Calculate bet size (2-6% of balance)
       ├─ Build transaction
       ├─ Sign with private key
       ├─ Send to blockchain
       ├─ Log to CSV (bet_history/bets.csv)
       └─ Send Telegram notification

Time: 5:00 - Round Locks
    │
    ├─ lockTimestamp set
    ├─ Contract records lockPrice from Chainlink oracle
    └─ No more bets accepted

Time: 10:00 - Round Ends
    │
    ├─ closeTimestamp set
    ├─ Contract records closePrice from Chainlink oracle
    ├─ Determine winner: closePrice > lockPrice = BULL, else BEAR
    └─ Distribute payouts (available for claiming)

Time: 10:00+ - Claimer Bot (Next 300s Cycle)
    │
    ├─ Read bet_history/bets.csv (unclaimed bets)
    ├─ For each unclaimed bet:
    │  ├─ Check if epoch finished
    │  ├─ Call claimable()
    │  ├─ If claimable > 0: Execute claim, update CSV
    │  └─ If claimable == 0: Mark loss, update CSV
    │
    ├─ Update shared_loss_state.json if loss detected
    └─ Send Telegram notifications

Time: 10:00 - Next Round Starts
    └─ Cycle repeats

### 10.2 Data Gathering Workflow (ML/DG.py)

This script scrapes historical round data from the blockchain to train the ML model.

```
┌──────────────────────────────────────────────────────────────┐
│              DATA GATHERING WORKFLOW                          │
└──────────────────────────────────────────────────────────────┘

python3 DG.py
    │
    ├─ Get current epoch from contract
    │  └─ contract.functions.currentEpoch().call()
    │
    ├─ Determine epoch range to scrape
    │  ├─ Default: Last 10,000 epochs
    │  └─ Can specify: start_epoch, end_epoch, num_epochs
    │
    ├─ Loop through each epoch:
    │  │
    │  ├─ Get round data: contract.functions.rounds(epoch).call()
    │  │  ├─ startTimestamp, lockTimestamp, closeTimestamp
    │  │  ├─ lockPrice, closePrice (8 decimals)
    │  │  ├─ totalAmount, bullAmount, bearAmount (18 decimals)
    │  │  └─ oracleCalled (true/false)
    │  │
    │  ├─ Skip if oracle not called (round incomplete)
    │  │
    │  ├─ Calculate derived data:
    │  │  ├─ winner = 'bull' if closePrice > lockPrice else 'bear'
    │  │  ├─ price_change_percent = ((close - lock) / lock) * 100
    │  │  ├─ bull_multiplier = total / bull (payout ratio)
    │  │  ├─ bear_multiplier = total / bear
    │  │  └─ timestamp = datetime.fromtimestamp(closeTimestamp)
    │  │
    │  └─ Append to data list
    │
    ├─ Create DataFrame from data
    │
    ├─ Save to CSV: pancakeswap_prediction_data_YYYYMMDD_HHMMSS.csv
    │
    └─ Print summary:
       ├─ Total rounds scraped
       ├─ Bull win rate
       ├─ Bear win rate
       └─ Tie rate
```

**Example Output CSV:**

```csv
epoch,timestamp,lock_price,close_price,price_change_percent,total_bets_amount,bull_bets_amount,bear_bets_amount,bull_multiplier,bear_multiplier,winner
418600,2025-01-19 10:15:00,645.23,645.89,0.102,12.345,7.123,5.222,1.733,2.364,bull
418601,2025-01-19 10:20:00,645.89,645.12,-0.119,15.678,6.234,9.444,2.515,1.661,bear
...
```

### 10.3 ML Training Workflow (ML/ML.py)

Once data is gathered, train the model to generate updated parameters.

```
┌──────────────────────────────────────────────────────────────┐
│              ML TRAINING WORKFLOW                             │
└──────────────────────────────────────────────────────────────┘

python3 ML.py
    │
    ├─ Load CSV data from DG.py
    │  └─ df = pd.read_csv('pancakeswap_prediction_data_...')
    │
    ├─ Feature Engineering:
    │  ├─ bet_ratio = bull_amount / bear_amount
    │  ├─ total_bet_log = log(total_amount + 1)
    │  ├─ price_volatility = rolling_std(price_change, 10)
    │  ├─ hour = extract hour from timestamp
    │  └─ day_of_week = extract weekday (0=Monday)
    │
    ├─ Prepare features & target:
    │  ├─ X = [bet_ratio, total_bet_log, price_volatility, hour, 
    │  │       day_of_week, bull_amount, bear_amount, total_amount]
    │  ├─ y = winner ('bull' or 'bear')
    │  └─ Remove ties from dataset
    │
    ├─ Train/Test Split (80/20):
    │  └─ X_train, X_test, y_train, y_test
    │
    ├─ Train Models:
    │  │
    │  ├─ Random Forest (100 trees)
    │  │  ├─ rf_model.fit(X_train, y_train)
    │  │  ├─ rf_accuracy = accuracy_score(y_test, rf_pred)
    │  │  └─ Extract feature_importances_
    │  │
    │  └─ Logistic Regression
    │     ├─ Scale features with StandardScaler
    │     ├─ lr_model.fit(X_train_scaled, y_train)
    │     └─ lr_accuracy = accuracy_score(y_test, lr_pred)
    │
    ├─ Pattern Analysis:
    │  │
    │  ├─ Bet Ratio Patterns:
    │  │  ├─ bull_avg_bet_ratio = mean(bet_ratio when winner==bull)
    │  │  └─ bear_avg_bet_ratio = mean(bet_ratio when winner==bear)
    │  │
    │  ├─ Hourly Patterns:
    │  │  └─ For each hour 0-23: % of bull wins
    │  │
    │  └─ Bet Size Patterns:
    │     └─ Group by Small/Medium/Large/Huge → bull win rate
    │
    ├─ Generate analysis_results.json:
    │  └─ {
    │       "model_accuracy": {...},
    │       "feature_importance": [...],
    │       "patterns": {
    │         "bull_avg_bet_ratio": 1.043,
    │         "bear_avg_bet_ratio": 0.975,
    │         "hourly_bull_rates": {...},
    │         "bet_size_bull_rates": {...}
    │       }
    │     }
    │
    ├─ Generate visualizations:
    │  ├─ Price change distribution
    │  ├─ Winner pie chart
    │  ├─ Bet amounts over time
    │  ├─ Bull vs Bear scatter
    │  ├─ Price change by winner (boxplot)
    │  └─ Multipliers distribution
    │
    └─ Print classification report & confusion matrix
```

### 10.4 Strategy Switching Workflow

```
┌──────────────────────────────────────────────────────────────┐
│            STRATEGY SWITCHING WORKFLOW                        │
└──────────────────────────────────────────────────────────────┘

python3 strategy_updater.py
    │
    ├─ Auto-detect all fin*.py files
    │
    ├─ Interactive Menu:
    │  │
    │  ├─ Option 1: Show current strategy
    │  │  ├─ Read each fin*.py
    │  │  ├─ Check whale logic line:
    │  │  │  ├─ 'opposite_side = "bear" if whale_bet_side == "bull"' → CONTRARIAN
    │  │  │  └─ 'opposite_side = "bear" if whale_bet_side == "bear"' → CONSENSUS
    │  │  └─ Display: fin1.py: CONTRARIAN, fin2.py: CONTRARIAN, etc.
    │  │
    │  ├─ Option 2: Switch to CONTRARIAN
    │  │  ├─ Select files to update (individual or all)
    │  │  ├─ Create backups in backup/ folder
    │  │  ├─ Replace enhanced_decision_logic() function
    │  │  ├─ Validate updates
    │  │  └─ Summary: X/Y files updated
    │  │
    │  ├─ Option 3: Switch to CONSENSUS
    │  │  └─ (Same process as Option 2)
    │  │
    │  └─ Option 4: Exit
    │
    └─ Done
```

**Important:** Strategy changes take effect **immediately** on next round. No need to restart bots.

---

## 11. Data Structures

### 11.1 bet_history/bets.csv Structure

This CSV file contains **40+ columns** capturing every detail of each bet:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| **datetime** | ISO8601 | When bet was placed | 2025-01-19T10:15:32.123456 |
| **epoch** | int | Round epoch number | 418606 |
| **decision** | str | Bot decision | 'bull' or 'bear' |
| **confidence** | str | Confidence level | 'HIGH (Against whale...)' |
| **bet_amount_bnb** | float | Amount bet in BNB | 0.001234 |
| **ml_score** | float | ML prediction score | 0.234 (-1 to 1) |
| **bull_amount** | float | Total bull bets | 7.123 |
| **bear_amount** | float | Total bear bets | 5.222 |
| **total_amount** | float | Total pool | 12.345 |
| **bull_payout** | float | Bull payout multiplier | 1.733x |
| **bear_payout** | float | Bear payout multiplier | 2.364x |
| **bull_percent** | float | % of pool on bull | 57.67 |
| **bear_percent** | float | % of pool on bear | 42.33 |
| **bet_ratio** | float | bull_amount / bear_amount | 1.364 |
| **whale_bet_side** | str | Whale detected side | 'bull', 'bear', or '' |
| **max_bet_on_bull** | float | Largest single bull bet | 2.345 |
| **max_bet_on_bear** | float | Largest single bear bet | 1.876 |
| **bull_whales** | int | Count of bull whales (≥0.8 BNB) | 2 |
| **bear_whales** | int | Count of bear whales | 1 |
| **current_streak** | int | Win streak length | 12 |
| **current_streak_type** | str | Streak direction | 'BULL' or 'BEAR' |
| **skip_rounds_remaining** | int | Loss prevention rounds | 0 to 5 |
| **last_loss_epoch** | int/null | Last loss epoch | 418590 or null |
| **live_bnb_price** | float | BNB price at bet time | 645.23 |
| **lock_price_previous** | float | Previous round lock price | 644.89 |
| **price_difference** | float | live - lock (USDT) | 0.34 |
| **btc_price** | float | BTC price | 98745.23 |
| **btc_5min_change** | float | BTC 5-min % change | 0.45 |
| **btc_influence** | float | BTC influence score | 0.2 |
| **real_price_volatility** | float | 10-round rolling std | 0.015 |
| **price_momentum** | float | Momentum score | 0.123 |
| **current_hour** | int | Hour of day | 14 |
| **current_day_of_week** | int | Day (0=Mon) | 3 (Thu) |
| **hourly_bull_rate** | float | Hour's bull win rate | 0.75 |
| **total_bet_log** | float | log(total_amount + 1) | 2.567 |
| **streak_valid** | bool | Streak validation | True/False |
| **last_round_price_change** | float | Previous round ∆ (USDT) | -0.87 |
| **big_move_detected** | bool | >$1.75 move? | True/False |
| **wallet_number** | int | Which bot | 1, 2, or 3 |
| **claimed** | str | Claimed status | 'yes' or 'no' |
| **result** | str | Outcome | 'win', 'loss', or '' |
| **reward_amount** | float | Net profit/loss | 0.045123 or -0.001 |

**Example Row:**

```csv
datetime,epoch,decision,confidence,bet_amount_bnb,ml_score,bull_amount,bear_amount,total_amount,bull_payout,bear_payout,bull_percent,bear_percent,bet_ratio,whale_bet_side,max_bet_on_bull,max_bet_on_bear,bull_whales,bear_whales,current_streak,current_streak_type,skip_rounds_remaining,last_loss_epoch,live_bnb_price,lock_price_previous,price_difference,btc_price,btc_5min_change,btc_influence,real_price_volatility,price_momentum,current_hour,current_day_of_week,hourly_bull_rate,total_bet_log,streak_valid,last_round_price_change,big_move_detected,wallet_number,claimed,result,reward_amount
2025-01-19T14:23:45.123456,418606,bear,"HIGH (Against bet ratio 1.45 + ML + Bad bull hour 19)",0.001234,0.234,7.123,5.222,12.345,1.733,2.364,57.67,42.33,1.364,bull,2.345,1.876,2,1,12,BULL,0,418590,645.23,644.89,0.34,98745.23,0.45,0.2,0.015,0.123,19,3,0.364,2.567,True,-0.87,False,1,yes,win,0.045123
```

### 11.2 shared_loss_state.json Structure

```json
{
  "skip_rounds_remaining": 5,
  "last_loss_epoch": 418606,
  "loss_bot": "Bot3",
  "timestamp": "2025-01-19T10:15:32.699043"
}
```

**Fields:**
- `skip_rounds_remaining`: Number of rounds ALL bots must skip (0-5)
- `last_loss_epoch`: Epoch where loss occurred
- `loss_bot`: Which bot lost (Bot1, Bot2, Bot3, or LOSS_W1, WIN_W2, etc.)
- `timestamp`: When state was last updated

### 11.3 rounds_cache.json Structure

```json
{
  "rounds_history": [
    {
      "epoch": 418582,
      "lock_price": 644.56,
      "close_price": 645.12,
      "lock_price_usdt": 644.56,
      "close_price_usdt": 645.12,
      "price_change_usdt": 0.56,
      "bull_payout": 1.85,
      "bear_payout": 2.23,
      "winner": "BULL",
      "total_amount": 10.234
    },
    {
      "epoch": 418583,
      "lock_price": 645.12,
      "close_price": 644.87,
      "lock_price_usdt": 645.12,
      "close_price_usdt": 644.87,
      "price_change_usdt": -0.25,
      "bull_payout": 2.12,
      "bear_payout": 1.89,
      "winner": "BEAR",
      "total_amount": 8.567
    }
    // ... 22 more rounds (total 24)
  ],
  "last_updated": "2025-01-19T10:15:32.123456"
}
```

**Purpose:**
- Caches last 24 rounds to avoid repeated blockchain queries
- Used for streak tracking, volatility calculation, momentum
- Updated incrementally (only fetches missing rounds)

### 11.4 analysis_results.json Structure

Generated by `ML/ML.py`, consumed by `ml_insights_updater.py`:

```json
{
  "model_accuracy": {
    "random_forest": 0.55,
    "logistic_regression": 0.50
  },
  "feature_importance": [
    {"feature": "bet_ratio", "importance": 0.1933},
    {"feature": "price_volatility", "importance": 0.1905},
    {"feature": "bull_bets_amount", "importance": 0.1434},
    {"feature": "bear_bets_amount", "importance": 0.1348},
    {"feature": "total_bet_log", "importance": 0.1315},
    {"feature": "total_bets_amount", "importance": 0.1177},
    {"feature": "hour", "importance": 0.0889},
    {"feature": "day_of_week", "importance": 0.0}
  ],
  "patterns": {
    "bull_avg_bet_ratio": 1.043021637000436,
    "bear_avg_bet_ratio": 0.9752999098946478,
    "hourly_bull_rates": {
      "0": 0.5, "1": 0.5, ..., "23": 0.5,
      "12": 0.6667, "17": 0.8182, "19": 0.3636
    },
    "bet_size_bull_rates": {
      "Small": 0.75,
      "Medium": 0.5543,
      "Large": 0.6667
    }
  }
}
```

---

## 12. API & Integration

### 12.1 PancakeSwap Prediction Contract

**Contract Address:** `0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA` (BSC Mainnet)

#### 12.1.1 Key Functions

```solidity
// View Functions
function currentEpoch() external view returns (uint256)
function rounds(uint256 epoch) external view returns (Round memory)
function claimable(uint256 epoch, address user) external view returns (uint256)

// State-Changing Functions
function betBull(uint256 epoch) external payable
function betBear(uint256 epoch) external payable
function claim(uint256[] calldata epochs) external
```

#### 12.1.2 Round Structure

```solidity
struct Round {
    uint256 epoch;
    uint256 startTimestamp;
    uint256 lockTimestamp;
    uint256 closeTimestamp;
    int256 lockPrice;          // 8 decimals
    int256 closePrice;         // 8 decimals
    uint256 lockOracleId;
    uint256 closeOracleId;
    uint256 totalAmount;       // 18 decimals (wei)
    uint256 bullAmount;        // 18 decimals
    uint256 bearAmount;        // 18 decimals
    uint256 rewardBaseCalAmount;
    uint256 rewardAmount;
    bool oracleCalled;
}
```

#### 12.1.3 Events

```solidity
event BetBull(address indexed sender, uint256 indexed epoch, uint256 amount)
event BetBear(address indexed sender, uint256 indexed epoch, uint256 amount)
event Claim(address indexed sender, uint256 indexed epoch, uint256 amount)
event StartRound(uint256 indexed epoch)
event LockRound(uint256 indexed epoch, int256 price)
event EndRound(uint256 indexed epoch, int256 price)
```

### 12.2 Chainlink Price Feeds

#### 12.2.1 BNB/USD Feed

**Address:** `0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE` (BSC Mainnet)

```python
def get_live_bnb_price():
    """Get BNB price with 8-second caching"""
    latest_data = price_feed.functions.latestRoundData().call()
    # Returns: (roundId, answer, startedAt, updatedAt, answeredInRound)
    price = latest_data[1] / 1e8  # 8 decimals
    return price
```

#### 12.2.2 BTC Tracking (Binance API)

```python
# Current price
GET https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT

# 5-minute klines
GET https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=6
```

### 12.3 Telegram Bot Integration

```python
def send_telegram_message(message):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload, timeout=5)
```

**Message Types:**
1. **Bet Placed**: "🚀 Bet placed on WALLET{X}, Round:{epoch}..."
2. **Win Detected**: "💰🥳💰 WIN! Wallet{X} NET PROFIT: {amount} BNB..."
3. **Loss Detected**: "⛔ LOSS! Wallet{X} lost in epoch {epoch}. ALL BOTS skip 5 rounds!"
4. **Errors**: "⚠️ Error: {error_message}"

---

## 13. Monitoring & Analytics

### 13.1 Real-Time Monitoring

#### 13.1.1 Console Output (Bot)

During betting cycle, bots display real-time data every 0.001 seconds:

```
📊 Bull: 57.67% | Bear: 42.33% | Ratio: 1.36 | Pool: 12.3450 | Price: $645.23 📈+0.34 | BTC: $98,745 (+0.45%) | Max Bull: 2.345 | Max Bear: 1.876 | ML: 0.234 | 🔥BULLx12✅ | 🎯 BEAR (HIGH)
```

**Legend:**
- `Bull%` / `Bear%`: Percentage of pool
- `Ratio`: bull_amount / bear_amount
- `Pool`: Total BNB in round
- `Price`: Live BNB price with difference from lock
- `BTC`: Bitcoin price with 5-min change
- `Max Bull/Bear`: Largest single bets
- `ML`: ML prediction score
- `🔥BULLx12✅`: Current streak (✅=valid, ❌=invalid)
- `🎯 BEAR (HIGH)`: Final decision with confidence

#### 13.1.2 Console Output (Claimer)

```
🤖 CLAIMER BOT STARTING - 2025-01-19 10:15:32

📂 Loaded 12 wallets: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
📊 Found 3 unclaimed bets

📋 Processing bet 1/3
🔍 Checking FINISHED epoch 418606 for wallet 1...
🎉 WIN! Claimable: 0.045123 BNB for wallet 1
🚀 Claim TX: 0xabc123...
✅ Real claimed payout: 0.045123 BNB | Original bet: 0.001234 BNB | Net profit: 0.043889 BNB
📝 Updated CSV: win for epoch 418606
💾 SHARED LOSS: 0 rounds remaining

✅ CLAIMER CYCLE COMPLETE: 3 processed, 0 skipped (live epochs)

⏳ WAITING 300 seconds...
⏳ Next cycle in 299s...
```

### 13.2 Performance Analytics

#### 13.2.1 Calculate Win Rate

```python
import pandas as pd

df = pd.read_csv('bet_history/bets.csv')

# Filter claimed bets only
claimed = df[df['claimed'] == 'yes']

# Calculate win rate
wins = len(claimed[claimed['result'] == 'win'])
losses = len(claimed[claimed['result'] == 'loss'])
total = wins + losses

win_rate = wins / total if total > 0 else 0
print(f"Win Rate: {win_rate:.2%} ({wins}W / {losses}L)")
```

#### 13.2.2 Calculate ROI

```python
# Calculate total profit/loss
total_profit = claimed['reward_amount'].sum()

# Calculate total bet amount
total_bet = claimed['bet_amount_bnb'].sum()

# ROI
roi = (total_profit / total_bet) * 100 if total_bet > 0 else 0
print(f"ROI: {roi:.2f}% (Net: {total_profit:.6f} BNB from {total_bet:.6f} BNB bet)")
```

#### 13.2.3 Analyze by Confidence

```python
# Group by confidence level
for confidence_level in ['HIGH', 'MEDIUM', 'LOW']:
    subset = claimed[claimed['confidence'].str.startswith(confidence_level)]
    subset_wins = len(subset[subset['result'] == 'win'])
    subset_total = len(subset)
    subset_winrate = subset_wins / subset_total if subset_total > 0 else 0
    subset_profit = subset['reward_amount'].sum()
    
    print(f"{confidence_level}: {subset_winrate:.2%} ({subset_wins}/{subset_total}), Profit: {subset_profit:.6f} BNB")
```

**Expected Output:**
```
HIGH: 58.33% (35/60), Profit: 0.234567 BNB
MEDIUM: 53.12% (17/32), Profit: 0.045123 BNB
LOW: 50.00% (5/10), Profit: -0.001234 BNB
```

#### 13.2.4 Analyze by Hour

```python
# Group by hour
hourly_stats = claimed.groupby('current_hour').agg({
    'result': lambda x: (x == 'win').mean(),
    'reward_amount': 'sum',
    'bet_amount_bnb': 'count'
})

print("Hourly Performance:")
print(hourly_stats)
```

### 13.3 Telegram Monitoring

Set up Telegram notifications to receive:
- ✅ Bet confirmations
- 💰 Win notifications with profit amounts
- ⛔ Loss notifications with skip count
- ⚠️ Error alerts

**Example Win Notification:**
```
💰🥳💰 WIN! Wallet1 NET PROFIT: 0.043889 BNB (Epoch 418606)💰🥳💰
```

**Example Loss Notification:**
```
⛔ LOSS! Wallet3 lost in epoch number 418610. ALL BOTS skip 5 rounds!
```

---

## 14. Troubleshooting

### 14.1 Common Issues

#### 14.1.1 "Failed to connect to BSC"

**Symptoms:**
```
❌ Failed to connect to BSC
```

**Solutions:**
1. Check internet connection
2. Verify RPC endpoint is working:
   ```bash
   curl https://bsc-mainnet.nodereal.io/v1/a16acfa17ef245b7973338fef461c447
   ```
3. Try alternative RPC:
   ```python
   web3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
   ```

#### 14.1.2 "Insufficient funds for gas"

**Symptoms:**
```
ValueError: insufficient funds for gas * price + value
```

**Solutions:**
1. Check wallet balance:
   ```python
   balance = web3.eth.get_balance(WALLET_ADDRESS)
   print(f"Balance: {web3.from_wei(balance, 'ether')} BNB")
   ```
2. Ensure balance > bet_amount + gas_cost (~0.0001 BNB)
3. Fund wallet if needed

#### 14.1.3 "Bet not accepted - Round already locked"

**Symptoms:**
```
Transaction reverted: Round locked
```

**Solutions:**
1. Bot tried to bet after 5-minute mark
2. Check system time vs blockchain time:
   ```python
   blockchain_time = web3.eth.get_block('latest').timestamp
   local_time = int(time.time())
   print(f"Offset: {blockchain_time - local_time}s")
   ```
3. Adjust timing if offset >  5 seconds

#### 14.1.4 "claimer_bot not claiming wins"

**Symptoms:**
- Wins in CSV but `claimed` still 'no'
- No claim transactions

**Solutions:**
1. Check if claimer is running: `screen -ls` or `tmux ls`
2. Check claimer logs for errors
3. Verify epochs are finished:
   ```python
   round_data = contract.functions.rounds(epoch).call()
   print(f"closePrice: {round_data[5]}")  # Should be > 0
   ```
4. Restart claimer: `python3 claimer_bot.py`

#### 14.1.5 "All bots skipping rounds forever"

**Symptoms:**
- `skip_rounds_remaining` never reaches 0
- Bots printing "LOSS PREVENTION: Skipping X more rounds"

**Solutions:**
1. Check `shared_loss_state.json`:
   ```bash
   cat shared_loss_state.json
   ```
2. Manually reset if stuck:
   ```bash
   echo '{"skip_rounds_remaining": 0, "last_loss_epoch": null, "loss_bot": null}' > shared_loss_state.json
   ```
3. Verify claimer is running (it resets skip count on wins)

#### 14.1.6 "ML score always 0 or neutral"

**Symptoms:**
- ML score showing 0.000 or very small values
- Bots never getting HIGH confidence

**Solutions:**
1. Check rounds_cache.json exists and has data:
   ```bash
   cat rounds_cache.json | jq '.rounds_history | length'
   # Should be 24
   ```
2. Re-fetch round history (delete cache):
   ```bash
   rm rounds_cache.json
   # Bot will re-fetch on next startup
   ```
3. Check BTC data is fetching:
   ```python
   btc_data = get_btc_data()
   print(btc_data)  # Should have price > 0
   ```

#### 14.1.7 "Strategy update didn't work"

**Symptoms:**
- Ran `strategy_updater.py` but bots still using old strategy

**Solutions:**
1. Verify files were actually updated:
   ```bash
   grep 'opposite_side = "bear" if whale_bet_side == "bull"' fin1.py
   # CONTRARIAN: Should find this line
   ```
2. Check for backup files:
   ```bash
   ls backup/fin1.py.backup_*
   ```
3. If needed, restore from backup and re-run updater

### 14.2 Debugging Tips

#### 14.2.1 Enable Verbose Logging

Add to main_loop():

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 14.2.2 Test Single Round

Modify main_loop() to exit after 1 round:

```python
# At end of main_loop()
print("✅ TEST MODE: Exiting after 1 round")
exit(0)
```

#### 14.2.3 Simulate Without Betting

Comment out transaction sending:

```python
def place_bet(decision, current_epoch, confidence, bet_data, ml_score):
    # ... calculate bet ...
    
    print(f"🧪 DRY RUN: Would bet {bet_amount_bnb:.6f} BNB on {side}")
    # signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)  # COMMENTED
    # tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)  # COMMENTED
    
    # Still log to CSV
    save_bet_snapshot_csv(bet_data, decision, confidence, ml_score, bet_amount_bnb, current_epoch)
```

#### 14.2.4 Check Contract State

```python
# Get current round info
current_epoch = contract.functions.currentEpoch().call()
round_data = contract.functions.rounds(current_epoch).call()

print(f"Epoch: {current_epoch}")
print(f"Start: {round_data[1]}")
print(f"Lock: {round_data[2]}")
print(f"Close: {round_data[3]}")
print(f"LockPrice: {round_data[4] / 1e8}")
print(f"ClosePrice: {round_data[5] / 1e8}")
print(f"TotalAmount: {round_data[8] / 1e18} BNB")
print(f"BullAmount: {round_data[9] / 1e18} BNB")
print(f"BearAmount: {round_data[10] / 1e18} BNB")
print(f"OracleCalled: {round_data[13]}")
```

---

## 15. FAQ

### 15.1 General Questions

**Q: Why three bots instead of one?**
A: Three bots provide:
- Diversification (separate wallets = isolated risk)
- Staggered timing (0min, 5min, 10min delays catch different market conditions)
- Better statistics (more bets = lower variance)

**Q: Why contrarian strategy?**
A: Historical data shows betting AGAINST whales and consensus has ~55% win rate vs ~50% for following them.

**Q: What's the minimum balance needed?**
A: Recommended 0.1 BNB per wallet (3 bots = 0.3 BNB total) to sustain 100+ bets.

**Q: How many bets per day?**
A: Typically 40-60 bets per day total across 3 bots (~15-20 per bot), depending on skip rounds.

**Q: What's the expected ROI?**
A: With 55% win rate and 2x average payout: ~10% ROI per 100 bets (before gas fees).

**Q: Is this profitable?**
A: Historically yes, but past performance doesn't guarantee future results. Crypto markets are volatile.

### 15.2 Technical Questions

**Q: Why use Chainlink for prices instead of contract prices?**
A: Contract prices update every 5 minutes. Chainlink provides live prices for better real-time analysis.

**Q: Why track BTC?**
A: BTC and BNB are correlated. BTC's 5-minute movement often predicts BNB's direction.

**Q: What happens if two bots lose simultaneously?**
A: Shared loss state ensures ALL bots skip 5 rounds. The state is updated by the claimer as it processes each loss.

**Q: Can I run more than 3 bots?**
A: Yes! The system supports up to 12 wallets. Copy fin1.py to fin4.py, change `BOT_NUMBER = 4`, and add corresponding .env entries.

**Q: Why 0.001 second monitoring interval?**
A: To catch bet changes as quickly as possible. The 8-second price cache prevents excessive API calls.

**Q: How accurate is the ML model?**
A: ~55% accuracy on test data (10k rounds). Not perfect, but better than random (50%).

**Q: Can I train my own ML model?**
A: Yes! Use `ML/DG.py` to scrape data, `ML/ML.py` to train, then `ml_insights_updater.py` to update bot params.

### 15.3 Strategy Questions

**Q: When should I use consensus vs contrarian?**
A: 
- **Contrarian**: When market is irrational (whale manipulation suspected)
- **Consensus**: When market is rational (large volume, many participants)

**Q: Why skip 5 rounds after loss?**
A: Prevents revenge betting. Gives time for market conditions to change.

**Q: What is "HIGH" confidence?**
A: HIGH confidence bets have:
- Whale detected + ML agreement, OR
- Bet ratio + ML consensus + good hour, OR
- Very strong ML signal (>0.3)

**Q: Why does bot sometimes bet WITH whale?**
A: When ML is very confident (|score| > 0.08), it overrides contrarian logic and follows whale.

**Q: What's the minimum pool size to bet?**
A: 1.5 BNB for Priority 2 logic, 2.0 BNB for Priority 4. Smaller pools are too volatile.

### 15.4 Operational Questions

**Q: How do I stop the bots?**
A: 
- If using screen: `screen -r bot1`, then Ctrl+C
- If using tmux: `tmux attach -t rich-bots`, select pane, Ctrl+C
- Or kill process: `pkill -f fin1.py`

**Q: How do I check if bots are running?**
A:
```bash
ps aux | grep "fin[0-9].py"
# Should show 3 processes
```

**Q: How often should I check the bots?**
A: Once daily is fine. Telegram notifications alert you to wins/losses.

**Q: What if I lose my `.env` file?**
A: **YOU LOSE ACCESS TO YOUR WALLETS.** Always backup your .env file securely!

**Q: Can I use the same wallet for multiple bots?**
A: No! Each bot needs a separate wallet to avoid nonce conflicts.

**Q: How do I update ML parameters?**
A:
1. Scrape data: `python3 ML/DG.py`
2. Train model: `python3 ML/ML.py` (generates analysis_results.json)
3. Update bots: `python3 ml_insights_updater.py`

**Q: Do I need to restart bots after updating?**
A: 
- **ML parameter updates**: No, changes apply next round
- **Strategy updates**: No, changes apply next round
- **Code logic changes**: Yes, restart required

---

## 16. Appendices

### Appendix A: Complete File Listings

#### A.1 Environment Variables (.env)

```bash
# Bot 1-3 (Active)
PRIVATE_KEY_1=0x...
WALLET_ADDRESS_1=0x...
PRIVATE_KEY_2=0x...
WALLET_ADDRESS_2=0x...
PRIVATE_KEY_3=0x...
WALLET_ADDRESS_3=0x...

# Bot 4-12 (Optional, for expansion)
PRIVATE_KEY_4=0x...
WALLET_ADDRESS_4=0x...
# ... up to 12 ...

# Telegram
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
```

#### A.2 Key Code Locations

| Feature | File | Line Range |
|---------|------|-----------|
| BOT_NUMBER config | fin1/2/3.py | 26 |
| ML score calculation | fin1/2/3.py | 578-692 |
| Decision logic | fin1/2/3.py | 694-819 |
| Bet placement | fin1/2/3.py | 915-970 |
| Shared loss loading | fin1/2/3.py | 204-230 |
| BTC tracking | fin1/2/3.py | 258-323 |
| Streak validation | fin1/2/3.py | 327-357 |
| Claim logic | claimer_bot.py | 110-216 |
| CSV update | claimer_bot.py | 218-240 |
| Strategy switching | strategy_updater.py | 30-284 |
| ML update | ml_insights_updater.py | 52-93 |

### Appendix B: Contract ABI (prediction_abi.json)

The full ABI is stored in `prediction_abi.json`. Key functions:

```json
[
  {
    "inputs": [],
    "name": "currentEpoch",
    "outputs": [{"type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{"name": "epoch", "type": "uint256"}],
    "name": "rounds",
    "outputs": [{"type": "tuple", "components": [...]}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {"name": "epoch", "type": "uint256"},
      {"name": "user", "type": "address"}
    ],
    "name": "claimable",
    "outputs": [{"type": "uint256"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{"name": "epoch", "type": "uint256"}],
    "name": "betBull",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [{"name": "epoch", "type": "uint256"}],
    "name": "betBear",
    "outputs": [],
    "stateMutability": "payable",
    "type": "function"
  },
  {
    "inputs": [{"name": "epochs", "type": "uint256[]"}],
    "name": "claim",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
]
```

### Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Epoch** | A single 5-minute prediction round |
| **Bet Ratio** | bull_amount / bear_amount |
| **Payout Multiplier** | total_pool / winning_side_amount |
| **ML Score** | Machine learning prediction score (-1 to +1) |
| **Contrarian** | Strategy of betting against consensus/whales |
| **Consensus** | Strategy of betting with consensus/whales |
| **Whale** | Large bet (≥2 BNB in current config) |
| **Streak** | Consecutive wins for same side (bull or bear) |
| **Lock Price** | Oracle price at 5-minute mark (when betting closes) |
| **Close Price** | Oracle price at 10-minute mark (determines winner) |
| **Skip Rounds** | Loss prevention mechanism (skip 5 rounds after loss) |
| **Shared Loss State** | JSON file coordinating skip count across all bots |
| **Net Profit** | Total payout - original bet - gas fees |
| **BTC Influence** | BTC's 5-min price change effect on prediction (-0.4 to +0.4) |
| **Price Momentum** | Recent price trend indicator (-1 to +1) |
| **Streak Validation** | Checking if streak matches current price action |

### Appendix D: Performance Benchmarks

Based on 10,000 historical rounds:

| Metric | Value |
|--------|-------|
| **Overall Bull Win Rate** | 50.2% |
| **Overall Bear Win Rate** | 49.8% |
| **Tie Rate** | <0.1% |
| **Average Pool Size** | 8.5 BNB |
| **Average Bet Ratio** | 1.02 |
| **Best Bull Hour** | Hour 17 (81.8% bull wins) |
| **Worst Bull Hour** | Hour 19 (36.4% bull wins) |
| **ML Model Accuracy** | 55.0% (Random Forest) |
| **Contrarian Strategy Win Rate** | ~55% |
| **Consensus Strategy Win Rate** | ~50% (theoretical) |

### Appendix E: Version History

| Version | Date | Changes |
|---------|------|---------|
| **1.0** | Dec 2024 | Initial release - Single bot |
| **1.5** | Dec 2024 | Added ML model, BTC tracking |
| **2.0** | Jan 2025 | Multi-bot architecture, shared loss state, claimer bot |

### Appendix F: Credits & License

**Developed by:** RICH Development Team  
**Contributors:**
- Core Bot Logic
- ML Model Training
- Strategy Development
- Documentation

**License:** Proprietary - For personal/authorized use only

**Disclaimer:** This software is provided "as is" without warranty. Trading crypto involves risk. Past performance does not guarantee future results. Use at your own risk.

---

## 🎓 Conclusion

The RICH Multi-Bot Prediction System represents a sophisticated approach to automated crypto betting, combining:

- **Advanced ML modeling** (Random Forest with 8 features)
- **Multi-bot coordination** (3 bots, shared loss prevention)
- **Real-time data analysis** (BTC correlation, price momentum, streaks)
- **Risk management** (5-round skip, dynamic bet sizing)
- **Comprehensive logging** (40+ data points per bet)
- **Flexible strategies** (Contrarian ⟷ Consensus switching)

With proper configuration and monitoring, this system provides a data-driven edge in PancakeSwap prediction markets.

**Remember:**
1. ✅ Always backup your `.env` file
2. ✅ Monitor Telegram notifications daily
3. ✅ Review CSV performance weekly
4. ✅ Retrain ML model monthly with fresh data
5. ✅ Keep bots updated with latest code

---

**For support or questions:**
- Check the FAQ section
- Review troubleshooting guide
- Analyze bet_history/bets.csv for insights

**Happy Trading! 🚀💰**

```
███████╗███╗   ██╗██████╗      ██████╗ ███████╗    ██████╗  ██████╗  ██████╗
██╔════╝████╗  ██║██╔══██╗    ██╔═══██╗██╔════╝    ██╔══██╗██╔═══██╗██╔════╝
█████╗  ██╔██╗ ██║██║  ██║    ██║   ██║█████╗      ██║  ██║██║   ██║██║     
██╔══╝  ██║╚██╗██║██║  ██║    ██║   ██║██╔══╝      ██║  ██║██║   ██║██║     
███████╗██║ ╚████║██████╔╝    ╚██████╔╝██║         ██████╔╝╚██████╔╝╚██████╗
╚══════╝╚═╝  ╚═══╝╚═════╝      ╚═════╝ ╚═╝         ╚═════╝  ╚═════╝  ╚═════╝
```
