# user_profile_agent.py
class UserProfileAgent:
    def run(self, user_details):
        q1 = user_details.get("Quiz_Answer_1") # Market drop reaction
        q2 = user_details.get("Quiz_Answer_2") # Primary goal
        horizon = user_details.get("horizon") # Investment Horizon

        # Rule 1: Highest Risk
        if (q1 == "C" or q2 == "C") and horizon == "7+ Years":
            return "Aggressive"

        # Rule 2: Lowest Risk (Capital Preservation)
        if q2 == "A": # Goal is Capital Preservation
             return "Very Conservative"
        if q1 == "A": # Sell everything on drop
             return "Conservative"

        # Rule 3: Medium Risk
        if q1 == "B" or q2 == "B": # Hold or Balanced goal
            if horizon == "7+ Years":
                return "Moderate"
            else: # Shorter horizon but balanced
                 return "Conservative" # Be safer for shorter term

        # Default fallback
        return "Moderate"