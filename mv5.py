import json
import os
import time
import secrets
from datetime import datetime
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from dotenv import load_dotenv, find_dotenv
from decimal import Decimal
from limit_orders import LimitOrderManager
import requests
import threading
import requests
import pandas as pd
from ta.volatility import AverageTrueRange

# === Config ===
load_dotenv(find_dotenv())

MAIN_PRIVATE_KEY = os.getenv("MAIN_PRIVATE_KEY")
MAIN_WALLET_ADDRESS = os.getenv("MAIN_WALLET_ADDRESS")

PREDICTION_CONTRACT = "0x18B2A687610328590Bc8F2e5fEdDe3b582A49cdA"
USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"
PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

web3 = Web3(Web3.HTTPProvider("https://bsc-mainnet.nodereal.io/v1/a16acfa17ef245b7973338fef461c447"))
web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

if not web3.is_connected():
    raise Exception("❌ Failed to connect to BSC")

with open("prediction_abi.json", "r") as f:
    PREDICTION_ABI = json.load(f)

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForETH",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# V3 QuoterV2 for accurate pricing (0.05% fee pool)
QUOTER_V2_ADDRESS = "0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997"

QUOTER_V2_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IQuoterV2.QuoteExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
            {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
            {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Create QuoterV2 contract instance
quoter_v2_contract = web3.eth.contract(
    address=Web3.to_checksum_address(QUOTER_V2_ADDRESS),
    abi=QUOTER_V2_ABI
)

# === V3 SMART ROUTER (for executing swaps) ===
SMART_ROUTER_ADDRESS = "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4"

SMART_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IV3SwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IV3SwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingleSupportingFeeOnTransferTokens",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "refundETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amountMinimum", "type": "uint256"},
            {"internalType": "address", "name": "recipient", "type": "address"}
        ],
        "name": "sweepToken",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountMinimum", "type": "uint256"},
            {"internalType": "address", "name": "recipient", "type": "address"}
        ],
        "name": "unwrapWETH9",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Create Smart Router contract instance
smart_router_contract = web3.eth.contract(
    address=Web3.to_checksum_address(SMART_ROUTER_ADDRESS),
    abi=SMART_ROUTER_ABI
)

prediction_contract = web3.eth.contract(
    address=Web3.to_checksum_address(PREDICTION_CONTRACT),
    abi=PREDICTION_ABI
)
usdt_contract = web3.eth.contract(
    address=Web3.to_checksum_address(USDT_CONTRACT),
    abi=ERC20_ABI
)
router_contract = web3.eth.contract(
    address=Web3.to_checksum_address(PANCAKE_ROUTER),
    abi=ROUTER_ABI
)

WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"

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

chainlink_contract = web3.eth.contract(
    address=CHAINLINK_BNB_USD,
    abi=CHAINLINK_ABI
)

# === TELEGRAM BOT FUNCTIONS ===

from telegram_handler import TelegramHandler


class WalletManager:
    def load_wallets(self):
        try:
            if os.path.exists(self.wallets_file):
                with open(self.wallets_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"⚠️ Error loading wallets: {e}")
            return []

    def save_wallets(self):
        try:
            with open(self.wallets_file, 'w') as f:
                json.dump(self.wallets, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving wallets: {e}")

    def __init__(self):
        self.wallets_file = "created_wallets.json"
        self.wallets = self.load_wallets()

    def create_new_wallet(self, name=None):
        try:
            private_key = "0x" + secrets.token_hex(32)
            account = Account.from_key(private_key)
            address = account.address
            if not name:
                name = f"Wallet_{len(self.wallets) + 1}_{datetime.now().strftime('%H%M%S')}"
            wallet_info = {
                "name": name,
                "address": address,
                "private_key": private_key,
                "created_at": datetime.now().isoformat(),
                "balance_bnb": 0,
                "balance_usdt": 0
            }
            self.wallets.append(wallet_info)
            self.save_wallets()
            print(f"✅ New wallet created!")
            print(f"📝 Name: {name}")
            print(f"📧 Address: {address}")
            print(f"🔑 Private Key: {private_key}")
            return wallet_info
        except Exception as e:
            print(f"❌ Error creating wallet: {e}")
            return None

    def get_wallet_balances(self, wallet_info):
        try:
            address = Web3.to_checksum_address(wallet_info["address"])
            bnb_balance = web3.eth.get_balance(address)
            bnb_balance = web3.from_wei(bnb_balance, 'ether')
            usdt_balance = usdt_contract.functions.balanceOf(address).call()
            usdt_balance = usdt_balance / 1e18
            wallet_info["balance_bnb"] = float(bnb_balance)
            wallet_info["balance_usdt"] = float(usdt_balance)
            return wallet_info
        except Exception as e:
            print(f"⚠️ Error getting balances: {e}")
            return wallet_info

    def list_wallets(self):
        if not self.wallets:
            print("📝 No wallets created yet.")
            return

        # Import limit_order_manager to check locked balances
        # We'll pass it as parameter instead - see main() changes below

        print("\n" + "=" * 80)
        print("📋 CREATED WALLETS")
        print("=" * 80)
        for i, wallet in enumerate(self.wallets):
            wallet = self.get_wallet_balances(wallet)
            print(f"{i + 1}. {wallet['name']}")
            print(f"   Address: {wallet['address']}")

            # Show BNB with available balance
            print(f"   BNB: {wallet['balance_bnb']:.6f}", end="")
            if hasattr(self, 'limit_order_manager'):
                locked_bnb, locked_usdt = self.limit_order_manager.get_locked_balances(wallet['address'])
                available_bnb = wallet['balance_bnb'] - locked_bnb
                if locked_bnb > 0:
                    print(f" → Available: {available_bnb:.6f} (🔒 {locked_bnb:.6f} locked)")
                else:
                    print()
            else:
                print()

            # Show USDT with available balance
            print(f"   USDT: {wallet['balance_usdt']:.2f}", end="")
            if hasattr(self, 'limit_order_manager'):
                locked_bnb, locked_usdt = self.limit_order_manager.get_locked_balances(wallet['address'])
                available_usdt = wallet['balance_usdt'] - locked_usdt
                if locked_usdt > 0:
                    print(f" → Available: {available_usdt:.2f} (🔒 {locked_usdt:.2f} locked)")
                else:
                    print()
            else:
                print()

            print(f"   Created: {wallet['created_at']}")
            print("-" * 80)

    def delete_wallet(self, wallet_index):
        try:
            if 0 <= wallet_index < len(self.wallets):
                deleted_wallet = self.wallets.pop(wallet_index)
                self.save_wallets()
                print(f"✅ Wallet '{deleted_wallet['name']}' deleted successfully!")
                return True
            else:
                print("❌ Invalid wallet index")
                return False
        except Exception as e:
            print(f"❌ Error deleting wallet: {e}")
            return False

    def empty_wallet(self, wallet_index, main_wallet_address, amount=None):
        """
        Empty wallet to main wallet
        If amount is None, sends all BNB
        If amount is specified, sends that amount only
        """
        try:
            if not (0 <= wallet_index < len(self.wallets)):
                print("❌ Invalid wallet index")
                return False

            wallet = self.wallets[wallet_index]
            wallet = self.get_wallet_balances(wallet)

            wallet_address = Web3.to_checksum_address(wallet['address'])
            total_balance = web3.eth.get_balance(wallet_address)
            total_balance_bnb = web3.from_wei(total_balance, 'ether')

            # Check minimum balance
            if total_balance_bnb <= 0.0001:
                print(f"❌ Wallet '{wallet['name']}' has insufficient BNB (need >0.0001 BNB)")
                return False

            # Determine amount to send
            if amount is None:
                # Send ALL (drain mode)
                print(f"\n💸 Draining wallet:  {wallet['name']}")
                print(f"💰 Total balance: {total_balance_bnb:.6f} BNB")

                gas_fee = web3.to_wei('0.0001', 'ether')
                amount_to_send = total_balance - gas_fee
                amount_bnb = web3.from_wei(amount_to_send, 'ether')

                print(f"📤 Sending:  {amount_bnb:.6f} BNB (keeping ~0.0001 for gas)")

            else:
                # Send SPECIFIC amount
                print(f"\n💸 Sending from wallet: {wallet['name']}")
                print(f"💰 Total balance: {total_balance_bnb:.6f} BNB")
                print(f"📤 Sending: {amount:.6f} BNB")

                # Validate amount
                gas_fee = web3.to_wei('0.0001', 'ether')
                amount_wei = web3.to_wei(amount, 'ether')

                if amount_wei + gas_fee > total_balance:
                    print(f"❌ Insufficient balance!")
                    print(f"   Available: {total_balance_bnb:.6f} BNB")
                    print(f"   Needed: {amount:.6f} BNB + ~0.0001 gas")
                    return False

                amount_to_send = amount_wei
                amount_bnb = amount

            print(f"📧 Sending to: {main_wallet_address}")

            nonce = web3.eth.get_transaction_count(wallet_address)

            tx = {
                'to': Web3.to_checksum_address(main_wallet_address),
                'value': amount_to_send,
                'gas': 21000,
                'gasPrice': web3.to_wei('3', 'gwei'),
                'nonce': nonce,
                'chainId': 56
            }

            signed_tx = web3.eth.account.sign_transaction(tx, wallet['private_key'])
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"🚀 Transaction sent! TX Hash: {web3.to_hex(tx_hash)}")
            print(f"⏳ Waiting for confirmation...")

            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                mode = "drained" if amount is None else f"sent {amount_bnb:.6f} BNB from"
                print(f"✅ Wallet {mode} successfully!")
                print(f"🔗 View on BSCScan: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")

                message = (
                    f"💸 Wallet {'Drained' if amount is None else 'Transfer'}!\n\n"
                    f"👤 Wallet: {wallet['name']}\n"
                    f"💰 Amount: {amount_bnb:.6f} BNB\n"
                    f"📧 Sent to: Main Wallet\n"
                    f"🔗 TX: {web3.to_hex(tx_hash)}\n"
                    f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
                )
                send_telegram_message(message)
                return True
            else:
                print("❌ Transaction failed!")
                return False

        except Exception as e:
            print(f"❌ Error emptying wallet: {e}")
            return False
            
    def send_to_external(self, main_wallet_address, main_private_key):
        """Send BNB or USDT from main wallet to external address"""
        try:
            print("\n" + "=" * 70)
            print("📤 SEND TO EXTERNAL ADDRESS")
            print("=" * 70)
            
            # Get main wallet balance
            main_address = Web3.to_checksum_address(main_wallet_address)
            bnb_balance = web3.eth.get_balance(main_address) / 1e18
            usdt_balance = usdt_contract.functions.balanceOf(main_address).call() / 1e18
            
            print(f"\n💰 Main Wallet Balance:")
            print(f"   💎 BNB:   {bnb_balance:.6f}")
            print(f"   💵 USDT: {usdt_balance:.2f}")
            
            # Select currency
            print(f"\n💱 SELECT CURRENCY:")
            print("1. 💎 BNB")
            print("2. 💵 USDT")
            print("3. ❌ Cancel")
            
            currency_choice = input("\nSelect (1-3): ").strip()
            
            if currency_choice == '3':
                print("❌ Cancelled")
                return False
            
            if currency_choice not in ['1', '2']:
                print("❌ Invalid choice")
                return False
            
            is_bnb = (currency_choice == '1')
            currency_name = "BNB" if is_bnb else "USDT"
            available_balance = bnb_balance if is_bnb else usdt_balance
            
            # Get recipient address
            print(f"\n📧 RECIPIENT ADDRESS:")
            recipient_input = input("Enter destination address (0x... ): ").strip()
            
            # Validate address
            try:
                recipient_address = Web3.to_checksum_address(recipient_input)
            except Exception as e:
                print(f"❌ Invalid address format: {e}")
                return False
            
            # Get amount
            print(f"\n💰 AMOUNT TO SEND:")
            print(f"Available:  {available_balance:.6f if is_bnb else available_balance:.2f} {currency_name}")
            
            amount_input = input(f"Enter {currency_name} amount (or 'all' for maximum): ").strip().lower()
            
            if amount_input == 'all': 
                if is_bnb:
                    # Reserve gas fee
                    gas_fee = 0.0001
                    if available_balance <= gas_fee:
                        print(f"❌ Insufficient balance to cover gas fee")
                        return False
                    amount = available_balance - gas_fee
                else:
                    amount = available_balance
            else:
                try:
                    amount = float(amount_input)
                except ValueError:
                    print("❌ Invalid amount")
                    return False
            
            # Validate amount
            if amount <= 0:
                print("❌ Amount must be positive")
                return False
            
            if is_bnb:
                gas_fee = 0.0001
                if amount + gas_fee > available_balance: 
                    print(f"❌ Insufficient balance!")
                    print(f"   Available: {available_balance:.6f} BNB")
                    print(f"   Needed: {amount:.6f} BNB + ~{gas_fee:.4f} gas")
                    return False
            else:
                if amount > available_balance:
                    print(f"❌ Insufficient balance!")
                    print(f"   Available: {available_balance:.2f} USDT")
                    print(f"   Requested: {amount:.2f} USDT")
                    return False
            
            # Show preview
            print(f"\n" + "=" * 70)
            print("📋 TRANSFER PREVIEW")
            print("=" * 70)
            print(f"💰 Amount: {amount:.6f if is_bnb else amount:.2f} {currency_name}")
            print(f"📤 From:  {main_wallet_address}")
            print(f"📥 To: {recipient_address}")
            if is_bnb:
                print(f"💵 Gas Fee: ~0.0001 BNB")
                print(f"💵 Remaining: {available_balance - amount - 0.0001:.6f} BNB")
            else:
                print(f"💵 Gas Fee: ~0.0001 BNB (from BNB balance)")
                print(f"💵 Remaining USDT: {available_balance - amount:.2f}")
            print("=" * 70)
            
            confirm = input("\n✅ Confirm transfer? (y/n): ").strip().lower()
            
            if confirm != 'y':
                print("❌ Cancelled")
                return False
            
            # Execute transfer
            if is_bnb:
                # Send BNB
                print(f"\n📤 Sending {amount:.6f} BNB...")
                
                nonce = web3.eth.get_transaction_count(main_address)
                
                tx = {
                    'to': recipient_address,
                    'value': web3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': web3.to_wei('3', 'gwei'),
                    'nonce': nonce,
                    'chainId': 56
                }
                
                signed_tx = web3.eth.account.sign_transaction(tx, main_private_key)
                tx_hash = web3.eth. send_raw_transaction(signed_tx.raw_transaction)
                
                print(f"⏳ TX Hash: {web3.to_hex(tx_hash)}")
                print(f"⏳ Waiting for confirmation...")
                
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    print(f"✅ Transfer successful!")
                    print(f"🔗 View on BSCScan: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")
                    
                    message = (
                        f"📤 BNB Transfer Complete!\n\n"
                        f"💰 Amount: {amount:.6f} BNB\n"
                        f"📥 To: {recipient_address[: 10]}... {recipient_address[-6:]}\n"
                        f"🔗 TX:  {web3.to_hex(tx_hash)}\n"
                        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                    )
                    send_telegram_message(message)
                    return True
                else:
                    print(f"❌ Transfer failed!")
                    return False
            
            else:
                # Send USDT
                print(f"\n📤 Sending {amount:.2f} USDT...")
                
                amount_wei = int(amount * 1e18)
                nonce = web3.eth.get_transaction_count(main_address)
                
                transfer_tx = usdt_contract.functions.transfer(
                    recipient_address,
                    amount_wei
                ).build_transaction({
                    'from': main_address,
                    'gas': 100000,
                    'gasPrice': web3.to_wei('3', 'gwei'),
                    'nonce': nonce,
                    'chainId':  56
                })
                
                signed_tx = web3.eth.account. sign_transaction(transfer_tx, main_private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                print(f"⏳ TX Hash: {web3.to_hex(tx_hash)}")
                print(f"⏳ Waiting for confirmation...")
                
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt. status == 1:
                    print(f"✅ Transfer successful!")
                    print(f"🔗 View on BSCScan: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")
                    
                    message = (
                        f"📤 USDT Transfer Complete!\n\n"
                        f"💰 Amount: {amount:.2f} USDT\n"
                        f"📥 To: {recipient_address[:10]}...{recipient_address[-6:]}\n"
                        f"🔗 TX: {web3.to_hex(tx_hash)}\n"
                        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                    )
                    send_telegram_message(message)
                    return True
                else:
                    print(f"❌ Transfer failed!")
                    return False
        
        except Exception as e:
            print(f"❌ Error during transfer: {e}")
            import traceback
            traceback.print_exc()
            return False        

def drain_all_wallets(wallet_manager, main_wallet_address):
    any_drained = False
    for idx, wallet in enumerate(wallet_manager.wallets):
        wallet = wallet_manager.get_wallet_balances(wallet)
        if Web3.to_checksum_address(wallet['address']) == Web3.to_checksum_address(main_wallet_address):
            continue
        balance = wallet['balance_bnb']
        if balance <= 0.00001:
            print(f"🦴 Wallet {wallet['name']} has no dust to drain.")
            continue
        print(f"\n💀 Draining wallet {wallet['name']}... Current BNB: {balance:.8f}")
        try:
            address = Web3.to_checksum_address(wallet['address'])
            private_key = wallet['private_key']
            nonce = web3.eth.get_transaction_count(address)
            total_balance_wei = web3.eth.get_balance(address)
            gas_price = web3.to_wei('0.1', 'gwei')
            gas_limit = 21000
            gas_fee = gas_limit * gas_price
            if total_balance_wei <= gas_fee:
                print(f"❌ Not enough to cover gas in {wallet['name']}")
                continue
            value = total_balance_wei - gas_fee
            tx = {
                'to': Web3.to_checksum_address(main_wallet_address),
                'value': value,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': 56
            }
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"🚀 Draining... TX Hash: {web3.to_hex(tx_hash)}")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                print(f"✅ Drained {wallet['name']}! Sent: {web3.from_wei(value, 'ether'):.8f} BNB")
                any_drained = True
            else:
                print(f"❌ Drain failed for {wallet['name']}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error while draining {wallet['name']}: {e}")
    if any_drained:
        send_telegram_message("💀 All wallets drained! Dust sent to main wallet.")
    else:
        print("🦴 No wallets had dust to drain.")


def distribute_bnb_manual(wallet_manager, main_wallet_address):
    """Manually distribute BNB to selected wallets"""
    try:
        if not wallet_manager.wallets:
            print("❌ No wallets available to distribute to.")
            return False

        # Show main wallet balance
        main_address = Web3.to_checksum_address(main_wallet_address)
        main_balance_bnb = web3.from_wei(web3.eth.get_balance(main_address), 'ether')

        print(f"\n💰 Main wallet balance: {main_balance_bnb:.6f} BNB")

        # Show all wallets
        wallet_manager.list_wallets()

        print("\n📋 DISTRIBUTION OPTIONS:")
        print("1. Send to ONE wallet")
        print("2. Send to MULTIPLE wallets (same amount each)")
        print("3. Send to MULTIPLE wallets (custom amounts)")
        print("4. Cancel")

        option = input("\nSelect option (1-4): ").strip()

        if option == '1':
            # Send to one wallet
            try:
                wallet_idx = int(input("\nSelect wallet number: ")) - 1
                if wallet_idx < 0 or wallet_idx >= len(wallet_manager.wallets):
                    print("❌ Invalid wallet")
                    return False

                amount = float(input("Enter BNB amount to send: "))
                if amount <= 0 or amount > float(main_balance_bnb):
                    print("❌ Invalid amount")
                    return False

                wallet = wallet_manager.wallets[wallet_idx]

                print(f"\n📤 PREVIEW:")
                print(f"💰 Amount: {amount} BNB")
                print(f"📧 To: {wallet['name']}")
                print(f"💵 Remaining: {float(main_balance_bnb) - amount:.6f} BNB")

                confirm = input("\nConfirm?  (y/n): ").strip().lower()
                if confirm != 'y':
                    print("❌ Cancelled")
                    return False

                # Execute transfer
                return execute_bnb_transfer(wallet, amount, main_wallet_address)

            except ValueError:
                print("❌ Invalid input")
                return False

        elif option == '2':
            # Send same amount to multiple wallets
            try:
                print("\nEnter wallet numbers separated by commas (e.g., 1,2,3):")
                wallet_input = input("Wallets: ").strip()
                wallet_indices = [int(x.strip()) - 1 for x in wallet_input.split(',')]

                # Validate
                for idx in wallet_indices:
                    if idx < 0 or idx >= len(wallet_manager.wallets):
                        print(f"❌ Invalid wallet number: {idx + 1}")
                        return False

                amount_each = float(input("Enter BNB amount per wallet: "))
                total_needed = amount_each * len(wallet_indices)

                if amount_each <= 0 or total_needed > float(main_balance_bnb):
                    print(f"❌ Invalid amount.  Need {total_needed:.6f} BNB total")
                    return False

                print(f"\n📤 PREVIEW:")
                print(f"💰 Amount per wallet: {amount_each} BNB")
                print(f"👥 Number of wallets: {len(wallet_indices)}")
                print(f"💵 Total:  {total_needed:.6f} BNB")
                print(f"💵 Remaining: {float(main_balance_bnb) - total_needed:.6f} BNB")

                confirm = input("\nConfirm?  (y/n): ").strip().lower()
                if confirm != 'y':
                    print("❌ Cancelled")
                    return False

                # Execute transfers
                success_count = 0
                for idx in wallet_indices:
                    wallet = wallet_manager.wallets[idx]
                    if execute_bnb_transfer(wallet, amount_each, main_wallet_address):
                        success_count += 1
                    time.sleep(1)

                print(f"\n✅ Sent to {success_count}/{len(wallet_indices)} wallets")

                if success_count > 0:
                    message = (
                        f"💰 BNB Distribution Complete!\n\n"
                        f"✅ Successful:  {success_count}/{len(wallet_indices)}\n"
                        f"💸 Per wallet: {amount_each} BNB\n"
                        f"💎 Total: {success_count * amount_each:.6f} BNB\n"
                        f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    send_telegram_message(message)

                return success_count > 0

            except ValueError:
                print("❌ Invalid input")
                return False

        elif option == '3':
            # Custom amounts for multiple wallets
            try:
                distributions = []

                while True:
                    wallet_idx = input("\nEnter wallet number (or 'done'): ").strip()
                    if wallet_idx.lower() == 'done':
                        break

                    wallet_idx = int(wallet_idx) - 1
                    if wallet_idx < 0 or wallet_idx >= len(wallet_manager.wallets):
                        print("❌ Invalid wallet")
                        continue

                    amount = float(input("Enter BNB amount: "))
                    if amount <= 0:
                        print("❌ Amount must be positive")
                        continue

                    distributions.append({
                        'wallet': wallet_manager.wallets[wallet_idx],
                        'amount': amount
                    })
                    print(f"✅ Added:  {wallet_manager.wallets[wallet_idx]['name']} - {amount} BNB")

                if not distributions:
                    print("❌ No distributions added")
                    return False

                total_needed = sum(d['amount'] for d in distributions)

                if total_needed > float(main_balance_bnb):
                    print(f"❌ Total needed ({total_needed:.6f} BNB) exceeds balance")
                    return False

                print(f"\n📤 PREVIEW:")
                for d in distributions:
                    print(f"  💰 {d['amount']} BNB → {d['wallet']['name']}")
                print(f"\n💵 Total: {total_needed:.6f} BNB")
                print(f"💵 Remaining: {float(main_balance_bnb) - total_needed:.6f} BNB")

                confirm = input("\nConfirm? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("❌ Cancelled")
                    return False

                # Execute transfers
                success_count = 0
                for d in distributions:
                    if execute_bnb_transfer(d['wallet'], d['amount'], main_wallet_address):
                        success_count += 1
                    time.sleep(1)

                print(f"\n✅ Sent to {success_count}/{len(distributions)} wallets")

                if success_count > 0:
                    message = (
                        f"💰 Custom BNB Distribution Complete!\n\n"
                        f"✅ Successful: {success_count}/{len(distributions)}\n"
                        f"💎 Total sent: {sum(d['amount'] for d in distributions[: success_count]):.6f} BNB\n"
                        f"⏰ Time:  {datetime.now().strftime('%H:%M:%S')}"
                    )
                    send_telegram_message(message)

                return success_count > 0

            except ValueError:
                print("❌ Invalid input")
                return False

        else:
            print("❌ Cancelled")
            return False

    except Exception as e:
        print(f"❌ Error during distribution: {e}")
        return False


def execute_bnb_transfer(wallet, amount, main_wallet_address):
    """Execute a single BNB transfer from main wallet to sub-wallet"""
    try:
        main_address = Web3.to_checksum_address(main_wallet_address)
        wallet_address = Web3.to_checksum_address(wallet['address'])

        print(f"\n📤 Sending {amount} BNB to {wallet['name']}...")

        nonce = web3.eth.get_transaction_count(main_address)

        tx = {
            'to': wallet_address,
            'value': web3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': web3.to_wei('0.1', 'gwei'),
            'nonce': nonce,
            'chainId': 56
        }

        signed_tx = web3.eth.account.sign_transaction(tx, MAIN_PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"⏳ TX Hash: {web3.to_hex(tx_hash)}")

        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            print(f"✅ Success!  Sent {amount} BNB to {wallet['name']}")
            return True
        else:
            print(f"❌ Failed!")
            return False

    except Exception as e:
        print(f"❌ Error:  {e}")
        return False


def get_current_bnb_price():
    """Get current BNB price from Chainlink oracle"""
    try:
        print("\n💰 FETCHING CURRENT BNB PRICE...")

        # Get data from Chainlink
        latest_data = chainlink_contract.functions.latestRoundData().call()

        # latest_data returns:  [roundId, answer, startedAt, updatedAt, answeredInRound]
        price = latest_data[1] / 1e8  # Chainlink returns price with 8 decimals
        updated_at = latest_data[3]

        # Calculate how old the price is
        current_time = int(time.time())
        age_seconds = current_time - updated_at
        age_minutes = age_seconds / 60

        print("\n" + "=" * 50)
        print("💎 BNB/USD PRICE (CHAINLINK ORACLE)")
        print("=" * 50)
        print(f"💵 Current Price: ${price:.2f}")
        print(f"🕐 Updated: {age_minutes:.1f} minutes ago")
        print(f"📅 Timestamp: {datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        return price

    except Exception as e:
        print(f"❌ Error fetching BNB price: {e}")
        return None


def calculate_bnb_atr(period=14, interval='1h', limit=100):
    """Calculate ATR (Average True Range) for BNB using Binance data"""
    try:
        print(f"\n📊 CALCULATING ATR (Period: {period}, Interval: {interval})...")

        # Fetch historical data from Binance
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'BNBUSDT',
            'interval': interval,  # 1m, 5m, 15m, 1h, 4h, 1d
            'limit': limit
        }

        response = requests.get(url, params=params)

        if not response.ok:
            print(f"❌ Error fetching data from Binance: {response.status_code}")
            return None

        data = response.json()

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        # Convert to numeric
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])

        # Calculate ATR using TA library
        atr_indicator = AverageTrueRange(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=period
        )

        atr_values = atr_indicator.average_true_range()
        current_atr = atr_values.iloc[-1]
        current_price = df['close'].iloc[-1]

        # Calculate ATR as percentage of price
        atr_percentage = (current_atr / current_price) * 100

        print("\n" + "=" * 50)
        print(f"📊 ATR ANALYSIS (BNB/USDT)")
        print("=" * 50)
        print(f"💰 Current Price: ${current_price:.2f}")
        print(f"📈 ATR ({period}): ${current_atr:.2f}")
        print(f"📊 ATR %: {atr_percentage:.2f}%")
        print(f"⏱️  Interval: {interval}")
        print(f"📅 Last Update: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)

        # Interpretation
        print("\n💡 INTERPRETATION:")
        if atr_percentage < 2:
            print("🟢 LOW volatility - Small price movements")
        elif atr_percentage < 4:
            print("🟡 MEDIUM volatility - Moderate price movements")
        else:
            print("🔴 HIGH volatility - Large price movements")

        print(f"\n📌 Expected price range: ${current_price - current_atr:.2f} - ${current_price + current_atr:.2f}")

        return {
            'atr': current_atr,
            'atr_percentage': atr_percentage,
            'current_price': current_price
        }

    except Exception as e:
        print(f"❌ Error calculating ATR: {e}")
        return None


def calculate_atr_interactive():
    """Interactive ATR calculation with custom parameters"""
    print("\n📊 ATR CALCULATOR")
    print("=" * 50)

    print("\n⏱️  SELECT TIMEFRAME:")
    print("1. 1 minute")
    print("2. 5 minutes")
    print("3. 15 minutes")
    print("4. 1 hour (default)")
    print("5. 4 hours")
    print("6. 1 day")

    interval_map = {
        '1': '1m',
        '2': '5m',
        '3': '15m',
        '4': '1h',
        '5': '4h',
        '6': '1d'
    }

    interval_choice = input("\nSelect (1-6, default=4): ").strip() or '4'
    interval = interval_map.get(interval_choice, '1h')

    try:
        period = input("\n📊 Enter ATR period (default=14): ").strip()
        period = int(period) if period else 14

        if period < 2:
            print("❌ Period must be at least 2")
            return

        calculate_bnb_atr(period=period, interval=interval)

    except ValueError:
        print("❌ Invalid input")


class SwapManager:
    def __init__(self):
        pass

    def get_usdt_to_bnb_rate(self, usdt_amount):
        """
        Get ACCURATE swap rate using V3 0.05% pool
        This matches PancakeSwap UI pricing
        """
        try:
            usdt_amount_wei = int(usdt_amount * 1e18)

            params = {
                'tokenIn': Web3.to_checksum_address(USDT_CONTRACT),
                'tokenOut': Web3.to_checksum_address(WBNB),
                'amountIn': usdt_amount_wei,
                'fee': 500,  # 0.05% fee pool (best rate)
                'sqrtPriceLimitX96': 0
            }

            # Call V3 QuoterV2
            result = quoter_v2_contract.functions.quoteExactInputSingle(params).call()
            bnb_amount = result[0] / 1e18

            return bnb_amount

        except Exception as e:
            print(f"⚠️ V3 Quoter error: {e}")
            print(f"⚠️ Falling back to Chainlink price...")

            # Fallback to Chainlink if V3 fails
            try:
                latest_data = chainlink_contract.functions.latestRoundData().call()
                bnb_price = latest_data[1] / 1e8
                return usdt_amount / bnb_price
            except:
                print(f"❌ Chainlink also failed!")
                return 0

    def get_bnb_to_usdt_rate(self, bnb_amount):
        """
        Get BNB → USDT rate using V3 0.05% pool
        """
        try:
            bnb_amount_wei = int(bnb_amount * 1e18)

            params = {
                'tokenIn': Web3.to_checksum_address(WBNB),
                'tokenOut': Web3.to_checksum_address(USDT_CONTRACT),
                'amountIn': bnb_amount_wei,
                'fee': 500,  # 0.05% fee pool
                'sqrtPriceLimitX96': 0
            }

            result = quoter_v2_contract.functions.quoteExactInputSingle(params).call()
            usdt_amount = result[0] / 1e18

            return usdt_amount

        except Exception as e:
            print(f"⚠️ V3 Quoter error:  {e}")

            # Fallback to Chainlink
            try:
                latest_data = chainlink_contract.functions.latestRoundData().call()
                bnb_price = latest_data[1] / 1e8
                return bnb_amount * bnb_price
            except:
                return 0

    def execute_swap(self, wallet, swap_direction, amount):
        """
        Execute swap using V3 0.05% pool (Smart Router)
        Falls back to V2 if V3 fails
        """
        try:
            wallet_address = Web3.to_checksum_address(wallet['address'])
            private_key = wallet['private_key']

            if swap_direction == 'usdt_to_bnb':
                return self._swap_usdt_to_bnb_v3(wallet_address, private_key, amount)

            elif swap_direction == 'bnb_to_usdt':
                return self._swap_bnb_to_usdt_v3(wallet_address, private_key, amount)

            else:
                print(f"❌ Unknown swap direction: {swap_direction}")
                return False

        except Exception as e:
            print(f"❌ Swap error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _swap_usdt_to_bnb_v3(self, wallet_address, private_key, usdt_amount):
        """
        USDT → BNB using V3 0. 05% pool
        ✅ WITH AUTO-UNWRAP
        """
        try:
            print(f"💱 Swapping {usdt_amount:.2f} USDT → BNB (V3 0.05%)")

            # Check USDT balance
            usdt_balance = usdt_contract.functions.balanceOf(wallet_address).call() / 1e18

            if usdt_balance < usdt_amount:
                print(f"❌ Insufficient USDT.   Have:   {usdt_balance:.2f}, Need: {usdt_amount:.2f}")
                return False

            # Get quote from V3
            usdt_amount_wei = int(usdt_amount * 1e18)

            params_quote = {
                'tokenIn': Web3.to_checksum_address(USDT_CONTRACT),
                'tokenOut': Web3.to_checksum_address(WBNB),
                'amountIn': usdt_amount_wei,
                'fee': 500,  # 0.05%
                'sqrtPriceLimitX96': 0
            }

            result = quoter_v2_contract.functions.quoteExactInputSingle(params_quote).call()
            expected_bnb = result[0] / 1e18

            print(f"📊 Expected BNB: {expected_bnb:.6f}")

            # Check allowance for Smart Router
            allowance = usdt_contract.functions.allowance(
                wallet_address,
                SMART_ROUTER_ADDRESS
            ).call()

            if allowance < usdt_amount_wei:
                print("🔓 Approving USDT for Smart Router...")
                nonce = web3.eth.get_transaction_count(wallet_address)

                approve_tx = usdt_contract.functions.approve(
                    SMART_ROUTER_ADDRESS,
                    usdt_amount_wei * 2  # Approve 2x for future swaps
                ).build_transaction({
                    'from': wallet_address,
                    'gas': 100000,
                    'gasPrice': web3.to_wei('3', 'gwei'),
                    'nonce': nonce,
                    'chainId': 56
                })

                signed_tx = web3.eth.account.sign_transaction(approve_tx, private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

                print(f"⏳ Approval TX:  {web3.to_hex(tx_hash)}")
                web3.eth.wait_for_transaction_receipt(tx_hash)
                print("✅ Approval confirmed!")

            # Execute V3 swap
            print("🔄 Executing V3 swap...")

            min_bnb_out = int(expected_bnb * 0.9995 * 1e18)  # 0.05% slippage
            nonce = web3.eth.get_transaction_count(wallet_address)

            swap_params = {
                'tokenIn': Web3.to_checksum_address(USDT_CONTRACT),
                'tokenOut': Web3.to_checksum_address(WBNB),
                'fee': 500,  # 0.05%
                'recipient': wallet_address,
                'amountIn': usdt_amount_wei,
                'amountOutMinimum': min_bnb_out,
                'sqrtPriceLimitX96': 0
            }

            swap_tx = smart_router_contract.functions.exactInputSingle(swap_params).build_transaction({
                'from': wallet_address,
                'gas': 300000,
                'gasPrice': web3.to_wei('3', 'gwei'),
                'nonce': nonce,
                'chainId': 56,
                'value': 0
            })

            signed_tx = web3.eth.account.sign_transaction(swap_tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"⏳ Swap TX: {web3.to_hex(tx_hash)}")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                print(f"✅ V3 Swap successful!  {usdt_amount:.2f} USDT → {expected_bnb:.6f} BNB")
                print(f"🔗 TX: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")

                # ✅ AUTO-UNWRAP WBNB → BNB
                print("🔄 Checking for WBNB to unwrap...")

                try:
                    # WBNB contract ABIs
                    wbnb_balance_abi = [
                        {
                            "constant": True,
                            "inputs": [{"name": "_owner", "type": "address"}],
                            "name": "balanceOf",
                            "outputs": [{"name": "balance", "type": "uint256"}],
                            "type": "function"
                        }
                    ]

                    wbnb_withdraw_abi = [
                        {
                            "constant": False,
                            "inputs": [{"name": "wad", "type": "uint256"}],
                            "name": "withdraw",
                            "outputs": [],
                            "stateMutability": "nonpayable",
                            "type": "function"
                        }
                    ]

                    # Get WBNB balance
                    wbnb_contract_balance = web3.eth.contract(
                        address=Web3.to_checksum_address(WBNB),
                        abi=wbnb_balance_abi
                    )

                    wbnb_balance = wbnb_contract_balance.functions.balanceOf(wallet_address).call()

                    if wbnb_balance > 0:
                        wbnb_balance_human = wbnb_balance / 1e18
                        print(f"🔄 Unwrapping {wbnb_balance_human:.6f} WBNB → BNB...")

                        # Unwrap WBNB
                        wbnb_contract = web3.eth.contract(
                            address=Web3.to_checksum_address(WBNB),
                            abi=wbnb_withdraw_abi
                        )

                        nonce = web3.eth.get_transaction_count(wallet_address)

                        unwrap_tx = wbnb_contract.functions.withdraw(wbnb_balance).build_transaction({
                            'from': wallet_address,
                            'gas': 50000,
                            'gasPrice': web3.to_wei('3', 'gwei'),
                            'nonce': nonce,
                            'chainId': 56,
                            'value': 0
                        })

                        signed_tx = web3.eth.account.sign_transaction(unwrap_tx, private_key)
                        unwrap_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

                        print(f"⏳ Unwrap TX: {web3.to_hex(unwrap_hash)}")
                        unwrap_receipt = web3.eth.wait_for_transaction_receipt(unwrap_hash)

                        if unwrap_receipt.status == 1:
                            print(f"✅ Unwrapped {wbnb_balance_human:.6f} WBNB → BNB")
                            print(f"🔗 Unwrap TX: https://bscscan.com/tx/{web3.to_hex(unwrap_hash)}")
                        else:
                            print(f"⚠️ Unwrap failed, but WBNB is in wallet")
                            print(f"💡 Use /unwrap command to manually unwrap")
                    else:
                        print("✅ No WBNB to unwrap (swap already gave native BNB)")

                except Exception as unwrap_error:
                    print(f"⚠️ Unwrap error: {unwrap_error}")
                    print(f"💡 You may have WBNB in wallet - use /unwrap command")
                    import traceback
                    traceback.print_exc()

                return True
            else:
                print(f"❌ V3 Swap failed!")
                return False

        except Exception as e:
            print(f"❌ V3 swap error: {e}")
            print("⚠️ Falling back to V2 router...")

            # Fallback to V2
            return self._swap_usdt_to_bnb_v2_fallback(wallet_address, private_key, usdt_amount)

    def _swap_bnb_to_usdt_v3(self, wallet_address, private_key, bnb_amount):
        """
        BNB → USDT using V3 0.05% pool
        """
        try:
            print(f"💱 Swapping {bnb_amount:.6f} BNB → USDT (V3 0.05%)")

            # Check BNB balance
            bnb_balance = web3.eth.get_balance(wallet_address) / 1e18

            if bnb_balance < bnb_amount:
                print(f"❌ Insufficient BNB. Have: {bnb_balance:.6f}, Need: {bnb_amount:.6f}")
                return False

            # Get quote from V3
            bnb_amount_wei = int(bnb_amount * 1e18)

            params_quote = {
                'tokenIn': Web3.to_checksum_address(WBNB),
                'tokenOut': Web3.to_checksum_address(USDT_CONTRACT),
                'amountIn': bnb_amount_wei,
                'fee': 500,  # 0.05%
                'sqrtPriceLimitX96': 0
            }

            result = quoter_v2_contract.functions.quoteExactInputSingle(params_quote).call()
            expected_usdt = result[0] / 1e18

            print(f"📊 Expected USDT: {expected_usdt:.2f}")

            # Execute V3 swap (BNB is sent as value, no approval needed)
            print("🔄 Executing V3 swap...")

            min_usdt_out = int(expected_usdt * 0.9995 * 1e18)  # 0.05% slippage
            nonce = web3.eth.get_transaction_count(wallet_address)

            swap_params = {
                'tokenIn': Web3.to_checksum_address(WBNB),
                'tokenOut': Web3.to_checksum_address(USDT_CONTRACT),
                'fee': 500,  # 0.05%
                'recipient': wallet_address,
                'amountIn': bnb_amount_wei,
                'amountOutMinimum': min_usdt_out,
                'sqrtPriceLimitX96': 0
            }

            swap_tx = smart_router_contract.functions.exactInputSingle(swap_params).build_transaction({
                'from': wallet_address,
                'value': bnb_amount_wei,  # Send BNB as value
                'gas': 300000,
                'gasPrice': web3.to_wei('3', 'gwei'),
                'nonce': nonce,
                'chainId': 56
            })

            signed_tx = web3.eth.account.sign_transaction(swap_tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"⏳ Swap TX:  {web3.to_hex(tx_hash)}")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                print(f"✅ V3 Swap successful! {bnb_amount:.6f} BNB → {expected_usdt:.2f} USDT")
                print(f"🔗 TX: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")
                return True
            else:
                print(f"❌ V3 Swap failed!")
                return False

        except Exception as e:
            print(f"❌ V3 swap error: {e}")
            print("⚠️ Falling back to V2 router...")

            # Fallback to V2
            return self._swap_bnb_to_usdt_v2_fallback(wallet_address, private_key, bnb_amount)

    def _swap_usdt_to_bnb_v2_fallback(self, wallet_address, private_key, usdt_amount):
        """Fallback to V2 if V3 fails"""
        try:
            print("🔄 Using V2 Router fallback...")

            usdt_amount_wei = int(usdt_amount * 1e18)
            path = [USDT_CONTRACT, WBNB]

            # Get V2 quote
            amounts = router_contract.functions.getAmountsOut(usdt_amount_wei, path).call()
            expected_bnb = amounts[1] / 1e18

            print(f"📊 V2 Expected:  {expected_bnb:.6f} BNB")

            # Check allowance
            allowance = usdt_contract.functions.allowance(wallet_address, PANCAKE_ROUTER).call()

            if allowance < usdt_amount_wei:
                print("🔓 Approving for V2...")
                nonce = web3.eth.get_transaction_count(wallet_address)
                approve_tx = usdt_contract.functions.approve(
                    PANCAKE_ROUTER, usdt_amount_wei * 2
                ).build_transaction({
                    'from': wallet_address,
                    'gas': 100000,
                    'gasPrice': web3.to_wei('3', 'gwei'),
                    'nonce': nonce,
                    'chainId': 56
                })
                signed_tx = web3.eth.account.sign_transaction(approve_tx, private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                web3.eth.wait_for_transaction_receipt(tx_hash)

            # Execute V2 swap
            min_bnb = int(expected_bnb * 0.9995 * 1e18)
            deadline = int(time.time()) + 300
            nonce = web3.eth.get_transaction_count(wallet_address)

            swap_tx = router_contract.functions.swapExactTokensForETH(
                usdt_amount_wei,
                min_bnb,
                path,
                wallet_address,
                deadline
            ).build_transaction({
                'from': wallet_address,
                'gas': 300000,
                'gasPrice': web3.to_wei('3', 'gwei'),
                'nonce': nonce,
                'chainId': 56
            })

            signed_tx = web3.eth.account.sign_transaction(swap_tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                print(f"✅ V2 Fallback successful!")
                return True
            else:
                print(f"❌ V2 Fallback also failed!")
                return False

        except Exception as e:
            print(f"❌ V2 fallback error: {e}")
            return False

    def _swap_bnb_to_usdt_v2_fallback(self, wallet_address, private_key, bnb_amount):
        """Fallback to V2 if V3 fails"""
        try:
            print("🔄 Using V2 Router fallback...")

            bnb_amount_wei = int(bnb_amount * 1e18)
            path = [WBNB, USDT_CONTRACT]

            # Get V2 quote
            amounts = router_contract.functions.getAmountsOut(bnb_amount_wei, path).call()
            expected_usdt = amounts[1] / 1e18

            print(f"📊 V2 Expected: {expected_usdt:.2f} USDT")

            # Execute V2 swap
            min_usdt = int(expected_usdt * 0.9995 * 1e18)
            deadline = int(time.time()) + 300
            nonce = web3.eth.get_transaction_count(wallet_address)

            swap_tx = router_contract.functions.swapExactETHForTokens(
                min_usdt,
                path,
                wallet_address,
                deadline
            ).build_transaction({
                'from': wallet_address,
                'value': bnb_amount_wei,
                'gas': 300000,
                'gasPrice': web3.to_wei('3', 'gwei'),
                'nonce': nonce,
                'chainId': 56
            })

            signed_tx = web3.eth.account.sign_transaction(swap_tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                print(f"✅ V2 Fallback successful!")
                return True
            else:
                print(f"❌ V2 Fallback also failed!")
                return False

        except Exception as e:
            print(f"❌ V2 fallback error: {e}")
            return False


def swap_usdt_to_bnb_main_wallet(usdt_amount):
    """
    Swap USDT to BNB from main wallet using V3 0.05% pool
    """
    try:
        main_address = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)

        # Check balance
        usdt_balance = usdt_contract.functions.balanceOf(main_address).call() / 1e18

        if usdt_balance < usdt_amount:
            print(f"❌ Insufficient USDT balance. You have {usdt_balance:.4f} USDT.")
            return

        # Get V3 quote
        usdt_amount_wei = int(usdt_amount * 1e18)

        params = {
            'tokenIn': Web3.to_checksum_address(USDT_CONTRACT),
            'tokenOut': Web3.to_checksum_address(WBNB),
            'amountIn': usdt_amount_wei,
            'fee': 500,  # 0.05%
            'sqrtPriceLimitX96': 0
        }

        result = quoter_v2_contract.functions.quoteExactInputSingle(params).call()
        expected_bnb = result[0] / 1e18

        print(f"\n💱 You will swap {usdt_amount} USDT → {expected_bnb:.6f} BNB (V3 0.05%)")

        # Check allowance
        allowance = usdt_contract.functions.allowance(main_address, SMART_ROUTER_ADDRESS).call()

        if allowance < usdt_amount_wei:
            print("🔓 Approving USDT for Smart Router...")
            nonce = web3.eth.get_transaction_count(main_address)

            approve_tx = usdt_contract.functions.approve(
                SMART_ROUTER_ADDRESS, usdt_amount_wei * 2
            ).build_transaction({
                'from': main_address,
                'gas': 100000,
                'gasPrice': web3.to_wei('3', 'gwei'),
                'nonce': nonce,
                'chainId': 56
            })

            signed_approve = web3.eth.account.sign_transaction(approve_tx, MAIN_PRIVATE_KEY)
            tx_hash = web3.eth.send_raw_transaction(signed_approve.raw_transaction)

            print(f"⏳ Waiting for approval...  TX: {web3.to_hex(tx_hash)}")
            web3.eth.wait_for_transaction_receipt(tx_hash)
            print("✅ Approval confirmed.")

        confirm = input(f"Proceed with V3 swap? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Swap cancelled.")
            return

        # Execute swap
        min_bnb_out = int(expected_bnb * 0.9995 * 1e18)  # 0.05% slippage
        nonce = web3.eth.get_transaction_count(main_address)

        swap_params = {
            'tokenIn': Web3.to_checksum_address(USDT_CONTRACT),
            'tokenOut': Web3.to_checksum_address(WBNB),
            'fee': 500,
            'recipient': main_address,
            'amountIn': usdt_amount_wei,
            'amountOutMinimum': min_bnb_out,
            'sqrtPriceLimitX96': 0
        }

        swap_tx = smart_router_contract.functions.exactInputSingle(swap_params).build_transaction({
            'from': main_address,
            'gas': 300000,
            'gasPrice': web3.to_wei('3', 'gwei'),
            'nonce': nonce,
            'chainId': 56,
            'value': 0
        })

        signed_swap = web3.eth.account.sign_transaction(swap_tx, MAIN_PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_swap.raw_transaction)

        print(f"⏳ Waiting for swap TX confirmation... TX: {web3.to_hex(tx_hash)}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            print(f"✅ V3 Swap completed!  TX: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")
        else:
            print("❌ Swap failed.")

    except Exception as e:
        print(f"❌ Error during swap: {e}")


def swap_bnb_to_usdt_main_wallet(bnb_amount):
    """
    Swap BNB to USDT from main wallet using V3 0.05% pool
    """
    try:
        main_address = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)

        # Check balance
        bnb_balance = web3.eth.get_balance(main_address) / 1e18

        if bnb_balance < bnb_amount:
            print(f"❌ Insufficient BNB balance. You have {bnb_balance:.4f} BNB.")
            return

        # Get V3 quote
        bnb_amount_wei = int(bnb_amount * 1e18)

        params = {
            'tokenIn': Web3.to_checksum_address(WBNB),
            'tokenOut': Web3.to_checksum_address(USDT_CONTRACT),
            'amountIn': bnb_amount_wei,
            'fee': 500,  # 0.05%
            'sqrtPriceLimitX96': 0
        }

        result = quoter_v2_contract.functions.quoteExactInputSingle(params).call()
        expected_usdt = result[0] / 1e18

        print(f"\n💱 You will swap {bnb_amount} BNB → {expected_usdt:.4f} USDT (V3 0.05%)")

        confirm = input(f"Proceed with V3 swap? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Swap cancelled.")
            return

        # Execute swap
        min_usdt_out = int(expected_usdt * 0.9995 * 1e18)  # 0.05% slippage
        nonce = web3.eth.get_transaction_count(main_address)

        swap_params = {
            'tokenIn': Web3.to_checksum_address(WBNB),
            'tokenOut': Web3.to_checksum_address(USDT_CONTRACT),
            'fee': 500,
            'recipient': main_address,
            'amountIn': bnb_amount_wei,
            'amountOutMinimum': min_usdt_out,
            'sqrtPriceLimitX96': 0
        }

        swap_tx = smart_router_contract.functions.exactInputSingle(swap_params).build_transaction({
            'from': main_address,
            'value': bnb_amount_wei,
            'gas': 300000,
            'gasPrice': web3.to_wei('3', 'gwei'),
            'nonce': nonce,
            'chainId': 56
        })

        signed_swap = web3.eth.account.sign_transaction(swap_tx, MAIN_PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_swap.raw_transaction)

        print(f"⏳ Waiting for swap TX confirmation... TX: {web3.to_hex(tx_hash)}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            print(f"✅ V3 Swap completed! TX: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")
        else:
            print("❌ Swap failed.")

    except Exception as e:
        print(f"❌ Error during main wallet BNB→USDT swap: {e}")


class BettingManager:
    def __init__(self):
        pass

    def place_bet(self, wallet_info, direction, bet_amount_bnb):
        """Place a bet using the specified wallet"""
        try:
            current_epoch = prediction_contract.functions.currentEpoch().call()
            round_data = prediction_contract.functions.rounds(current_epoch).call()
            current_time = int(time.time())
            lock_timestamp = round_data[2]
            if current_time >= lock_timestamp:
                print("⚠️ Current round is locked, cannot place bets")
                return False

            print(f"\n🎯 Placing bet...")
            print(f"👤 Wallet: {wallet_info['name']}")
            print(f"📊 Direction: {direction.upper()}")
            print(f"💰 Amount: {bet_amount_bnb} BNB")
            print(f"🔢 Round: {current_epoch}")
            print(f"⏰ Time remaining: {lock_timestamp - current_time} seconds")

            address = Web3.to_checksum_address(wallet_info['address'])
            private_key = wallet_info['private_key']
            balance = web3.eth.get_balance(address)
            balance_bnb = web3.from_wei(balance, 'ether')
            bet_amount_wei = web3.to_wei(bet_amount_bnb, 'ether')

            if balance < bet_amount_wei + web3.to_wei('0.00003', 'ether'):
                print(f"❌ Insufficient balance. Have: {balance_bnb:.6f} BNB")
                return False

            if direction.lower() == 'up':
                function = prediction_contract.functions.betBull(current_epoch)
            else:
                function = prediction_contract.functions.betBear(current_epoch)

            nonce = web3.eth.get_transaction_count(address)

            tx = function.build_transaction({
                'from': address,
                'value': bet_amount_wei,
                'gas': 200000,
                'gasPrice': web3.to_wei('0.1', 'gwei'),
                'nonce': nonce
            })

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"🚀 Bet placed! TX Hash: {web3.to_hex(tx_hash)}")
            print(f"🔗 View on BSCScan: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")
            return True

        except Exception as e:
            print(f"❌ Error placing bet: {e}")
            return False


class RewardManager:
    def __init__(self):
        pass

    def get_claimable_epochs(self, wallet_address):
        """Get all epochs where wallet has claimable rewards"""
        try:
            claimable_epochs = []
            wallet_address = Web3.to_checksum_address(wallet_address)

            # Get current epoch to know the range to check
            current_epoch = prediction_contract.functions.currentEpoch().call()

            # Check last 100 rounds (you can adjust this range)
            start_epoch = max(1, current_epoch - 5)

            print(f"🔍 Checking epochs {start_epoch} to {current_epoch - 1} for claimable rewards...")

            for epoch in range(start_epoch, current_epoch):
                try:
                    # Check if user has bet in this round
                    user_round = prediction_contract.functions.ledger(epoch, wallet_address).call()

                    # user_round structure: [position, amount, claimed]
                    # position: 0 = Bull, 1 = Bear
                    # amount: bet amount
                    # claimed: True if already claimed

                    if user_round[1] > 0 and not user_round[2]:  # Has bet and not claimed
                        # Check if round is claimable (finished and user won)
                        if prediction_contract.functions.claimable(epoch, wallet_address).call():
                            round_data = prediction_contract.functions.rounds(epoch).call()
                            claimable_epochs.append({
                                'epoch': epoch,
                                'bet_amount': web3.from_wei(user_round[1], 'ether'),
                                'position': 'BULL' if user_round[0] == 0 else 'BEAR',
                                'claimed': user_round[2]
                            })

                except Exception as e:
                    # Skip epochs that cause errors (might not exist yet)
                    continue

            return claimable_epochs

        except Exception as e:
            print(f"❌ Error getting claimable epochs: {e}")
            return []

    def get_claimable_amount(self, wallet_address, epoch):
        """Get the claimable amount for a specific epoch"""
        try:
            wallet_address = Web3.to_checksum_address(wallet_address)

            # This calls the contract's view function to calculate rewards
            # Note: This might not exist in all prediction contracts
            # Alternative: calculate based on round data

            user_round = prediction_contract.functions.ledger(epoch, wallet_address).call()
            round_data = prediction_contract.functions.rounds(epoch).call()

            if user_round[1] > 0 and not user_round[2]:  # Has bet and not claimed
                bet_amount = user_round[1]

                # Get total amounts for calculation
                # round_data structure varies, but typically includes:
                # [startTimestamp, lockTimestamp, closeTimestamp, lockPrice, closePrice, lockOracleId, closeOracleId, totalAmount, bullAmount, bearAmount, rewardBaseCalAmount, rewardAmount, oraclesCalled]

                total_amount = round_data[7]  # totalAmount
                bull_amount = round_data[8]  # bullAmount
                bear_amount = round_data[9]  # bearAmount
                reward_amount = round_data[11]  # rewardAmount

                # Calculate user's share of the rewards
                if user_round[0] == 0:  # Bull position
                    if bull_amount > 0:
                        user_reward = (bet_amount * reward_amount) // bull_amount
                    else:
                        user_reward = 0
                else:  # Bear position
                    if bear_amount > 0:
                        user_reward = (bet_amount * reward_amount) // bear_amount
                    else:
                        user_reward = 0

                return web3.from_wei(user_reward, 'ether')

            return 0

        except Exception as e:
            print(f"⚠️ Error calculating claimable amount: {e}")
            return 0

    def claim_rewards(self, wallet_info, epochs_to_claim=None):
        """Claim rewards for specified epochs or all claimable epochs"""
        try:
            wallet_address = Web3.to_checksum_address(wallet_info['address'])
            private_key = wallet_info['private_key']

            # Get all claimable epochs if none specified
            if epochs_to_claim is None:
                claimable_epochs = self.get_claimable_epochs(wallet_address)
                epochs_to_claim = [epoch['epoch'] for epoch in claimable_epochs]

            if not epochs_to_claim:
                print("🎉 No rewards to claim!")
                return True

            print(f"\n🎁 Claiming rewards for {len(epochs_to_claim)} epochs...")

            successful_claims = 0
            total_claimed = 0

            for epoch in epochs_to_claim:
                try:
                    print(f"🎯 Claiming epoch {epoch}...")

                    # Check if still claimable
                    if not prediction_contract.functions.claimable(epoch, wallet_address).call():
                        print(f"⚠️ Epoch {epoch} is not claimable, skipping...")
                        continue

                    # Get estimated reward amount
                    estimated_reward = self.get_claimable_amount(wallet_address, epoch)

                    # Build claim transaction
                    nonce = web3.eth.get_transaction_count(wallet_address)

                    claim_tx = prediction_contract.functions.claim([epoch]).build_transaction({
                        'from': wallet_address,
                        'gas': 200000,
                        'gasPrice': web3.to_wei('0.1', 'gwei'),
                        'nonce': nonce,
                        'chainId': 56
                    })

                    # Sign and send transaction
                    signed_tx = web3.eth.account.sign_transaction(claim_tx, private_key)
                    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

                    print(f"⏳ Waiting for claim confirmation... TX: {web3.to_hex(tx_hash)}")
                    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

                    if receipt.status == 1:
                        print(f"✅ Claimed epoch {epoch}! Estimated reward: {estimated_reward:.6f} BNB")
                        print(f"🔗 TX: https://bscscan.com/tx/{web3.to_hex(tx_hash)}")
                        successful_claims += 1
                        total_claimed += estimated_reward
                    else:
                        print(f"❌ Failed to claim epoch {epoch}")

                    # Small delay between claims
                    time.sleep(2)

                except Exception as e:
                    print(f"❌ Error claiming epoch {epoch}: {e}")
                    continue

            print(f"\n🎉 CLAIM SUMMARY:")
            print(f"✅ Successfully claimed: {successful_claims}/{len(epochs_to_claim)} epochs")
            print(f"💰 Total estimated rewards: {total_claimed:.6f} BNB")

            if successful_claims > 0:
                # Send Telegram notification
                message = (
                    f"🎁 Rewards Claimed!\n\n"
                    f"👤 Wallet: {wallet_info['name']}\n"
                    f"✅ Epochs claimed: {successful_claims}\n"
                    f"💰 Total rewards: {total_claimed:.6f} BNB\n"
                    f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
                )
                send_telegram_message(message)

            return successful_claims > 0

        except Exception as e:
            print(f"❌ Error during reward claiming: {e}")
            return False

    def show_claimable_rewards(self, wallet_info):
        """Show all claimable rewards for a wallet"""
        try:
            print(f"\n🔍 Checking claimable rewards for: {wallet_info['name']}")
            print(f"📧 Address: {wallet_info['address']}")

            claimable_epochs = self.get_claimable_epochs(wallet_info['address'])

            if not claimable_epochs:
                print("🎉 No claimable rewards found!")
                return

            print(f"\n💎 CLAIMABLE REWARDS ({len(claimable_epochs)} epochs):")
            print("=" * 80)

            total_claimable = 0
            for epoch_data in claimable_epochs:
                estimated_reward = self.get_claimable_amount(wallet_info['address'], epoch_data['epoch'])
                total_claimable += estimated_reward

                print(f"🎯 Epoch {epoch_data['epoch']}")
                print(f"   Position: {epoch_data['position']}")
                print(f"   Bet Amount: {epoch_data['bet_amount']:.6f} BNB")
                print(f"   Estimated Reward: {estimated_reward:.6f} BNB")
                print("-" * 80)

            print(f"💰 TOTAL ESTIMATED REWARDS: {total_claimable:.6f} BNB")

            return claimable_epochs

        except Exception as e:
            print(f"❌ Error showing claimable rewards: {e}")
            return []


def get_current_bnb_price_v3():
    """Get current BNB price using V3 0.05% pool (most accurate)"""
    try:
        print("\n💰 FETCHING CURRENT BNB PRICE (V3 0.05% Pool)...")

        one_bnb_wei = int(1 * 1e18)

        params = {
            'tokenIn': Web3.to_checksum_address(WBNB),
            'tokenOut': Web3.to_checksum_address(USDT_CONTRACT),
            'amountIn': one_bnb_wei,
            'fee': 500,  # 0.05% fee pool
            'sqrtPriceLimitX96': 0
        }

        result = quoter_v2_contract.functions.quoteExactInputSingle(params).call()
        usdt_out = result[0] / 1e18

        # Also get Chainlink for comparison
        try:
            chainlink_data = chainlink_contract.functions.latestRoundData().call()
            chainlink_price = chainlink_data[1] / 1e8
            diff = usdt_out - chainlink_price
            diff_pct = (diff / chainlink_price) * 100
        except:
            chainlink_price = None
            diff = 0
            diff_pct = 0

        print("\n" + "=" * 60)
        print("💎 BNB/USD PRICE")
        print("=" * 60)
        print(f"🥞 V3 0.05% Pool:   ${usdt_out:.2f}")

        if chainlink_price:
            print(f"📊 Chainlink:        ${chainlink_price:.2f}")
            print(f"📈 Difference:     ${diff:+.2f} ({diff_pct:+.3f}%)")

        print("=" * 60)
        print(f"✅ Using V3 price: ${usdt_out:.2f}")
        print("=" * 60)

        return usdt_out

    except Exception as e:
        print(f"❌ Error fetching V3 price: {e}")

        # Fallback to Chainlink
        try:
            chainlink_data = chainlink_contract.functions.latestRoundData().call()
            price = chainlink_data[1] / 1e8
            print(f"⚠️ Falling back to Chainlink: ${price:.2f}")
            return price
        except:
            print("❌ All price sources failed!")
            return None


def send_telegram_message(message):
    try:
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=payload)
        if not response.ok:
            print(f"⚠️ Telegram error: {response.text}")
    except Exception as e:
        print(f"⚠️ Telegram exception: {e}")


def main():
    wallet_manager = WalletManager()
    swap_manager = SwapManager()
    betting_manager = BettingManager()
    reward_manager = RewardManager()

    # 🎯 Initialize Limit Order Manager with correct parameters
    limit_order_manager = LimitOrderManager(
        swap_manager,
        betting_manager,
        wallet_manager,
        web3,  # Your global web3 instance
        chainlink_contract,  # Your global chainlink_contract
        USDT_CONTRACT,  # Pass USDT address string (not contract object)
        WBNB  # Pass WBNB address string
    )
    # Link limit_order_manager to wallet_manager for locked balance checks
    wallet_manager.limit_order_manager = limit_order_manager

    print("🤖 Multi-Wallet Prediction Bot")
    print("⚡ INSTANT TELEGRAM BETTING ACTIVE!")
    print("📱 Send:  /bet 1/50/up")
    print("=" * 50)

    telegram_handler = TelegramHandler(
        wallet_manager,
        swap_manager,
        betting_manager,
        reward_manager,
        limit_order_manager
    )
    telegram_handler.set_bot_commands()

    def telegram_monitor():
        """INSTANT Telegram monitoring - NO DELAYS ⚡"""
        while True:
            try:
                telegram_handler.process_commands()
                limit_order_manager.check_and_execute_orders()
            except Exception as e:
                print(f"⚠️ Telegram monitor error: {e}")
                time.sleep(1)

    # ✅ START THE TELEGRAM THREAD!
    telegram_thread = threading.Thread(target=telegram_monitor, daemon=True)
    telegram_thread.start()
    print("⚡ INSTANT Telegram monitor started!")
    print("⚡ Limit order monitor started!")

    while True:
        print("\n📋 MAIN MENU:")
        print("1. Check main wallet balance")
        print("2. Swap BNB to USDT (Main Wallet, 0.1% slippage)")
        print("3. Swap USDT to BNB (Main Wallet, 0.1% slippage)")
        print("4. List all wallets")
        print("5. Create new wallet")
        print("6. Start betting process")
        print("7. Claim rewards")
        print("8. Empty wallet (send all BNB to main wallet)")
        print("9. Drain all wallets (send ALL BNB to main wallet)")
        print("10. Distribute BNB (manual)")
        print("11. Delete wallet")
        print("12. Show total BNB + USDT balance of all sub-wallets")
        print("13. Create limit order")
        print("14. View pending limit orders")
        print("15. Create take-profit order")
        print("16. Cancel any order")
        print("17. Calculate ATR")
        print("18. Show current BNB price")
        print("19. View PnL (Profit & Loss)")
        print("20. Send BNB/USDT to external address")
        print("21. Exit")
        print("\n⚡ INSTANT TELEGRAM:  /bet [wallet]/[usdt]/[up|down]")

        choice = input("\nSelect option (1-20): ").strip()

        if choice == '1':
            try:
                main_address = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)
                bnb_balance = web3.eth.get_balance(main_address)
                bnb_balance = web3.from_wei(bnb_balance, 'ether')
                usdt_balance = usdt_contract.functions.balanceOf(main_address).call()
                usdt_balance = usdt_balance / 1e18
                print(f"\n💰 MAIN WALLET BALANCE:")
                print(f"📧 Address: {MAIN_WALLET_ADDRESS}")
                print(f"💎 BNB:   {bnb_balance:.6f}")
                print(f"💵 USDT: {usdt_balance:.2f}")
            except Exception as e:
                print(f"❌ Error checking balance: {e}")

        elif choice == '2':
            try:
                bnb_balance = web3.eth.get_balance(Web3.to_checksum_address(MAIN_WALLET_ADDRESS)) / 1e18
                print(f"\n💎 Main Wallet BNB Balance: {bnb_balance:.4f} BNB")
                amount = float(input("Enter BNB amount to swap: "))
                if amount <= 0 or amount > bnb_balance:
                    print("❌ Invalid amount.")
                else:
                    swap_bnb_to_usdt_main_wallet(amount)
            except Exception as e:
                print(f"❌ Error:  {e}")

        elif choice == '3':
            try:
                usdt_balance = usdt_contract.functions.balanceOf(
                    Web3.to_checksum_address(MAIN_WALLET_ADDRESS)).call() / 1e18
                print(f"\n💵 Main Wallet USDT Balance: {usdt_balance:.4f} USDT")
                amount = float(input("Enter USDT amount to swap: "))
                if amount <= 0 or amount > usdt_balance:
                    print("❌ Invalid amount.")
                else:
                    swap_usdt_to_bnb_main_wallet(amount)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif choice == '4':
            wallet_manager.list_wallets()

        elif choice == '5':
            name = input("Enter wallet name (or press Enter for auto-name): ").strip()
            if not name:
                name = None
            wallet_manager.create_new_wallet(name)

        elif choice == '6':
            wallet_manager.list_wallets()
            if not wallet_manager.wallets:
                print("❌ No wallets available.  Create a wallet first.")
                continue
            try:
                wallet_idx = int(input("\nSelect wallet number: ")) - 1
                if wallet_idx < 0 or wallet_idx >= len(wallet_manager.wallets):
                    print("❌ Invalid wallet selection")
                    continue
                selected_wallet = wallet_manager.wallets[wallet_idx]
            except ValueError:
                print("❌ Invalid input")
                continue
            try:
                usdt_amount = float(input("Enter USDT amount to convert and send: "))
                if usdt_amount <= 0:
                    print("❌ Amount must be positive")
                    continue
            except ValueError:
                print("❌ Invalid amount")
                continue
            direction = input("Enter bet direction (up/down): ").strip().lower()
            if direction not in ['up', 'down']:
                print("❌ Direction must be 'up' or 'down'")
                continue
            expected_bnb = swap_manager.get_usdt_to_bnb_rate(usdt_amount)
            print(f"\n📊 TRANSACTION PREVIEW:")
            print(f"💱 {usdt_amount} USDT → ~{expected_bnb:.6f} BNB")
            print(f"📧 Recipient: {selected_wallet['name']}")
            print(f"🎯 Bet Direction: {direction.upper()}")
            confirm = input("\nConfirm transaction? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Transaction cancelled")
                continue
            success = swap_manager.swap_usdt_to_bnb(
                usdt_amount,
                selected_wallet['address']
            )
            if success:
                print("✅ Swap completed!  Waiting 0.5 seconds before placing bet...")
                time.sleep(0.5)
                selected_wallet = wallet_manager.get_wallet_balances(selected_wallet)
                bet_amount = selected_wallet['balance_bnb'] * 0.95
                betting_success = betting_manager.place_bet(
                    selected_wallet,
                    direction,
                    bet_amount
                )
                if betting_success:
                    message = (
                        f"🤖 Multi-Wallet Bot Activity\n\n"
                        f"💱 Swapped: {usdt_amount} USDT → {expected_bnb:.6f} BNB\n"
                        f"🎯 Bet: {direction.upper()} with {bet_amount:.6f} BNB\n"
                        f"👤 Wallet: {selected_wallet['name']}\n"
                        f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    send_telegram_message(message)
                    print("🎉 Complete process finished successfully!")
                else:
                    print("❌ Bet placement failed")
            else:
                print("❌ Swap failed")

        elif choice == '7':
            wallet_manager.list_wallets()
            if not wallet_manager.wallets:
                print("❌ No wallets available.")
                continue
            try:
                wallet_idx = int(input("\nSelect wallet number: ")) - 1
                if wallet_idx < 0 or wallet_idx >= len(wallet_manager.wallets):
                    print("❌ Invalid wallet selection")
                    continue
                selected_wallet = wallet_manager.wallets[wallet_idx]
            except ValueError:
                print("❌ Invalid input")
                continue
            claimable_epochs = []
            if hasattr(reward_manager, "show_claimable_rewards"):
                claimable_epochs = reward_manager.show_claimable_rewards(selected_wallet)
            if claimable_epochs:
                print("\n🎯 CLAIM OPTIONS:")
                print("1. Claim all rewards")
                print("2. Show details only")
                print("3. Cancel")
                claim_choice = input("\nSelect option (1-3): ").strip()
                if claim_choice == '1':
                    confirm = input("\n🎁 Confirm claiming all rewards? (y/n): ").strip().lower()
                    if confirm == 'y' and hasattr(reward_manager, "claim_rewards"):
                        success = reward_manager.claim_rewards(selected_wallet)
                        if success:
                            print("🎉 Rewards claimed successfully!")
                        else:
                            print("❌ Failed to claim rewards")
                    else:
                        print("❌ Claim cancelled")
                elif claim_choice == '2':
                    print("✅ Details shown above")
                else:
                    print("❌ Cancelled")

        elif choice == '8':
            # Empty/Send from wallet
            wallet_manager.list_wallets()
            if not wallet_manager.wallets:
                print("❌ No wallets available.")
                continue

            try:
                wallet_idx = int(input("\nSelect wallet number: ")) - 1
                if wallet_idx < 0 or wallet_idx >= len(wallet_manager.wallets):
                    print("❌ Invalid wallet selection")
                    continue

                selected_wallet = wallet_manager.wallets[wallet_idx]
                selected_wallet = wallet_manager.get_wallet_balances(selected_wallet)

                print(f"\n💸 SEND/DRAIN OPTIONS:")
                print(f"👤 Wallet: {selected_wallet['name']}")
                print(f"💰 Current BNB: {selected_wallet['balance_bnb']:.6f}")
                print(f"📧 Will send to: {MAIN_WALLET_ADDRESS}")
                print()
                print("1. 💀 Drain ALL BNB (send everything)")
                print("2. 💵 Send SPECIFIC amount")
                print("3. ❌ Cancel")

                send_choice = input("\nSelect option (1-3): ").strip()

                if send_choice == '1':
                    # Drain all
                    print(f"\n⚠️ WARNING: This will send ALL BNB from '{selected_wallet['name']}' to main wallet")
                    confirm = input("Confirm draining?  (y/n): ").strip().lower()
                    if confirm == 'y':
                        wallet_manager.empty_wallet(wallet_idx, MAIN_WALLET_ADDRESS, amount=None)
                    else:
                        print("❌ Cancelled")

                elif send_choice == '2':
                    # Send specific amount
                    try:
                        amount = float(
                            input(f"\n💰 Enter BNB amount to send (max:  {selected_wallet['balance_bnb']:.6f}): "))

                        if amount <= 0:
                            print("❌ Amount must be positive")
                            continue

                        if amount > selected_wallet['balance_bnb']:
                            print(f"❌ Amount exceeds balance ({selected_wallet['balance_bnb']:.6f} BNB)")
                            continue

                        print(f"\n📋 TRANSFER PREVIEW:")
                        print(f"👤 From: {selected_wallet['name']}")
                        print(f"💰 Amount: {amount:.6f} BNB")
                        print(f"📧 To: Main Wallet")
                        print(f"💵 Remaining in wallet: {selected_wallet['balance_bnb'] - amount:.6f} BNB (approx)")

                        confirm = input("\nConfirm transfer? (y/n): ").strip().lower()
                        if confirm == 'y':
                            wallet_manager.empty_wallet(wallet_idx, MAIN_WALLET_ADDRESS, amount=amount)
                        else:
                            print("❌ Cancelled")

                    except ValueError:
                        print("❌ Invalid amount")

                else:
                    print("❌ Cancelled")

            except ValueError:
                print("❌ Invalid input")

        elif choice == '9':
            confirm = input(
                "⚠️ This will send ALL BNB from ALL wallets to your main wallet.\nProceed? (y/n): ").strip().lower()
            if confirm == 'y':
                drain_all_wallets(wallet_manager, MAIN_WALLET_ADDRESS)
            else:
                print("❌ Operation cancelled")

        elif choice == '10':
            wallet_manager.list_wallets()
            if not wallet_manager.wallets:
                print("❌ No wallets available to distribute to.")
                continue
            distribute_bnb_manual(wallet_manager, MAIN_WALLET_ADDRESS)

        elif choice == '11':
            wallet_manager.list_wallets()
            if not wallet_manager.wallets:
                print("❌ No wallets available to delete.")
                continue
            try:
                wallet_idx = int(input("\nSelect wallet number to delete: ")) - 1
                if wallet_idx < 0 or wallet_idx >= len(wallet_manager.wallets):
                    print("❌ Invalid wallet selection")
                    continue
                selected_wallet = wallet_manager.wallets[wallet_idx]
                print(f"\n⚠️ WARNING: You are about to delete wallet '{selected_wallet['name']}'")
                print(f"📧 Address: {selected_wallet['address']}")
                print("🔥 This action cannot be undone!")
                confirm = input("\nType 'DELETE' to confirm: ").strip()
                if confirm == 'DELETE':
                    wallet_manager.delete_wallet(wallet_idx)
                else:
                    print("❌ Deletion cancelled")
            except ValueError:
                print("❌ Invalid input")

        elif choice == '12':
            # Show total BNB + USDT balance of all sub-wallets
            total_bnb = 0
            total_usdt = 0
            print("\n" + "=" * 80)
            print("💰 SUB-WALLETS BALANCE SUMMARY")
            print("=" * 80)
            for wallet in wallet_manager.wallets:
                # Skip main wallet
                if Web3.to_checksum_address(wallet['address']) == Web3.to_checksum_address(MAIN_WALLET_ADDRESS):
                    continue
                # Get balances
                wallet = wallet_manager.get_wallet_balances(wallet)
                total_bnb += wallet['balance_bnb']
                total_usdt += wallet['balance_usdt']
                # Show individual wallet
                print(f"\n📌 {wallet['name']}")
                print(f"   💎 BNB: {wallet['balance_bnb']:.6f}")
                print(f"   💵 USDT: {wallet['balance_usdt']:.2f}")
            print("\n" + "=" * 80)
            print(f"💼 TOTAL BNB: {total_bnb:.6f}")
            print(f"💼 TOTAL USDT: ${total_usdt:.2f}")
            # Calculate total value in USDT
            try:
                current_bnb_price = limit_order_manager.get_bnb_price()
                if current_bnb_price:
                    bnb_value_usdt = total_bnb * current_bnb_price
                    total_value = bnb_value_usdt + total_usdt
                    print(f"\n💰 TOTAL VALUE:  ${total_value:.2f} USDT")
                    print(f"   └─ BNB:  ${bnb_value_usdt:.2f} (@ ${current_bnb_price:.2f}/BNB)")
                    print(f"   └─ USDT: ${total_usdt:.2f}")
            except:
                pass
            print("=" * 80)

        elif choice == '13':
            # Create limit order with interactive wizard
            limit_order_manager.create_order_interactive()



        elif choice == '14':

            # View pending limit orders (simple view)

            limit_order_manager.view_orders()

            # Also show waiting take-profit orders

            waiting_orders = [o for o in limit_order_manager.orders if o['status'] == 'waiting_for_execution']

            if waiting_orders:

                print("\n" + "=" * 80)

                print("⏳ WAITING TAKE-PROFIT ORDERS")

                print("=" * 80)

                for order in waiting_orders:
                    linked_id = order.get('linked_order_id', 'N/A')

                    profit = order.get('profit_target_usdt', 0)

                    swap_emoji = "💵→💎" if order['swap_direction'] == 'usdt_to_bnb' else "💎→💵"

                    print(f"\n⏳ Order #{order['id']} {swap_emoji} (Take-Profit)")

                    print(f"   🔗 Linked to Order #{linked_id}")

                    print(f"   👤 Wallet: {order['wallet_name']}")

                    print(f"   🔄 Swap: {order['amount_label']} -> {order.get('receive_label', 'N/A')}")

                    print(f"   🎯 Trigger: ${order['trigger_price']:.2f}")

                    print(f"   💰 Expected Profit: ${profit:.2f} USDT")

                    print(f"   📊 Status:  Waiting for Order #{linked_id} to execute")

                    print(f"   ⏰ Created: {order['created_at'][:19]}")

                print("\n" + "=" * 80)

                print(f"💼 Total Waiting: {len(waiting_orders)}")

                print("=" * 80)

        elif choice == '15':
            # Keep all the existing code from your choice '16'
            limit_order_manager.view_orders()

            if not limit_order_manager.orders:
                print("❌ No orders available")
                continue

            try:
                order_id = int(input("\nEnter order ID for take-profit:  "))
                profit_usdt = float(input("Enter profit target in USDT: "))

                if profit_usdt <= 0:
                    print("❌ Profit must be positive")
                    continue

                # Find order
                original_order = None
                for order in limit_order_manager.orders:
                    if order['id'] == order_id:
                        original_order = order
                        break

                if not original_order:
                    print(f"❌ Order #{order_id} not found!")
                    continue

                if original_order['status'] != 'pending':
                    print(f"❌ Order #{order_id} is not pending!")
                    continue

                trigger_price = original_order['trigger_price']

                # Calculate take-profit based on direction
                if original_order['swap_direction'] == 'bnb_to_usdt':
                    bnb_amount = original_order['amount']
                    expected_usdt = bnb_amount * trigger_price * 0.9995
                    usdt_to_swap_back = expected_usdt - profit_usdt

                    if usdt_to_swap_back <= 0:
                        print(f"❌ Profit target too high! Max profit: ${expected_usdt:.2f}")
                        continue

                    tp_target_price = (usdt_to_swap_back / bnb_amount) * 0.9995
                    tp_direction = 'usdt_to_bnb'
                    tp_amount = usdt_to_swap_back
                    tp_amount_label = f"{usdt_to_swap_back:.2f} USDT"
                    tp_receive = bnb_amount
                    tp_receive_label = f"~{bnb_amount:.6f} BNB"

                elif original_order['swap_direction'] == 'usdt_to_bnb':
                    usdt_spent = original_order['amount']
                    bnb_received = original_order['expected_receive']
                    target_usdt = usdt_spent + profit_usdt
                    tp_target_price = (target_usdt / bnb_received) * 1.0005
                    tp_direction = 'bnb_to_usdt'
                    tp_amount = bnb_received
                    tp_amount_label = f"{bnb_received:.6f} BNB"
                    tp_receive = target_usdt
                    tp_receive_label = f"~{target_usdt:.2f} USDT"

                else:
                    print(f"❌ Unknown swap direction: {original_order['swap_direction']}")
                    continue

                # Show preview
                print(f"\n🎯 TAKE-PROFIT ORDER PREVIEW:")
                print("=" * 70)
                print(f"📋 Original Order #{order_id}:")
                print(f"   🔄 {original_order['amount_label']} → {original_order.get('receive_label', 'N/A')}")
                print(f"   🎯 Triggers at:  ${trigger_price:.2f}")
                print(f"\n💰 Take-Profit Order:")
                print(f"   🔄 {tp_amount_label} → {tp_receive_label}")
                print(f"   🎯 Will trigger at: ${tp_target_price:.2f}")
                print(f"   💵 Expected Profit: ${profit_usdt:.2f} USDT")
                print(f"\n⚡ Auto-creates when Order #{order_id} executes!")
                print("=" * 70)

                confirm = input("\n✅ Create take-profit order? (y/n): ").strip().lower()

                if confirm != 'y':
                    print("❌ Cancelled")
                    continue

                # Create placeholder order
                current_price = limit_order_manager.get_bnb_price()
                tp_order_id = len(limit_order_manager.orders) + 1

                tp_order = {
                    'id': tp_order_id,
                    'wallet_idx': original_order['wallet_idx'],
                    'wallet_name': original_order['wallet_name'],
                    'wallet_address': original_order['wallet_address'],
                    'swap_direction': tp_direction,
                    'amount': tp_amount,
                    'amount_label': tp_amount_label,
                    'trigger_price': tp_target_price,
                    'current_price_at_creation': current_price,
                    'expected_receive': tp_receive,
                    'receive_label': tp_receive_label,
                    'created_at': datetime.now().isoformat(),
                    'status': 'waiting_for_execution',
                    'linked_order_id': order_id,
                    'profit_target_usdt': profit_usdt
                }

                limit_order_manager.orders.append(tp_order)
                limit_order_manager.save_orders()

                print(f"\n✅ TAKE-PROFIT ORDER #{tp_order_id} CREATED!")
                print(f"⏳ Waiting for Order #{order_id} to execute...")
                print(f"💰 Target profit: ${profit_usdt:.2f} USDT")

                # Send Telegram notification
                message = (
                    f"🎯 TAKE-PROFIT ORDER CREATED (Terminal)\n\n"
                    f"🆔 Order #{tp_order_id}\n"
                    f"🔗 Linked to Order #{order_id}\n"
                    f"💰 Target:  ${profit_usdt:.2f} profit\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
                send_telegram_message(message)

            except ValueError:
                print("❌ Invalid input")
            except Exception as e:
                print(f"❌ Error:  {e}")
                import traceback
                traceback.print_exc()


        elif choice == '17':

            calculate_atr_interactive()

        elif choice == '16':

            # Cancel order (including take-profit)

            try:

                # Show all cancellable orders

                cancellable = [o for o in limit_order_manager.orders

                               if o['status'] in ['pending', 'waiting_for_execution']]

                if not cancellable:
                    print("\n📝 No orders available to cancel")

                    continue

                print("\n📋 CANCELLABLE ORDERS:")

                print("=" * 80)

                for order in cancellable:
                    status_emoji = "⏳" if order['status'] == 'waiting_for_execution' else "🎯"

                    tp_label = " (Take-Profit)" if order['status'] == 'waiting_for_execution' else ""

                    linked = f" → Linked to #{order.get('linked_order_id')}" if order.get('linked_order_id') else ""

                    print(f"{status_emoji} Order #{order['id']}{tp_label}{linked}")

                    print(f"   {order['amount_label']} → {order.get('receive_label', 'N/A')}")

                    print(f"   Target: ${order['trigger_price']:.2f}")

                    print()

                order_id = int(input("Enter order ID to cancel (0 to go back): "))

                if order_id == 0:
                    print("❌ Cancelled")

                    continue

                # Find order

                target_order = None

                for order in limit_order_manager.orders:

                    if order['id'] == order_id:
                        target_order = order

                        break

                if not target_order:
                    print(f"❌ Order #{order_id} not found!")

                    continue

                if target_order['status'] not in ['pending', 'waiting_for_execution']:
                    print(f"❌ Order #{order_id} cannot be cancelled (Status: {target_order['status']})")

                    continue

                # Show confirmation

                print(f"\n⚠️  CANCEL ORDER #{order_id}?")

                print(f"   {target_order['amount_label']} → {target_order.get('receive_label', 'N/A')}")

                if target_order['status'] == 'waiting_for_execution':
                    print(f"   ⚠️  This is a take-profit order!")

                confirm = input("\nConfirm cancellation?  (y/n): ").strip().lower()

                if confirm == 'y':

                    success = limit_order_manager.cancel_order(order_id)

                    if success:

                        print(f"✅ Order #{order_id} cancelled!")

                    else:

                        print(f"❌ Failed to cancel order #{order_id}")

                else:

                    print("❌ Cancelled")


            except ValueError:

                print("❌ Invalid input")

            except Exception as e:

                print(f"❌ Error: {e}")


        elif choice == '16':

            # Create take-profit order

            limit_order_manager.view_orders()

            if not limit_order_manager.orders:
                print("❌ No orders available")

                continue

            try:

                order_id = int(input("\nEnter order ID for take-profit: "))

                profit_usdt = float(input("Enter profit target in USDT: "))

                if profit_usdt <= 0:
                    print("❌ Profit must be positive")

                    continue

                # Find order

                original_order = None

                for order in limit_order_manager.orders:

                    if order['id'] == order_id:
                        original_order = order

                        break

                if not original_order:
                    print(f"❌ Order #{order_id} not found!")

                    continue

                if original_order['status'] != 'pending':
                    print(f"❌ Order #{order_id} is not pending!")

                    continue

                # ✅ GET TRIGGER PRICE FIRST (before any calculations)

                trigger_price = original_order['trigger_price']

                # Calculate take-profit based on direction

                if original_order['swap_direction'] == 'bnb_to_usdt':

                    # Original: BNB → USDT, so take-profit is USDT → BNB

                    bnb_amount = original_order['amount']

                    expected_usdt = bnb_amount * trigger_price * 0.9995

                    usdt_to_swap_back = expected_usdt - profit_usdt

                    if usdt_to_swap_back <= 0:
                        print(f"❌ Profit target too high!  Max profit: ${expected_usdt:.2f}")

                        continue

                    tp_target_price = (usdt_to_swap_back / bnb_amount) * 0.9995

                    tp_direction = 'usdt_to_bnb'

                    tp_amount = usdt_to_swap_back

                    tp_amount_label = f"{usdt_to_swap_back:.2f} USDT"

                    tp_receive = bnb_amount

                    tp_receive_label = f"~{bnb_amount:.6f} BNB"


                elif original_order['swap_direction'] == 'usdt_to_bnb':

                    # Original: USDT → BNB, so take-profit is BNB → USDT

                    usdt_spent = original_order['amount']

                    bnb_received = original_order['expected_receive']

                    target_usdt = usdt_spent + profit_usdt

                    tp_target_price = (target_usdt / bnb_received) * 1.0005

                    tp_direction = 'bnb_to_usdt'

                    tp_amount = bnb_received

                    tp_amount_label = f"{bnb_received:.6f} BNB"

                    tp_receive = target_usdt

                    tp_receive_label = f"~{target_usdt:.2f} USDT"


                else:

                    print(f"❌ Unknown swap direction:  {original_order['swap_direction']}")

                    continue

                # Show preview

                print(f"\n🎯 TAKE-PROFIT ORDER PREVIEW:")

                print("=" * 70)

                print(f"📋 Original Order #{order_id}:")

                print(f"   🔄 {original_order['amount_label']} → {original_order.get('receive_label', 'N/A')}")

                print(f"   🎯 Triggers at: ${trigger_price:.2f}")

                print(f"\n💰 Take-Profit Order:")

                print(f"   🔄 {tp_amount_label} → {tp_receive_label}")

                print(f"   🎯 Will trigger at: ${tp_target_price:.2f}")

                print(f"   💵 Expected Profit: ${profit_usdt:.2f} USDT")

                print(f"\n⚡ Auto-creates when Order #{order_id} executes!")

                print("=" * 70)

                confirm = input("\n✅ Create take-profit order? (y/n): ").strip().lower()

                if confirm != 'y':
                    print("❌ Cancelled")

                    continue

                # Create placeholder order

                current_price = limit_order_manager.get_bnb_price()

                tp_order_id = len(limit_order_manager.orders) + 1

                tp_order = {

                    'id': tp_order_id,

                    'wallet_idx': original_order['wallet_idx'],

                    'wallet_name': original_order['wallet_name'],

                    'wallet_address': original_order['wallet_address'],

                    'swap_direction': tp_direction,

                    'amount': tp_amount,

                    'amount_label': tp_amount_label,

                    'trigger_price': tp_target_price,

                    'current_price_at_creation': current_price,

                    'expected_receive': tp_receive,

                    'receive_label': tp_receive_label,

                    'created_at': datetime.now().isoformat(),

                    'status': 'waiting_for_execution',

                    'linked_order_id': order_id,

                    'profit_target_usdt': profit_usdt

                }

                limit_order_manager.orders.append(tp_order)

                limit_order_manager.save_orders()

                print(f"\n✅ TAKE-PROFIT ORDER #{tp_order_id} CREATED!")

                print(f"⏳ Waiting for Order #{order_id} to execute...")

                print(f"💰 Target profit: ${profit_usdt:.2f} USDT")

                # Send Telegram notification

                message = (

                    f"🎯 TAKE-PROFIT ORDER CREATED (Terminal)\n\n"

                    f"🆔 Order #{tp_order_id}\n"

                    f"🔗 Linked to Order #{order_id}\n"

                    f"💰 Target:  ${profit_usdt:.2f} profit\n"

                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"

                )

                send_telegram_message(message)


            except ValueError:

                print("❌ Invalid input")

            except Exception as e:

                print(f"❌ Error:  {e}")

                import traceback

                traceback.print_exc()  # ✅ Show full error for debugging

        elif choice == '17':

            calculate_atr_interactive()



        elif choice == '19':

            # View PnL

            try:

                print("\n💰 CALCULATING PROFIT & LOSS...")

                pnl_data = limit_order_manager.calculate_pnl()

                if not pnl_data or pnl_data['total_trades'] == 0:
                    print("\n📊 No completed trades yet!")

                    print("💡 Complete at least one buy + sell cycle to see PnL")

                    continue

                print("\n" + "=" * 80)

                print("💰 PROFIT & LOSS REPORT")

                print("=" * 80)

                # Summary

                win_rate = (pnl_data['successful_trades'] / pnl_data['total_trades']) * 100

                avg_pnl = pnl_data['total_pnl_usdt'] / pnl_data['total_trades']

                print(f"\n📊 SUMMARY:")

                print(f"   Total Trades: {pnl_data['total_trades']}")

                print(f"   Winning Trades: {pnl_data['successful_trades']}")

                print(f"   Win Rate: {win_rate:.1f}%")

                print(f"   Total Volume: ${pnl_data['total_volume_usdt']:.2f} USDT")

                print(f"   Total PnL:  ${pnl_data['total_pnl_usdt']:.2f} USDT")

                print(f"   Average PnL:  ${avg_pnl:.2f} USDT per trade")

                # Individual trades

                print(f"\n📋 TRADE HISTORY:")

                print("-" * 80)

                for i, trade in enumerate(pnl_data['trades'], 1):
                    pnl_emoji = "🟢" if trade['pnl'] > 0 else "🔴"

                    print(f"\n{pnl_emoji} Trade #{i} - {trade['wallet']}")

                    print(
                        f"   Buy:   {trade['bnb_amount']:.6f} BNB at ${trade['buy_price']:.2f} (Order #{trade['buy_order_id']})")

                    print(
                        f"   Sell: {trade['bnb_amount']:.6f} BNB at ${trade['sell_price']:.2f} (Order #{trade['sell_order_id']})")

                    print(f"   Spent: ${trade['usdt_spent']:.2f} USDT")

                    print(f"   Received: ${trade['usdt_received']:.2f} USDT")

                    print(f"   PnL:  ${trade['pnl']:.2f} USDT ({trade['pnl_percent']:+.2f}%)")

                    print(f"   Time: {trade['buy_time'][:19]} → {trade['sell_time'][: 19]}")

                print("\n" + "=" * 80)

                # Send summary to Telegram

                message = (

                    f"💰 <b>PnL REPORT</b>\n\n"

                    f"📊 Trades: {pnl_data['total_trades']}\n"

                    f"✅ Win Rate: {win_rate:.1f}%\n"

                    f"💵 Total PnL: ${pnl_data['total_pnl_usdt']:.2f}\n"

                    f"📈 Avg PnL: ${avg_pnl:.2f}\n"

                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"

                )

                send_telegram_message(message)


            except Exception as e:

                print(f"❌ Error:  {e}")

                import traceback

                traceback.print_exc()

        elif choice == '18':
            get_current_bnb_price_v3()


        elif choice == '20':
            # Send to external address
            wallet_manager.send_to_external(MAIN_WALLET_ADDRESS, MAIN_PRIVATE_KEY)

        elif choice == '21':
            print("👋 Goodbye!")
            break


if __name__ == "__main__":
    main()
