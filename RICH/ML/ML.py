import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Load your data - UPDATE THIS FILENAME
df = pd.read_csv('pancakeswap_prediction_data_20260119_195510.csv')

print("=== BASIC DATA OVERVIEW ===")
print(f"Dataset shape: {df.shape}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print("\nFirst few rows:")
print(df.head())

print("\n=== WINNER DISTRIBUTION ===")
print(df['winner'].value_counts())
print(f"Bull win rate: {(df['winner'] == 'bull').mean():.3f}")
print(f"Bear win rate: {(df['winner'] == 'bear').mean():.3f}")

print("\n=== BASIC STATISTICS ===")
print(df[['price_change_percent', 'total_bets_amount', 'bull_multiplier', 'bear_multiplier']].describe())

# Create visualizations
plt.figure(figsize=(15, 12))

# 1. Price change distribution
plt.subplot(2, 3, 1)
plt.hist(df['price_change_percent'], bins=50, alpha=0.7, edgecolor='black')
plt.title('Price Change Distribution')
plt.xlabel('Price Change %')
plt.ylabel('Frequency')

# 2. Winner distribution
plt.subplot(2, 3, 2)
winner_counts = df['winner'].value_counts()
plt.pie(winner_counts.values, labels=winner_counts.index, autopct='%1.1f%%')
plt.title('Winner Distribution')

# 3. Bet amounts over time
plt.subplot(2, 3, 3)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df_sample = df.iloc[::100]  # Sample every 100th row for clarity
plt.plot(df_sample['timestamp'], df_sample['total_bets_amount'], alpha=0.7)
plt.title('Total Bet Amount Over Time')
plt.xticks(rotation=45)

# 4. Bull vs Bear bet amounts
plt.subplot(2, 3, 4)
plt.scatter(df['bull_bets_amount'], df['bear_bets_amount'], alpha=0.5, s=1)
plt.xlabel('Bull Bet Amount')
plt.ylabel('Bear Bet Amount')
plt.title('Bull vs Bear Bet Amounts')

# 5. Price change by winner
plt.subplot(2, 3, 5)
sns.boxplot(data=df, x='winner', y='price_change_percent')
plt.title('Price Change by Winner')

# 6. Multipliers distribution
plt.subplot(2, 3, 6)
plt.hist(df['bull_multiplier'], bins=30, alpha=0.5, label='Bull', color='green')
plt.hist(df['bear_multiplier'], bins=30, alpha=0.5, label='Bear', color='red')
plt.xlabel('Multiplier')
plt.ylabel('Frequency')
plt.title('Payout Multipliers Distribution')
plt.legend()

plt.tight_layout()
plt.show()

print("\n=== CORRELATION ANALYSIS ===")
# Calculate correlations
numeric_cols = ['price_change_percent', 'total_bets_amount', 'bull_bets_amount', 
                'bear_bets_amount', 'bull_multiplier', 'bear_multiplier']
correlation_matrix = df[numeric_cols].corr()
print(correlation_matrix)

# Feature Engineering
print("\n=== FEATURE ENGINEERING ===")
df['bet_ratio'] = df['bull_bets_amount'] / (df['bear_bets_amount'] + 0.001)  # Avoid division by zero
df['total_bet_log'] = np.log(df['total_bets_amount'] + 1)
df['price_volatility'] = df['price_change_percent'].rolling(window=10).std().fillna(0)
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek

print("New features created:")
print("- bet_ratio: Bull bets / Bear bets")
print("- total_bet_log: Log of total bet amount")
print("- price_volatility: 10-period rolling standard deviation")
print("- hour: Hour of the day")
print("- day_of_week: Day of the week (0=Monday)")

# Machine Learning Models
print("\n=== MACHINE LEARNING MODELS ===")

# Prepare features for ML
feature_columns = ['bet_ratio', 'total_bet_log', 'price_volatility', 'hour', 'day_of_week',
                   'bull_bets_amount', 'bear_bets_amount', 'total_bets_amount']

X = df[feature_columns].fillna(0)
y = df['winner']

# Remove ties for binary classification
mask = y != 'tie'
X = X[mask]
y = y[mask]

print(f"Training data shape: {X.shape}")
print(f"Target distribution: {y.value_counts()}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Model 1: Random Forest
print("\n--- Random Forest Model ---")
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_pred)

print(f"Random Forest Accuracy: {rf_accuracy:.4f}")
print("Feature Importance:")
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)
print(feature_importance)

# Model 2: Logistic Regression
print("\n--- Logistic Regression Model ---")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr_model = LogisticRegression(random_state=42)
lr_model.fit(X_train_scaled, y_train)
lr_pred = lr_model.predict(X_test_scaled)
lr_accuracy = accuracy_score(y_test, lr_pred)

print(f"Logistic Regression Accuracy: {lr_accuracy:.4f}")

# Detailed evaluation of best model
best_model = rf_model if rf_accuracy > lr_accuracy else lr_model
best_pred = rf_pred if rf_accuracy > lr_accuracy else lr_pred
best_name = "Random Forest" if rf_accuracy > lr_accuracy else "Logistic Regression"

print(f"\n=== DETAILED EVALUATION - {best_name} ===")
print("Classification Report:")
print(classification_report(y_test, best_pred))

print("Confusion Matrix:")
cm = confusion_matrix(y_test, best_pred)
print(cm)

# Pattern Analysis
print("\n=== PATTERN ANALYSIS ===")

# 1. Bet ratio patterns
print("\n1. Bet Ratio Analysis:")
df_no_ties = df[df['winner'] != 'tie'].copy()
bull_wins = df_no_ties[df_no_ties['winner'] == 'bull']
bear_wins = df_no_ties[df_no_ties['winner'] == 'bear']

print(f"Average bet ratio when bulls win: {bull_wins['bet_ratio'].mean():.3f}")
print(f"Average bet ratio when bears win: {bear_wins['bet_ratio'].mean():.3f}")

# 2. Time patterns
print("\n2. Time-based Patterns:")
hourly_stats = df_no_ties.groupby('hour')['winner'].apply(lambda x: (x == 'bull').mean())
print("Bull win rate by hour:")
for hour, rate in hourly_stats.items():
    print(f"Hour {hour:2d}: {rate:.3f}")

# 3. Bet size patterns
print("\n3. Bet Size Patterns:")
df_no_ties['bet_size_category'] = pd.cut(df_no_ties['total_bets_amount'], 
                                        bins=[0, 1, 5, 10, float('inf')], 
                                        labels=['Small', 'Medium', 'Large', 'Huge'])
bet_size_stats = df_no_ties.groupby('bet_size_category')['winner'].apply(lambda x: (x == 'bull').mean())
print("Bull win rate by bet size:")
print(bet_size_stats)

# Save analysis results
print("\n=== SAVING ANALYSIS RESULTS ===")
analysis_results = {
    'model_accuracy': {
        'random_forest': rf_accuracy,
        'logistic_regression': lr_accuracy
    },
    'feature_importance': feature_importance.to_dict('records'),
    'patterns': {
        'bull_avg_bet_ratio': bull_wins['bet_ratio'].mean(),
        'bear_avg_bet_ratio': bear_wins['bet_ratio'].mean(),
        'hourly_bull_rates': hourly_stats.to_dict(),
        'bet_size_bull_rates': bet_size_stats.to_dict()
    }
}

# Save to JSON
import json
with open('analysis_results.json', 'w') as f:
    json.dump(analysis_results, f, indent=2, default=str)

print("Analysis complete!")
print("Results saved to 'analysis_results.json'")
print(f"\nKey Findings:")
print(f"- Best model accuracy: {max(rf_accuracy, lr_accuracy):.4f}")
print(f"- Most important feature: {feature_importance.iloc[0]['feature']}")
print(f"- Bull win rate: {(df['winner'] == 'bull').mean():.3f}")
print(f"- Total data points analyzed: {len(df)}")