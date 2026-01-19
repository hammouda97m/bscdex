import os
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()


class TelegramHandler:
    def __init__(self, wallet_manager, swap_manager, betting_manager, reward_manager, limit_order_manager):
        self.wallet_manager = wallet_manager
        self.swap_manager = swap_manager
        self.betting_manager = betting_manager
        self.reward_manager = reward_manager
        self.limit_order_manager = limit_order_manager
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.last_update_id = 0
        self.pending_cancel_order = None
        self.pending_swap = None

    def send_message(self, message):
        """Send message to Telegram"""
        try:
            if not self.token or not self.chat_id:
                return False
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}
            response = requests.post(url, data=payload, timeout=5)
            return response.ok
        except Exception as e:
            print(f"⚠️ Telegram error: {e}")
            return False

    def get_updates(self):
        """Get new messages from Telegram"""
        try:
            if not self.token:
                return []
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            params = {"offset": self.last_update_id + 1, "timeout": 0}
            response = requests.get(url, params=params, timeout=2)
            if response.ok:
                data = response.json()
                updates = data.get('result', [])
                if updates:
                    self.last_update_id = updates[-1]['update_id']
                return updates
        except:
            pass
        return []

    def process_commands(self):
        """Process incoming Telegram commands"""
        updates = self.get_updates()

        for update in updates:
            try:
                if 'message' not in update or 'text' not in update['message']:
                    continue

                message_text = update['message']['text']. strip()

                # ✅ CHECK FOR PENDING SWAP CONFIRMATION FIRST
                if hasattr(self, 'pending_swap') and self.pending_swap:
                    response = message_text.strip().upper()

                    if response == 'YES':
                        # Execute the swap
                        self._execute_pending_swap()
                        self. pending_swap = None
                        continue

                    elif response == 'NO' or response == '/CANCEL':
                        self.send_message("❌ Swap cancelled")
                        self.pending_swap = None
                        continue

                    elif not message_text.startswith('/'):
                        self.send_message("❌ Please reply <b>YES</b> to confirm or <b>NO</b> to cancel")
                        continue

                # ✅ CHECK FOR PENDING LIMIT ORDER CONFIRMATION
                if hasattr(self, 'pending_limit_order') and self.pending_limit_order:
                    response = message_text.strip().upper()

                    if response == 'YES':
                        # Create order using proper method
                        order_data = self. pending_limit_order

                        order = self.limit_order_manager.create_order(
                            wallet_idx=order_data['wallet_idx'],
                            wallet_name=order_data['wallet_name'],
                            wallet_address=order_data['wallet_address'],
                            swap_direction=order_data['swap_direction'],
                            amount=order_data['amount'],
                            trigger_price=order_data['trigger_price']
                        )

                        if order:
                            self.send_message(
                                f"✅ <b>LIMIT ORDER CREATED!  </b>\n\n"
                                f"🆔 Order #{order['id']}\n"
                                f"👤 {order['wallet_name']}\n"
                                f"🔄 {order['amount_label']}\n"
                                f"🎯 Target:   ${order['trigger_price']:.2f}\n"
                                f"⚡ Monitoring started!"
                            )
                        else:
                            self.send_message("❌ Failed to create order")

                        self.pending_limit_order = None
                        continue

                    elif response == 'NO' or response == '/CANCEL':
                        self.send_message("❌ Order cancelled")
                        self.pending_limit_order = None
                        continue

                    elif not message_text.startswith('/'):
                        self.send_message("❌ Please reply <b>YES</b> to confirm or <b>NO</b> to cancel")
                        continue

                # Parse commands
                if not message_text.startswith('/'):
                    continue

                parts = message_text.split()
                command = parts[0]. lower()
                args = parts[1:] if len(parts) > 1 else []

                print(f"📱 Telegram command:  {message_text}")

                # Route to handler
                self.handle_command(command, args)

            except Exception as e:
                print(f"⚠️ Error processing update:   {e}")
                self.send_message(f"❌ Error:    {str(e)}")

    def handle_command(self, command, args):
        """Route commands to appropriate handlers"""

        # === HELP ===
        if command == '/help' or command == '/start':
            self.cmd_help()

        # === WALLET COMMANDS ===
        elif command == '/wallets':
            self.cmd_wallets()
        elif command == '/balance':
            self.cmd_balance()
        elif command == '/create':
            self.cmd_create_wallet(args)
        elif command == '/send':
            self.cmd_send(args)

        # === SWAP COMMANDS ===
        elif command == '/swap_usdt':
            self.cmd_swap_usdt(args)
        elif command == '/swap_bnb':
            self.cmd_swap_bnb(args)

        # === BETTING COMMANDS ===
        elif command == '/bet':
            self.cmd_bet(args)

        # === REWARD COMMANDS ===
        elif command == '/claim':
            self.cmd_claim(args)
        elif command == '/rewards':
            self.cmd_show_rewards(args)

        # === LIMIT ORDER COMMANDS ===
        elif command == '/orders':
            self.cmd_view_orders()
        elif command == '/cancel':
            self.cmd_cancel_order(args)

        # === UTILITY COMMANDS ===
        elif command == '/price':
            self.cmd_price()
        elif command == '/atr':
            self.cmd_calculate_atr(args)
        elif command == '/drain':
            self.cmd_drain_all()
        elif command == '/empty':
            self.cmd_empty_wallet(args)
        elif command == '/limit':
            self.cmd_create_limit_order(args)
        elif command == '/profit':
            self.cmd_create_take_profit(args)
        elif command == '/orders':
            self.cmd_view_orders()
        elif command == '/pnl':
            self.cmd_view_pnl()
        elif command == '/unwrap':
            self.cmd_unwrap(args)

        else:
            self.send_message(f"❌ Unknown command: {command}\n\nSend /help for commands")

    # ===================================
    # COMMAND IMPLEMENTATIONS
    # ===================================

    def cmd_help(self):
        """Show all available commands"""
        help_text = """
🤖 <b>Pancakeswap Control Bot Version 2.1.0
Developed and programmed by Moe Yassin
www.moeyassin.com</b>

📋 <b>WALLET COMMANDS: </b>
/wallets - List all wallets
/balance - Main wallet balance
/create [name] - Create new wallet
/send [bnb|usdt] [amount] [address] - Send to external


💱 <b>SWAP COMMANDS:</b>
/swap_usdt [amount] - Swap USDT→BNB (main wallet)
/swap_bnb [amount] - Swap BNB→USDT (main wallet)

🎯 <b>BETTING COMMANDS:</b>
/bet [wallet]/[usdt]/[up|down] - Place bet
Example: /bet 1/50/up

🎁 <b>REWARD COMMANDS:</b>
/rewards [wallet] - Show claimable rewards
/claim [wallet] - Claim all rewards

📊 <b>LIMIT ORDERS: </b>
/limit - Create new limit order (interactive)
/profit [order_id] [profit_usdt] - Auto take-profit
/orders - View pending orders
/cancel [order_id] - Cancel order

💰 <b>UTILITY: </b>
/price - Current BNB price
/atr - Calculate ATR (volatility)
/pnl - View profit & loss
/empty [wallet] - Empty wallet to main
/drain - Drain ALL wallets
/unwrap [wallet] - Unwraps WBNB

/help - Show this message
"""
        self.send_message(help_text)

    def cmd_wallets(self):
        """List all wallets with available balance"""
        try:
            if not self.wallet_manager.wallets:
                self.send_message("📝 No wallets created yet")
                return

            message = "📋 <b>YOUR WALLETS</b>\n\n"

            for i, wallet in enumerate(self.wallet_manager.wallets):
                wallet = self.wallet_manager.get_wallet_balances(wallet)

                # Get locked balances
                locked_bnb, locked_usdt = self.limit_order_manager.get_locked_balances(wallet['address'])
                available_bnb = wallet['balance_bnb'] - locked_bnb
                available_usdt = wallet['balance_usdt'] - locked_usdt

                message += f"<b>{i + 1}.  {wallet['name']}</b>\n"

                # BNB with available balance
                message += f"💎 BNB: {wallet['balance_bnb']:.6f}\n"
                if locked_bnb > 0:
                    message += f"   └─ Available: {available_bnb:.6f} (🔒 {locked_bnb:.6f})\n"

                # USDT with available balance
                message += f"💵 USDT: {wallet['balance_usdt']:.2f}\n"
                if locked_usdt > 0:
                    message += f"   └─ Available: {available_usdt:.2f} (🔒 {locked_usdt:.2f})\n"

                message += f"📧 {wallet['address'][:10]}... {wallet['address'][-6:]}\n\n"

            self.send_message(message)

        except Exception as e:
            self.send_message(f"❌ Error:  {str(e)}")

    def cmd_balance(self):
        """Show main wallet balance"""
        try:
            from web3 import Web3
            from mv5 import web3, usdt_contract, MAIN_WALLET_ADDRESS

            main_address = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)
            bnb_balance = web3.eth.get_balance(main_address)
            bnb_balance = web3.from_wei(bnb_balance, 'ether')
            usdt_balance = usdt_contract.functions.balanceOf(main_address).call() / 1e18

            message = (
                f"💰 <b>MAIN WALLET BALANCE</b>\n\n"
                f"💎 BNB: {bnb_balance:.6f}\n"
                f"💵 USDT: {usdt_balance:.2f}\n"
                f"📧 {MAIN_WALLET_ADDRESS[:10]}...{MAIN_WALLET_ADDRESS[-6:]}"
            )
            self.send_message(message)

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def cmd_create_wallet(self, args):
        """Create new wallet"""
        try:
            name = ' '.join(args) if args else None
            wallet = self.wallet_manager.create_new_wallet(name)

            if wallet:
                message = (
                    f"✅ <b>NEW WALLET CREATED! </b>\n\n"
                    f"📝 Name:  {wallet['name']}\n"
                    f"📧 Address: {wallet['address']}\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_message(message)
            else:
                self.send_message("❌ Failed to create wallet")

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def cmd_swap_usdt(self, args):
        """Swap USDT to BNB (main wallet) with confirmation"""
        try:
            if not args:
                self.send_message("❌ Usage:   /swap_usdt [amount]\nExample: /swap_usdt 50")
                return

            amount = float(args[0])

            if amount <= 0:
                self.send_message("❌ Amount must be positive")
                return

            # Check balance first
            from web3 import Web3
            from mv5 import web3, usdt_contract, MAIN_WALLET_ADDRESS

            main_address = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)
            usdt_balance = usdt_contract.functions.balanceOf(main_address).call() / 1e18

            if amount > usdt_balance:
                self.send_message(
                    f"❌ Insufficient USDT!\n\n"
                    f"Available:  {usdt_balance:.2f} USDT\n"
                    f"Needed:  {amount:.2f} USDT"
                )
                return

            # Get rate
            expected_bnb = self.swap_manager.get_usdt_to_bnb_rate(amount)

            # Store pending swap
            self.pending_swap = {
                'type': 'usdt_to_bnb',
                'amount': amount,
                'expected_output': expected_bnb,
                'wallet_address': main_address
            }

            # Show preview with confirmation request
            message = (
                f"💱 <b>SWAP PREVIEW</b>\n\n"
                f"📤 {amount:.2f} USDT\n"
                f"📥 ~{expected_bnb:.6f} BNB\n"
                f"🎯 V3 0.05% Pool\n"
                f"💵 Slippage: 0.05%\n\n"
                f"Reply <b>YES</b> to confirm or <b>NO</b> to cancel"
            )
            self.send_message(message)

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
            self.pending_swap = None

    def cmd_swap_bnb(self, args):
        """Swap BNB to USDT (main wallet) with confirmation"""
        try:
            if not args:
                self.send_message("❌ Usage:  /swap_bnb [amount]\nExample: /swap_bnb 0.5")
                return

            amount = float(args[0])

            if amount <= 0:
                self.send_message("❌ Amount must be positive")
                return

            # Check balance first
            from web3 import Web3
            from mv5 import web3, MAIN_WALLET_ADDRESS

            main_address = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)
            bnb_balance = web3.eth.get_balance(main_address) / 1e18

            if amount > bnb_balance:
                self.send_message(
                    f"❌ Insufficient BNB!\n\n"
                    f"Available: {bnb_balance:.6f} BNB\n"
                    f"Needed:   {amount:.6f} BNB"
                )
                return

            # Get rate
            expected_usdt = self.swap_manager.get_bnb_to_usdt_rate(amount)

            # Store pending swap
            self.pending_swap = {
                'type': 'bnb_to_usdt',
                'amount': amount,
                'expected_output': expected_usdt,
                'wallet_address': main_address
            }

            # Show preview with confirmation request
            message = (
                f"💱 <b>SWAP PREVIEW</b>\n\n"
                f"📤 {amount:.6f} BNB\n"
                f"📥 ~{expected_usdt:.2f} USDT\n"
                f"🎯 V3 0.05% Pool\n"
                f"💵 Slippage: 0.05%\n\n"
                f"Reply <b>YES</b> to confirm or <b>NO</b> to cancel"
            )
            self.send_message(message)

        except Exception as e:
            self.send_message(f"❌ Error:  {str(e)}")
            self.pending_swap = None

    def cmd_bet(self, args):
        """Place bet:  /bet 1/50/up"""
        try:
            if not args:
                self.send_message("❌ Usage: /bet [wallet]/[usdt]/[up|down]\nExample: /bet 1/50/up")
                return

            # Parse:  wallet/usdt/direction
            parts = args[0].split('/')

            if len(parts) != 3:
                self.send_message("❌ Format: /bet [wallet]/[usdt]/[up|down]\nExample: /bet 1/50/up")
                return

            wallet_idx = int(parts[0]) - 1
            usdt_amount = float(parts[1])
            direction = parts[2].lower()

            if direction not in ['up', 'down']:
                self.send_message("❌ Direction must be 'up' or 'down'")
                return

            if wallet_idx < 0 or wallet_idx >= len(self.wallet_manager.wallets):
                self.send_message("❌ Invalid wallet number")
                return

            wallet = self.wallet_manager.wallets[wallet_idx]
            expected_bnb = self.swap_manager.get_usdt_to_bnb_rate(usdt_amount)

            preview_msg = (
                f"⚡ <b>PLACING BET! </b>\n\n"
                f"💱 {usdt_amount} USDT → ~{expected_bnb:.6f} BNB\n"
                f"👤 Wallet: {wallet['name']}\n"
                f"🎯 Direction: {direction.upper()}\n"
                f"⏳ Processing..."
            )
            self.send_message(preview_msg)

            # Execute swap
            success = self.swap_manager.swap_usdt_to_bnb(usdt_amount, wallet['address'])

            if not success:
                self.send_message("❌ Swap failed!")
                return

            time.sleep(0.5)

            # Place bet
            wallet = self.wallet_manager.get_wallet_balances(wallet)
            bet_amount = wallet['balance_bnb'] * 0.95

            betting_success = self.betting_manager.place_bet(wallet, direction, bet_amount)

            if betting_success:
                success_msg = (
                    f"🎯 <b>BET PLACED!</b>\n\n"
                    f"💱 Swapped: {usdt_amount} USDT\n"
                    f"🎲 Bet:  {direction.upper()} with {bet_amount:.6f} BNB\n"
                    f"👤 Wallet: {wallet['name']}\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_message(success_msg)
            else:
                self.send_message("❌ Bet placement failed!")

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def cmd_show_rewards(self, args):
        """Show claimable rewards"""
        try:
            if not args:
                self.send_message("❌ Usage: /rewards [wallet_number]\nExample: /rewards 1")
                return

            wallet_idx = int(args[0]) - 1

            if wallet_idx < 0 or wallet_idx >= len(self.wallet_manager.wallets):
                self.send_message("❌ Invalid wallet number")
                return

            wallet = self.wallet_manager.wallets[wallet_idx]
            claimable = self.reward_manager.show_claimable_rewards(wallet)

            if not claimable:
                self.send_message(f"🎉 No claimable rewards for {wallet['name']}")
                return

            # Success message sent by show_claimable_rewards

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def cmd_claim(self, args):
        """Claim rewards"""
        try:
            if not args:
                self.send_message("❌ Usage: /claim [wallet_number]\nExample: /claim 1")
                return

            wallet_idx = int(args[0]) - 1

            if wallet_idx < 0 or wallet_idx >= len(self.wallet_manager.wallets):
                self.send_message("❌ Invalid wallet number")
                return

            wallet = self.wallet_manager.wallets[wallet_idx]

            self.send_message(f"🎁 Claiming rewards for {wallet['name']}.. .");

            success = self.reward_manager.claim_rewards(wallet)

            if not success:
                self.send_message("❌ No rewards claimed")

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def cmd_view_orders(self):
        """View all orders with linked relationships"""
        try:
            all_orders = self.limit_order_manager.orders

            if not all_orders:
                self.send_message("📝 No orders found!\n\n💡 Create one with /limit")
                return

            pending = [o for o in all_orders if o['status'] == 'pending']
            waiting = [o for o in all_orders if o['status'] == 'waiting_for_execution']
            executed = [o for o in all_orders if o['status'] == 'executed']
            cancelled = [o for o in all_orders if o['status'] == 'cancelled']

            current_price = self.limit_order_manager.get_bnb_price()

            message = "📋 <b>LIMIT ORDERS</b>\n\n"

            # Active Orders
            if pending:
                message += "🎯 <b>ACTIVE ORDERS: </b>\n"
                for order in pending:
                    trigger_price = order['trigger_price']
                    price_diff = ((trigger_price - current_price) / current_price) * 100 if current_price else 0
                    swap_emoji = "💵→💎" if order['swap_direction'] == 'usdt_to_bnb' else "💎→💵"
                    direction = "⬇️" if price_diff < 0 else "⬆️"

                    message += f"\n{swap_emoji} <b>Order #{order['id']}</b>\n"
                    message += f"🔄 {order['amount_label']} → {order.get('receive_label', 'N/A')}\n"
                    message += f"📊 Current:  ${current_price:.2f}\n"
                    message += f"🎯 Target: ${trigger_price:.2f} {direction} ({price_diff:+.2f}%)\n"

                    # Check for linked TP orders
                    linked_tp = [o for o in waiting if o.get('linked_order_id') == order['id']]
                    if linked_tp:
                        message += f"🔗 Has {len(linked_tp)} TP order(s)\n"

                    message += f"⏰ {order['created_at'][: 19]}\n"

            # Waiting Take-Profit Orders
            if waiting:
                message += "\n⏳ <b>WAITING TAKE-PROFIT: </b>\n"
                for order in waiting:
                    linked_id = order.get('linked_order_id', 'N/A')
                    profit = order.get('profit_target_usdt', 0)
                    swap_emoji = "💵→💎" if order['swap_direction'] == 'usdt_to_bnb' else "💎→💵"

                    message += f"\n{swap_emoji} <b>Order #{order['id']}</b> (TP)\n"
                    message += f"🔗 Linked to Order #{linked_id}\n"
                    message += f"🔄 {order['amount_label']} → {order.get('receive_label', 'N/A')}\n"
                    message += f"🎯 Target: ${order['trigger_price']:.2f}\n"
                    message += f"💰 Profit: ${profit:.2f}\n"

            # Recently Executed (last 3)
            if executed:
                message += f"\n✅ <b>RECENTLY EXECUTED ({len(executed)} total):</b>\n"
                for order in executed[-3:]:
                    exec_price = order.get('execution_price', order['trigger_price'])
                    message += f"✅ #{order['id']}: {order['amount_label']} at ${exec_price:.2f}\n"

            # Summary
            message += f"\n📊 <b>SUMMARY:</b>\n"
            message += f"Active:  {len(pending)} | Waiting: {len(waiting)} | "
            message += f"Executed: {len(executed)} | Cancelled: {len(cancelled)}"

            self.send_message(message)

        except Exception as e:
            self.send_message(f"❌ Error:  {str(e)}")

    def cmd_cancel_order(self, args):
        """Cancel limit order (and any linked TP orders)"""
        try:
            if not args:
                self.send_message("❌ Usage: /cancel [order_id]\nExample: /cancel 5")
                return

            order_id = int(args[0])

            # Find the order first to show preview
            target_order = None
            linked_orders = []

            for order in self.limit_order_manager.orders:
                if order['id'] == order_id:
                    target_order = order
                elif (order.get('linked_order_id') == order_id and
                      order['status'] == 'waiting_for_execution'):
                    linked_orders.append(order)

            if not target_order:
                self.send_message(f"❌ Order #{order_id} not found!")
                return

            if target_order['status'] not in ['pending', 'waiting_for_execution']:
                self.send_message(
                    f"❌ Order #{order_id} cannot be cancelled\n"
                    f"Status:  {target_order['status']}"
                )
                return

            # Show what will be cancelled
            preview_msg = f"⚠️ <b>CANCEL ORDER #{order_id}? </b>\n\n"
            preview_msg += f"📊 {target_order['amount_label']} → {target_order.get('receive_label', 'N/A')}\n"
            preview_msg += f"🎯 Target: ${target_order['trigger_price']:.2f}\n"

            if linked_orders:
                preview_msg += f"\n🔗 <b>LINKED ORDERS (will also cancel):</b>\n"
                for linked in linked_orders:
                    preview_msg += f"   • Order #{linked['id']} (TP)\n"

            if target_order.get('linked_order_id'):
                parent_id = target_order.get('linked_order_id')
                preview_msg += f"\n⚠️ This is a TP order for #{parent_id}\n"

            preview_msg += f"\n❌ This cannot be undone!"

            self.send_message(preview_msg)

            # Execute cancellation
            success = self.limit_order_manager.cancel_order(order_id)

            if success:
                cancelled_count = 1 + len(linked_orders)
                success_msg = f"✅ <b>CANCELLED! </b>\n\n"
                success_msg += f"Order #{order_id}"

                if linked_orders:
                    success_msg += f"\n🔗 + {len(linked_orders)} linked TP order(s)"

                success_msg += f"\n\n📊 Total cancelled: {cancelled_count}"
                self.send_message(success_msg)
            else:
                self.send_message(f"❌ Failed to cancel order #{order_id}")

        except ValueError:
            self.send_message("❌ Invalid order ID!  Use:  /cancel [number]")
        except Exception as e:
            self.send_message(f"❌ Error:  {str(e)}")

    def cmd_empty_wallet(self, args):
        """Empty or send specific amount from wallet"""
        try:
            if not args:
                self.send_message(
                    "❌ Usage:\n/empty [wallet] - Drain all\n/empty [wallet] [amount] - Send specific\n\nExample:\n/empty 1 - Drain wallet 1\n/empty 1 0.5 - Send 0.5 BNB from wallet 1")
                return

            wallet_idx = int(args[0]) - 1

            if wallet_idx < 0 or wallet_idx >= len(self.wallet_manager.wallets):
                self.send_message("❌ Invalid wallet number")
                return

            from mv5 import MAIN_WALLET_ADDRESS

            wallet = self.wallet_manager.wallets[wallet_idx]
            wallet = self.wallet_manager.get_wallet_balances(wallet)

            # Check if amount specified
            if len(args) >= 2:
                # Send specific amount
                try:
                    amount = float(args[1])

                    if amount <= 0:
                        self.send_message("❌ Amount must be positive")
                        return

                    if amount > wallet['balance_bnb']:
                        self.send_message(
                            f"❌ Insufficient balance!\n\n"
                            f"Available: {wallet['balance_bnb']:.6f} BNB\n"
                            f"Requested: {amount:.6f} BNB"
                        )
                        return

                    preview = (
                        f"💸 <b>SEND PREVIEW</b>\n\n"
                        f"👤 From:  {wallet['name']}\n"
                        f"💰 Amount: {amount:.6f} BNB\n"
                        f"📧 To:  Main Wallet\n"
                        f"💵 Remaining: ~{wallet['balance_bnb'] - amount:.6f} BNB\n\n"
                        f"⏳ Processing..."
                    )
                    self.send_message(preview)

                    success = self.wallet_manager.empty_wallet(wallet_idx, MAIN_WALLET_ADDRESS, amount=amount)

                    if not success:
                        self.send_message("❌ Transfer failed!")

                except ValueError:
                    self.send_message("❌ Invalid amount format!")
                    return
            else:
                # Drain all
                self.send_message(f"💀 Draining {wallet['name']} ({wallet['balance_bnb']:.6f} BNB)...")

                success = self.wallet_manager.empty_wallet(wallet_idx, MAIN_WALLET_ADDRESS, amount=None)

                if not success:
                    self.send_message("❌ Drain failed!")

        except Exception as e:
            self.send_message(f"❌ Error:   {str(e)}")

    def cmd_drain_all(self):
        """Drain all wallets"""
        try:
            from mv5 import MAIN_WALLET_ADDRESS, drain_all_wallets

            self.send_message("💀 Draining ALL wallets...")

            drain_all_wallets(self.wallet_manager, MAIN_WALLET_ADDRESS)

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")

    def cmd_create_limit_order(self, args):
        """Create limit order - Interactive wizard"""
        try:
            # Check if we're waiting for confirmation
            if hasattr(self, 'pending_limit_order') and self.pending_limit_order:
                response = ' '.join(args).strip().upper()

                if response == 'YES':
                    # Create the order
                    order_data = self.pending_limit_order
                    order = self.limit_order_manager.create_order(
                        wallet_idx=order_data['wallet_idx'],
                        wallet_name=order_data['wallet_name'],
                        wallet_address=order_data['wallet_address'],
                        swap_direction=order_data['swap_direction'],
                        amount=order_data['amount'],
                        trigger_price=order_data['trigger_price']
                    )

                    if order:
                        self.send_message(
                            f"✅ <b>LIMIT ORDER CREATED!</b>\n\n"
                            f"🆔 Order #{order['id']}\n"
                            f"👤 {order['wallet_name']}\n"
                            f"🔄 {order['amount_label']}\n"
                            f"🎯 Target: ${order['trigger_price']:.2f}\n"
                            f"⚡ Monitoring started!"
                        )
                    else:
                        self.send_message("❌ Failed to create order")

                    # Clear pending order
                    self.pending_limit_order = None
                    return

                elif response == 'NO' or response == '/CANCEL':
                    self.send_message("❌ Order cancelled")
                    self.pending_limit_order = None
                    return

                else:
                    self.send_message("❌ Please reply <b>YES</b> to confirm or <b>NO</b> to cancel")
                    return

            # Start new order creation
            if not args or len(args) < 4:
                # Show interactive wizard
                current_price = self.limit_order_manager.get_bnb_price()

                message = (
                    f"🎯 <b>CREATE LIMIT ORDER</b>\n\n"
                    f"📊 Current BNB: ${current_price:.2f}\n\n"
                    f"Reply with:\n"
                    f"<code>[wallet] [amount] [direction] [target_price]</code>\n\n"
                    f"<b>Examples:</b>\n"
                    f"• <code>1 50 usdt_bnb 900</code> - Buy BNB at $900\n"
                    f"• <code>1 0.5 bnb_usdt 920</code> - Sell BNB at $920\n\n"
                    f"<b>Direction:</b>\n"
                    f"• <code>usdt_bnb</code> = Buy BNB (when price DROPS)\n"
                    f"• <code>bnb_usdt</code> = Sell BNB (when price RISES)\n\n"
                    f"Or send /cancel to cancel"
                )

                self.send_message(message)
                return

            # Parse arguments
            try:
                wallet_idx = int(args[0]) - 1
                amount = float(args[1])
                direction = args[2].lower()
                target_price = float(args[3])
            except (ValueError, IndexError):
                self.send_message(
                    "❌ Invalid format!\n\n"
                    "Use: <code>[wallet] [amount] [direction] [price]</code>\n"
                    "Example:  <code>1 50 usdt_bnb 900</code>"
                )
                return

            # Validate direction
            if direction not in ['usdt_bnb', 'bnb_usdt', 'usdt_to_bnb', 'bnb_to_usdt']:
                self.send_message("❌ Direction must be <code>usdt_bnb</code> or <code>bnb_usdt</code>")
                return

            # Normalize direction
            if direction == 'usdt_bnb':
                direction = 'usdt_to_bnb'
            elif direction == 'bnb_usdt':
                direction = 'bnb_to_usdt'

            # Get wallet
            if wallet_idx < 0 or wallet_idx >= len(self.wallet_manager.wallets):
                self.send_message(f"❌ Invalid wallet number!  Use /wallets to see available wallets")
                return

            wallet = self.wallet_manager.wallets[wallet_idx]
            wallet = self.wallet_manager.get_wallet_balances(wallet)

            # Validate balance with locked funds check
            locked_bnb, locked_usdt = self.limit_order_manager.get_locked_balances(wallet['address'])

            if direction == 'bnb_to_usdt':
                available_bnb = wallet['balance_bnb'] - locked_bnb
                if wallet['balance_bnb'] < amount:
                    self.send_message(
                        f"❌ Insufficient BNB!\n\n"
                        f"Total:  {wallet['balance_bnb']:.6f} BNB\n"
                        f"🔒 Locked:  {locked_bnb:.6f} BNB\n"
                        f"✅ Available: {available_bnb:.6f} BNB\n"
                        f"❌ Needed: {amount:.6f} BNB\n"
                        f"❌ Short by: {amount - available_bnb:.6f} BNB"
                    )
                    return
                amount_label = f"{amount:.6f} BNB"
                expected_usdt = amount * target_price * 0.9995
                receive_label = f"~{expected_usdt:.2f} USDT"
            else:
                available_usdt = wallet['balance_usdt'] - locked_usdt
                if wallet['balance_usdt'] < amount:
                    self.send_message(
                        f"❌ Insufficient USDT!\n\n"
                        f"Total:  {wallet['balance_usdt']:.2f} USDT\n"
                        f"🔒 Locked: {locked_usdt:.2f} USDT\n"
                        f"✅ Available: {available_usdt:.2f} USDT\n"
                        f"❌ Needed: {amount:.2f} USDT\n"
                        f"❌ Short by:  {amount - available_usdt:.2f} USDT"
                    )
                    return
                amount_label = f"{amount:.2f} USDT"
                expected_bnb = amount / target_price * 0.9995
                receive_label = f"~{expected_bnb:.6f} BNB"

            # Get current price
            current_price = self.limit_order_manager.get_bnb_price()
            price_diff = ((target_price - current_price) / current_price) * 100 if current_price else 0

            # Determine direction text
            if direction == 'bnb_to_usdt':
                direction_text = "RISES" if target_price > current_price else "DROPS"
            else:
                direction_text = "DROPS" if target_price < current_price else "RISES"

            # Store pending order
            self.pending_limit_order = {
                'wallet_idx': wallet_idx,
                'wallet_name': wallet['name'],
                'wallet_address': wallet['address'],
                'swap_direction': direction,
                'amount': amount,
                'amount_label': amount_label,
                'receive_label': receive_label,
                'trigger_price': target_price
            }

            # Send preview
            preview_message = (
                f"📋 <b>LIMIT ORDER PREVIEW</b>\n\n"
                f"👤 Wallet: {wallet['name']}\n"
                f"🔄 Order: {amount_label} → {receive_label}\n"
                f"📊 Current: ${current_price:.2f}\n"
                f"🎯 Target:  ${target_price:.2f} ({price_diff:+.2f}%)\n"
                f"⏳ Executes when BNB {direction_text} to ${target_price:.2f}\n"
                f"🤖 Monitored automatically\n\n"
                f"Reply <b>YES</b> to confirm or <b>NO</b> to cancel"
            )

            self.send_message(preview_message)

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
            self.pending_limit_order = None

    def _execute_limit_order_creation(self, args, current_price):
        """Execute limit order creation from parsed arguments"""
        try:
            # Parse:  wallet_number, amount, direction, target_price
            if len(args) < 4:
                self.send_message(
                    "❌ <b>Invalid format! </b>\n\n"
                    "Usage: <code>/limit [wallet] [amount] [direction] [price]</code>\n\n"
                    "Example: <code>/limit 1 50 usdt_bnb 900</code>"
                )
                return False

            wallet_idx = int(args[0]) - 1
            amount = float(args[1])
            direction_input = args[2].lower()
            target_price = float(args[3])

            # Validate direction
            if direction_input in ['usdt_bnb', 'usdt', 'buy']:
                swap_direction = 'usdt_to_bnb'
                direction_label = "USDT→BNB (Buy BNB)"
                amount_label = f"{amount:.2f} USDT"
            elif direction_input in ['bnb_usdt', 'bnb', 'sell']:
                swap_direction = 'bnb_to_usdt'
                direction_label = "BNB→USDT (Sell BNB)"
                amount_label = f"{amount:.6f} BNB"
            else:
                self.send_message(
                    "❌ Invalid direction!\n\n"
                    "Use: <code>usdt_bnb</code> (buy) or <code>bnb_usdt</code> (sell)"
                )
                return False

            # Validate wallet
            if wallet_idx < 0 or wallet_idx >= len(self.wallet_manager.wallets):
                self.send_message(f"❌ Invalid wallet number!  (1-{len(self.wallet_manager.wallets)})")
                return False

            wallet = self.wallet_manager.wallets[wallet_idx]
            wallet = self.wallet_manager.get_wallet_balances(wallet)

            # Validate balance
            if swap_direction == 'usdt_to_bnb':
                if wallet['balance_usdt'] < amount:
                    self.send_message(
                        f"❌ Insufficient USDT!\n\n"
                        f"Have: {wallet['balance_usdt']:.2f} USDT\n"
                        f"Need: {amount:.2f} USDT"
                    )
                    return False
                expected_receive = amount / target_price
                receive_label = f"~{expected_receive:.6f} BNB"
            else:
                if wallet['balance_bnb'] < amount:
                    self.send_message(
                        f"❌ Insufficient BNB!\n\n"
                        f"Have: {wallet['balance_bnb']:.6f} BNB\n"
                        f"Need: {amount:.6f} BNB"
                    )
                    return False
                expected_receive = amount * target_price * 0.9995
                receive_label = f"~{expected_receive:.2f} USDT"

            # Calculate price difference
            price_diff = ((target_price - current_price) / current_price) * 100

            # Determine trigger direction
            if swap_direction == 'bnb_to_usdt':
                trigger_direction = "RISES" if target_price > current_price else "DROPS"
            else:
                trigger_direction = "DROPS" if target_price < current_price else "RISES"

            # Show preview
            preview_msg = (
                f"📋 <b>LIMIT ORDER PREVIEW</b>\n\n"
                f"👤 Wallet: {wallet['name']}\n"
                f"🔄 Order:  {amount_label} → {receive_label}\n"
                f"📊 Current:  ${current_price:.2f}\n"
                f"🎯 Target: ${target_price:.2f} ({price_diff:+.2f}%)\n"
                f"⏳ Executes when BNB {trigger_direction} to ${target_price:.2f}\n"
                f"🤖 Monitored automatically\n\n"
                f"Reply <code>YES</code> to confirm or <code>NO</code> to cancel"
            )
            self.send_message(preview_msg)

            # For now, auto-confirm (you can add state machine for YES/NO)
            # Create the order
            order_id = len(self.limit_order_manager.orders) + 1

            order = {
                'id': order_id,
                'wallet_idx': wallet_idx,
                'wallet_name': wallet['name'],
                'wallet_address': wallet['address'],
                'swap_direction': swap_direction,
                'amount': amount,
                'amount_label': amount_label,
                'trigger_price': target_price,
                'current_price_at_creation': current_price,
                'expected_receive': expected_receive,
                'receive_label': receive_label,
                'created_at': datetime.now().isoformat(),
                'status': 'pending'
            }

            self.limit_order_manager.orders.append(order)
            self.limit_order_manager.save_orders()

            success_msg = (
                f"✅ <b>LIMIT ORDER #{order_id} CREATED!</b>\n\n"
                f"🎯 Will execute when BNB {trigger_direction} to ${target_price:.2f}\n"
                f"⚡ Monitoring in background.. .\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            self.send_message(success_msg)

            return True

        except ValueError:
            self.send_message(
                "❌ Invalid number format!\n\n"
                "Make sure wallet, amount, and price are numbers"
            )
            return False
        except Exception as e:
            self.send_message(f"❌ Error:  {str(e)}")
            return False

    def cmd_create_take_profit(self, args):
        """Create automatic take-profit order"""
        try:
            if len(args) < 2:
                self.send_message(
                    "❌ <b>Usage:</b>\n"
                    "<code>/profit [order_id] [profit_usdt]</code>\n\n"
                    "<b>Example:</b>\n"
                    "<code>/profit 1 4</code> - Make $4 profit on order #1\n\n"
                    "Bot will auto-create reverse order when original executes!"
                )
                return

            order_id = int(args[0])
            profit_usdt = float(args[1])

            if profit_usdt <= 0:
                self.send_message("❌ Profit must be positive!")
                return

            # Find the original order
            original_order = None
            for order in self.limit_order_manager.orders:
                if order['id'] == order_id:
                    original_order = order
                    break

            if not original_order:
                self.send_message(f"❌ Order #{order_id} not found!")
                return

            if original_order['status'] == 'executed':
                self.send_message(f"❌ Order #{order_id} already executed!")
                return

            if original_order['status'] == 'cancelled':
                self.send_message(f"❌ Order #{order_id} was cancelled!")
                return

            # Calculate take-profit details (preview)
            current_price = self.limit_order_manager.get_bnb_price()
            trigger_price = original_order['trigger_price']

            if original_order['swap_direction'] == 'bnb_to_usdt':
                # Original: BNB → USDT
                bnb_amount = original_order['amount']
                expected_usdt = bnb_amount * trigger_price * 0.9995
                usdt_to_swap_back = expected_usdt - profit_usdt
                tp_target_price = (usdt_to_swap_back / bnb_amount) * 0.9995

                tp_direction = 'usdt_to_bnb'
                tp_amount = usdt_to_swap_back
                tp_amount_label = f"{usdt_to_swap_back:.2f} USDT"
                tp_receive_label = f"~{bnb_amount:.6f} BNB"

            else:
                # Original:  USDT → BNB
                usdt_spent = original_order['amount']
                bnb_received = original_order['expected_receive']
                target_usdt = usdt_spent + profit_usdt
                tp_target_price = (target_usdt / bnb_received) * 1.0005

                tp_direction = 'bnb_to_usdt'
                tp_amount = bnb_received
                tp_amount_label = f"{bnb_received:.6f} BNB"
                tp_receive_label = f"~{target_usdt:.2f} USDT"

            # Show preview
            preview_msg = (
                f"🎯 <b>TAKE-PROFIT ORDER PREVIEW</b>\n\n"
                f"📋 <b>Original Order #{order_id}:</b>\n"
                f"🔄 {original_order['amount_label']} → {original_order.get('receive_label', 'N/A')}\n"
                f"🎯 Triggers at: ${trigger_price:.2f}\n"
                f"📊 Status: {original_order['status']}\n\n"
                f"💰 <b>Take-Profit Order:</b>\n"
                f"🔄 {tp_amount_label} → {tp_receive_label}\n"
                f"🎯 Will trigger at: ${tp_target_price:.2f}\n"
                f"💵 Expected Profit: ${profit_usdt:.2f} USDT\n\n"
                f"⚡ <b>Auto-creates when #{order_id} executes! </b>\n"
                f"📊 Slippage buffer: 0.05%"
            )
            self.send_message(preview_msg)

            # Create placeholder take-profit order
            tp_order_id = len(self.limit_order_manager.orders) + 1

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
                'expected_receive': bnb_amount if tp_direction == 'usdt_to_bnb' else target_usdt,
                'receive_label': tp_receive_label,
                'created_at': datetime.now().isoformat(),
                'status': 'waiting_for_execution',
                'linked_order_id': order_id,
                'profit_target_usdt': profit_usdt
            }

            self.limit_order_manager.orders.append(tp_order)
            self.limit_order_manager.save_orders()

            success_msg = (
                f"✅ <b>TAKE-PROFIT ORDER #{tp_order_id} CREATED!</b>\n\n"
                f"⏳ Waiting for Order #{order_id} to execute...\n"
                f"🤖 Will auto-activate when ready\n"
                f"💰 Target profit: ${profit_usdt:.2f} USDT\n"
                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
            )
            self.send_message(success_msg)

        except ValueError:
            self.send_message("❌ Invalid format! Use: <code>/profit [order_id] [profit_usdt]</code>")
        except Exception as e:
            self.send_message(f"❌ Error:  {str(e)}")
            
    def cmd_view_pnl(self):
        """View PnL report"""
        try:
            pnl_data = self.limit_order_manager.calculate_pnl()
            
            if not pnl_data or pnl_data['total_trades'] == 0:
                self.send_message("📊 No completed trades yet!\n\n💡 Complete at least one buy + sell cycle")
                return
            
            win_rate = (pnl_data['successful_trades'] / pnl_data['total_trades']) * 100
            avg_pnl = pnl_data['total_pnl_usdt'] / pnl_data['total_trades']
            
            message = f"💰 <b>PROFIT & LOSS REPORT</b>\n\n"
            message += f"📊 <b>SUMMARY: </b>\n"
            message += f"Total Trades: {pnl_data['total_trades']}\n"
            message += f"Winning:  {pnl_data['successful_trades']} ({win_rate:.1f}%)\n"
            message += f"Volume: ${pnl_data['total_volume_usdt']:.2f}\n"
            message += f"Total PnL: ${pnl_data['total_pnl_usdt']:.2f}\n"
            message += f"Avg PnL: ${avg_pnl:.2f}\n\n"
            
            message += f"📋 <b>RECENT TRADES: </b>\n"
            for i, trade in enumerate(pnl_data['trades'][-5:], 1):  # Last 5
                pnl_emoji = "🟢" if trade['pnl'] > 0 else "🔴"
                message += f"\n{pnl_emoji} Trade #{i}: ${trade['pnl']:.2f} ({trade['pnl_percent']:+.2f}%)\n"
                message += f"   Buy ${trade['buy_price']:.2f} → Sell ${trade['sell_price']:.2f}\n"
            
            self.send_message(message)
            
        except Exception as e:
            self.send_message(f"❌ Error:  {str(e)}")

    def cmd_calculate_atr(self, args):
        """Calculate ATR with optional timeframe parameter"""
        try:
            # Default values
            interval = '1h'
            period = 14

            # Parse arguments if provided
            if args:
                # /atr 1h 14  or  /atr 15m  or  /atr 4h 20
                if len(args) >= 1:
                    interval_input = args[0].lower()
                    # Map common inputs
                    interval_map = {
                        '1m': '1m',
                        '5m': '5m',
                        '15m': '15m',
                        '1h': '1h',
                        '4h': '4h',
                        '1d': '1d'
                    }
                    interval = interval_map.get(interval_input, '1h')

                if len(args) >= 2:
                    try:
                        period = int(args[1])
                        if period < 2 or period > 100:
                            period = 14
                    except:
                        period = 14

            self.send_message(f"📊 Calculating ATR ({interval}, period={period})...")

            # Import the function from mv5
            from mv5 import calculate_bnb_atr

            # Calculate ATR
            atr_data = calculate_bnb_atr(period=period, interval=interval, limit=100)

            if not atr_data:
                self.send_message("❌ Failed to calculate ATR")
                return

            current_price = atr_data['current_price']
            atr_value = atr_data['atr']
            atr_percent = atr_data['atr_percentage']

            # Determine volatility level
            if atr_percent < 2:
                volatility = "🟢 LOW"
                interpretation = "Small price movements"
            elif atr_percent < 4:
                volatility = "🟡 MEDIUM"
                interpretation = "Moderate price movements"
            else:
                volatility = "🔴 HIGH"
                interpretation = "Large price movements"

            # Calculate price range
            price_low = current_price - atr_value
            price_high = current_price + atr_value

            # Build message
            message = f"📊 <b>ATR ANALYSIS (BNB/USDT)</b>\n\n"
            message += f"⏱️ Timeframe: {interval.upper()}\n"
            message += f"📈 Period: {period}\n\n"
            message += f"💰 Current Price: ${current_price:.2f}\n"
            message += f"📊 ATR: ${atr_value:.2f}\n"
            message += f"📊 ATR %: {atr_percent:.2f}%\n\n"
            message += f"🎯 <b>Volatility: {volatility}</b>\n"
            message += f"💡 {interpretation}\n\n"
            message += f"📌 Expected Range:\n"
            message += f"   Low:   ${price_low:.2f}\n"
            message += f"   High: ${price_high:.2f}\n\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"

            self.send_message(message)

        except Exception as e:
            self.send_message(f"❌ Error calculating ATR: {str(e)}")

    def set_bot_commands(self):
        """Set bot command menu (shows in Telegram menu button)"""
        try:
            if not self.token:
                return False

            url = f"https://api.telegram.org/bot{self.token}/setMyCommands"

            commands = [
                {"command": "start", "description": "🏠 Show help menu"},
                {"command": "help", "description": "❓ Show all commands"},

                # Wallets
                {"command": "wallets", "description": "📋 List all wallets"},
                {"command": "balance", "description": "💰 Main wallet balance"},
                {"command": "create", "description": "➕ Create new wallet"},
                {"command": "send", "description": "📤 Send BNB/USDT to address"},

                # Swaps
                {"command": "swap_usdt", "description": "💱 Swap USDT → BNB"},
                {"command": "swap_bnb", "description": "💱 Swap BNB → USDT"},

                # Betting
                {"command": "bet", "description": "🎯 Place bet"},

                # Rewards
                {"command": "rewards", "description": "🎁 Show claimable rewards"},
                {"command": "claim", "description": "💎 Claim rewards"},

                # Limit Orders
                {"command": "limit", "description": "📊 Create limit order"},
                {"command": "profit", "description": "💰 Create take-profit order"},
                {"command": "orders", "description": "📋 View pending orders"},
                {"command": "cancel", "description": "❌ Cancel order"},

                # Utility
                {"command": "price", "description": "💵 Current BNB price"},
                {"command": "atr", "description": "📊 Calculate ATR"},
                {"command": "pnl", "description": "💰 View profit & loss"},
                {"command": "empty", "description": "💸 Empty wallet"},
                {"command": "drain", "description": "💀 Drain all wallets"}
            ]

            payload = {"commands": commands}
            response = requests.post(url, json=payload, timeout=5)

            if response.ok:
                print("✅ Telegram bot menu set successfully!")
                return True
            else:
                print(f"⚠️ Failed to set bot menu: {response.text}")
                return False

        except Exception as e:
            print(f"⚠️ Error setting bot commands: {e}")
            return False

    def cmd_price(self):
        """Show current BNB price using V3 0.05% pool (exact copy from mv5.py)"""
        try:
            from web3 import Web3
            from mv5 import web3, quoter_v2_contract, chainlink_contract, WBNB, USDT_CONTRACT

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

            # Build message
            message = "💎 <b>BNB/USD PRICE</b>\n\n"
            message += f"🥞 V3 0.05% Pool:  ${usdt_out:.2f}\n"

            if chainlink_price:
                message += f"📊 Chainlink: ${chainlink_price:.2f}\n"
                message += f"📈 Difference: ${diff:+.2f} ({diff_pct:+.3f}%)\n"

            message += f"\n✅ Using V3 price:  ${usdt_out:.2f}\n"
            message += f"⏰ {datetime.now().strftime('%H:%M:%S')}"

            self.send_message(message)

        except Exception as e:
            # Fallback to Chainlink
            try:
                from mv5 import chainlink_contract
                chainlink_data = chainlink_contract.functions.latestRoundData().call()
                price = chainlink_data[1] / 1e8

                message = (
                    f"⚠️ <b>BNB/USD PRICE (Chainlink Fallback)</b>\n\n"
                    f"💵 ${price:.2f}\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_message(message)
            except:
                self.send_message(f"❌ All price sources failed!\n{str(e)}")

    def _execute_pending_swap(self):
        """Execute the pending swap after confirmation"""
        try:
            if not self.pending_swap:
                self.send_message("❌ No pending swap found")
                return

            swap_type = self.pending_swap['type']
            amount = self.pending_swap['amount']
            wallet_address = self.pending_swap['wallet_address']

            from web3 import Web3
            from mv5 import (web3, MAIN_PRIVATE_KEY, SMART_ROUTER_ADDRESS,
                             USDT_CONTRACT, WBNB, smart_router_contract,
                             quoter_v2_contract, usdt_contract)

            self.send_message("⏳ Executing swap...")

            if swap_type == 'usdt_to_bnb':
                # USDT → BNB (WITH AUTO-UNWRAP)
                usdt_amount = amount
                usdt_amount_wei = int(usdt_amount * 1e18)

                params_quote = {
                    'tokenIn': Web3.to_checksum_address(USDT_CONTRACT),
                    'tokenOut': Web3.to_checksum_address(WBNB),
                    'amountIn': usdt_amount_wei,
                    'fee': 500,
                    'sqrtPriceLimitX96': 0
                }

                result = quoter_v2_contract.functions.quoteExactInputSingle(params_quote).call()
                expected_bnb = result[0] / 1e18

                # Check allowance
                allowance = usdt_contract.functions.allowance(wallet_address, SMART_ROUTER_ADDRESS).call()

                if allowance < usdt_amount_wei:
                    self.send_message("🔓 Approving USDT...")
                    nonce = web3.eth.get_transaction_count(wallet_address)

                    approve_tx = usdt_contract.functions.approve(
                        SMART_ROUTER_ADDRESS, usdt_amount_wei * 2
                    ).build_transaction({
                        'from': wallet_address,
                        'gas': 100000,
                        'gasPrice': web3.to_wei('3', 'gwei'),
                        'nonce': nonce,
                        'chainId': 56
                    })

                    signed_tx = web3.eth.account.sign_transaction(approve_tx, MAIN_PRIVATE_KEY)
                    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    web3.eth.wait_for_transaction_receipt(tx_hash)
                    self.send_message("✅ Approval confirmed!")

                # Execute swap
                min_bnb_out = int(expected_bnb * 0.9995 * 1e18)
                nonce = web3.eth.get_transaction_count(wallet_address)

                swap_params = {
                    'tokenIn': Web3.to_checksum_address(USDT_CONTRACT),
                    'tokenOut': Web3.to_checksum_address(WBNB),
                    'fee': 500,
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

                signed_tx = web3.eth.account.sign_transaction(swap_tx, MAIN_PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

                self.send_message(f"⏳ Swap TX:  {web3.to_hex(tx_hash)[:16]}...")

                receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status == 1:
                    # ✅ NOW UNWRAP WBNB → BNB
                    self.send_message("🔄 Unwrapping WBNB → BNB...")

                    # WBNB contract (withdraw function)
                    wbnb_abi = [
                        {
                            "constant": False,
                            "inputs": [{"name": "wad", "type": "uint256"}],
                            "name": "withdraw",
                            "outputs": [],
                            "stateMutability": "nonpayable",
                            "type": "function"
                        }
                    ]

                    wbnb_contract = web3.eth.contract(
                        address=Web3.to_checksum_address(WBNB),
                        abi=wbnb_abi
                    )

                    # Get WBNB balance
                    wbnb_balance_abi = [
                        {
                            "constant": True,
                            "inputs": [{"name": "_owner", "type": "address"}],
                            "name": "balanceOf",
                            "outputs": [{"name": "balance", "type": "uint256"}],
                            "type": "function"
                        }
                    ]

                    wbnb_contract_balance = web3.eth.contract(
                        address=Web3.to_checksum_address(WBNB),
                        abi=wbnb_balance_abi
                    )

                    wbnb_balance = wbnb_contract_balance.functions.balanceOf(wallet_address).call()

                    if wbnb_balance > 0:
                        nonce = web3.eth.get_transaction_count(wallet_address)

                        unwrap_tx = wbnb_contract.functions.withdraw(wbnb_balance).build_transaction({
                            'from': wallet_address,
                            'gas': 50000,
                            'gasPrice': web3.to_wei('3', 'gwei'),
                            'nonce': nonce,
                            'chainId': 56,
                            'value': 0
                        })

                        signed_unwrap = web3.eth.account.sign_transaction(unwrap_tx, MAIN_PRIVATE_KEY)
                        unwrap_hash = web3.eth.send_raw_transaction(signed_unwrap.raw_transaction)

                        unwrap_receipt = web3.eth.wait_for_transaction_receipt(unwrap_hash)

                        if unwrap_receipt.status == 1:
                            success_msg = (
                                f"✅ <b>SWAP COMPLETED!</b>\n\n"
                                f"💱 {usdt_amount:.2f} USDT → {expected_bnb:.6f} BNB\n"
                                f"🔄 Auto-unwrapped WBNB → BNB\n"
                                f"🔗 Swap: <a href='https://bscscan.com/tx/{web3.to_hex(tx_hash)}'>View</a>\n"
                                f"🔗 Unwrap: <a href='https://bscscan.com/tx/{web3.to_hex(unwrap_hash)}'>View</a>\n"
                                f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                            )
                            self.send_message(success_msg)
                        else:
                            self.send_message(
                                "⚠️ Swap succeeded but unwrap failed.  Use /unwrap to convert WBNB manually.")
                    else:
                        success_msg = (
                            f"✅ <b>SWAP COMPLETED!</b>\n\n"
                            f"💱 {usdt_amount:.2f} USDT → {expected_bnb:.6f} BNB\n"
                            f"🔗 <a href='https://bscscan.com/tx/{web3.to_hex(tx_hash)}'>View TX</a>\n"
                            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                        )
                        self.send_message(success_msg)
                else:
                    self.send_message("❌ Swap failed!")

            elif swap_type == 'bnb_to_usdt':
                # BNB → USDT (unchanged)
                bnb_amount = amount
                bnb_amount_wei = int(bnb_amount * 1e18)

                params_quote = {
                    'tokenIn': Web3.to_checksum_address(WBNB),
                    'tokenOut': Web3.to_checksum_address(USDT_CONTRACT),
                    'amountIn': bnb_amount_wei,
                    'fee': 500,
                    'sqrtPriceLimitX96': 0
                }

                result = quoter_v2_contract.functions.quoteExactInputSingle(params_quote).call()
                expected_usdt = result[0] / 1e18

                # Execute swap
                min_usdt_out = int(expected_usdt * 0.9995 * 1e18)
                nonce = web3.eth.get_transaction_count(wallet_address)

                swap_params = {
                    'tokenIn': Web3.to_checksum_address(WBNB),
                    'tokenOut': Web3.to_checksum_address(USDT_CONTRACT),
                    'fee': 500,
                    'recipient': wallet_address,
                    'amountIn': bnb_amount_wei,
                    'amountOutMinimum': min_usdt_out,
                    'sqrtPriceLimitX96': 0
                }

                swap_tx = smart_router_contract.functions.exactInputSingle(swap_params).build_transaction({
                    'from': wallet_address,
                    'value': bnb_amount_wei,
                    'gas': 300000,
                    'gasPrice': web3.to_wei('3', 'gwei'),
                    'nonce': nonce,
                    'chainId': 56
                })

                signed_tx = web3.eth.account.sign_transaction(swap_tx, MAIN_PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

                self.send_message(f"⏳ TX: {web3.to_hex(tx_hash)[:16]}...")

                receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status == 1:
                    success_msg = (
                        f"✅ <b>SWAP COMPLETED!</b>\n\n"
                        f"💱 {bnb_amount:.6f} BNB → {expected_usdt:.2f} USDT\n"
                        f"🔗 <a href='https://bscscan.com/tx/{web3.to_hex(tx_hash)}'>View TX</a>\n"
                        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                    )
                    self.send_message(success_msg)
                else:
                    self.send_message("❌ Swap failed!")

        except Exception as e:
            self.send_message(f"❌ Execution error: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def cmd_send(self, args):
        """Send BNB or USDT to external address"""
        try:
            if len(args) < 3:
                self.send_message(
                    "❌ <b>Usage:</b>\n"
                    "<code>/send [bnb|usdt] [amount] [address]</code>\n\n"
                    "<b>Examples:</b>\n"
                    "<code>/send bnb 0.5 0x742d35... </code>\n"
                    "<code>/send usdt 100 0x742d35...</code>\n"
                    "<code>/send bnb all 0x742d35...</code>"
                )
                return
            
            currency = args[0].lower()
            amount_input = args[1]. lower()
            recipient_input = args[2]
            
            # Validate currency
            if currency not in ['bnb', 'usdt']: 
                self.send_message("❌ Currency must be 'bnb' or 'usdt'")
                return
            
            is_bnb = (currency == 'bnb')
            
            # Validate address
            from web3 import Web3
            try:
                recipient_address = Web3.to_checksum_address(recipient_input)
            except: 
                self.send_message("❌ Invalid address format!")
                return
            
            # Get balances
            from mv5 import web3, MAIN_WALLET_ADDRESS, usdt_contract
            
            main_address = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)
            bnb_balance = web3.eth. get_balance(main_address) / 1e18
            usdt_balance = usdt_contract.functions.balanceOf(main_address).call() / 1e18
            
            available_balance = bnb_balance if is_bnb else usdt_balance
            
            # Parse amount
            if amount_input == 'all': 
                if is_bnb:
                    gas_fee = 0.0001
                    if available_balance <= gas_fee:
                        self.send_message("❌ Insufficient balance for gas fee")
                        return
                    amount = available_balance - gas_fee
                else: 
                    amount = available_balance
            else:
                try: 
                    amount = float(amount_input)
                except ValueError: 
                    self.send_message("❌ Invalid amount!")
                    return
            
            # Validate amount
            if amount <= 0:
                self. send_message("❌ Amount must be positive")
                return
            
            if is_bnb:
                gas_fee = 0.0001
                if amount + gas_fee > available_balance:
                    self.send_message(
                        f"❌ Insufficient balance!\n\n"
                        f"Available: {available_balance:.6f} BNB\n"
                        f"Needed: {amount:.6f} + ~{gas_fee:.4f} gas"
                    )
                    return
            else: 
                if amount > available_balance: 
                    self.send_message(
                        f"❌ Insufficient balance!\n\n"
                        f"Available:  {available_balance:.2f} USDT\n"
                        f"Requested: {amount:.2f} USDT"
                    )
                    return
            
            # Show preview and execute
            preview = (
                f"📤 <b>TRANSFER PREVIEW</b>\n\n"
                f"💰 Amount: {amount:.6f if is_bnb else amount:.2f} {currency. upper()}\n"
                f"📥 To: {recipient_address[: 10]}...{recipient_address[-8:]}\n"
                f"💵 Gas:  ~0.0001 BNB\n\n"
                f"⏳ Processing..."
            )
            self.send_message(preview)
            
            # Execute transfer
            from mv5 import MAIN_PRIVATE_KEY
            
            if is_bnb: 
                # Send BNB
                nonce = web3.eth.get_transaction_count(main_address)
                
                tx = {
                    'to':  recipient_address,
                    'value': web3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': web3.to_wei('3', 'gwei'),
                    'nonce': nonce,
                    'chainId':  56
                }
                
                signed_tx = web3.eth.account.sign_transaction(tx, MAIN_PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                self.send_message(f"⏳ TX:  {web3.to_hex(tx_hash)[:16]}...")
                
                receipt = web3.eth. wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    success_msg = (
                        f"✅ <b>BNB TRANSFER COMPLETE!</b>\n\n"
                        f"💰 Amount: {amount:.6f} BNB\n"
                        f"📥 To: {recipient_address[:10]}...{recipient_address[-8:]}\n"
                        f"🔗 <a href='https://bscscan.com/tx/{web3.to_hex(tx_hash)}'>View TX</a>\n"
                        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                    )
                    self.send_message(success_msg)
                else:
                    self.send_message("❌ Transfer failed!")
            
            else:
                # Send USDT
                amount_wei = int(amount * 1e18)
                nonce = web3.eth.get_transaction_count(main_address)
                
                transfer_tx = usdt_contract.functions.transfer(
                    recipient_address,
                    amount_wei
                ).build_transaction({
                    'from': main_address,
                    'gas': 100000,
                    'gasPrice':  web3.to_wei('3', 'gwei'),
                    'nonce': nonce,
                    'chainId': 56
                })
                
                signed_tx = web3.eth.account.sign_transaction(transfer_tx, MAIN_PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_tx. raw_transaction)
                
                self.send_message(f"⏳ TX: {web3.to_hex(tx_hash)[:16]}...")
                
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    success_msg = (
                        f"✅ <b>USDT TRANSFER COMPLETE!</b>\n\n"
                        f"💰 Amount: {amount:.2f} USDT\n"
                        f"📥 To: {recipient_address[:10]}...{recipient_address[-8:]}\n"
                        f"🔗 <a href='https://bscscan.com/tx/{web3.to_hex(tx_hash)}'>View TX</a>\n"
                        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                    )
                    self. send_message(success_msg)
                else:
                    self.send_message("❌ Transfer failed!")
        
        except Exception as e:
            self. send_message(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

    def cmd_unwrap(self, args=None):
        """Unwrap WBNB to native BNB from any wallet"""
        try:
            from web3 import Web3
            from mv5 import web3, WBNB

            # Check if wallet specified
            if args and len(args) > 0:
                try:
                    wallet_idx = int(args[0]) - 1

                    if wallet_idx < 0 or wallet_idx >= len(self.wallet_manager.wallets):
                        self.send_message("❌ Invalid wallet number!")
                        return

                    wallet = self.wallet_manager.wallets[wallet_idx]
                    wallet_address = Web3.to_checksum_address(wallet['address'])
                    private_key = wallet['private_key']
                    wallet_name = wallet['name']

                except ValueError:
                    self.send_message("❌ Invalid wallet number format!")
                    return
            else:
                # No wallet specified - check main wallet
                from mv5 import MAIN_WALLET_ADDRESS, MAIN_PRIVATE_KEY
                wallet_address = Web3.to_checksum_address(MAIN_WALLET_ADDRESS)
                private_key = MAIN_PRIVATE_KEY
                wallet_name = "Main Wallet"

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
            wbnb_balance_human = wbnb_balance / 1e18

            if wbnb_balance == 0:
                self.send_message(f"✅ No WBNB in {wallet_name}!\n\n💡 Try: /checkwbnb to see all wallets")
                return

            self.send_message(f"🔄 Unwrapping {wbnb_balance_human:.6f} WBNB from {wallet_name}...")

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
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

            self.send_message(f"⏳ TX:  {web3.to_hex(tx_hash)[:16]}...")

            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt.status == 1:
                success_msg = (
                    f"✅ <b>UNWRAP COMPLETED!</b>\n\n"
                    f"👤 {wallet_name}\n"
                    f"🔄 {wbnb_balance_human:.6f} WBNB → BNB\n"
                    f"🔗 <a href='https://bscscan.com/tx/{web3.to_hex(tx_hash)}'>View TX</a>\n"
                    f"⏰ {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_message(success_msg)
            else:
                self.send_message("❌ Unwrap failed!")

        except Exception as e:
            self.send_message(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()