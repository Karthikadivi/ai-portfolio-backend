# explainable_ai_agent.py
class ExplainableAIAgent:
    def run(self, fund_data, user_profile):
        reasons = []
        sharpe = fund_data.get('sharpe_ratio', 0) # Use .get for safety
        risk = fund_data.get('risk_label', 'Medium')
        category = fund_data.get('category', '')

        # Rule 1: Safety (FD, SGB, Liquid)
        if risk == "Very Low":
             if 'Fixed Deposit' in category:
                  reasons.append("Guaranteed Returns & Capital Safety (FD)")
             elif 'Gold Bond' in category: # SGB
                  reasons.append("Government Backed + Gold Exposure (SGB)")
             elif 'Liquid' in category:
                  reasons.append("Very Safe for Short Term Parking")
             return reasons[:2] # Very Low risk ku safety reason pothum

        # Rule 2: Sharpe Ratio
        if sharpe > 1.2: reasons.append(f"Excellent Risk-Adjusted Return (Sharpe: {sharpe:.2f})")
        elif sharpe > 0.8: reasons.append(f"Good Risk-Adjusted Return (Sharpe: {sharpe:.2f})")

        # Rule 3: Matching Profile
        if risk == 'Low' and user_profile in ["Conservative", "Moderate"]: reasons.append("Provides Stability & Lower Risk")
        if risk == 'Medium' and user_profile == 'Moderate': reasons.append("Matches your Balanced Profile")
        if risk == 'High' and user_profile == 'Aggressive': reasons.append("Matches your Aggressive Growth goal")

        # Rule 4: Category Specific
        if 'Index Fund' in category: reasons.append("Low-cost & Diversified Market Exposure")
        if 'Gold' in category: reasons.append("Hedge against Inflation (Gold)")
        if 'Small-Cap' in category: reasons.append("High Growth Potential (Small Cap)")
        if 'Large-Cap' in category: reasons.append("Invests in Stable Large Companies")

        if not reasons: reasons.append("A solid choice for diversification")
        return reasons[:2]