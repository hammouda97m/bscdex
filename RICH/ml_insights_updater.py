#!/usr/bin/env python3
"""
Python Code Updater Script
Updates ML insights data in trading bot code from JSON configuration files
"""

import json
import re
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional


class CodeUpdater:
    def __init__(self, target_file: str, json_config_file: str):
        self.target_file = target_file
        self.json_config_file = json_config_file
        self.backup_suffix = f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def load_json_config(self) -> Dict[str, Any]:
        """Load configuration data from JSON file"""
        try:
            with open(self.json_config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON config file not found: {self.json_config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {self.json_config_file}: {e}")

    def create_backup(self) -> str:
        """Create a backup of the target file"""
        backup_file = self.target_file + self.backup_suffix
        shutil.copy2(self.target_file, backup_file)
        print(f"✅ Backup created: {backup_file}")
        return backup_file

    def read_target_file(self) -> str:
        """Read the target Python file"""
        try:
            with open(self.target_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Target file not found: {self.target_file}")

    def write_target_file(self, content: str) -> None:
        """Write updated content to the target file"""
        with open(self.target_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Updated file saved: {self.target_file}")

    def format_hourly_bull_rates(self, hourly_data: Dict[str, float]) -> str:
        """Format hourly bull rates dictionary for Python code"""
        # Convert string keys to integers and format
        formatted_items = []
        for hour in range(24):  # Ensure all hours 0-23 are present
            hour_str = str(hour)
            rate = hourly_data.get(hour_str, 0.5)  # Default to 0.5 if missing
            formatted_items.append(f"    {hour}: {rate}")

        # Group items in lines of 6 for better readability
        lines = []
        for i in range(0, len(formatted_items), 6):
            line_items = formatted_items[i:i + 6]
            lines.append(",".join(line_items))

        return "HOURLY_BULL_RATES = {\n" + ",\n".join(lines) + "\n}"

    def format_feature_weights(self, feature_importance: list) -> str:
        """Format feature importance as FEATURE_WEIGHTS dictionary"""
        # Convert list of feature importance to dictionary
        weights_dict = {}
        for item in feature_importance:
            feature_name = item["feature"]
            importance = item["importance"]
            weights_dict[feature_name] = importance

        # Format for Python code
        formatted_items = []
        for feature, weight in weights_dict.items():
            formatted_items.append(f'    "{feature}": {weight:.4f}')

        return "FEATURE_WEIGHTS = {\n" + ",\n".join(formatted_items) + "\n}"

    def format_bet_ratio_thresholds(self, patterns: Dict[str, Any]) -> str:
        """Format bet ratio thresholds"""
        bull_ratio = patterns.get("bull_avg_bet_ratio", 1.2241450793651707)
        bear_ratio = patterns.get("bear_avg_bet_ratio", 1.074188804168328)

        return f"""# Key thresholds from your analysis
BULL_WIN_BET_RATIO = {bull_ratio}
BEAR_WIN_BET_RATIO = {bear_ratio}"""

    def update_section(self, content: str, section_name: str, new_content: str) -> str:
        """Update a specific section in the code"""
        patterns = {
            "HOURLY_BULL_RATES": {
                "start": r"HOURLY_BULL_RATES\s*=\s*{",
                "end": r"}"
            },
            "FEATURE_WEIGHTS": {
                "start": r"FEATURE_WEIGHTS\s*=\s*{",
                "end": r"}"
            },
            "THRESHOLDS": {
                "start": r"# Key thresholds from your analysis",
                "end": r"BEAR_WIN_BET_RATIO\s*=\s*[0-9.]+"
            }
        }

        if section_name not in patterns:
            raise ValueError(f"Unknown section: {section_name}")

        pattern = patterns[section_name]

        # Create regex pattern to match the entire section
        if section_name == "THRESHOLDS":
            # For thresholds, match the comment and both variables
            regex_pattern = rf"({pattern['start']}.*?{pattern['end']})"
        else:
            # For dictionaries, match from the variable name to the closing brace
            regex_pattern = rf"({pattern['start']}.*?{pattern['end']})"

        # Use DOTALL flag to match across multiple lines
        match = re.search(regex_pattern, content, re.DOTALL)

        if not match:
            print(f"⚠️ Warning: Could not find {section_name} section to update")
            return content

        # Replace the matched section with new content
        updated_content = content.replace(match.group(1), new_content)
        print(f"✅ Updated {section_name} section")

        return updated_content

    def update_code(self) -> bool:
        """Main method to update the code file"""
        try:
            print(f"🔄 Starting code update process...")
            print(f"📂 Target file: {self.target_file}")
            print(f"📊 JSON config: {self.json_config_file}")

            # Load JSON configuration
            config = self.load_json_config()
            print(f"✅ Loaded JSON configuration")

            # Create backup
            backup_file = self.create_backup()

            # Read target file
            content = self.read_target_file()

            # Update HOURLY_BULL_RATES
            if "patterns" in config and "hourly_bull_rates" in config["patterns"]:
                hourly_rates_content = self.format_hourly_bull_rates(config["patterns"]["hourly_bull_rates"])
                content = self.update_section(content, "HOURLY_BULL_RATES", hourly_rates_content)

            # Update FEATURE_WEIGHTS
            if "feature_importance" in config:
                feature_weights_content = self.format_feature_weights(config["feature_importance"])
                content = self.update_section(content, "FEATURE_WEIGHTS", feature_weights_content)

            # Update bet ratio thresholds
            if "patterns" in config:
                thresholds_content = self.format_bet_ratio_thresholds(config["patterns"])
                content = self.update_section(content, "THRESHOLDS", thresholds_content)

            # Write updated content
            self.write_target_file(content)

            print(f"\n🎉 Code update completed successfully!")
            print(f"📁 Backup saved as: {backup_file}")

            return True

        except Exception as e:
            print(f"❌ Error during code update: {e}")
            return False

    def validate_updates(self) -> bool:
        """Validate that the updates were applied correctly"""
        try:
            content = self.read_target_file()

            # Check if key sections exist
            checks = [
                ("HOURLY_BULL_RATES", "HOURLY_BULL_RATES = {"),
                ("FEATURE_WEIGHTS", "FEATURE_WEIGHTS = {"),
                ("BULL_WIN_BET_RATIO", "BULL_WIN_BET_RATIO ="),
                ("BEAR_WIN_BET_RATIO", "BEAR_WIN_BET_RATIO =")
            ]

            all_found = True
            for check_name, check_pattern in checks:
                if check_pattern not in content:
                    print(f"❌ Validation failed: {check_name} not found")
                    all_found = False
                else:
                    print(f"✅ Validation passed: {check_name} found")

            return all_found

        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False


def update_multiple_files(file_pattern: str = "fin{}.py", file_range: range = range(1, 13),
                          json_config: str = "analysis_results.json") -> bool:
    """Update multiple files matching the pattern"""
    print("🚀 ML Trading Bot Code Updater - Multiple Files")
    print("=" * 60)

    # Check if JSON config exists
    if not os.path.exists(json_config):
        print(f"❌ JSON config file not found: {json_config}")
        return False

    # Find all matching files
    target_files = []
    for i in file_range:
        filename = file_pattern.format(i)
        if os.path.exists(filename):
            target_files.append(filename)
        else:
            print(f"⚠️ File not found (skipping): {filename}")

    if not target_files:
        print("❌ No target files found!")
        return False

    print(f"📂 Found {len(target_files)} files to update:")
    for file in target_files:
        print(f"   • {file}")

    # Ask for confirmation if updating multiple files
    if len(target_files) > 1:
        print(f"\n⚠️ About to update {len(target_files)} files with data from {json_config}")
        response = input("Continue? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Update cancelled by user")
            return False

    # Update each file
    success_count = 0
    failed_files = []

    for i, target_file in enumerate(target_files, 1):
        print(f"\n{'=' * 20} UPDATING FILE {i}/{len(target_files)} {'=' * 20}")
        print(f"📁 Processing: {target_file}")

        try:
            # Create updater and run
            updater = CodeUpdater(target_file, json_config)

            # Perform update
            success = updater.update_code()

            if success:
                # Validate updates
                print(f"🔍 Validating {target_file}...")
                validation_success = updater.validate_updates()

                if validation_success:
                    print(f"✅ {target_file} updated and validated successfully!")
                    success_count += 1
                else:
                    print(f"⚠️ {target_file} updated but validation failed")
                    failed_files.append(f"{target_file} (validation failed)")
                    success_count += 1  # Still count as success since file was updated
            else:
                print(f"❌ Failed to update {target_file}")
                failed_files.append(f"{target_file} (update failed)")

        except Exception as e:
            print(f"❌ Error processing {target_file}: {e}")
            failed_files.append(f"{target_file} (exception: {e})")

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 UPDATE SUMMARY")
    print(f"✅ Successfully updated: {success_count}/{len(target_files)} files")

    if failed_files:
        print(f"❌ Failed files: {len(failed_files)}")
        for failed_file in failed_files:
            print(f"   • {failed_file}")

    if success_count == len(target_files):
        print("\n🎉 All files updated successfully!")
        print("🎯 Your trading bot codes have been updated with the latest ML insights.")
        return True
    else:
        print(f"\n⚠️ {len(failed_files)} files had issues. Check the logs above.")
        return False


def update_single_file(target_file: str = "fin1.py", json_config: str = "analysis_results.json") -> bool:
    """Update a single file (original functionality)"""
    print("🚀 ML Trading Bot Code Updater - Single File")
    print("=" * 50)

    # Check if files exist
    if not os.path.exists(target_file):
        print(f"❌ Target file not found: {target_file}")
        return False

    if not os.path.exists(json_config):
        print(f"❌ JSON config file not found: {json_config}")
        return False

    # Create updater and run
    updater = CodeUpdater(target_file, json_config)

    # Perform update
    success = updater.update_code()

    if success:
        # Validate updates
        print("\n🔍 Validating updates...")
        validation_success = updater.validate_updates()

        if validation_success:
            print("\n✅ All updates validated successfully!")
            print("🎯 Your trading bot code has been updated with the latest ML insights.")
        else:
            print("\n⚠️ Some validations failed. Please check the updated file manually.")

    return success


def main():
    """Main function with options for single or multiple file updates"""
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--single" and len(sys.argv) > 2:
            # Update specific single file: python code_updater.py --single fin5.py
            return update_single_file(sys.argv[2])
        elif sys.argv[1] == "--help":
            print("🚀 ML Trading Bot Code Updater - Usage")
            print("=" * 50)
            print("Update all fin*.py files (fin1.py to fin12.py):")
            print("  python code_updater.py")
            print("")
            print("Update specific single file:")
            print("  python code_updater.py --single fin5.py")
            print("")
            print("Update custom range:")
            print("  python code_updater.py --range 1 5  # Updates fin1.py to fin5.py")
            return True
        elif sys.argv[1] == "--range" and len(sys.argv) > 3:
            # Update custom range: python code_updater.py --range 1 5
            start = int(sys.argv[2])
            end = int(sys.argv[3]) + 1
            return update_multiple_files(file_range=range(start, end))

    # Default: Update all files fin1.py through fin12.py
    return update_multiple_files()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)