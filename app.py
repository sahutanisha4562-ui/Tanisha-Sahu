import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

BUSINESS_PRESETS = {
    "bakery": {"startup": 250000, "rent": 25000, "staff": 45000, "utilities": 10000, "marketing": 8000, "other": 12000, "margin": 0.42, "sales_factor": 1.0,
               "equipment": ["Oven and mixer", "Refrigerator", "Display counter", "Utensils and packaging"],
               "products": ["Cakes and pastries", "Bread and cookies", "Custom celebration orders"],
               "locations": ["Residential neighbourhood", "Near schools or offices", "High-footfall market"]},
    "clothing store": {"startup": 300000, "rent": 30000, "staff": 25000, "utilities": 7000, "marketing": 10000, "other": 15000, "margin": 0.35, "sales_factor": 1.0,
               "equipment": ["Racks and shelves", "Billing system", "Trial mirror and fitting room", "Initial inventory"],
               "products": ["Everyday wear", "Seasonal collections", "Accessories"],
               "locations": ["Busy market street", "Residential shopping area", "Near colleges"]},
    "cafe": {"startup": 450000, "rent": 35000, "staff": 50000, "utilities": 15000, "marketing": 10000, "other": 18000, "margin": 0.55, "sales_factor": 1.0,
               "equipment": ["Coffee machine", "Refrigerator", "Food preparation equipment", "Tables and seating"],
               "products": ["Tea and coffee", "Snacks and sandwiches", "Desserts"],
               "locations": ["College area", "Office district", "High-footfall neighbourhood"]},
    "mobile accessories": {"startup": 180000, "rent": 18000, "staff": 15000, "utilities": 4000, "marketing": 5000, "other": 8000, "margin": 0.32, "sales_factor": 1.0,
               "equipment": ["Display racks", "Billing device", "Storage cabinets", "Starter inventory"],
               "products": ["Phone covers", "Chargers and cables", "Screen protectors"],
               "locations": ["Electronics market", "Near colleges", "Busy shopping lane"]},
    "digital marketing": {"startup": 80000, "rent": 5000, "staff": 15000, "utilities": 3000, "marketing": 5000, "other": 7000, "margin": 0.65, "sales_factor": 1.0,
               "equipment": ["Laptop or desktop", "Reliable internet", "Design and analytics tools", "Portfolio website"],
               "products": ["Social media management", "Local business ads", "Content and design packages"],
               "locations": ["Home office", "Coworking space", "Remote-first setup"]},
    "tuition classes": {"startup": 100000, "rent": 12000, "staff": 15000, "utilities": 4000, "marketing": 4000, "other": 5000, "margin": 0.60, "sales_factor": 1.0,
               "equipment": ["Whiteboard", "Desks and chairs", "Study material", "Basic projector (optional)"],
               "products": ["School subject batches", "Exam preparation", "Weekend workshops"],
               "locations": ["Residential area", "Near schools", "Accessible neighbourhood"]},
}

def get_preset(business):
    key = business.lower().strip()
    for name, data in BUSINESS_PRESETS.items():
        if name in key or key in name:
            return name, data
    return "general service business", {
        "startup": 200000, "rent": 20000, "staff": 25000, "utilities": 7000,
        "marketing": 7000, "other": 10000, "margin": 0.40, "sales_factor": 1.0,
        "equipment": ["Essential tools and equipment", "Phone or computer", "Basic supplies"],
        "products": ["Core product or service", "Premium option", "Custom packages"],
        "locations": ["Target-customer neighbourhood", "Small shared workspace", "Online-first model"]
    }

def make_ai_plan(details):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[
                {"role": "system", "content": (
                    "You are a practical small-business planning assistant for India. "
                    "Give concise, cautious, actionable advice. Do not claim estimates are guaranteed. "
                    "Return valid JSON with keys: summary (string), ideas (array of strings), "
                    "marketing (array of strings), risks (array of strings), first_steps (array of strings). "
                    "Use INR and respect the user's budget and location."
                )},
                {"role": "user", "content": str(details)}
            ]
        )
        import json
        text = response.output_text
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end+1])
    except Exception:
        return None
    return None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or request.form
    business = str(data.get("business", "")).strip()
    location = str(data.get("location", "Pune")).strip() or "Pune"
    budget = max(0, float(data.get("budget", 300000) or 0))
    customers = max(1, int(float(data.get("customers", 30) or 30)))
    avg_sale = max(0, float(data.get("avg_sale", 500) or 0))
    if not business:
        return jsonify({"error": "Please enter a business idea."}), 400

    preset_name, p = get_preset(business)
    startup_cost = p["startup"]
    monthly_fixed = p["rent"] + p["staff"] + p["utilities"] + p["marketing"] + p["other"]
    monthly_revenue = customers * avg_sale * 30
    gross_margin = p["margin"]
    variable_costs = monthly_revenue * (1 - gross_margin)
    monthly_profit = monthly_revenue - variable_costs - monthly_fixed
    break_even_months = round(startup_cost / monthly_profit, 1) if monthly_profit > 0 else None
    contingency = startup_cost * 0.10
    recommended_fund = startup_cost + contingency + monthly_fixed * 3
    cash_gap = max(0, recommended_fund - budget)
    break_even_revenue = monthly_fixed / gross_margin if gross_margin else 0
    ai_plan = make_ai_plan({
        "business": business, "location": location, "budget_inr": budget,
        "estimated_startup_cost_inr": startup_cost, "monthly_fixed_cost_inr": monthly_fixed,
        "estimated_monthly_revenue_inr": monthly_revenue, "estimated_monthly_profit_inr": monthly_profit
    })
    return jsonify({
        "business": business, "matched_category": preset_name, "location": location, "budget": round(budget),
        "startup_cost": round(startup_cost), "contingency": round(contingency), "monthly_fixed": round(monthly_fixed),
        "monthly_revenue": round(monthly_revenue), "variable_costs": round(variable_costs),
        "monthly_profit": round(monthly_profit), "break_even_months": break_even_months,
        "recommended_fund": round(recommended_fund), "cash_gap": round(cash_gap),
        "break_even_revenue": round(break_even_revenue), "equipment": p["equipment"],
        "products": p["products"], "locations": p["locations"],
        "marketing": [
            "Create a Google Business Profile and collect genuine customer reviews",
            "Post short videos and offers on Instagram and WhatsApp",
            "Partner with nearby offices, colleges or community groups",
            "Track which products bring repeat customers"
        ],
        "risks": [
            "Actual sales may be lower than expected during the first months",
            "Confirm rent, deposits, licences, taxes and supplier prices locally",
            "Keep emergency funds and avoid spending the entire budget on setup"
        ],
        "ai_plan": ai_plan,
        "notice": "Planning estimate only. Replace assumptions with local quotations and real customer research before investing."
    })

if __name__ == "__main__":
    app.run(debug=True)
