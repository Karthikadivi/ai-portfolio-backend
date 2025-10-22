import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# Agents ah import pannunga
from user_profile_agent import UserProfileAgent
from fund_screener_agent import FundScreenerAgent
from explainable_ai_agent import ExplainableAIAgent

# --- 1. SETUP ---
app = Flask(__name__)
CORS(app) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'THIS_IS_A_VERY_SECRET_KEY_12345'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# --- Global variables ---
# SCHEMES_DATA inga thevai illai, ScreenerAgent kulla load pannuthu
profile_agent = None
screener_agent = None
explainer_agent = None

# --- 2. DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    portfolios = db.relationship('Portfolio', backref='owner', lazy=True)

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_name = db.Column(db.String(100), nullable=False)
    allocation = db.Column(db.String(200), nullable=False)
    schemes = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- 3. AI AGENTS INITIALIZATION ---
def init_agents():
    global profile_agent, screener_agent, explainer_agent
    try:
        profile_agent = UserProfileAgent()
        screener_agent = FundScreenerAgent() # Data va athuve load pannidum
        explainer_agent = ExplainableAIAgent()
        if not screener_agent.schemes_db: # Check if data loaded
             raise Exception("Scheme data failed to load in FundScreenerAgent.")
        print("--- Backend API Ready v2.0: Database & 3 Agents Initialized ---")
    except Exception as e:
        print(f"FATAL ERROR during Agent Init: {e}")

# --- 4. API ENDPOINTS ---

@app.route("/signup", methods=["POST"])
def signup():
    # (No change needed here)
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user_exists = User.query.filter_by(email=email).first()
    if user_exists: return jsonify({"error": "Email already exists"}), 409
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    # (No change needed here)
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify({"error": "Invalid email or password"}), 401

@app.route("/generate_portfolio", methods=["POST"])
def generate_portfolio_route():
    print("\n--- New Portfolio Request v2.0 Received ---")
    user_details = request.json

    # Agents ah use pannunga
    risk_profile = profile_agent.run(user_details)
    print(f"[Agent 1 - Profile]: User is '{risk_profile}'")
    shortlisted_funds = screener_agent.run(risk_profile)
    print(f"[Agent 2 - Screener]: Found {len(shortlisted_funds)} matching funds for '{risk_profile}'.")

    if not shortlisted_funds:
         return jsonify({"error": f"No suitable funds found for profile '{risk_profile}'"}), 404

    # --- Puthu, Updated Optimization Logic ---
    final_portfolio_plan = {}
    final_schemes_list = [] # Format: [{"fund": {...}, "percent": X}, ...]

    # Helper function to find best fund by category/risk
    def find_best(category_keyword, risk_levels, current_shortlist):
         for fund in current_shortlist:
              if any(keyword in fund['category'] for keyword in category_keyword) and fund['risk_label'] in risk_levels:
                   return fund
         # Fallback: just return the top fund from the shortlist if specific category not found
         if current_shortlist:
            return current_shortlist[0]
         return None # Should not happen if shortlist is valid

    if risk_profile == "Aggressive":
        final_portfolio_plan["allocation"] = {"High Risk Equity/Stock": 60, "Medium Risk Equity/Index": 20, "Gold/Debt": 20}
        fund1 = find_best(['Stock', 'Small-Cap', 'Mid-Cap'], ['High'], shortlisted_funds)
        fund2 = find_best(['Flexi-Cap', 'Large-Cap'], ['High','Medium'], [f for f in shortlisted_funds if f != fund1]) # Avoid duplicate
        fund3 = find_best(['Index Fund'], ['Medium'], shortlisted_funds)
        fund4 = find_best(['Gold', 'Liquid'], ['Low', 'Very Low'], screener_agent.run("Conservative"))
        if fund1: final_schemes_list.append({"fund": fund1, "percent": 30})
        if fund2: final_schemes_list.append({"fund": fund2, "percent": 30})
        if fund3: final_schemes_list.append({"fund": fund3, "percent": 20})
        if fund4: final_schemes_list.append({"fund": fund4, "percent": 20})

    elif risk_profile == "Moderate":
        final_portfolio_plan["allocation"] = {"Medium Risk Equity/Index": 40, "Low Risk Debt/Gold": 40, "Very Low Risk FD/Liquid": 20}
        fund1 = find_best(['Index Fund', 'Large-Cap', 'Flexi-Cap'], ['Medium'], shortlisted_funds)
        fund2 = find_best(['Gold', 'Short-Term Debt'], ['Low'], shortlisted_funds)
        fund3 = find_best(['Fixed Deposit', 'Liquid'], ['Very Low'], screener_agent.run("Very Conservative"))
        if fund1: final_schemes_list.append({"fund": fund1, "percent": 40})
        if fund2: final_schemes_list.append({"fund": fund2, "percent": 40})
        if fund3: final_schemes_list.append({"fund": fund3, "percent": 20})

    elif risk_profile == "Conservative":
        final_portfolio_plan["allocation"] = {"Low Risk Gold/Debt": 50, "Very Low Risk FD/Liquid": 50}
        fund1 = find_best(['Gold', 'Debt'], ['Low'], shortlisted_funds)
        fund2 = find_best(['Fixed Deposit', 'Liquid', 'SGB'], ['Very Low'], shortlisted_funds)
        if fund1: final_schemes_list.append({"fund": fund1, "percent": 50})
        if fund2: final_schemes_list.append({"fund": fund2, "percent": 50})

    elif risk_profile == "Very Conservative":
        final_portfolio_plan["allocation"] = {"Fixed Deposit / SGB": 70, "Liquid Fund": 30}
        fund1 = find_best(['Fixed Deposit', 'SGB'], ['Very Low'], shortlisted_funds)
        fund2 = find_best(['Liquid'], ['Very Low'], [f for f in shortlisted_funds if f != fund1])
        if fund1: final_schemes_list.append({"fund": fund1, "percent": 70})
        if fund2: final_schemes_list.append({"fund": fund2, "percent": 30})

    # --- Recalculate percentages if some funds were not found ---
    total_percent = sum(item['percent'] for item in final_schemes_list)
    if total_percent > 0 and total_percent != 100:
         print(f"WARN: Adjusting percentages from {total_percent}% to 100%")
         for item in final_schemes_list:
              item['percent'] = round((item['percent'] / total_percent) * 100)
    # Ensure it sums to 100 after rounding
    current_sum = sum(item['percent'] for item in final_schemes_list)
    if current_sum != 100 and final_schemes_list:
        diff = 100 - current_sum
        final_schemes_list[0]['percent'] += diff # Add difference to the first item

    print(f"[Agent 3 - Manager v2.0]: Portfolio structure created.")

    # XAI Agent ah koopidunga
    final_explained_schemes = []
    for item in final_schemes_list:
        fund_object = item["fund"]
        fund_percent = item["percent"]
        reasons = explainer_agent.run(fund_object, risk_profile)
        print(f"[Agent 4 - Explainer v2.0]: Explaining '{fund_object['scheme_name']}'...")
        fund_object['explanation'] = reasons
        fund_object['percent'] = fund_percent
        # Remove unnecessary internal data before sending to frontend
        fund_object.pop('ticker', None) 
        fund_object.pop('volatility', None) 
        fund_object.pop('sharpe_ratio', None) 
        final_explained_schemes.append(fund_object)

    final_response = {
        "profile": risk_profile,
        "allocation": final_portfolio_plan.get("allocation", {}), # Use .get for safety
        "schemes": final_explained_schemes
    }

    print("--- Complete Response v2.0 Ready. Sending to Frontend. ---")
    return jsonify(final_response)

@app.route("/save_portfolio", methods=["POST"])
@jwt_required() 
def save_portfolio():
    # (No change needed here)
    current_user_id = get_jwt_identity()
    data = request.json
    new_portfolio = Portfolio(
        profile_name = data.get('profile_name', 'My Portfolio'),
        allocation = json.dumps(data.get('allocation')),
        schemes = json.dumps(data.get('schemes')),
        user_id = current_user_id
    )
    db.session.add(new_portfolio)
    db.session.commit()
    return jsonify({"message": "Portfolio saved successfully"}), 201

# --- 5. RUN THE SERVER ---
if __name__ == "__main__":
    init_agents() # Agents ah initialize pannunga
    with app.app_context():
        db.create_all() 
        print("Database tables checked/created.")

    app.run(host='0.0.0.0', port=5000, debug=True)