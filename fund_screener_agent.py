# fund_screener_agent.py
import json # JSON load panna import pannanum

class FundScreenerAgent:
    def __init__(self): # Data va inga load pannuvom
        self.schemes_db = []
        try:
            # Puthu file ah load pannunga
            with open("schemes_master_list_v2.json", "r") as f:
                self.schemes_db = json.load(f)
            print(f"FundScreenerAgent v2.0 initialized with {len(self.schemes_db)} diverse schemes.")
        except Exception as e:
             print(f"ERROR loading schemes_master_list_v2.json: {e}")


    def run(self, user_profile):
        shortlist = []

        if user_profile == "Aggressive":
            shortlist = [s for s in self.schemes_db if s['risk_label'] in ['High', 'Medium']]
            shortlist.sort(key=lambda x: x.get('sharpe_ratio', 0), reverse=True) # Use .get for safety

        elif user_profile == "Moderate":
            shortlist = [s for s in self.schemes_db if s['risk_label'] in ['Medium', 'Low']]
            shortlist.sort(key=lambda x: x.get('sharpe_ratio', 0), reverse=True)

        elif user_profile == "Conservative":
            shortlist = [s for s in self.schemes_db if s['risk_label'] in ['Low', 'Very Low']]
            # Conservative ku safety mukkiyam, Sharpe Ratio illa
            shortlist.sort(key=lambda x: x.get('volatility', 1), reverse=False) # Sort by lowest volatility

        elif user_profile == "Very Conservative":
            shortlist = [s for s in self.schemes_db if s['risk_label'] == 'Very Low']
            # Ingayum safety thaan mukkiyam
            shortlist.sort(key=lambda x: x.get('volatility', 1), reverse=False)

        return shortlist[:20] # Top 20 ah anuppalam