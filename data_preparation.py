import pandas as pd
import yfinance as yf
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
import json

warnings.filterwarnings("ignore")

def get_all_scheme_types():
    """
    UPDATED: Includes diverse schemes: MFs, ETFs, Stocks, FD, SGB.
    'has_market_data' flag helps skip non-market items in yfinance.
    """
    print("Fetching diverse scheme list...")
    schemes = [
        # === Market Linked ===
        # Equity Mutual Funds / ETFs / Stocks
        {"scheme_name": "Nifty 50 Bees ETF", "category": "Index Fund (Large-Cap)", "ticker": "NIFTYBEES.NS", "has_market_data": True},
        {"scheme_name": "Bank Bees ETF", "category": "Index Fund (Sectoral)", "ticker": "BANKBEES.NS", "has_market_data": True},
        # Note: Adding real MF tickers is hard with yfinance. Using ETFs/Stocks as proxy.
        # {"scheme_name": "Axis Midcap Fund", "category": "Mid-Cap Equity", "ticker": "AXISMIDCAP.NS?", "has_market_data": True}, # Example - Ticker might not work
        # {"scheme_name": "Quant Small Cap Fund", "category": "Small-Cap Equity", "ticker": "QUANTSMA.NS?", "has_market_data": True}, # Example - Ticker might not work
        {"scheme_name": "Parag Parikh Flexi Cap Fund", "category": "Flexi-Cap Equity", "ticker": "PARAGFLEX.NS?", "has_market_data": True}, # Example - Ticker might not work - Replace "?" if you find working tickers
        {"scheme_name": "Reliance Industries", "category": "Large-Cap Stock", "ticker": "RELIANCE.NS", "has_market_data": True},
        {"scheme_name": "Tata Motors", "category": "Auto Stock", "ticker": "TATAMOTORS.NS", "has_market_data": True},
        {"scheme_name": "Infosys", "category": "IT Stock", "ticker": "INFY.NS", "has_market_data": True},

        # Debt Mutual Funds / ETFs
        {"scheme_name": "Liquid Bees ETF", "category": "Liquid Debt", "ticker": "LIQUIDBEES.NS", "has_market_data": True},
        # {"scheme_name": "HDFC Short Term Debt Fund", "category": "Short-Term Debt", "ticker": "HDFCSHORT.NS?", "has_market_data": True}, # Example - Ticker might not work

        # Gold
        {"scheme_name": "Gold Bees ETF", "category": "Gold ETF", "ticker": "GOLDBEES.NS", "has_market_data": True},
        # {"scheme_name": "SBI Gold Fund", "category": "Gold Mutual Fund", "ticker": "SBIGOLD.NS?", "has_market_data": True}, # Example - Ticker might not work

        # Hybrid Mutual Funds (Example - Ticker likely won't work)
        # {"scheme_name": "ICICI Pru Balanced Advantage Fund", "category": "Hybrid Fund", "ticker": "ICICIBALANCED.NS?", "has_market_data": True},

        # === Non-Market Linked (Manual Data) ===
        {"scheme_name": "Bank Fixed Deposit (1 Year)", "category": "Fixed Deposit", "ticker": "BANKFD1Y", "has_market_data": False, "avg_return": 0.07, "volatility_manual": 0.0},
        {"scheme_name": "Post Office Fixed Deposit (5 Year)", "category": "Fixed Deposit", "ticker": "POFD5Y", "has_market_data": False, "avg_return": 0.075, "volatility_manual": 0.0},
        {"scheme_name": "Sovereign Gold Bond (SGB)", "category": "Gold Bond", "ticker": "SGB", "has_market_data": False, "avg_return": 0.08, "volatility_manual": 0.13} # Approx Gold volatility
    ]
    return schemes

def get_scheme_features(ticker):
    """
    Downloads data ONLY for market-linked schemes.
    """
    try:
        data = yf.Ticker(ticker).history(period="3y")
        if data.empty: return None
        daily_returns = data['Close'].pct_change().dropna()
        # Handle potential cases where std dev is zero (e.g., LIQUIDBEES sometimes)
        if daily_returns.std() == 0:
            volatility = 0.001 # Assign a very small volatility
            sharpe_ratio = 0 # Cannot calculate sharpe if std dev is zero
        else:
            volatility = daily_returns.std() * np.sqrt(252)
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)

        return {"ticker": ticker, "volatility": volatility, "sharpe_ratio": sharpe_ratio}
    except Exception as e:
        print(f"  > Error or no data for {ticker}: {e}")
        return None

def run_ai_labeling_job():
    print("--- Starting AI Data Preparation Job v2.0 ---")
    schemes = get_all_scheme_types()
    all_scheme_data = []
    market_linked_schemes = []

    print("Step 1: Processing all schemes...")
    for scheme in schemes:
        if scheme["has_market_data"]:
            features = get_scheme_features(scheme['ticker'])
            if features:
                full_data = {**scheme, **features}
                market_linked_schemes.append(full_data) # Keep market data separate for AI
                all_scheme_data.append(full_data)
                print(f"  > [Market Data] Processed {scheme['scheme_name']}")
            else:
                # If market data fails for a market scheme, skip it
                 print(f"  > [Market Data] Skipped {scheme['scheme_name']} due to data issues.")
        else:
            # For non-market schemes, use manual data if available
            manual_features = {
                "volatility": scheme.get("volatility_manual", 0.0),
                # Sharpe ratio needs calculation, use a placeholder or estimate if needed
                "sharpe_ratio": scheme.get("sharpe_ratio_manual", 0.5) # Placeholder
            }
            full_data = {**scheme, **manual_features}
            all_scheme_data.append(full_data)
            print(f"  > [Manual Data] Processed {scheme['scheme_name']}")

    # Convert market-linked schemes to DataFrame for AI
    if not market_linked_schemes:
         print("No market-linked data to run AI model. Exiting.")
         return None

    df_market = pd.DataFrame(market_linked_schemes)
    df_market.dropna(inplace=True)

    print(f"\nStep 2: Running K-Means AI Model on {len(df_market)} Market-Linked Schemes...")
    features_for_ai = df_market[['volatility', 'sharpe_ratio']]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features_for_ai)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10) # 3 clusters for market data: Low-M, Med-M, High-M
    df_market['cluster'] = kmeans.fit_predict(scaled_features)

    print("  > AI Model complete. Analyzing market clusters...")
    cluster_volatility = df_market.groupby('cluster')['volatility'].mean().sort_values()

    # Map market clusters: Low-Market, Medium-Market, High-Market
    market_cluster_mapping = {
        cluster_volatility.index[0]: "Low-M",
        cluster_volatility.index[1]: "Medium-M",
        cluster_volatility.index[2]: "High-M"
    }
    df_market['market_risk_label'] = df_market['cluster'].map(market_cluster_mapping)
    print(f"  > Market Cluster mapping: {market_cluster_mapping}")

    # --- Step 3: Final Labeling (Hybrid Approach) ---
    print("\nStep 3: Assigning Final Risk Labels...")
    final_labeled_schemes = []
    market_labeled_dict = df_market.set_index('ticker')['market_risk_label'].to_dict()

    for scheme in all_scheme_data:
        final_label = "Medium" # Default label

        # Rule 1: Manual Labels for Safest Categories
        if scheme['category'] in ['Fixed Deposit', 'Liquid Debt']:
            final_label = "Very Low"
        elif scheme['category'] == 'Gold Bond': # SGB
             final_label = "Very Low" # Government backed
        elif scheme['category'] == 'Gold ETF':
             final_label = "Low" # Gold is less volatile than equity

        # Rule 2: Use AI Labels for Market-Linked Categories
        elif scheme['has_market_data'] and scheme['ticker'] in market_labeled_dict:
            market_label = market_labeled_dict[scheme['ticker']]
            if market_label == "High-M":
                final_label = "High"
            elif market_label == "Medium-M":
                final_label = "Medium"
            elif market_label == "Low-M": # AI's low volatility market items
                 final_label = "Low" # Assign final "Low"

        # Rule 3: Category based override for High risk (if AI misses)
        if 'Small-Cap' in scheme['category'] or 'Sectoral' in scheme['category']:
             final_label = "High" # Always consider these high risk

        scheme['risk_label'] = final_label
        # Clean up temporary fields before saving
        scheme.pop('has_market_data', None)
        scheme.pop('volatility_manual', None)
        scheme.pop('sharpe_ratio_manual', None)
        scheme.pop('cluster', None)
        scheme.pop('market_risk_label', None)

        final_labeled_schemes.append(scheme)
        print(f"  > Labeled '{scheme['scheme_name']}' as '{final_label}'")

    print("\n--- AI Data Preparation Job v2.0 Complete ---")
    final_schemes_json = json.dumps(final_labeled_schemes, indent=4) # Pretty print directly
    return final_schemes_json

if __name__ == "__main__":
    final_schemes_json = run_ai_labeling_job()
    if final_schemes_json:
        print("\nFinal JSON Output (Saved to schemes_master_list_v2.json):")
        print(final_schemes_json)

        # Save to a NEW file to avoid overwriting the old one
        with open("schemes_master_list_v2.json", "w") as f:
            f.write(final_schemes_json)
        print("\nSuccessfully saved output to 'schemes_master_list_v2.json'")