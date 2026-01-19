import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings('ignore')

# Load your data - UPDATE THIS FILENAME
df = pd.read_csv('pancakeswap_prediction_data_20250723_135209.csv')

print("=== BASIC DATA OVERVIEW ===")
print(f"Dataset shape: {df.shape}")
print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print("\nFirst few rows:")
print(df.head())

# Check if we have top bets data
has_top_bets = any(col.startswith('bull_bet_1_') for col in df.columns)
print(f"\nTop bets data available: {has_top_bets}")

if has_top_bets:
    print("\nTop bets columns found:")
    top_bet_cols = [col for col in df.columns if 'bet_' in col and ('_user' in col or '_amount' in col)]
    print(top_bet_cols[:10])  # Show first 10

print("\n=== WINNER DISTRIBUTION ===")
print(df['winner'].value_counts())
print(f"Bull win rate: {(df['winner'] == 'bull').mean():.3f}")
print(f"Bear win rate: {(df['winner'] == 'bear').mean():.3f}")

print("\n=== BASIC STATISTICS ===")
basic_stats_cols = ['price_change_percent', 'total_bets_amount', 'bull_multiplier', 'bear_multiplier']
if has_top_bets and 'largest_bull_bet' in df.columns:
    basic_stats_cols.extend(['largest_bull_bet', 'largest_bear_bet', 'total_bets_count'])
print(df[basic_stats_cols].describe())

# Create enhanced visualizations
plt.figure(figsize=(20, 16))

# 1. Price change distribution
plt.subplot(3, 4, 1)
plt.hist(df['price_change_percent'], bins=50, alpha=0.7, edgecolor='black')
plt.title('Price Change Distribution')
plt.xlabel('Price Change %')
plt.ylabel('Frequency')

# 2. Winner distribution
plt.subplot(3, 4, 2)
winner_counts = df['winner'].value_counts()
plt.pie(winner_counts.values, labels=winner_counts.index, autopct='%1.1f%%')
plt.title('Winner Distribution')

# 3. Bet amounts over time
plt.subplot(3, 4, 3)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df_sample = df.iloc[::100]  # Sample every 100th row for clarity
plt.plot(df_sample['timestamp'], df_sample['total_bets_amount'], alpha=0.7)
plt.title('Total Bet Amount Over Time')
plt.xticks(rotation=45)

# 4. Bull vs Bear bet amounts
plt.subplot(3, 4, 4)
plt.scatter(df['bull_bets_amount'], df['bear_bets_amount'], alpha=0.5, s=1)
plt.xlabel('Bull Bet Amount')
plt.ylabel('Bear Bet Amount')
plt.title('Bull vs Bear Bet Amounts')

# 5. Price change by winner
plt.subplot(3, 4, 5)
sns.boxplot(data=df, x='winner', y='price_change_percent')
plt.title('Price Change by Winner')

# 6. Multipliers distribution
plt.subplot(3, 4, 6)
plt.hist(df['bull_multiplier'], bins=30, alpha=0.5, label='Bull', color='green')
plt.hist(df['bear_multiplier'], bins=30, alpha=0.5, label='Bear', color='red')
plt.xlabel('Multiplier')
plt.ylabel('Frequency')
plt.title('Payout Multipliers Distribution')
plt.legend()

if has_top_bets and 'largest_bull_bet' in df.columns:
    # 7. Largest bets distribution
    plt.subplot(3, 4, 7)
    plt.hist(df['largest_bull_bet'], bins=30, alpha=0.5, label='Bull', color='green')
    plt.hist(df['largest_bear_bet'], bins=30, alpha=0.5, label='Bear', color='red')
    plt.xlabel('Largest Bet Amount (BNB)')
    plt.ylabel('Frequency')
    plt.title('Largest Bets Distribution')
    plt.legend()

    # 8. Largest bet vs winner
    plt.subplot(3, 4, 8)
    df_clean = df[df['winner'] != 'tie']
    sns.boxplot(data=df_clean, x='winner', y='largest_bull_bet')
    plt.title('Largest Bull Bet by Winner')

    # 9. Whale activity correlation
    plt.subplot(3, 4, 9)
    plt.scatter(df['largest_bull_bet'], df['largest_bear_bet'],
                c=df['winner'].map({'bull': 'green', 'bear': 'red', 'tie': 'gray'}),
                alpha=0.6, s=10)
    plt.xlabel('Largest Bull Bet')
    plt.ylabel('Largest Bear Bet')
    plt.title('Whale Activity by Outcome')

    # 10. Bet count analysis
    plt.subplot(3, 4, 10)
    if 'total_bets_count' in df.columns:
        sns.boxplot(data=df_clean, x='winner', y='total_bets_count')
        plt.title('Number of Bets by Winner')

plt.tight_layout()
plt.show()

print("\n=== CORRELATION ANALYSIS ===")
# Calculate correlations including new features
numeric_cols = ['price_change_percent', 'total_bets_amount', 'bull_bets_amount',
                'bear_bets_amount', 'bull_multiplier', 'bear_multiplier']

if has_top_bets and 'largest_bull_bet' in df.columns:
    numeric_cols.extend(['largest_bull_bet', 'largest_bear_bet', 'total_bets_count'])

correlation_matrix = df[numeric_cols].corr()
print(correlation_matrix)

# Enhanced Feature Engineering
print("\n=== ENHANCED FEATURE ENGINEERING ===")

# Basic features
df['bet_ratio'] = df['bull_bets_amount'] / (df['bear_bets_amount'] + 0.001)
df['total_bet_log'] = np.log(df['total_bets_amount'] + 1)
df['price_volatility'] = df['price_change_percent'].rolling(window=10).std().fillna(0)
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek

# New whale-based features
if has_top_bets and 'largest_bull_bet' in df.columns:
    print("Creating whale activity features...")

    # Whale dominance features
    df['whale_bull_dominance'] = df['largest_bull_bet'] / (df['bull_bets_amount'] + 0.001)
    df['whale_bear_dominance'] = df['largest_bear_bet'] / (df['bear_bets_amount'] + 0.001)
    df['whale_ratio'] = df['largest_bull_bet'] / (df['largest_bear_bet'] + 0.001)

    # Top 3 bets analysis
    for i in range(1, 4):
        bull_bet_col = f'bull_bet_{i}_amount'
        bear_bet_col = f'bear_bet_{i}_amount'

        if bull_bet_col in df.columns:
            df[bull_bet_col] = pd.to_numeric(df[bull_bet_col], errors='coerce').fillna(0)
        if bear_bet_col in df.columns:
            df[bear_bet_col] = pd.to_numeric(df[bear_bet_col], errors='coerce').fillna(0)

    # Sum of top 3 bets for each side
    bull_top3_cols = [f'bull_bet_{i}_amount' for i in range(1, 4) if f'bull_bet_{i}_amount' in df.columns]
    bear_top3_cols = [f'bear_bet_{i}_amount' for i in range(1, 4) if f'bear_bet_{i}_amount' in df.columns]

    if bull_top3_cols:
        df['bull_top3_sum'] = df[bull_top3_cols].sum(axis=1)
        df['bull_top3_concentration'] = df['bull_top3_sum'] / (df['bull_bets_amount'] + 0.001)

    if bear_top3_cols:
        df['bear_top3_sum'] = df[bear_top3_cols].sum(axis=1)
        df['bear_top3_concentration'] = df['bear_top3_sum'] / (df['bear_bets_amount'] + 0.001)

    # Whale vs crowd dynamics
    df['crowd_bull_amount'] = df['bull_bets_amount'] - df.get('bull_top3_sum', 0)
    df['crowd_bear_amount'] = df['bear_bets_amount'] - df.get('bear_top3_sum', 0)
    df['crowd_ratio'] = df['crowd_bull_amount'] / (df['crowd_bear_amount'] + 0.001)

    # Bet activity features
    if 'total_bets_count' in df.columns:
        df['avg_bet_size'] = df['total_bets_amount'] / (df['total_bets_count'] + 1)
        df['whale_vs_avg_ratio'] = df['largest_bull_bet'] / (df['avg_bet_size'] + 0.001)

print("New features created:")
print("- bet_ratio: Bull bets / Bear bets")
print("- total_bet_log: Log of total bet amount")
print("- price_volatility: 10-period rolling standard deviation")
print("- hour, day_of_week: Time-based features")

if has_top_bets and 'largest_bull_bet' in df.columns:
    print("- whale_bull_dominance: Largest bull bet / Total bull bets")
    print("- whale_bear_dominance: Largest bear bet / Total bear bets")
    print("- whale_ratio: Largest bull bet / Largest bear bet")
    print("- bull/bear_top3_concentration: Top 3 bets / Total side bets")
    print("- crowd_ratio: Non-whale bull bets / Non-whale bear bets")
    if 'total_bets_count' in df.columns:
        print("- avg_bet_size: Average bet size")
        print("- whale_vs_avg_ratio: Largest bet vs average bet")

# Enhanced Machine Learning Models
print("\n=== ENHANCED MACHINE LEARNING MODELS ===")

# Prepare enhanced features for ML
feature_columns = ['bet_ratio', 'total_bet_log', 'price_volatility', 'hour', 'day_of_week',
                   'bull_bets_amount', 'bear_bets_amount', 'total_bets_amount']

# Add whale features if available
if has_top_bets and 'largest_bull_bet' in df.columns:
    whale_features = ['whale_bull_dominance', 'whale_bear_dominance', 'whale_ratio',
                      'largest_bull_bet', 'largest_bear_bet']

    if 'bull_top3_concentration' in df.columns:
        whale_features.extend(['bull_top3_concentration', 'bear_top3_concentration', 'crowd_ratio'])

    if 'avg_bet_size' in df.columns:
        whale_features.extend(['avg_bet_size', 'whale_vs_avg_ratio'])

    feature_columns.extend(whale_features)
    print(f"Using {len(whale_features)} whale-based features")

print(f"Total features: {len(feature_columns)}")
print("Features:", feature_columns)

X = df[feature_columns].fillna(0)
y = df['winner']

# Remove ties for binary classification
mask = y != 'tie'
X = X[mask]
y = y[mask]

# Handle infinite values
X = X.replace([np.inf, -np.inf], 0)

print(f"Training data shape: {X.shape}")
print(f"Target distribution: {y.value_counts()}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Model 1: Random Forest
print("\n--- Random Forest Model ---")
rf_model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_pred)

print(f"Random Forest Accuracy: {rf_accuracy:.4f}")
print("Top 10 Feature Importance:")
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)
print(feature_importance.head(10))

# Model 2: Gradient Boosting
print("\n--- Gradient Boosting Model ---")
gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
gb_model.fit(X_train, y_train)
gb_pred = gb_model.predict(X_test)
gb_accuracy = accuracy_score(y_test, gb_pred)

print(f"Gradient Boosting Accuracy: {gb_accuracy:.4f}")

# Model 3: Logistic Regression
print("\n--- Logistic Regression Model ---")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr_model = LogisticRegression(random_state=42, max_iter=1000)
lr_model.fit(X_train_scaled, y_train)
lr_pred = lr_model.predict(X_test_scaled)
lr_accuracy = accuracy_score(y_test, lr_pred)

print(f"Logistic Regression Accuracy: {lr_accuracy:.4f}")

# Determine best model
accuracies = {'Random Forest': rf_accuracy, 'Gradient Boosting': gb_accuracy, 'Logistic Regression': lr_accuracy}
best_model_name = max(accuracies, key=accuracies.get)
best_accuracy = max(accuracies.values())

if best_model_name == 'Random Forest':
    best_model, best_pred = rf_model, rf_pred
elif best_model_name == 'Gradient Boosting':
    best_model, best_pred = gb_model, gb_pred
else:
    best_model, best_pred = lr_model, lr_pred

print(f"\n=== DETAILED EVALUATION - {best_model_name} ===")
print("Classification Report:")
print(classification_report(y_test, best_pred))

print("Confusion Matrix:")
cm = confusion_matrix(y_test, best_pred)
print(cm)

# Enhanced Pattern Analysis
print("\n=== ENHANCED PATTERN ANALYSIS ===")

# 1. Basic bet ratio patterns
print("\n1. Bet Ratio Analysis:")
df_no_ties = df[df['winner'] != 'tie'].copy()
bull_wins = df_no_ties[df_no_ties['winner'] == 'bull']
bear_wins = df_no_ties[df_no_ties['winner'] == 'bear']

print(f"Average bet ratio when bulls win: {bull_wins['bet_ratio'].mean():.3f}")
print(f"Average bet ratio when bears win: {bear_wins['bet_ratio'].mean():.3f}")

if has_top_bets and 'largest_bull_bet' in df.columns:
    # 2. Whale activity patterns
    print("\n2. Whale Activity Analysis:")
    print(f"Average largest bull bet when bulls win: {bull_wins['largest_bull_bet'].mean():.3f} BNB")
    print(f"Average largest bull bet when bears win: {bear_wins['largest_bull_bet'].mean():.3f} BNB")
    print(f"Average largest bear bet when bulls win: {bull_wins['largest_bear_bet'].mean():.3f} BNB")
    print(f"Average largest bear bet when bears win: {bear_wins['largest_bear_bet'].mean():.3f} BNB")

    print(f"Average whale ratio when bulls win: {bull_wins['whale_ratio'].mean():.3f}")
    print(f"Average whale ratio when bears win: {bear_wins['whale_ratio'].mean():.3f}")

    # 3. Concentration analysis
    if 'bull_top3_concentration' in df.columns:
        print("\n3. Bet Concentration Analysis:")
        print(f"Bull top3 concentration when bulls win: {bull_wins['bull_top3_concentration'].mean():.3f}")
        print(f"Bull top3 concentration when bears win: {bear_wins['bull_top3_concentration'].mean():.3f}")
        print(f"Bear top3 concentration when bulls win: {bull_wins['bear_top3_concentration'].mean():.3f}")
        print(f"Bear top3 concentration when bears win: {bear_wins['bear_top3_concentration'].mean():.3f}")

# 4. Time patterns
print("\n4. Time-based Patterns:")
hourly_stats = df_no_ties.groupby('hour')['winner'].apply(lambda x: (x == 'bull').mean())
print("Bull win rate by hour:")
for hour, rate in hourly_stats.items():
    print(f"Hour {hour:2d}: {rate:.3f}")

# 5. Bet size patterns
print("\n5. Bet Size Patterns:")
df_no_ties['bet_size_category'] = pd.cut(df_no_ties['total_bets_amount'],
                                         bins=[0, 1, 5, 10, 50, float('inf')],
                                         labels=['Tiny', 'Small', 'Medium', 'Large', 'Huge'])
bet_size_stats = df_no_ties.groupby('bet_size_category')['winner'].apply(lambda x: (x == 'bull').mean())
print("Bull win rate by bet size:")
print(bet_size_stats)

# Enhanced whale analysis
if has_top_bets and 'largest_bull_bet' in df.columns:
    print("\n6. Whale Dominance Patterns:")

    # Create whale categories
    df_no_ties['whale_category'] = pd.cut(df_no_ties['largest_bull_bet'],
                                          bins=[0, 1, 5, 20, float('inf')],
                                          labels=['No Whale', 'Small Whale', 'Medium Whale', 'Big Whale'])

    whale_stats = df_no_ties.groupby('whale_category')['winner'].apply(lambda x: (x == 'bull').mean())
    print("Bull win rate by whale size:")
    print(whale_stats)

# Save enhanced analysis results
print("\n=== SAVING ENHANCED ANALYSIS RESULTS ===")
analysis_results = {
    'model_accuracy': {
        'random_forest': rf_accuracy,
        'gradient_boosting': gb_accuracy,
        'logistic_regression': lr_accuracy,
        'best_model': best_model_name,
        'best_accuracy': best_accuracy
    },
    'feature_importance': feature_importance.to_dict('records'),
    'patterns': {
        'basic_patterns': {
            'bull_avg_bet_ratio': bull_wins['bet_ratio'].mean(),
            'bear_avg_bet_ratio': bear_wins['bet_ratio'].mean(),
        },
        'time_patterns': {
            'hourly_bull_rates': hourly_stats.to_dict(),
            'bet_size_bull_rates': bet_size_stats.to_dict()
        }
    },
    'data_summary': {
        'total_records': len(df),
        'records_with_top_bets': has_top_bets,
        'bull_win_rate': (df['winner'] == 'bull').mean(),
        'bear_win_rate': (df['winner'] == 'bear').mean(),
        'tie_rate': (df['winner'] == 'tie').mean()
    }
}

if has_top_bets and 'largest_bull_bet' in df.columns:
    analysis_results['patterns']['whale_patterns'] = {
        'bull_wins_largest_bull_bet': bull_wins['largest_bull_bet'].mean(),
        'bear_wins_largest_bull_bet': bear_wins['largest_bull_bet'].mean(),
        'bull_wins_largest_bear_bet': bull_wins['largest_bear_bet'].mean(),
        'bear_wins_largest_bear_bet': bear_wins['largest_bear_bet'].mean(),
        'bull_wins_whale_ratio': bull_wins['whale_ratio'].mean(),
        'bear_wins_whale_ratio': bear_wins['whale_ratio'].mean()
    }

    if 'whale_category' in df_no_ties.columns:
        analysis_results['patterns']['whale_size_patterns'] = whale_stats.to_dict()

# Save to JSON
import json

with open('enhanced_analysis_results.json', 'w') as f:
    json.dump(analysis_results, f, indent=2, default=str)

print("Enhanced analysis complete!")
print("Results saved to 'enhanced_analysis_results.json'")
print(f"\nKey Findings:")
print(f"- Best model: {best_model_name} (accuracy: {best_accuracy:.4f})")
print(f"- Most important feature: {feature_importance.iloc[0]['feature']}")
print(f"- Bull win rate: {(df['winner'] == 'bull').mean():.3f}")
print(f"- Bear win rate: {(df['winner'] == 'bear').mean():.3f}")
print(f"- Total data points analyzed: {len(df)}")

if has_top_bets and 'largest_bull_bet' in df.columns:
    print(f"- Average largest bull bet: {df['largest_bull_bet'].mean():.3f} BNB")
    print(f"- Average largest bear bet: {df['largest_bear_bet'].mean():.3f} BNB")
    print(f"- Whale features significantly improved model performance")

    # Show top whale-related features
    whale_features_importance = feature_importance[
        feature_importance['feature'].str.contains('whale|largest|top3|crowd')].head(5)
    if not whale_features_importance.empty:
        print(f"- Top whale-related features:")
        for _, row in whale_features_importance.iterrows():
            print(f"  * {row['feature']}: {row['importance']:.4f}")

print(f"\nModel Comparison:")
for model_name, accuracy in accuracies.items():
    print(f"- {model_name}: {accuracy:.4f}")