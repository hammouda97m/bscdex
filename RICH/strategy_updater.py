#!/usr/bin/env python3
"""
Strategy Updater Tool
Allows switching between contrarian and consensus betting strategies
by updating the enhanced_decision_logic function in your main bot file.
"""

import os
import re
import shutil
from datetime import datetime


class StrategyUpdater:
    def __init__(self, target_files=None):
        if target_files is None:
            # Auto-detect all fin*.py files
            self.target_files = []
            for i in range(1, 13):  # fin1.py to fin12.py
                filename = f"fin{i}.py"
                if os.path.exists(filename):
                    self.target_files.append(filename)

            if not self.target_files:
                print("❌ No fin*.py files found in current directory!")
        else:
            self.target_files = target_files if isinstance(target_files, list) else [target_files]

        # Store the contrarian strategy code
        self.contrarian_code = '''def enhanced_decision_logic(bet_data, ml_score):
    """
    UPDATED: Enhanced decision making based on new 10k rounds analysis
    MODIFIED: Now bets AGAINST whales and AGAINST bet ratio patterns
    """

    bull_amount = bet_data["bull_amount"]
    bear_amount = bet_data["bear_amount"]
    total_amount = bet_data["total_amount"]
    bull_payout = bet_data["bull_payout"]
    bear_payout = bet_data["bear_payout"]
    whale_bet_side = bet_data["whale_bet_side"]
    max_bet_on_bull = bet_data["max_bet_on_bull"]
    max_bet_on_bear = bet_data["max_bet_on_bear"]

    # Calculate bet ratio
    bet_ratio = bull_amount / bear_amount if bear_amount > 0 else 2.0

    # Priority 1: SMART whale logic - Follow whale UNLESS ML very weak OR skip active
    if whale_bet_side and skip_rounds_remaining == 0:  # ONLY if not skipping rounds
        if abs(ml_score) <= 0.08:  # ML very weak = bet against whale
            opposite_side = "bear" if whale_bet_side == "bull" else "bull" #<----- HERE YOU CONTROL IF YOU WANNA CONTRARIAN OR FOLLOW
            confidence = "HIGH (Against whale - ML too weak)"
            return opposite_side, confidence
        else:  # ML confident = follow whale
            #same_side = "bear" if whale_bet_side == "bull" else "bull"     #<-------- If you wanna filp, comment this and uncomment the lower one.
            same_side = whale_bet_side  # "bull" or "bear"
            confidence = "HIGH (Follow whale - ML agrees)"
            return same_side, confidence


    # Priority 2: MODIFIED - FLIPPED BETTING LOGIC (bet against the patterns)
    if total_amount > 1.5 and skip_rounds_remaining == 0 and abs(bull_payout - bear_payout) >= 1.2:

        # FLIPPED LOGIC: Bet against the bet ratio + large bet patterns
        payout_decision = None

        # FLIPPED: When bet_ratio > 0.5 AND large bet on bull >= 0.8 BNB -> bet BEAR
        if bet_ratio > BEAR_WIN_BET_RATIO and max_bet_on_bull >= 0.7:
            payout_decision = "bear"  # FLIP here
        # FLIPPED: When bet_ratio < 0.5 AND large bet on bear >= 0.8 BNB -> bet BULL
        elif bet_ratio < BULL_WIN_BET_RATIO and max_bet_on_bear >= 0.7:
            payout_decision = "bull"  # FLIP here
        else:
            payout_decision = None  # No clear edge

        # Get ML-based decision (require stronger threshold for agreement)
        ml_decision = None
        if ml_score > 0.05:  # ML suggests bull (UPDATED from 0.05)
            ml_decision = "bull" #<------------- FLIP HERE
        elif ml_score < -0.05:  # ML suggests bear (UPDATED from -0.05)
            ml_decision = "bear" #<------------- FLIP HERE

        # REQUIRE BOTH TO AGREE - Skip if they disagree or no payout decision
        if payout_decision and payout_decision == ml_decision:
            # Both methods agree! Now check time-based confidence boost
            current_hour = datetime.now().hour
            # Get hours with top/bottom bull win rates from HOURLY_BULL_RATES
            good_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate >= 0.6]
            bad_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate <= 0.4]

            base_confidence = "HIGH" if abs(ml_score) > 0.3 else "MEDIUM"

            # NEW: Add streak information to confidence (with validation)
            streak_info = ""
            if current_streak >= 7:
                current_epoch = bet_data.get("current_epoch", 0)
                if should_use_streak_for_ml(current_epoch):
                    streak_emoji = "🟢" if current_streak_type == "BULL" else "🔴"
                    streak_info = f" + {streak_emoji}Streak x{current_streak}"
                else:
                    streak_info = f" + ❌Streak x{current_streak} (Invalid)"

            # Time-based confidence adjustments
            if payout_decision == "bull":
                if current_hour in good_bull_hours:
                    confidence = f"HIGH (Against bet ratio {bet_ratio:.2f} + ML + Good bull hour {current_hour}{streak_info})"
                elif current_hour in bad_bull_hours:
                    confidence = f"MEDIUM (Against bet ratio {bet_ratio:.2f} + ML, but bad bull hour {current_hour}{streak_info})"
                else:
                    confidence = f"{base_confidence} (Against bet ratio {bet_ratio:.2f} + ML consensus{streak_info})"
            else:  # bear decision
                if current_hour in bad_bull_hours:
                    confidence = f"HIGH (Against bet ratio {bet_ratio:.2f} + ML + Bad bull hour {current_hour}{streak_info})"
                elif current_hour in good_bull_hours:
                    confidence = f"MEDIUM (Against bet ratio {bet_ratio:.2f} + ML, but good bull hour {current_hour}{streak_info})"
                else:
                    confidence = f"{base_confidence} (Against bet ratio {bet_ratio:.2f} + ML consensus{streak_info})"

            return payout_decision, confidence

        else:
            # Methods disagree or no clear payout edge - SKIP
            if payout_decision is None:
                return None, f"SKIP (No clear bet ratio edge: {bet_ratio:.2f}, max bull: {max_bet_on_bull:.3f}, max bear: {max_bet_on_bear:.3f})"
            elif ml_decision is None:
                return None, f"SKIP (Bet ratio says {payout_decision}, but ML neutral: {ml_score:.3f})"
            else:
                return None, f"SKIP (Bet ratio says {payout_decision}, ML says {ml_decision})"

    # Priority 3: Pure ML decision (only for very strong signals) - UNCHANGED
    if abs(ml_score) > 0.2:  # Very strong ML signal
        decision = "bull" if ml_score > 0 else "bear" #<----------------------- FLIP HERE
        streak_info = ""
        if current_streak >= 6:
            current_epoch = bet_data.get("current_epoch", 0)
            if should_use_streak_for_ml(current_epoch):
                streak_emoji = "🟢" if current_streak_type == "BULL" else "🔴"
                streak_info = f" + {streak_emoji}Streak x{current_streak}"
            else:
                streak_info = f" + ❌Streak x{current_streak} (Invalid)"
        return decision, f"MEDIUM (Very strong ML signal: {ml_score:.3f}{streak_info})"

    # Priority 4: Time + Large bet combination (more restrictive) - UNCHANGED
    if total_amount > 2.0:  # Decent pool size
        current_hour = datetime.now().hour
        good_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate >= 0.6]
        bad_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate <= 0.4]

        # Enhanced with large bet detection
        if current_hour in good_bull_hours and ml_score > 0.15 and max_bet_on_bull >= 1.0:
            return "bull", f"LOW (Good bull hour {current_hour} + ML + Large bull bet {max_bet_on_bull:.3f})" #<---------- FLIP HERE
        elif current_hour in bad_bull_hours and ml_score < -0.15 and max_bet_on_bear >= 1.0:
            return "bear", f"LOW (Bad bull hour {current_hour} + ML + Large bear bet {max_bet_on_bear:.3f})"  #<---------- FLIP HERE

    return None, f"No edge detected (ratio: {bet_ratio:.2f}, ML: {ml_score:.3f})"'''

        # Store the consensus strategy code
        self.consensus_code = '''def enhanced_decision_logic(bet_data, ml_score):
    """
    UPDATED: Enhanced decision making based on new 10k rounds analysis
    MODIFIED: Now bets AGAINST whales and AGAINST bet ratio patterns
    """

    bull_amount = bet_data["bull_amount"]
    bear_amount = bet_data["bear_amount"]
    total_amount = bet_data["total_amount"]
    bull_payout = bet_data["bull_payout"]
    bear_payout = bet_data["bear_payout"]
    whale_bet_side = bet_data["whale_bet_side"]
    max_bet_on_bull = bet_data["max_bet_on_bull"]
    max_bet_on_bear = bet_data["max_bet_on_bear"]

    # Calculate bet ratio
    bet_ratio = bull_amount / bear_amount if bear_amount > 0 else 2.0

    # Priority 1: SMART whale logic - Follow whale UNLESS ML very weak OR skip active
    if whale_bet_side and skip_rounds_remaining == 0:  # ONLY if not skipping rounds
        if abs(ml_score) <= 0.08:  # ML very weak = bet against whale
            opposite_side = "bear" if whale_bet_side == "bear" else "bull"
            confidence = "HIGH (Against whale - ML too weak)"
            return opposite_side, confidence
        else:  # ML confident = follow whale
            #same_side = "bear" if whale_bet_side == "bull" else "bull"     #<-------- If you wanna filp, comment this and uncomment the lower one.
            same_side = whale_bet_side  # "bull" or "bear"
            confidence = "HIGH (Follow whale - ML agrees)"
            return same_side, confidence


    # Priority 2: MODIFIED - FLIPPED BETTING LOGIC (bet against the patterns)
    if total_amount > 1.5 and skip_rounds_remaining == 0 and abs(bull_payout - bear_payout) >= 1.2:

        # FLIPPED LOGIC: Bet against the bet ratio + large bet patterns
        payout_decision = None

        # FLIPPED: When bet_ratio > 0.5 AND large bet on bull >= 0.8 BNB -> bet BEAR
        if bet_ratio > BEAR_WIN_BET_RATIO and max_bet_on_bull >= 0.7:
            payout_decision = "bull"  # FLIP here
        # FLIPPED: When bet_ratio < 0.5 AND large bet on bear >= 0.8 BNB -> bet BULL
        elif bet_ratio < BULL_WIN_BET_RATIO and max_bet_on_bear >= 0.7:
            payout_decision = "bear"  # FLIP here
        else:
            payout_decision = None  # No clear edge

        # Get ML-based decision (require stronger threshold for agreement)
        ml_decision = None
        if ml_score > 0.05:  # ML suggests bull (UPDATED from 0.05)
            ml_decision = "bear"
        elif ml_score < -0.05:  # ML suggests bear (UPDATED from -0.05)
            ml_decision = "bull"

        # REQUIRE BOTH TO AGREE - Skip if they disagree or no payout decision
        if payout_decision and payout_decision == ml_decision: #<---------------- ML IS EFFECTIVE
        #if payout_decision:                         #<---------------- ML IS COMPLETELY INEFFECTIVE
            # Both methods agree! Now check time-based confidence boost
            current_hour = datetime.now().hour
            # Get hours with top/bottom bull win rates from HOURLY_BULL_RATES
            good_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate >= 0.6]
            bad_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate <= 0.4]

            base_confidence = "HIGH" if abs(ml_score) > 0.3 else "MEDIUM"

            # NEW: Add streak information to confidence (with validation)
            streak_info = ""
            if current_streak >= 7:
                current_epoch = bet_data.get("current_epoch", 0)
                if should_use_streak_for_ml(current_epoch):
                    streak_emoji = "🟢" if current_streak_type == "BULL" else "🔴"
                    streak_info = f" + {streak_emoji}Streak x{current_streak}"
                else:
                    streak_info = f" + ❌Streak x{current_streak} (Invalid)"

            # Time-based confidence adjustments
            if payout_decision == "bull":
                if current_hour in good_bull_hours:
                    confidence = f"HIGH (Against bet ratio {bet_ratio:.2f} + ML + Good bull hour {current_hour}{streak_info})"
                elif current_hour in bad_bull_hours:
                    confidence = f"MEDIUM (Against bet ratio {bet_ratio:.2f} + ML, but bad bull hour {current_hour}{streak_info})"
                else:
                    confidence = f"{base_confidence} (Against bet ratio {bet_ratio:.2f} + ML consensus{streak_info})"
            else:  # bear decision
                if current_hour in bad_bull_hours:
                    confidence = f"HIGH (Against bet ratio {bet_ratio:.2f} + ML + Bad bull hour {current_hour}{streak_info})"
                elif current_hour in good_bull_hours:
                    confidence = f"MEDIUM (Against bet ratio {bet_ratio:.2f} + ML, but good bull hour {current_hour}{streak_info})"
                else:
                    confidence = f"{base_confidence} (Against bet ratio {bet_ratio:.2f} + ML consensus{streak_info})"

            return payout_decision, confidence

        else:
            # Methods disagree or no clear payout edge - SKIP
            if payout_decision is None:
                return None, f"SKIP (No clear bet ratio edge: {bet_ratio:.2f}, max bull: {max_bet_on_bull:.3f}, max bear: {max_bet_on_bear:.3f})"
            elif ml_decision is None:
                return None, f"SKIP (Bet ratio says {payout_decision}, but ML neutral: {ml_score:.3f})"
            else:
                return None, f"SKIP (Bet ratio says {payout_decision}, ML says {ml_decision})"

    # Priority 3: Pure ML decision (only for very strong signals) - UNCHANGED
    if abs(ml_score) > 0.2:  # Very strong ML signal
        decision = "bear" if ml_score > 0 else "bull"
        streak_info = ""
        if current_streak >= 6:
            current_epoch = bet_data.get("current_epoch", 0)
            if should_use_streak_for_ml(current_epoch):
                streak_emoji = "🟢" if current_streak_type == "BULL" else "🔴"
                streak_info = f" + {streak_emoji}Streak x{current_streak}"
            else:
                streak_info = f" + ❌Streak x{current_streak} (Invalid)"
        return decision, f"MEDIUM (Very strong ML signal: {ml_score:.3f}{streak_info})"

    # Priority 4: Time + Large bet combination (more restrictive) - UNCHANGED
    if total_amount > 2.0:  # Decent pool size
        current_hour = datetime.now().hour
        good_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate >= 0.6]
        bad_bull_hours = [h for h, rate in HOURLY_BULL_RATES.items() if rate <= 0.4]

        # Enhanced with large bet detection
        if current_hour in good_bull_hours and ml_score > 0.15 and max_bet_on_bull >= 1.0:
            return "bear", f"LOW (Good bull hour {current_hour} + ML + Large bull bet {max_bet_on_bull:.3f})"
        elif current_hour in bad_bull_hours and ml_score < -0.15 and max_bet_on_bear >= 1.0:
            return "bull", f"LOW (Bad bull hour {current_hour} + ML + Large bear bet {max_bet_on_bear:.3f})"

    return None, f"No edge detected (ratio: {bet_ratio:.2f}, ML: {ml_score:.3f})"'''

    def create_backup(self, target_file):
        """Create a backup of the original file in the backup folder"""
        if os.path.exists(target_file):
            # Create backup directory if it doesn't exist
            backup_dir = "backup"
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{target_file}.backup_{timestamp}"
            backup_file = os.path.join(backup_dir, backup_filename)

            shutil.copy2(target_file, backup_file)
            print(f"✅ Backup created: {backup_file}")
            return backup_file
        else:
            print(f"❌ Target file {target_file} not found!")
            return None

    def find_function_bounds(self, content):
        """Find the start and end positions of the enhanced_decision_logic function"""
        # Pattern to match the function definition
        pattern = r'def enhanced_decision_logic\(bet_data, ml_score\):'
        match = re.search(pattern, content)

        if not match:
            return None, None

        start_pos = match.start()

        # Find the end of the function by looking for the next function definition
        # or the end of the file
        lines = content[start_pos:].split('\n')

        # Count indentation of the function definition
        func_line = lines[0]
        base_indent = len(func_line) - len(func_line.lstrip())

        end_line = 1
        for i, line in enumerate(lines[1:], 1):
            # Skip empty lines and comments
            if line.strip() == '' or line.strip().startswith('#'):
                continue

            # Check indentation - if it's at the same level or less, we've found the end
            current_indent = len(line) - len(line.lstrip()) if line.strip() else float('inf')

            if current_indent <= base_indent and line.strip():
                end_line = i
                break
        else:
            # Function goes to end of file
            end_line = len(lines)

        # Calculate absolute end position
        end_pos = start_pos + len('\n'.join(lines[:end_line]))

        return start_pos, end_pos

    def update_strategy(self, strategy_type, selected_files=None):
        """Update the strategy in the target files"""
        files_to_update = selected_files if selected_files else self.target_files

        if not files_to_update:
            print("❌ No files specified for update!")
            return False

        success_count = 0
        failed_files = []

        for target_file in files_to_update:
            print(f"\n🔄 Processing {target_file}...")

            if not os.path.exists(target_file):
                print(f"❌ File {target_file} not found!")
                failed_files.append(target_file)
                continue

            # Create backup first
            backup_file = self.create_backup(target_file)
            if not backup_file:
                failed_files.append(target_file)
                continue

            try:
                # Read the current file
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find the function bounds
                start_pos, end_pos = self.find_function_bounds(content)

                if start_pos is None or end_pos is None:
                    print(f"❌ Could not find enhanced_decision_logic function in {target_file}!")
                    failed_files.append(target_file)
                    continue

                # Choose the appropriate strategy code
                if strategy_type.lower() == 'contrarian':
                    new_function = self.contrarian_code
                    strategy_name = "CONTRARIAN"
                elif strategy_type.lower() == 'consensus':
                    new_function = self.consensus_code
                    strategy_name = "CONSENSUS"
                else:
                    print("❌ Invalid strategy type! Use 'contrarian' or 'consensus'")
                    return False

                # Replace the function
                new_content = content[:start_pos] + new_function + content[end_pos:]

                # Write the updated content back to the file
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print(f"✅ {target_file} updated to {strategy_name} strategy!")
                success_count += 1

            except Exception as e:
                print(f"❌ Error updating {target_file}: {e}")
                # Restore from backup if something went wrong
                if backup_file and os.path.exists(backup_file):
                    shutil.copy2(backup_file, target_file)
                    print(f"🔄 Restored {target_file} from backup")
                failed_files.append(target_file)

        # Summary
        print(f"\n📊 Update Summary:")
        print(f"✅ Successfully updated: {success_count} files")
        if failed_files:
            print(f"❌ Failed to update: {len(failed_files)} files ({', '.join(failed_files)})")

        return success_count > 0

    def show_current_strategy(self):
        """Analyze the current strategy in all files"""
        if not self.target_files:
            print("❌ No target files found!")
            return

        print(f"\n📊 Strategy Status for {len(self.target_files)} files:")
        print("-" * 50)

        contrarian_count = 0
        consensus_count = 0
        unknown_count = 0

        for target_file in self.target_files:
            if not os.path.exists(target_file):
                print(f"❌ {target_file}: FILE NOT FOUND")
                unknown_count += 1
                continue

            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for key indicators to determine strategy
                if 'opposite_side = "bear" if whale_bet_side == "bull" else "bull"' in content:
                    print(f"🔴 {target_file}: CONTRARIAN")
                    contrarian_count += 1
                elif 'opposite_side = "bear" if whale_bet_side == "bear" else "bull"' in content:
                    print(f"🔵 {target_file}: CONSENSUS")
                    consensus_count += 1
                else:
                    print(f"❓ {target_file}: UNKNOWN/MIXED")
                    unknown_count += 1

            except Exception as e:
                print(f"❌ {target_file}: ERROR - {e}")
                unknown_count += 1

        print("-" * 50)
        print(f"📈 Summary: {contrarian_count} Contrarian | {consensus_count} Consensus | {unknown_count} Unknown/Error")

    def select_files_menu(self):
        """Interactive menu to select which files to update"""
        if not self.target_files:
            return []

        print(f"\n📁 Available files:")
        for i, file in enumerate(self.target_files, 1):
            # Quick check for current strategy
            strategy = "❓"
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'opposite_side = "bear" if whale_bet_side == "bull" else "bull"' in content:
                    strategy = "🔴 CONTRARIAN"
                elif 'opposite_side = "bear" if whale_bet_side == "bear" else "bull"' in content:
                    strategy = "🔵 CONSENSUS"
            except:
                pass

            print(f"  {i}. {file} ({strategy})")

        print(f"  {len(self.target_files) + 1}. All files")
        print(f"  {len(self.target_files) + 2}. Cancel")

        while True:
            try:
                choice = input(f"\nSelect files to update (1-{len(self.target_files) + 2}): ").strip()

                if choice == str(len(self.target_files) + 2):  # Cancel
                    return []
                elif choice == str(len(self.target_files) + 1):  # All files
                    return self.target_files.copy()
                else:
                    file_num = int(choice)
                    if 1 <= file_num <= len(self.target_files):
                        return [self.target_files[file_num - 1]]
                    else:
                        print("❌ Invalid choice!")
            except ValueError:
                print("❌ Please enter a valid number!")


def main():
    print("🤖 PancakeSwap Bot Strategy Updater")
    print("=" * 50)

    # Initialize the updater
    updater = StrategyUpdater()

    if not updater.target_files:
        print("❌ No fin*.py files found in the current directory!")
        print("💡 Make sure you're running this script in the same directory as your bot files.")
        return

    print(f"🎯 Found {len(updater.target_files)} bot files: {', '.join(updater.target_files)}")

    while True:
        print("\nOptions:")
        print("1. Show current strategy for all files")
        print("2. Switch to CONTRARIAN strategy")
        print("3. Switch to CONSENSUS strategy")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == '1':
            updater.show_current_strategy()

        elif choice == '2':
            print("\n🔄 Select files to switch to CONTRARIAN strategy:")
            selected_files = updater.select_files_menu()

            if selected_files:
                print(f"\n🔄 Switching {len(selected_files)} file(s) to CONTRARIAN strategy...")
                if updater.update_strategy('contrarian', selected_files):
                    print("\n✅ Strategy update completed!")
                    print("📋 CONTRARIAN strategy characteristics:")
                    print("   • Bets against whale positions when ML is weak")
                    print("   • Follows ML signals directly (bull ML = bull bet)")
                    print("   • Bets against bet ratio patterns")
                else:
                    print("❌ Some files failed to update!")
            else:
                print("⚠️ No files selected. Operation cancelled.")

        elif choice == '3':
            print("\n🔄 Select files to switch to CONSENSUS strategy:")
            selected_files = updater.select_files_menu()

            if selected_files:
                print(f"\n🔄 Switching {len(selected_files)} file(s) to CONSENSUS strategy...")
                if updater.update_strategy('consensus', selected_files):
                    print("\n✅ Strategy update completed!")
                    print("📋 CONSENSUS strategy characteristics:")
                    print("   • More conservative whale following")
                    print("   • Inverts ML signals (bull ML = bear bet)")
                    print("   • Bets against bet ratio patterns")
                else:
                    print("❌ Some files failed to update!")
            else:
                print("⚠️ No files selected. Operation cancelled.")

        elif choice == '4':
            print("\n👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice! Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()