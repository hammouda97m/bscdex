import json
import os
import time
from datetime import datetime
from web3 import Web3


class LimitOrderManager:
    def __init__(self, swap_manager, betting_manager, wallet_manager, web3, chainlink_contract, usdt_address,
                 wbnb_address):
        self.orders_file = "limit_orders.json"
        self.orders = self.load_orders()
        self.swap_manager = swap_manager
        self.betting_manager = betting_manager
        self.wallet_manager = wallet_manager
        self.web3 = web3
        self.chainlink = chainlink_contract
        self.usdt_address = usdt_address
        self.wbnb = wbnb_address

    def load_orders(self):
        """Load pending orders from file"""
        try:
            if os.path.exists(self.orders_file):
                with open(self.orders_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"⚠️ Error loading orders:  {e}")
            return []

    def save_orders(self):
        """Save orders to file"""
        try:
            with open(self.orders_file, 'w') as f:
                json.dump(self.orders, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving orders: {e}")

    def get_bnb_price(self):
        """Get current BNB/USD price using V3 0.05% pool (most accurate)"""
        try:
            # Method 1: Use V3 0.05% pool (actual swap price)
            try:
                one_bnb_wei = int(1 * 1e18)

                # Import the quoter from mv5
                from mv5 import quoter_v2_contract, WBNB, USDT_CONTRACT

                params = {
                    'tokenIn': self.web3.to_checksum_address(WBNB),
                    'tokenOut': self.web3.to_checksum_address(USDT_CONTRACT),
                    'amountIn': one_bnb_wei,
                    'fee': 500,  # 0.05% fee pool (most accurate)
                    'sqrtPriceLimitX96': 0
                }

                result = quoter_v2_contract.functions.quoteExactInputSingle(params).call()
                usdt_out = result[0] / 1e18

                # This is the ACTUAL BNB price from V3 pool
                return float(usdt_out)

            except Exception as e:
                print(f"⚠️ V3 price check failed: {e}")

                # Fallback to Chainlink oracle
                latest_data = self.chainlink.functions.latestRoundData().call()
                price = latest_data[1] / 1e8
                print(f"⚠️ Using Chainlink fallback: ${price:.2f}")
                return float(price)

        except Exception as e:
            print(f"⚠️ Error getting BNB price: {e}")
            return None

    def get_locked_balances(self, wallet_address):
        """Calculate BNB and USDT locked in PENDING orders only"""
        try:
            from web3 import Web3
            wallet_address = Web3.to_checksum_address(wallet_address)

            locked_bnb = 0
            locked_usdt = 0

            for order in self.orders:
                # Only count PENDING orders (not waiting_for_execution, executed, or cancelled)
                if order['status'] != 'pending':
                    continue

                # Check if this order belongs to this wallet
                order_wallet = Web3.to_checksum_address(order['wallet_address'])
                if order_wallet != wallet_address:
                    continue

                # Add to locked balance based on swap direction
                if order['swap_direction'] == 'bnb_to_usdt':
                    locked_bnb += order['amount']
                elif order['swap_direction'] == 'usdt_to_bnb':
                    locked_usdt += order['amount']

            return locked_bnb, locked_usdt

        except Exception as e:
            print(f"⚠️ Error calculating locked balances: {e}")
            return 0, 0

    def create_order_interactive(self):
        """Create price-monitoring limit order (SAME LAYOUT!)"""
        try:
            current_price = self.get_bnb_price()
            if not current_price:
                print("❌ Failed to get current BNB price!")
                return False

            print(f"\n📊 Current BNB Price:   ${current_price:.2f}")
            print("\n" + "=" * 70)
            print("🔄 SWAP DIRECTION:")
            print("=" * 70)
            print("1. 💵 USDT → BNB (Buy BNB at lower price)")
            print("2. 💎 BNB → USDT (Sell BNB at higher price)")
            print("3. ❌ Cancel")
            print("=" * 70)

            swap_choice = input("\nSelect swap direction (1-3): ").strip()

            if swap_choice == '3':
                print("❌ Cancelled")
                return False

            if swap_choice not in ['1', '2']:
                print("❌ Invalid choice!")
                return False

            swap_direction = 'usdt_to_bnb' if swap_choice == '1' else 'bnb_to_usdt'

            # Get wallet
            print("\n👛 SELECT WALLET:")
            self.wallet_manager.list_wallets()

            if not self.wallet_manager.wallets:
                print("❌ No wallets available!")
                return False

            wallet_idx = int(input("\nWallet number: ")) - 1
            if wallet_idx < 0 or wallet_idx >= len(self.wallet_manager.wallets):
                print("❌ Invalid wallet!")
                return False

            wallet = self.wallet_manager.wallets[wallet_idx]
            wallet = self.wallet_manager.get_wallet_balances(wallet)
            wallet_address = wallet['address']

            # Get amount based on swap direction
            if swap_direction == 'usdt_to_bnb':
                # Calculate locked balances
                locked_bnb, locked_usdt = self.get_locked_balances(wallet['address'])
                available_usdt = wallet['balance_usdt'] - locked_usdt

                print(f"\n💵 Wallet USDT Balance:")
                print(f"   Total: {wallet['balance_usdt']:.2f} USDT")
                if locked_usdt > 0:
                    print(f"   🔒 Locked:  {locked_usdt:.2f} USDT (in pending orders)")
                    print(f"   ✅ Available: {available_usdt:.2f} USDT")
                else:
                    print(f"   ✅ Available: {available_usdt:.2f} USDT")

                amount_input = input("💰 Enter USDT amount to swap: ").strip()

                try:
                    amount = float(amount_input)
                except ValueError:
                    print("❌ Invalid number format!")
                    return False

                if amount <= 0:
                    print("❌ Amount must be positive!")
                    return False

                # Check available balance (excluding locked funds)
                if amount > available_usdt:
                    print("\n❌ INSUFFICIENT AVAILABLE BALANCE!")
                    print(f"   💵 Total balance: {wallet['balance_usdt']:.2f} USDT")
                    print(f"   🔒 Locked in orders:  {locked_usdt:.2f} USDT")
                    print(f"   ✅ Available: {available_usdt:.2f} USDT")
                    print(f"   ❌ You need: {amount:.2f} USDT")
                    print(f"   ❌ Short by: {amount - available_usdt:.2f} USDT")
                    return False

                amount_label = "{:.2f} USDT".format(amount)


            else:

                # Calculate locked balances

                locked_bnb, locked_usdt = self.get_locked_balances(wallet['address'])

                available_bnb = wallet['balance_bnb'] - locked_bnb

                print(f"\n💎 Wallet BNB Balance:")

                print(f"   Total:  {wallet['balance_bnb']:.6f} BNB")

                if locked_bnb > 0:

                    print(f"   🔒 Locked: {locked_bnb:.6f} BNB (in pending orders)")

                    print(f"   ✅ Available: {available_bnb:.6f} BNB")

                else:

                    print(f"   ✅ Available: {available_bnb:.6f} BNB")

                amount_input = input("💰 Enter BNB amount to swap: ").strip()

                try:
                    amount = float(amount_input)
                except ValueError:
                    print("❌ Invalid number format!")
                    return False

                if amount <= 0:
                    print("❌ Amount must be positive!")
                    return False

                # Check available balance (excluding locked funds)
                if amount > available_bnb:
                    print("\n❌ INSUFFICIENT AVAILABLE BALANCE!")
                    print(f"   💎 Total balance: {wallet['balance_bnb']:.6f} BNB")
                    print(f"   🔒 Locked in orders: {locked_bnb:.6f} BNB")
                    print(f"   ✅ Available: {available_bnb:.6f} BNB")
                    print(f"   ❌ You need: {amount:.6f} BNB")
                    print(f"   ❌ Short by:  {amount - available_bnb:.6f} BNB")
                    return False

                amount_label = "{:.6f} BNB".format(amount)

            # Get trigger price
            print("\n" + "=" * 70)
            print("🎯 TARGET PRICE (Limit Order Price):")
            print("=" * 70)
            print("1. 💲 Set exact BNB price (e.g., 920)")
            print("2. 📊 Set percentage from current (e.g., +5 or -3)")
            print("=" * 70)

            price_choice = input("\nSelect (1-2): ").strip()

            if price_choice == '1':
                price_input = input("🎯 Enter target BNB price: $").strip().replace("$", "").replace(",", "").strip()
                try:
                    trigger_price = float(price_input)
                except ValueError:
                    print("❌ Invalid price!")
                    return False

            elif price_choice == '2':
                print(f"\n📊 Current BNB Price:  ${current_price:.2f}")
                percentage_input = input("\n📈 Enter percentage (e.g., +5 or -3): ").strip().replace("%", "").strip()
                try:
                    percentage = float(percentage_input)
                    trigger_price = current_price * (1 + percentage / 100)
                except ValueError:
                    print("❌ Invalid percentage!")
                    return False

            else:
                print("❌ Invalid choice!")
                return False

            # Calculate expected output
            if swap_direction == 'usdt_to_bnb':
                expected_receive = amount / trigger_price
                receive_label = "~{:.6f} BNB".format(expected_receive)
            else:
                expected_receive = amount * trigger_price * 0.9995  # Account for slippage
                receive_label = "~{:.2f} USDT".format(expected_receive)

            # Show preview
            price_diff = ((trigger_price - current_price) / current_price) * 100

            # Determine if price needs to rise or fall
            if swap_direction == 'bnb_to_usdt':
                # Selling BNB - want higher price
                direction_label = "RISES" if trigger_price > current_price else "DROPS"
            else:
                # Buying BNB - want lower price
                direction_label = "DROPS" if trigger_price < current_price else "RISES"

            print("\n" + "=" * 70)
            print("📋 LIMIT ORDER PREVIEW:")
            print("=" * 70)
            print(f"👤 Wallet: {wallet['name']}")
            print(f"🔄 Order:  {amount_label} -> {receive_label}")
            print(f"📊 Current BNB:  ${current_price:.2f}")
            print(f"🎯 Limit Price: ${trigger_price:.2f} ({price_diff:+.2f}%)")
            print(f"⏳ Will execute when BNB {direction_label} to ${trigger_price:.2f}")
            print(f"🤖 Bot monitors price every ~1.5 seconds")
            print("=" * 70)

            confirm = input("\n✅ Create this limit order? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Cancelled")
                return False

            # Create the order (save locally)
            order_id = len(self.orders) + 1

            order = {
                'id': order_id,
                'wallet_idx': wallet_idx,
                'wallet_name': wallet['name'],
                'wallet_address': wallet_address,
                'swap_direction': swap_direction,
                'amount': amount,
                'amount_label': amount_label,
                'trigger_price': trigger_price,
                'current_price_at_creation': current_price,
                'expected_receive': expected_receive,
                'receive_label': receive_label,
                'created_at': datetime.now().isoformat(),
                'status': 'pending'
            }

            self.orders.append(order)
            self.save_orders()

            print(f"\n✅ LIMIT ORDER #{order_id} CREATED!")
            print(f"⚡ Monitoring in background...")
            print(f"🎯 Will execute when BNB {direction_label} to ${trigger_price:.2f}")

            # Send Telegram notification
            self.send_telegram_notification(order, "created")

            return True

        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            return False
        except Exception as e:
            print(f"❌ Error:  {e}")
            return False


    def create_order(self, wallet_idx, wallet_name, wallet_address, swap_direction, amount, trigger_price):
        """Create a new limit order programmatically (used by Telegram bot)"""
        try:
            current_price = self.get_bnb_price()
            if not current_price:
                print("❌ Failed to get current BNB price!")
                return None

            # Calculate expected output and labels
            if swap_direction == 'usdt_to_bnb':
                amount_label = f"{amount:.2f} USDT"
                expected_receive = amount / trigger_price * 0.9995
                receive_label = f"~{expected_receive:.6f} BNB"
            else:  # bnb_to_usdt
                amount_label = f"{amount:.6f} BNB"
                expected_receive = amount * trigger_price * 0.9995
                receive_label = f"~{expected_receive:.2f} USDT"

            # Create the order
            order_id = len(self.orders) + 1

            order = {
                'id': order_id,
                'wallet_idx': wallet_idx,
                'wallet_name': wallet_name,
                'wallet_address': wallet_address,
                'swap_direction': swap_direction,
                'amount': amount,
                'amount_label': amount_label,
                'trigger_price': trigger_price,
                'current_price_at_creation': current_price,
                'expected_receive': expected_receive,
                'receive_label': receive_label,
                'created_at': datetime.now().isoformat(),
                'status':  'pending'
            }

            self.orders.append(order)
            self.save_orders()

            print(f"✅ LIMIT ORDER #{order_id} CREATED!")
            print(f"⚡ Monitoring in background...")

            # Send Telegram notification
            self.send_telegram_notification(order, "created")

            return order

        except Exception as e:
            print(f"❌ Error creating order:  {e}")
            return None

    def view_orders(self):
        """Display all pending orders"""
        try:
            pending_orders = [o for o in self.orders if o['status'] == 'pending']

            if not pending_orders:
                print("\n📝 No pending limit orders")
                return

            current_price = self.get_bnb_price()

            print("\n" + "=" * 80)
            print("📋 PENDING LIMIT ORDERS")
            print("=" * 80)

            for order in pending_orders:
                trigger_price = order['trigger_price']
                price_diff = ((trigger_price - current_price) / current_price) * 100 if current_price else 0

                swap_emoji = "💵→💎" if order['swap_direction'] == 'usdt_to_bnb' else "💎→💵"

                # Determine direction
                if order['swap_direction'] == 'bnb_to_usdt':
                    direction = "RISES" if trigger_price > current_price else "DROPS"
                else:
                    direction = "DROPS" if trigger_price < current_price else "RISES"

                # Handle old orders that might not have receive_label
                receive_label = order.get('receive_label', 'N/A')

                print(f"\n🎯 Order #{order['id']} {swap_emoji}")
                print(f"   👤 Wallet: {order['wallet_name']}")
                print(f"   🔄 Swap: {order['amount_label']} -> {receive_label}")
                print(f"   📊 Current BNB: ${current_price:.2f}" if current_price else "   📊 Current:  N/A")
                print(f"   🎯 Trigger: ${trigger_price:.2f} ({price_diff:+.2f}%)")
                print(f"   ⏳ Waiting for BNB to {direction} to ${trigger_price:.2f}")
                print(f"   ⏰ Created: {order['created_at'][: 19]}")
                print("-" * 80)

            print(f"\n💼 Total Pending: {len(pending_orders)}")

        except Exception as e:
            print(f"❌ Error viewing orders:  {e}")

    def cancel_order(self, order_id):
        """Cancel a pending order by ID and any related take-profit orders"""
        try:
            cancelled_orders = []

            # Find and cancel the main order
            main_order = None
            for order in self.orders:
                if order['id'] == order_id:
                    if order['status'] not in ['pending', 'waiting_for_execution']:
                        print(f"❌ Order #{order_id} cannot be cancelled (Status: {order['status']})")
                        return False

                    main_order = order
                    order['status'] = 'cancelled'
                    order['cancelled_at'] = datetime.now().isoformat()
                    cancelled_orders.append(order_id)
                    break

            if not main_order:
                print(f"❌ Order #{order_id} not found")
                return False

            # Check if this order has any linked take-profit orders
            for order in self.orders:
                if (order.get('linked_order_id') == order_id and
                        order['status'] == 'waiting_for_execution'):
                    order['status'] = 'cancelled'
                    order['cancelled_at'] = datetime.now().isoformat()
                    order['cancelled_reason'] = f"Parent order #{order_id} was cancelled"
                    cancelled_orders.append(order['id'])

                    print(f"🔗 Also cancelled linked TP order #{order['id']}")

            # Check if this order IS a take-profit order linked to another order
            if main_order.get('linked_order_id'):
                parent_id = main_order.get('linked_order_id')
                print(f"⚠️ This was a take-profit order linked to Order #{parent_id}")

                # Check if parent is still pending
                for order in self.orders:
                    if order['id'] == parent_id and order['status'] == 'pending':
                        print(f"ℹ️ Parent Order #{parent_id} is still active")

            self.save_orders()

            # Send notifications
            for cancelled_id in cancelled_orders:
                for order in self.orders:
                    if order['id'] == cancelled_id:
                        self.send_telegram_notification(order, "cancelled")

            if len(cancelled_orders) > 1:
                print(f"✅ Cancelled {len(cancelled_orders)} orders:  {cancelled_orders}")
            else:
                print(f"✅ Order #{order_id} cancelled!")

            return True

        except Exception as e:
            print(f"❌ Error cancelling order: {e}")
            import traceback
            traceback.print_exc()
            return False

    def execute_swap(self, wallet, swap_direction, amount):
        """
        Execute swap using V3 0. 05% pool (Smart Router)
        Auto-unwraps WBNB to native BNB for USDT→BNB swaps
        """
        try:
            wallet_address = Web3.to_checksum_address(wallet['address'])
            private_key = wallet['private_key']

            if swap_direction == 'usdt_to_bnb':
                # Execute V3 swap (USDT → WBNB)
                print(f"💱 Swapping {amount:.2f} USDT → BNB...")
                swap_success = self.swap_manager._swap_usdt_to_bnb_v3(wallet_address, private_key, amount)

                if not swap_success:
                    print("❌ Swap failed!")
                    return False

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
                    wbnb_contract_balance = self.web3.eth.contract(
                        address=Web3.to_checksum_address(self.wbnb),
                        abi=wbnb_balance_abi
                    )

                    wbnb_balance = wbnb_contract_balance.functions.balanceOf(wallet_address).call()

                    if wbnb_balance > 0:
                        wbnb_balance_human = wbnb_balance / 1e18
                        print(f"🔄 Unwrapping {wbnb_balance_human:.6f} WBNB → BNB...")

                        # Unwrap WBNB
                        wbnb_contract = self.web3.eth.contract(
                            address=Web3.to_checksum_address(self.wbnb),
                            abi=wbnb_withdraw_abi
                        )

                        nonce = self.web3.eth.get_transaction_count(wallet_address)

                        unwrap_tx = wbnb_contract.functions.withdraw(wbnb_balance).build_transaction({
                            'from': wallet_address,
                            'gas': 50000,
                            'gasPrice': self.web3.to_wei('3', 'gwei'),
                            'nonce': nonce,
                            'chainId': 56,
                            'value': 0
                        })

                        signed_tx = self.web3.eth.account.sign_transaction(unwrap_tx, private_key)
                        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)

                        print(f"⏳ Unwrap TX: {self.web3.to_hex(tx_hash)}")
                        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

                        if receipt.status == 1:
                            print(f"✅ Unwrapped {wbnb_balance_human:.6f} WBNB → BNB")
                            print(f"🔗 TX:  https://bscscan.com/tx/{self.web3.to_hex(tx_hash)}")
                        else:
                            print(f"⚠️ Unwrap failed, but you have WBNB in wallet")
                            print(f"💡 Use /unwrap command to manually unwrap")
                    else:
                        print("✅ No WBNB to unwrap (swap already gave native BNB)")

                except Exception as unwrap_error:
                    print(f"⚠️ Unwrap error: {unwrap_error}")
                    print(f"💡 You may have WBNB in wallet - use /unwrap command")
                    import traceback
                    traceback.print_exc()

                return True

            elif swap_direction == 'bnb_to_usdt':
                # BNB → USDT (no unwrapping needed)
                print(f"💱 Swapping {amount:.6f} BNB → USDT...")
                return self.swap_manager._swap_bnb_to_usdt_v3(wallet_address, private_key, amount)

            else:
                print(f"❌ Unknown swap direction: {swap_direction}")
                return False

        except Exception as e:
            print(f"❌ Swap error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def check_and_execute_orders(self):
        """Background:  Check prices and execute orders when triggered"""
        try:
            current_price = self.get_bnb_price()
            if not current_price:
                return

            pending_orders = [o for o in self.orders if o['status'] == 'pending']

            for order in pending_orders:
                trigger_price = order['trigger_price']
                swap_direction = order['swap_direction']

                # Check if order should trigger
                should_execute = False

                if swap_direction == 'bnb_to_usdt':
                    # Selling BNB - execute when price reaches or exceeds target
                    if current_price >= trigger_price:
                        should_execute = True
                else:
                    # Buying BNB - execute when price drops to or below target
                    if current_price <= trigger_price:
                        should_execute = True

                if should_execute:
                    print(f"\n🎯 ORDER #{order['id']} TRIGGERED!")
                    print(f"📊 Target:  ${trigger_price:.2f} | Current: ${current_price:.2f}")
                    print(f"⚡ Executing swap...")

                    # Get wallet
                    wallet = self.wallet_manager.wallets[order['wallet_idx']]

                    # Execute the swap
                    success = self.swap_manager.execute_swap(
                        wallet=wallet,
                        swap_direction=swap_direction,
                        amount=order['amount']
                    )

                    if success:
                        order['status'] = 'executed'
                        order['executed_at'] = datetime.now().isoformat()
                        order['execution_price'] = current_price
                        self.save_orders()

                        print(f"✅ Order #{order['id']} executed successfully!")
                        self.send_telegram_notification(order, "executed")

                        self.check_and_create_take_profit(order)
                    else:
                        print(f"❌ Order #{order['id']} execution failed!")
                        # Keep order pending to retry

        except Exception as e:
            print(f"⚠️ Error checking orders:  {e}")

    def send_telegram_notification(self, order, status):
        """Send Telegram notification"""
        try:
            token = os.getenv("TELEGRAM_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")

            if not token or not chat_id:
                return

            swap_label = "USDT→BNB" if order['swap_direction'] == 'usdt_to_bnb' else "BNB→USDT"

            if status == "created":
                message = (
                    f"🎯 LIMIT ORDER CREATED!\n\n"
                    f"🆔 #{order['id']}\n"
                    f"👤 {order['wallet_name']}\n"
                    f"🔄 {order['amount_label']} -> {order.get('receive_label', 'N/A')}\n"
                    f"📊 Current:  ${order.get('current_price_at_creation', 0):.2f}\n"
                    f"🎯 Target: ${order['trigger_price']:.2f}\n"
                    f"🤖 Monitoring automatically.. .\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
            elif status == "executed":
                message = (
                    f"✅ LIMIT ORDER EXECUTED!\n\n"
                    f"🆔 #{order['id']}\n"
                    f"👤 {order['wallet_name']}\n"
                    f"🔄 {order['amount_label']} ({swap_label})\n"
                    f"🎯 Target: ${order['trigger_price']:.2f}\n"
                    f"📊 Executed at: ${order.get('execution_price', 0):.2f}\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
            elif status == "cancelled":
                message = (
                    f"❌ LIMIT ORDER CANCELLED\n\n"
                    f"🆔 #{order['id']}\n"
                    f"👤 {order['wallet_name']}\n"
                    f"🔄 {order['amount_label']}\n"
                    f"🎯 Target was:  ${order['trigger_price']:.2f}\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
            elif status == "take_profit_activated":
                profit = order.get('profit_target_usdt', 0)
                linked_id = order.get('linked_order_id', 'N/A')
                message = (
                    f"🎯 <b>TAKE-PROFIT ORDER ACTIVATED!</b>\n\n"
                    f"🆔 Order #{order['id']}\n"
                    f"🔗 Linked to Order #{linked_id}\n"
                    f"👤 {order['wallet_name']}\n"
                    f"🔄 {order['amount_label']} → {order.get('receive_label', 'N/A')}\n"
                    f"🎯 Target: ${order['trigger_price']:.2f}\n"
                    f"💰 Expected Profit: ${profit:.2f} USDT\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
            else:
                message = f"Status update for order #{order['id']}"

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}
            import requests
            requests.post(url, data=payload, timeout=5)

        except Exception as e:
            print(f"⚠️ Telegram error: {e}")

    def check_and_create_take_profit(self, executed_order):
        """Check if there are pending take-profit orders for this executed order"""
        try:
            # Look for take-profit orders waiting for this order
            for tp_order in self.orders:
                if (tp_order.get('status') == 'waiting_for_execution' and
                        tp_order.get('linked_order_id') == executed_order['id']):

                    print(f"\n🎯 Creating take-profit order for #{executed_order['id']}...")

                    # Get the actual execution details
                    executed_price = executed_order.get('execution_price', executed_order['trigger_price'])

                    # Recalculate based on actual execution
                    profit_target = tp_order['profit_target_usdt']

                    if executed_order['swap_direction'] == 'bnb_to_usdt':
                        # Original:  BNB → USDT, so take-profit is USDT → BNB
                        bnb_amount = executed_order['amount']
                        usdt_received = bnb_amount * executed_price * 0.9995  # Account for slippage
                        usdt_to_swap = usdt_received - profit_target

                        # Calculate target price with 0.05% slippage buffer
                        target_price = (usdt_to_swap / bnb_amount) * 0.9995

                        # Update the pending order
                        tp_order['trigger_price'] = target_price
                        tp_order['amount'] = usdt_to_swap
                        tp_order['amount_label'] = f"{usdt_to_swap:.2f} USDT"
                        tp_order['expected_receive'] = bnb_amount
                        tp_order['receive_label'] = f"~{bnb_amount:.6f} BNB"
                        tp_order['status'] = 'pending'
                        tp_order['current_price_at_creation'] = self.get_bnb_price()

                    else:
                        # Original: USDT → BNB, so take-profit is BNB → USDT
                        usdt_spent = executed_order['amount']
                        bnb_received = executed_order['expected_receive']
                        target_usdt = usdt_spent + profit_target

                        # Calculate target price with 0.05% slippage buffer
                        target_price = (target_usdt / bnb_received) * 1.0005

                        # Update the pending order
                        tp_order['trigger_price'] = target_price
                        tp_order['amount'] = bnb_received
                        tp_order['amount_label'] = f"{bnb_received:.6f} BNB"
                        tp_order['expected_receive'] = target_usdt
                        tp_order['receive_label'] = f"~{target_usdt:.2f} USDT"
                        tp_order['status'] = 'pending'
                        tp_order['current_price_at_creation'] = self.get_bnb_price()

                    self.save_orders()

                    print(f"✅ Take-profit order #{tp_order['id']} is now ACTIVE!")

                    # Send notification
                    self.send_telegram_notification(tp_order, "take_profit_activated")

        except Exception as e:
            print(f"⚠️ Error creating take-profit:  {e}")

    def calculate_pnl(self):
        """Calculate total profit/loss - WITH INVENTORY TRACKING"""
        try:
            pnl_data = {
                'total_trades': 0,
                'successful_trades': 0,
                'total_volume_usdt': 0,
                'total_pnl_usdt': 0,
                'trades': []
            }

            # Get all executed orders sorted by time
            executed_orders = [o for o in self.orders if o['status'] == 'executed']
            executed_orders.sort(key=lambda x: x.get('executed_at', ''))

            # Track inventory per wallet (FIFO)
            wallet_inventory = {}

            for order in executed_orders:
                wallet_id = order['wallet_idx']

                if wallet_id not in wallet_inventory:
                    wallet_inventory[wallet_id] = {
                        'bnb_stack': [],  # List of (bnb_amount, cost_basis)
                        'total_bnb': 0,
                        'total_cost': 0
                    }

                inventory = wallet_inventory[wallet_id]

                if order['swap_direction'] == 'usdt_to_bnb':
                    # BUY:  Add to inventory
                    usdt_spent = order['amount']
                    buy_price = order.get('execution_price', order['trigger_price'])
                    bnb_bought = usdt_spent / buy_price * 0.9995

                    # Add to stack
                    inventory['bnb_stack'].append({
                        'bnb': bnb_bought,
                        'cost': usdt_spent,
                        'price': buy_price,
                        'order_id': order['id']
                    })
                    inventory['total_bnb'] += bnb_bought
                    inventory['total_cost'] += usdt_spent

                else:
                    # SELL: Remove from inventory (FIFO)
                    bnb_to_sell = order['amount']
                    sell_price = order.get('execution_price', order['trigger_price'])
                    usdt_received = bnb_to_sell * sell_price * 0.9995

                    bnb_remaining = bnb_to_sell
                    total_cost_basis = 0

                    # Take from inventory (FIFO)
                    while bnb_remaining > 0.0001 and inventory['bnb_stack']:
                        oldest = inventory['bnb_stack'][0]

                        if oldest['bnb'] <= bnb_remaining:
                            # Use entire oldest position
                            bnb_remaining -= oldest['bnb']
                            total_cost_basis += oldest['cost']
                            inventory['bnb_stack'].pop(0)
                        else:
                            # Use partial oldest position
                            ratio = bnb_remaining / oldest['bnb']
                            cost_used = oldest['cost'] * ratio
                            total_cost_basis += cost_used

                            oldest['bnb'] -= bnb_remaining
                            oldest['cost'] -= cost_used
                            bnb_remaining = 0

                    # Calculate PnL
                    pnl = usdt_received - total_cost_basis
                    pnl_percent = (pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0

                    # Find corresponding buy order(s)
                    buy_order_ids = []
                    for item in inventory['bnb_stack']:
                        if item.get('order_id'):
                            buy_order_ids.append(item['order_id'])

                    avg_buy_price = total_cost_basis / bnb_to_sell if bnb_to_sell > 0 else 0

                    pnl_data['trades'].append({
                        'wallet': order['wallet_name'],
                        'buy_order_id': buy_order_ids[0] if buy_order_ids else 'N/A',
                        'sell_order_id': order['id'],
                        'bnb_amount': bnb_to_sell,
                        'buy_price': avg_buy_price,
                        'sell_price': sell_price,
                        'usdt_spent': total_cost_basis,
                        'usdt_received': usdt_received,
                        'pnl': pnl,
                        'pnl_percent': pnl_percent,
                        'buy_time': 'Multiple' if len(buy_order_ids) > 1 else order.get('executed_at', 'N/A'),
                        'sell_time': order.get('executed_at', 'N/A')
                    })

                    pnl_data['total_trades'] += 1
                    pnl_data['total_volume_usdt'] += total_cost_basis
                    pnl_data['total_pnl_usdt'] += pnl

                    if pnl > 0:
                        pnl_data['successful_trades'] += 1

            return pnl_data

        except Exception as e:
            print(f"❌ Error calculating PnL:  {e}")
            import traceback
            traceback.print_exc()
            return None