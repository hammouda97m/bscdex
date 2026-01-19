# BSCDex - Comprehensive Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Architecture](#architecture)
4. [Core Components](#core-components)
5. [Smart Contract Integration](#smart-contract-integration)
6. [Configuration](#configuration)
7. [API Reference](#api-reference)
8. [Data Structures](#data-structures)
9. [Workflows](#workflows)
10. [Security](#security)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)

---

## Overview

**BSCDex** is an advanced automated trading and prediction bot for PancakeSwap on the Binance Smart Chain (BSC). It provides a comprehensive suite of tools for:

- **Prediction Market Trading**: Automated betting on BNB price movements
- **Limit Order Management**: Create and monitor limit orders with take-profit strategies
- **Multi-Wallet Management**: Create, manage, and monitor multiple trading wallets
- **Automated Swaps**: Execute BNB ↔ USDT swaps using PancakeSwap V3 (0.05% pool)
- **Telegram Bot Integration**: Full remote control via Telegram commands
- **Real-time Monitoring**: Track rounds, streaks, and price movements
- **Reward Management**: Claim prediction rewards automatically

### Key Features

1. **Advanced Limit Orders**
   - Price-triggered swap execution
   - Automatic take-profit orders
   - Linked order management
   - Balance locking to prevent double-spending

2. **Smart Trading**
   - V3 0.05% pool for best rates
   - Automatic WBNB → BNB unwrapping
   - Chainlink oracle price fallback
   - Slippage protection (0.05%)

3. **Telegram Control**
   - Interactive command system
   - Confirmation dialogs for critical operations
   - Real-time notifications
   - Comprehensive menu system

4. **Analytics & Monitoring**
   - PnL tracking with FIFO accounting
   - ATR (Average True Range) volatility analysis
   - 24-round history tracking
   - Streak detection and notifications

---

## Repository Structure

```
bscdex/
├── .git/                          # Git version control
├── README.md                      # Basic repository description
├── prediction_abi.json           # PancakeSwap Prediction contract ABI
├── prediction_bot.zip            # Legacy bot archive
├── combiviewer.py                # Prediction rounds viewer and monitor
├── limit_orders.py               # Limit order management system
├── mv5.py                        # Main bot application
├── telegram_handler.py           # Telegram bot command handler
├── created_wallets.json          # Wallet storage (auto-generated)
├── limit_orders.json             # Order storage (auto-generated)
└── rounds_cache.json             # Rounds history cache (auto-generated)
```

### File Descriptions

| File | Lines | Purpose |
|------|-------|---------|
| `combiviewer.py` | 805 | Standalone viewer for PancakeSwap prediction rounds with Telegram notifications |
| `limit_orders.py` | 915 | Complete limit order system with take-profit functionality |
| `mv5.py` | 3,127 | Main bot orchestrator with wallet management, swaps, betting, and rewards |
| `telegram_handler.py` | 1,926 | Telegram bot interface with 30+ commands |
| `prediction_abi.json` | 1 (JSON) | Smart contract ABI for PancakeSwap Prediction V2 |

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     BSCDex System                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   Telegram   │────────>│   Handler    │                 │
│  │     Bot      │<────────│   (Commands) │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│  ┌────────────────────────────────▼──────────────────────┐ │
│  │              Main Bot (mv5.py)                        │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │  WalletManager │ SwapManager │ BettingManager │       │ │
│  │  RewardManager │ LimitOrderManager                    │ │
│  └───────┬───────────────┬────────────────┬──────────────┘ │
│          │               │                │                 │
├──────────▼───────────────▼────────────────▼─────────────────┤
│           BSC Blockchain Interactions                        │
├─────────────────────────────────────────────────────────────┤
│  PancakeSwap V3    │  Chainlink Oracle  │  WBNB/USDT      │
│  Smart Router      │  Price Feeds       │  Contracts       │
│  Prediction V2     │                    │                   │
└─────────────────────────────────────────────────────────────┘
```

### Threading Model

```
Main Thread
├── Interactive CLI Menu
└── Background Threads
    ├── Telegram Monitor (polling every 0.5s)
    └── Limit Order Monitor (checking prices every 1.5s)
```

### Data Flow

```
User Command (Telegram/CLI)
    │
    ▼
Command Handler (TelegramHandler/Main Menu)
    │
    ▼
Manager Layer (WalletManager, SwapManager, etc.)
    │
    ▼
Web3 Contract Calls
    │
    ▼
BSC Blockchain
    │
    ▼
Transaction Confirmation
    │
    ▼
Telegram Notification / Console Output
```

---

## Core Components

### 1. Main Bot (`mv5.py`)

The central orchestrator that integrates all components.

#### Key Classes

##### `WalletManager`
Manages multiple trading wallets.

**Methods:**
- `create_new_wallet(name=None)` - Generate new wallet with private key
- `get_wallet_balances(wallet_info)` - Fetch BNB and USDT balances
- `list_wallets()` - Display all wallets with available balances
- `delete_wallet(wallet_index)` - Remove wallet from storage
- `empty_wallet(wallet_index, main_wallet_address, amount=None)` - Transfer funds
- `send_to_external(main_wallet_address, main_private_key)` - Send to external address

**Data Structure:**
```python
{
    "name": "Wallet_1",
    "address": "0x...",
    "private_key": "0x...",
    "created_at": "2024-01-19T12:00:00",
    "balance_bnb": 0.5,
    "balance_usdt": 100.0
}
```

##### `SwapManager`
Handles token swaps using PancakeSwap V3.

**Methods:**
- `get_usdt_to_bnb_rate(usdt_amount)` - Query V3 0.05% pool for rate
- `get_bnb_to_usdt_rate(bnb_amount)` - Query V3 0.05% pool for rate
- `execute_swap(wallet, swap_direction, amount)` - Execute swap
- `_swap_usdt_to_bnb_v3(wallet_address, private_key, usdt_amount)` - USDT → BNB with auto-unwrap
- `_swap_bnb_to_usdt_v3(wallet_address, private_key, bnb_amount)` - BNB → USDT

**Key Features:**
- Uses QuoterV2 for accurate pricing
- 0.05% fee pool (best rates)
- Automatic WBNB unwrapping for USDT → BNB swaps
- Chainlink price fallback
- Approval management for ERC20 tokens

##### `BettingManager`
Places bets on PancakeSwap Prediction V2.

**Methods:**
- `place_bet(wallet_info, direction, bet_amount_bnb)` - Place bull/bear bet

**Validation:**
- Checks round lock status
- Validates wallet balance
- Ensures sufficient gas

##### `RewardManager`
Claims prediction rewards.

**Methods:**
- `get_claimable_epochs(wallet_address)` - Find claimable rounds
- `get_claimable_amount(wallet_address, epoch)` - Calculate reward amount
- `claim_rewards(wallet_info, epochs_to_claim=None)` - Claim all/specific epochs
- `show_claimable_rewards(wallet_info)` - Display claimable rewards

**Reward Calculation:**
```python
user_reward = (user_bet_amount * total_reward_pool) / winning_side_total
```

---

### 2. Limit Order System (`limit_orders.py`)

Advanced limit order management with take-profit functionality.

#### Key Features

1. **Order Types**
   - **Pending**: Active, monitoring price
   - **Waiting for Execution**: Take-profit orders waiting for parent order
   - **Executed**: Successfully completed
   - **Cancelled**: Manually cancelled

2. **Balance Locking**
   - Prevents double-spending
   - Shows available vs. locked balances
   - Validates order creation against available balance

3. **Take-Profit Orders**
   - Automatically created when parent order executes
   - Linked order management
   - Profit target in USDT
   - Cascading cancellation

#### Class: `LimitOrderManager`

**Constructor:**
```python
def __init__(self, swap_manager, betting_manager, wallet_manager, 
             web3, chainlink_contract, usdt_address, wbnb_address)
```

**Core Methods:**

##### Order Creation
```python
create_order_interactive()  # Interactive CLI wizard
create_order(wallet_idx, wallet_name, wallet_address, 
             swap_direction, amount, trigger_price)  # Programmatic
```

##### Order Management
```python
view_orders()  # Display all orders
cancel_order(order_id)  # Cancel order and linked TPs
```

##### Execution
```python
check_and_execute_orders()  # Background monitoring
execute_swap(wallet, swap_direction, amount)  # Execute swap with auto-unwrap
```

##### Take-Profit
```python
check_and_create_take_profit(executed_order)  # Activate waiting TP orders
```

##### PnL Tracking
```python
calculate_pnl()  # FIFO inventory tracking
get_locked_balances(wallet_address)  # Check locked funds
```

**Order Data Structure:**
```python
{
    "id": 1,
    "wallet_idx": 0,
    "wallet_name": "Wallet_1",
    "wallet_address": "0x...",
    "swap_direction": "usdt_to_bnb",  # or "bnb_to_usdt"
    "amount": 50.0,
    "amount_label": "50.00 USDT",
    "trigger_price": 900.0,
    "current_price_at_creation": 920.0,
    "expected_receive": 0.054348,
    "receive_label": "~0.054348 BNB",
    "created_at": "2024-01-19T12:00:00",
    "status": "pending",
    "execution_price": 900.5,  # Set when executed
    "executed_at": "2024-01-19T12:30:00",  # Set when executed
    "linked_order_id": None,  # For take-profit orders
    "profit_target_usdt": 0.0  # For take-profit orders
}
```

#### PnL Calculation Algorithm

**FIFO (First-In-First-Out) Inventory Tracking:**

```python
# Example:
# Buy 1: 0.5 BNB at $900 = $450
# Buy 2: 0.3 BNB at $910 = $273
# Sell:  0.6 BNB at $920 = $552

# FIFO allocation:
# - Use all 0.5 BNB from Buy 1 ($450)
# - Use 0.1 BNB from Buy 2 ($91)
# Total cost basis: $541
# Revenue: $552
# PnL: $11 (+2.03%)
```

---

### 3. Telegram Handler (`telegram_handler.py`)

Full-featured Telegram bot with 30+ commands.

#### Architecture

```
TelegramHandler
├── Command Processing (polling)
├── State Management (pending confirmations)
├── Message Formatting (HTML)
└── Notification System
```

#### Command Categories

##### Wallet Commands
- `/wallets` - List all wallets with locked balance info
- `/balance` - Main wallet balance
- `/create [name]` - Create new wallet
- `/send [bnb|usdt] [amount] [address]` - Send to external address

##### Swap Commands
- `/swap_usdt [amount]` - Swap USDT → BNB (with confirmation)
- `/swap_bnb [amount]` - Swap BNB → USDT (with confirmation)

##### Betting Commands
- `/bet [wallet]/[usdt]/[up|down]` - Place bet
  - Example: `/bet 1/50/up`

##### Reward Commands
- `/rewards [wallet]` - Show claimable rewards
- `/claim [wallet]` - Claim all rewards

##### Limit Order Commands
- `/limit` - Create limit order (interactive)
- `/profit [order_id] [profit_usdt]` - Create take-profit order
- `/orders` - View all orders with links
- `/cancel [order_id]` - Cancel order (and linked TPs)

##### Utility Commands
- `/price` - Current BNB price (V3 + Chainlink)
- `/atr [interval] [period]` - Calculate ATR volatility
- `/pnl` - View profit & loss report
- `/empty [wallet] [amount?]` - Empty/send from wallet
- `/drain` - Drain all wallets to main
- `/unwrap [wallet?]` - Unwrap WBNB to BNB

#### State Management

The bot maintains state for multi-step operations:

```python
self.pending_swap = {
    'type': 'usdt_to_bnb',
    'amount': 50.0,
    'expected_output': 0.054,
    'wallet_address': '0x...'
}

self.pending_limit_order = {
    'wallet_idx': 0,
    'wallet_name': 'Wallet_1',
    'swap_direction': 'usdt_to_bnb',
    'amount': 50.0,
    'trigger_price': 900.0
}
```

**Confirmation Flow:**
1. User sends command: `/swap_usdt 50`
2. Bot stores in `pending_swap` and sends preview
3. User replies: `YES` or `NO`
4. Bot executes or cancels based on response

---

### 4. Prediction Viewer (`combiviewer.py`)

Standalone viewer for PancakeSwap Prediction rounds.

#### Features

1. **Round History**
   - Caches last 24 rounds
   - Displays: Open/Close prices, payouts, winners, pool size
   - Shows current streak

2. **Live Monitoring**
   - Real-time price updates (Chainlink)
   - Countdown timer
   - Bet data in last 25 seconds

3. **Notifications**
   - Streak alerts (7+ consecutive wins)
   - Big price movements (>$2.50)
   - 24-round summary in all notifications

4. **ML Insights**
   - Hourly bull rates
   - Feature weights
   - Bet ratio analysis
   - Volatility calculation

#### Key Functions

```python
fetch_round_history()  # Fetch and cache rounds
display_rounds_history()  # Display formatted table
check_streak_and_notify()  # Detect streaks
check_price_movement_and_notify()  # Detect big moves
get_max_bets_for_round(epoch, start_ts, lock_ts)  # Find whale bets
calculate_ml_prediction_score(bet_data)  # ML prediction
```

#### ML Model Features

**Hourly Bull Rates:**
```python
HOURLY_BULL_RATES = {
    0: 0.518, 1: 0.505, 2: 0.514, 3: 0.528, 4: 0.509, 5: 0.528,
    # ... 24 hours
}
```

**Feature Weights:**
```python
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
```

**Prediction Score:**
```python
score = 0.0

# Bet ratio factor
if bet_ratio > 1.117:  # Bulls favored
    score += 0.3 * weight["bet_ratio"]
elif bet_ratio < 1.051:  # Bears favored
    score -= 0.3 * weight["bet_ratio"]

# Volatility factor
volatility_factor = min(price_volatility * 2, 0.2)
score += volatility_factor * weight["price_volatility"]

# Pool size factor
if total_amount > 5.0:
    score += 0.2 * weight["total_bets_amount"]

# Hourly bias
hour_bias = (hourly_bull_rate - 0.5) * 2
score += hour_bias * weight["hour"]

# Whale influence
if bull_whales > bear_whales:
    score += 0.1
elif bear_whales > bull_whales:
    score -= 0.1

return max(-1.0, min(1.0, score))
```

---

## Smart Contract Integration

### PancakeSwap Prediction V2

**Contract Address:** `0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA`

#### Key Functions Used

##### Betting
```solidity
function betBull(uint256 epoch) external payable
function betBear(uint256 epoch) external payable
```

##### Information
```solidity
function currentEpoch() external view returns (uint256)
function rounds(uint256 epoch) external view returns (Round)
function ledger(uint256 epoch, address user) external view returns (BetInfo)
function claimable(uint256 epoch, address user) external view returns (bool)
```

##### Claiming
```solidity
function claim(uint256[] calldata epochs) external
```

#### Round Structure

```solidity
struct Round {
    uint256 epoch;
    uint256 startTimestamp;
    uint256 lockTimestamp;
    uint256 closeTimestamp;
    int256 lockPrice;        // Oracle price at lock (8 decimals)
    int256 closePrice;       // Oracle price at close (8 decimals)
    uint256 lockOracleId;
    uint256 closeOracleId;
    uint256 totalAmount;     // Total BNB in pool
    uint256 bullAmount;      // BNB on bull side
    uint256 bearAmount;      // BNB on bear side
    uint256 rewardBaseCalAmount;
    uint256 rewardAmount;    // Total rewards after treasury fee
    bool oracleCalled;
}
```

#### BetInfo Structure

```solidity
struct BetInfo {
    Position position;  // 0 = Bull, 1 = Bear
    uint256 amount;     // Bet amount in wei
    bool claimed;       // Whether rewards claimed
}
```

### PancakeSwap V3 Smart Router

**Contract Address:** `0x13f4EA83D0bd40E75C8222255bc855a974568Dd4`

#### Key Function

```solidity
function exactInputSingle(ExactInputSingleParams calldata params) 
    external payable returns (uint256 amountOut)

struct ExactInputSingleParams {
    address tokenIn;
    address tokenOut;
    uint24 fee;             // 500 = 0.05%
    address recipient;
    uint256 amountIn;
    uint256 amountOutMinimum;
    uint160 sqrtPriceLimitX96;
}
```

### PancakeSwap V3 QuoterV2

**Contract Address:** `0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997`

#### Price Quote Function

```solidity
function quoteExactInputSingle(QuoteExactInputSingleParams calldata params)
    external returns (
        uint256 amountOut,
        uint160 sqrtPriceX96After,
        uint32 initializedTicksCrossed,
        uint256 gasEstimate
    )

struct QuoteExactInputSingleParams {
    address tokenIn;
    address tokenOut;
    uint256 amountIn;
    uint24 fee;
    uint160 sqrtPriceLimitX96;
}
```

### Chainlink Price Feed

**Contract Address:** `0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE`

```solidity
function latestRoundData() external view returns (
    uint80 roundId,
    int256 answer,      // Price in 8 decimals
    uint256 startedAt,
    uint256 updatedAt,
    uint80 answeredInRound
)
```

### WBNB (Wrapped BNB)

**Contract Address:** `0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c`

```solidity
function withdraw(uint256 wad) external  // Unwrap WBNB → BNB
function balanceOf(address owner) external view returns (uint256)
```

### USDT (Tether)

**Contract Address:** `0x55d398326f99059fF775485246999027B3197955`

```solidity
function approve(address spender, uint256 amount) external returns (bool)
function transfer(address to, uint256 amount) external returns (bool)
function balanceOf(address account) external view returns (uint256)
function allowance(address owner, address spender) external view returns (uint256)
```

---

## Configuration

### Environment Variables (.env)

```bash
# Main Wallet
MAIN_PRIVATE_KEY="0x..."
MAIN_WALLET_ADDRESS="0x..."

# Telegram Bot
TELEGRAM_TOKEN="bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
TELEGRAM_CHAT_ID="123456789"
```

### Network Configuration

```python
# BSC Mainnet
RPC_URL = "https://bsc-mainnet.nodereal.io/v1/..."
CHAIN_ID = 56
GAS_PRICE = 3  # gwei (adjustable)

# Contract Addresses
PREDICTION_CONTRACT = "0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA"
USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
SMART_ROUTER_ADDRESS = "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4"
QUOTER_V2_ADDRESS = "0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997"
CHAINLINK_BNB_USD = "0x0567F2323251f0Aab15c8dFb1967E4e8A7D42aeE"
```

### Trading Parameters

```python
# Slippage
SLIPPAGE_TOLERANCE = 0.9995  # 0.05%

# Fees
V3_FEE_TIER = 500  # 0.05% (best rate pool)

# Gas Limits
SWAP_GAS_LIMIT = 300000
BET_GAS_LIMIT = 200000
CLAIM_GAS_LIMIT = 200000
UNWRAP_GAS_LIMIT = 50000
TRANSFER_GAS_LIMIT = 21000
APPROVE_GAS_LIMIT = 100000
```

---

## API Reference

### Web3 Connection

```python
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

web3 = Web3(Web3.HTTPProvider(RPC_URL))
web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# Check connection
if not web3.is_connected():
    raise Exception("Failed to connect to BSC")
```

### Contract Interaction Patterns

#### Reading Data

```python
# Get current epoch
current_epoch = prediction_contract.functions.currentEpoch().call()

# Get round data
round_data = prediction_contract.functions.rounds(epoch).call()

# Get user bet
user_bet = prediction_contract.functions.ledger(epoch, address).call()

# Check if claimable
is_claimable = prediction_contract.functions.claimable(epoch, address).call()
```

#### Writing Data (Transactions)

```python
# Build transaction
nonce = web3.eth.get_transaction_count(wallet_address)

tx = contract.functions.betBull(epoch).build_transaction({
    'from': wallet_address,
    'value': web3.to_wei(amount, 'ether'),
    'gas': 200000,
    'gasPrice': web3.to_wei('3', 'gwei'),
    'nonce': nonce,
    'chainId': 56
})

# Sign transaction
signed_tx = web3.eth.account.sign_transaction(tx, private_key)

# Send transaction
tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

# Wait for confirmation
receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

if receipt.status == 1:
    print("Transaction successful!")
```

### V3 Swap Pattern

```python
# 1. Get quote
params = {
    'tokenIn': USDT_CONTRACT,
    'tokenOut': WBNB,
    'amountIn': usdt_amount_wei,
    'fee': 500,
    'sqrtPriceLimitX96': 0
}
result = quoter_v2_contract.functions.quoteExactInputSingle(params).call()
expected_bnb = result[0] / 1e18

# 2. Check allowance
allowance = usdt_contract.functions.allowance(wallet, SMART_ROUTER).call()
if allowance < usdt_amount_wei:
    # Approve
    approve_tx = usdt_contract.functions.approve(
        SMART_ROUTER, usdt_amount_wei * 2
    ).build_transaction({...})
    # Sign and send...

# 3. Execute swap
swap_params = {
    'tokenIn': USDT_CONTRACT,
    'tokenOut': WBNB,
    'fee': 500,
    'recipient': wallet,
    'amountIn': usdt_amount_wei,
    'amountOutMinimum': int(expected_bnb * 0.9995 * 1e18),
    'sqrtPriceLimitX96': 0
}
swap_tx = smart_router_contract.functions.exactInputSingle(swap_params).build_transaction({...})
# Sign and send...

# 4. Unwrap WBNB → BNB (if needed)
wbnb_balance = wbnb_contract.functions.balanceOf(wallet).call()
if wbnb_balance > 0:
    unwrap_tx = wbnb_contract.functions.withdraw(wbnb_balance).build_transaction({...})
    # Sign and send...
```

---

## Data Structures

### Wallet Storage (`created_wallets.json`)

```json
[
  {
    "name": "Wallet_1_120000",
    "address": "0x1234...",
    "private_key": "0xabcd...",
    "created_at": "2024-01-19T12:00:00.000000",
    "balance_bnb": 0.5,
    "balance_usdt": 100.0
  }
]
```

### Limit Orders Storage (`limit_orders.json`)

```json
{
  "rounds_history": [...],
  "last_updated": "2024-01-19T12:00:00.000000"
}
```

### Rounds Cache (`rounds_cache.json`)

```json
{
  "rounds_history": [
    {
      "epoch": 12345,
      "lock_price": 920.5,
      "close_price": 922.3,
      "lock_price_usdt": 920.5,
      "close_price_usdt": 922.3,
      "price_change_usdt": 1.8,
      "bull_payout": 1.95,
      "bear_payout": 0.0,
      "winner": "BULL",
      "total_amount": 10.5,
      "max_bull_bet": 2.5,
      "max_bear_bet": 1.3
    }
  ],
  "last_updated": "2024-01-19T12:00:00.000000"
}
```

---

## Workflows

### 1. Placing a Bet (Full Flow)

```
User (Telegram): /bet 1/50/up
    │
    ▼
TelegramHandler.cmd_bet()
    │
    ├─> Parse: wallet=1, usdt=50, direction=up
    ├─> Validate wallet exists
    ├─> Get swap rate: 50 USDT → ~0.054 BNB
    │
    ▼
SwapManager.swap_usdt_to_bnb()
    │
    ├─> Check USDT balance
    ├─> Get V3 quote from QuoterV2
    ├─> Check/Approve USDT for Smart Router
    ├─> Execute exactInputSingle() on Smart Router
    ├─> Wait for confirmation
    ├─> Check for WBNB balance
    ├─> Unwrap WBNB → BNB if needed
    │
    ▼
BettingManager.place_bet()
    │
    ├─> Get current epoch
    ├─> Check round not locked
    ├─> Validate BNB balance
    ├─> Build betBull(epoch) transaction
    ├─> Sign and send
    ├─> Wait for confirmation
    │
    ▼
Send success notification to Telegram
```

### 2. Limit Order Execution

```
Background Thread (every 1.5s)
    │
    ▼
LimitOrderManager.check_and_execute_orders()
    │
    ├─> Get current BNB price from V3 or Chainlink
    ├─> Loop through pending orders
    │   │
    │   ▼
    │   For each order:
    │   ├─> Check if trigger condition met:
    │   │   • BNB→USDT: price >= trigger_price
    │   │   • USDT→BNB: price <= trigger_price
    │   │
    │   ▼
    │   If triggered:
    │   ├─> Execute swap via SwapManager
    │   ├─> Mark order as executed
    │   ├─> Send Telegram notification
    │   ├─> Check for linked take-profit orders
    │   │   │
    │   │   ▼
    │   │   If TP order exists:
    │   │   ├─> Activate TP order (status: pending)
    │   │   ├─> Send TP activated notification
    │   │
    │   ▼
    │   Save orders to file
```

### 3. Creating Take-Profit Order

```
User: /profit 5 4  (Order #5, $4 profit)
    │
    ▼
Find original order #5
    │
    ├─> Validate order is pending
    ├─> Get trigger price from order
    │
    ▼
Calculate TP parameters:
    │
    ├─> If original: BNB → USDT
    │   ├─> expected_usdt = bnb_amount * trigger_price * 0.9995
    │   ├─> usdt_to_swap_back = expected_usdt - profit_target
    │   ├─> tp_target_price = (usdt_to_swap_back / bnb_amount) * 0.9995
    │   └─> tp_direction = usdt_to_bnb
    │
    └─> If original: USDT → BNB
        ├─> bnb_received = original.expected_receive
        ├─> target_usdt = usdt_spent + profit_target
        ├─> tp_target_price = (target_usdt / bnb_received) * 1.0005
        └─> tp_direction = bnb_to_usdt
    │
    ▼
Create TP order:
    ├─> status = waiting_for_execution
    ├─> linked_order_id = 5
    ├─> Save to orders file
    │
    ▼
Send preview notification
```

### 4. PnL Calculation (FIFO)

```
Get all executed orders, sorted by time
    │
    ▼
Initialize inventory per wallet:
    ├─> bnb_stack = []  # List of (bnb, cost_basis)
    ├─> total_bnb = 0
    └─> total_cost = 0
    │
    ▼
For each order:
    │
    ├─> If USDT → BNB (BUY):
    │   ├─> Add to stack:
    │   │   ├─> bnb_bought = usdt_spent / buy_price * 0.9995
    │   │   └─> stack.append({bnb: bnb_bought, cost: usdt_spent})
    │   │
    │   └─> Update totals
    │
    └─> If BNB → USDT (SELL):
        ├─> bnb_to_sell = order.amount
        ├─> Pop from stack (FIFO):
        │   │
        │   └─> While bnb_remaining > 0 and stack not empty:
        │       ├─> Take oldest entry
        │       ├─> If entry.bnb <= bnb_remaining:
        │       │   ├─> Use entire entry
        │       │   ├─> cost_basis += entry.cost
        │       │   └─> Pop entry
        │       └─> Else:
        │           ├─> Use partial entry
        │           ├─> cost_basis += entry.cost * ratio
        │           └─> Update entry
        │
        ├─> usdt_received = bnb_to_sell * sell_price * 0.9995
        ├─> pnl = usdt_received - cost_basis
        └─> pnl_percent = (pnl / cost_basis) * 100
```

---

## Security

### Private Key Management

**⚠️ CRITICAL SECURITY CONSIDERATIONS:**

1. **Environment Variables**
   - Store private keys in `.env` file
   - **NEVER** commit `.env` to Git
   - Add `.env` to `.gitignore`

2. **File Permissions**
   ```bash
   chmod 600 .env
   chmod 600 created_wallets.json
   ```

3. **Wallet Storage**
   - `created_wallets.json` contains private keys in plaintext
   - Protect this file with proper permissions
   - Consider encryption for production use

### Transaction Security

1. **Gas Price Management**
   - Default: 3 gwei (low priority)
   - Adjust based on network congestion
   - Consider using web3.eth.gas_price for dynamic pricing

2. **Slippage Protection**
   - Set `amountOutMinimum` to protect against front-running
   - Current: 0.05% slippage tolerance

3. **Nonce Management**
   - Always fetch fresh nonce before transaction
   - Handle nonce conflicts (transaction replacement)

4. **Approval Safety**
   - Approve 2x amount for future transactions
   - Consider revoking approvals when done

### Smart Contract Risks

1. **Rug Pull Protection**
   - Only interact with verified contracts
   - Check contract source on BSCScan
   - Verify contract addresses

2. **Oracle Manipulation**
   - Use Chainlink as backup price source
   - Compare prices before large trades

3. **Prediction Market Risks**
   - Bot can fail to claim in time
   - Oracle delays can affect rounds
   - Treasury fee reduces rewards (default 3%)

### Operational Security

1. **Telegram Bot**
   - Use secret token
   - Restrict to specific chat_id
   - Consider adding authentication layer

2. **RPC Endpoint**
   - Use private RPC endpoint
   - Monitor rate limits
   - Have backup endpoints

3. **Error Handling**
   - Log all errors
   - Alert on critical failures
   - Implement retry logic

---

## Deployment

### Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies
pip install web3 python-dotenv requests pandas ta
```

### Installation

```bash
# Clone repository
git clone https://github.com/hammouda97m/bscdex.git
cd bscdex

# Create .env file
cat > .env << EOF
MAIN_PRIVATE_KEY="0x..."
MAIN_WALLET_ADDRESS="0x..."
TELEGRAM_TOKEN="bot123456789:..."
TELEGRAM_CHAT_ID="123456789"
EOF

# Set permissions
chmod 600 .env
```

### Running the Bot

```bash
# Main bot (interactive menu + Telegram)
python mv5.py

# Prediction viewer only
python combiviewer.py
```

### systemd Service (Linux)

```ini
[Unit]
Description=BSCDex Trading Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bscdex
ExecStart=/usr/bin/python3 /path/to/bscdex/mv5.py
Restart=on-failure
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

```bash
# Install service
sudo cp bscdex.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bscdex
sudo systemctl start bscdex

# Check status
sudo systemctl status bscdex
sudo journalctl -u bscdex -f
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "mv5.py"]
```

```bash
# Build
docker build -t bscdex .

# Run
docker run -d --name bscdex \
  --env-file .env \
  -v $(pwd)/created_wallets.json:/app/created_wallets.json \
  -v $(pwd)/limit_orders.json:/app/limit_orders.json \
  bscdex
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Errors

**Problem:** `Failed to connect to BSC`

**Solutions:**
- Check RPC endpoint URL
- Try alternative RPC:
  ```python
  # Free public RPCs
  "https://bsc-dataseed.binance.org/"
  "https://bsc-dataseed1.defibit.io/"
  ```
- Check internet connection
- Verify POA middleware is injected

#### 2. Transaction Failures

**Problem:** Transaction reverts or fails

**Solutions:**
- Increase gas limit:
  ```python
  'gas': 400000  # Increase from 300000
  ```
- Increase gas price:
  ```python
  'gasPrice': web3.to_wei('5', 'gwei')  # Increase from 3
  ```
- Check wallet balance (BNB for gas)
- Verify contract approval

#### 3. Price Fetch Errors

**Problem:** `V3 price check failed`

**Solutions:**
- Bot automatically falls back to Chainlink
- Verify QuoterV2 contract address
- Check pool liquidity (0.05% pool)

#### 4. Swap Failures

**Problem:** Swap fails with "Insufficient allowance"

**Solutions:**
- Reset approval:
  ```python
  # Approve 0 first
  usdt_contract.functions.approve(SMART_ROUTER, 0)
  # Then approve amount
  usdt_contract.functions.approve(SMART_ROUTER, amount)
  ```

#### 5. Telegram Not Working

**Problem:** Bot doesn't respond to commands

**Solutions:**
- Verify `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`
- Check bot has correct permissions
- Test with BotFather commands
- Verify network connectivity

#### 6. WBNB Unwrap Issues

**Problem:** WBNB not unwrapping to BNB

**Solutions:**
- Manually unwrap via Telegram: `/unwrap 1`
- Check WBNB balance:
  ```python
  wbnb_contract.functions.balanceOf(wallet).call()
  ```
- Verify gas available for unwrap transaction

#### 7. Order Not Executing

**Problem:** Limit order not triggering

**Solutions:**
- Check order status: `/orders`
- Verify price monitoring thread is running
- Check if balance is locked
- Verify trigger price is realistic

#### 8. PnL Calculation Wrong

**Problem:** PnL shows incorrect values

**Solutions:**
- Ensure all trades are captured in `limit_orders.json`
- Check FIFO order execution
- Verify swap execution prices

### Debug Mode

Enable detailed logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add to web3 calls
import sys
logging.getLogger('web3').setLevel(logging.DEBUG)
```

### Testing Commands

```bash
# Test connection
python -c "from mv5 import web3; print(web3.is_connected())"

# Test price fetch
python -c "from mv5 import get_current_bnb_price_v3; print(get_current_bnb_price_v3())"

# Test wallet balance
python -c "
from mv5 import web3, MAIN_WALLET_ADDRESS
from web3 import Web3
addr = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)
print(f'BNB: {web3.eth.get_balance(addr) / 1e18}')
"
```

---

## Advanced Topics

### Custom Fee Tiers

Change from 0.05% to other pools:

```python
# 0.01% pool (lowest fee, less liquidity)
'fee': 100

# 0.05% pool (best for most trades)
'fee': 500

# 0.30% pool (higher fee, more liquidity)
'fee': 3000

# 1.00% pool (exotic pairs)
'fee': 10000
```

### Multi-Hop Swaps

For tokens without direct pools:

```python
# Example: TOKEN → WBNB → USDT
from mv5 import smart_router_contract

path = encode(['address', 'uint24', 'address', 'uint24', 'address'], [
    TOKEN_ADDRESS,
    3000,  # TOKEN → WBNB (0.3%)
    WBNB,
    500,   # WBNB → USDT (0.05%)
    USDT_CONTRACT
])

params = {
    'path': path,
    'recipient': wallet,
    'amountIn': amount_wei,
    'amountOutMinimum': min_out
}

tx = smart_router_contract.functions.exactInput(params).build_transaction({...})
```

### Custom Prediction Strategies

Implement custom betting logic:

```python
def should_bet_bull(round_data, ml_score):
    """Custom strategy"""
    
    # High ML score
    if ml_score > 0.5:
        return True
    
    # Bet ratio favors bulls
    bet_ratio = round_data['bull_amount'] / round_data['bear_amount']
    if bet_ratio > 1.2:
        return False  # Contrarian
    
    # Price volatility
    if calculate_price_volatility() < 0.02:  # Low volatility
        return True  # Bet on continuation
    
    return False
```

### Webhook Integration

Add webhook support for external signals:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/bet', methods=['POST'])
def webhook_bet():
    data = request.json
    wallet_idx = data['wallet']
    usdt_amount = data['amount']
    direction = data['direction']
    
    # Validate signature
    if not verify_signature(request.headers['X-Signature']):
        return {'error': 'Invalid signature'}, 401
    
    # Execute bet
    wallet = wallet_manager.wallets[wallet_idx]
    # ... place bet
    
    return {'success': True}

app.run(port=5000)
```

---

## Performance Optimization

### 1. RPC Caching

Implement request caching:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=128)
def cached_contract_call(function_name, *args, cache_time=10):
    """Cache contract read calls"""
    return getattr(contract.functions, function_name)(*args).call()

# Use with timestamp invalidation
def get_current_epoch():
    current_time = int(time.time() / 10) * 10  # Round to 10s
    return cached_contract_call('currentEpoch', current_time)
```

### 2. Batch Operations

Query multiple wallets at once:

```python
from web3 import Web3

# Create batch request
batch = web3.batch_requests()

for wallet in wallets:
    batch.add(web3.eth.get_balance, wallet['address'])
    batch.add(usdt_contract.functions.balanceOf(wallet['address']).call)

results = batch.execute()
```

### 3. Async Operations

Use async/await for parallel operations:

```python
import asyncio
from web3 import AsyncWeb3

async def fetch_all_wallets():
    tasks = []
    for wallet in wallets:
        tasks.append(get_wallet_balance_async(wallet))
    return await asyncio.gather(*tasks)
```

---

## API Integration Examples

### Get Round History

```python
def get_last_n_rounds(n=24):
    """Get last N completed rounds"""
    current_epoch = prediction_contract.functions.currentEpoch().call()
    
    rounds = []
    for epoch in range(current_epoch - n, current_epoch):
        round_data = prediction_contract.functions.rounds(epoch).call()
        
        if round_data[3] == 0:  # closeTimestamp == 0
            continue  # Skip incomplete rounds
        
        rounds.append({
            'epoch': round_data[0],
            'lock_price': round_data[4] / 1e8,
            'close_price': round_data[5] / 1e8,
            'total_amount': round_data[8] / 1e18,
            'bull_amount': round_data[9] / 1e18,
            'bear_amount': round_data[10] / 1e18,
            'winner': 'BULL' if round_data[5] > round_data[4] else 'BEAR'
        })
    
    return rounds
```

### Calculate Win Rate

```python
def calculate_win_rate(wallet_address, n=100):
    """Calculate user's win rate over last N rounds"""
    current_epoch = prediction_contract.functions.currentEpoch().call()
    
    wins = 0
    total = 0
    
    for epoch in range(current_epoch - n, current_epoch):
        try:
            user_bet = prediction_contract.functions.ledger(epoch, wallet_address).call()
            
            if user_bet[1] == 0:  # No bet
                continue
            
            total += 1
            
            if prediction_contract.functions.claimable(epoch, wallet_address).call():
                wins += 1
        except:
            continue
    
    return (wins / total * 100) if total > 0 else 0
```

---

## Contributing

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused (single responsibility)

### Testing

```python
# Unit test example
import unittest
from mv5 import SwapManager

class TestSwapManager(unittest.TestCase):
    def setUp(self):
        self.swap_manager = SwapManager()
    
    def test_get_usdt_to_bnb_rate(self):
        rate = self.swap_manager.get_usdt_to_bnb_rate(100)
        self.assertGreater(rate, 0)
        self.assertLess(rate, 1)  # 100 USDT < 1 BNB typically

if __name__ == '__main__':
    unittest.main()
```

---

## License

This project is for educational purposes. Use at your own risk.

**⚠️ Disclaimer:**
- Trading cryptocurrencies involves risk
- Bot can lose funds due to market volatility
- No warranty or guarantee of profits
- Author not responsible for financial losses

---

## Credits

**Developer:** Moe Yassin (www.moeyassin.com)

**Version:** 2.1.0

**Built with:**
- Web3.py - Ethereum interaction
- PancakeSwap V3 - DEX protocol
- Chainlink - Price oracles
- python-telegram-bot - Telegram integration

---

## Changelog

### v2.1.0 (Current)
- Added take-profit order system
- Implemented FIFO PnL tracking
- Added balance locking for limit orders
- Improved Telegram confirmations
- Added /unwrap command
- Enhanced error handling

### v2.0.0
- Complete rewrite with V3 integration
- Added limit order system
- Telegram bot implementation
- Multi-wallet support
- Automatic WBNB unwrapping

### v1.0.0 (Legacy)
- Basic prediction betting
- V2 router swaps
- Single wallet support

---

## FAQ

**Q: Why is my swap getting less BNB than expected?**
A: Slippage (0.05%), fees (0.05%), and price impact all reduce output.

**Q: Can I use multiple Telegram accounts?**
A: Currently limited to one chat_id. Modify `TelegramHandler` for multi-user support.

**Q: How often does the bot check prices for limit orders?**
A: Every ~1.5 seconds in the background thread.

**Q: What happens if the bot crashes with pending orders?**
A: Orders are saved to `limit_orders.json` and resume on restart.

**Q: Can I change the prediction contract?**
A: Yes, update `PREDICTION_CONTRACT` and provide the correct ABI.

**Q: How do I backup my wallets?**
A: Save `created_wallets.json` and `.env` securely. These contain private keys.

**Q: Why use V3 instead of V2?**
A: V3 0.05% pool offers better rates than V2 0.25% fee.

**Q: Can I run multiple bots?**
A: Yes, but use different wallet files and Telegram chat_ids.

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/hammouda97m/bscdex/issues
- Developer: www.moeyassin.com

---

**Last Updated:** January 19, 2026

**Document Version:** 1.0.0
