"""
Generate realistic test data for WealthTech API
Creates clients and documents that match real-world financial scenarios
"""
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Realistic first and last names
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Emma", "Sophia", "Olivia", "Ava", "Isabella", "Mia", "Charlotte", "Amelia"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"
]

WEALTH_TIERS = {
    "mass_market": {"min": 10_000, "max": 100_000, "weight": 50},
    "mass_affluent": {"min": 100_000, "max": 500_000, "weight": 30},
    "high_net_worth": {"min": 500_000, "max": 5_000_000, "weight": 15},
    "ultra_high_net_worth": {"min": 5_000_000, "max": 50_000_000, "weight": 5}
}

DOCUMENT_TEMPLATES = {
    "tax_return": [
        "Tax Return for fiscal year {year}. Total income: ${income:,}. Total deductions: ${deductions:,}. Tax liability: ${tax:,}. Filing status: {status}. Dependents: {dependents}. State: {state}. Federal withholding: ${withholding:,}.",
        "Individual Income Tax Return {year}. Wages and salaries: ${wages:,}. Investment income: ${investment:,}. Capital gains: ${capital_gains:,}. Itemized deductions: ${deductions:,}. Taxable income: ${taxable:,}. Adjusted gross income: ${agi:,}.",
        "Annual tax filing {year}. Self-employment income: ${self_income:,}. Retirement contributions: ${retirement:,}. Health savings account: ${hsa:,}. Mortgage interest: ${mortgage:,}. Charitable donations: ${charity:,}. Refund amount: ${refund:,}."
    ],
    "bank_statement": [
        "Monthly bank statement for {month} {year}. Account ending in {account}. Beginning balance: ${beginning:,}. Total deposits: ${deposits:,}. Total withdrawals: ${withdrawals:,}. Ending balance: ${ending:,}. Interest earned: ${interest:.2f}.",
        "Checking account statement {month} {year}. Account number: ****{account}. Opening balance: ${opening:,}. Direct deposits: {num_deposits}. ATM withdrawals: {num_atm}. Check payments: {num_checks}. Service fees: ${fees:.2f}. Closing balance: ${closing:,}.",
        "Savings account summary {month} {year}. Account: ****{account}. Previous balance: ${prev:,}. Deposits this period: ${deposits:,}. Withdrawals: ${withdrawals:,}. Interest rate: {rate}% APY. Interest earned: ${interest:.2f}. Current balance: ${current:,}."
    ],
    "investment_report": [
        "Investment portfolio quarterly report Q{quarter} {year}. Total portfolio value: ${portfolio:,}. Stocks: ${stocks:,} ({stock_pct}%). Bonds: ${bonds:,} ({bond_pct}%). Cash: ${cash:,}. Quarter return: {return_pct}%. Year-to-date return: {ytd_pct}%. Asset allocation maintains target ranges.",
        "Portfolio performance review {month} {year}. Equities: ${equities:,}. Fixed income: ${fixed_income:,}. Alternative investments: ${alternatives:,}. Total value: ${total:,}. Month return: {monthly_return}%. Dividends received: ${dividends:,}. Realized gains: ${gains:,}.",
        "Annual investment summary {year}. Beginning value: ${beginning:,}. Contributions: ${contributions:,}. Withdrawals: ${withdrawals:,}. Market gains/losses: ${market_change:,}. Ending value: ${ending:,}. Total return: {total_return}%. Benchmark comparison: {benchmark}%."
    ],
    "insurance_policy": [
        "Life insurance policy #{policy}. Policyholder: {name}. Coverage amount: ${coverage:,}. Policy type: {policy_type}. Premium: ${premium:,} annually. Beneficiaries: {beneficiaries}. Effective date: {effective}. Renewal date: {renewal}.",
        "Health insurance policy documentation. Policy number: {policy}. Coverage: {coverage_type}. Deductible: ${deductible:,}. Out-of-pocket maximum: ${oop_max:,}. Monthly premium: ${premium:,}. Copay: ${copay}. Coinsurance: {coinsurance}%.",
        "Property and casualty insurance. Policy: {policy}. Property address: {address}. Coverage: ${coverage:,}. Deductible: ${deductible:,}. Premium: ${premium:,}/year. Liability limit: ${liability:,}. Effective: {effective}. Expiration: {expiration}."
    ],
    "utility_bill": [
        "Electric utility bill for {month} {year}. Service address: {address}. Account: {account}. Usage: {kwh} kWh. Rate: ${rate:.3f}/kWh. Service charge: ${service:.2f}. Total amount due: ${total:.2f}. Due date: {due_date}. Can serve as proof of residence.",
        "Natural gas statement {month} {year}. Customer: {name}. Service location: {address}. Usage: {therms} therms. Delivery charges: ${delivery:.2f}. Supply charges: ${supply:.2f}. Taxes: ${tax:.2f}. Total: ${total:.2f}. Payment due: {due_date}.",
        "Water and sewer bill {month} {year}. Account number: {account}. Property: {address}. Water usage: {gallons} gallons. Water charges: ${water:.2f}. Sewer charges: ${sewer:.2f}. Total due: ${total:.2f}. Billing period: {period}."
    ],
    "mortgage_statement": [
        "Mortgage statement {month} {year}. Loan number: {loan}. Property: {address}. Principal balance: ${principal:,}. Monthly payment: ${payment:,}. Principal paid: ${principal_paid:.2f}. Interest paid: ${interest_paid:.2f}. Escrow balance: ${escrow:,}. Interest rate: {rate}%.",
        "Home loan account summary {month} {year}. Account: {account}. Original loan amount: ${original:,}. Current balance: ${balance:,}. Payment due: ${payment:,}. Payment breakdown - Principal: ${p:.2f}, Interest: ${i:.2f}, Taxes: ${t:.2f}, Insurance: ${ins:.2f}.",
        "Mortgage year-end statement {year}. Loan: {loan}. Payments made: {num_payments}. Total principal paid: ${principal_paid:,}. Total interest paid: ${interest_paid:,}. Remaining balance: ${balance:,}. Property address: {address}. For tax purposes."
    ],
    "estate_document": [
        "Last Will and Testament. Testator: {name}. Executed: {date}. Primary beneficiaries: {beneficiaries}. Executor: {executor}. Assets distribution outlined per attached schedule. Witnessed and notarized. Legal document for estate planning purposes.",
        "Living Trust document. Grantor and Trustee: {name}. Established: {date}. Trust assets: ${assets:,}. Successor trustee: {successor}. Beneficiaries: {beneficiaries}. Trust type: Revocable Living Trust. Distribution terms specified in Article IV.",
        "Power of Attorney designation. Principal: {name}. Attorney-in-fact: {agent}. Powers granted: Financial and healthcare decisions. Effective: {effective}. Durable provision: Remains in effect during incapacity. Notarized: {date}."
    ],
    "loan_document": [
        "Personal loan agreement. Borrower: {name}. Loan amount: ${amount:,}. Interest rate: {rate}% APR. Term: {term} months. Monthly payment: ${payment:.2f}. Purpose: {purpose}. Origination date: {origination}. Maturity date: {maturity}.",
        "Auto loan statement {month} {year}. Loan: {loan}. Vehicle: {vehicle}. Original amount: ${original:,}. Current balance: ${balance:,}. Payment: ${payment:.2f}/month. Rate: {rate}%. Payments remaining: {remaining}. Payoff amount: ${payoff:,}.",
        "Student loan servicer statement {month} {year}. Borrower: {name}. Loan type: {loan_type}. Balance: ${balance:,}. Interest rate: {rate}%. Monthly payment: ${payment:.2f}. Forbearance status: {forbearance}. Repayment plan: {plan}."
    ],
    "retirement_statement": [
        "401(k) quarterly statement Q{quarter} {year}. Account holder: {name}. Employer: {employer}. Total balance: ${balance:,}. Employee contributions: ${employee:,}. Employer match: ${match:,}. Investment allocation: {allocation}. Vested balance: ${vested:,}.",
        "IRA account statement {month} {year}. Account: {account}. Account type: {type} IRA. Beginning balance: ${beginning:,}. Contributions: ${contributions:,}. Earnings/losses: ${earnings:,}. Ending balance: ${ending:,}. Year-to-date return: {ytd}%.",
        "Pension benefit statement {year}. Participant: {name}. Service years: {years}. Vested percentage: {vested}%. Estimated monthly benefit at age {age}: ${benefit:,}. Survivor benefit: ${survivor:,}. Early retirement: Available at age {early_age}."
    ]
}

def generate_client(wealth_tier: str) -> Dict:
    """Generate a realistic client"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Generate email variations
    email_formats = [
        f"{first_name.lower()}.{last_name.lower()}@gmail.com",
        f"{first_name.lower()}{last_name.lower()}@yahoo.com",
        f"{first_name[0].lower()}{last_name.lower()}@outlook.com",
        f"{first_name.lower()}.{last_name.lower()}{random.randint(1,99)}@hotmail.com"
    ]
    
    tier_info = WEALTH_TIERS[wealth_tier]
    net_worth = random.randint(tier_info["min"], tier_info["max"])
    
    descriptions = [
        f"{wealth_tier.replace('_', ' ').title()} client with net worth of approximately ${net_worth:,}",
        f"Investment portfolio totaling ${net_worth:,}. {wealth_tier.replace('_', ' ').title()} segment.",
        f"Wealth management client. Assets: ${net_worth:,}. Category: {wealth_tier.replace('_', ' ')}.",
        f"Client since {random.randint(2015, 2023)}. Total assets: ${net_worth:,}. Tier: {wealth_tier.replace('_', ' ')}."
    ]
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": random.choice(email_formats),
        "description": random.choice(descriptions)
    }


def generate_document(client_name: str, doc_type: str) -> Dict:
    """Generate a realistic document based on type"""
    template = random.choice(DOCUMENT_TEMPLATES[doc_type])
    
    current_year = datetime.now().year
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    
    # Generate realistic values based on document type
    values = {}
    
    if doc_type == "tax_return":
        income = random.randint(50_000, 500_000)
        values = {
            "year": random.randint(2020, 2024),
            "income": income,
            "deductions": int(income * random.uniform(0.15, 0.30)),
            "tax": int(income * random.uniform(0.15, 0.28)),
            "status": random.choice(["Single", "Married Filing Jointly", "Head of Household"]),
            "dependents": random.randint(0, 4),
            "state": random.choice(["CA", "NY", "TX", "FL", "IL", "PA", "OH"]),
            "withholding": int(income * random.uniform(0.18, 0.25)),
            "wages": int(income * 0.7),
            "investment": int(income * 0.2),
            "capital_gains": int(income * 0.1),
            "taxable": int(income * 0.85),
            "agi": int(income * 0.92),
            "self_income": int(income * 0.6),
            "retirement": random.randint(5000, 22500),
            "hsa": random.randint(0, 7750),
            "mortgage": random.randint(8000, 25000),
            "charity": random.randint(1000, 15000),
            "refund": random.randint(500, 8000)
        }
        
    elif doc_type == "bank_statement":
        beginning = random.randint(5_000, 50_000)
        deposits = random.randint(3_000, 15_000)
        withdrawals = random.randint(2_000, 12_000)
        values = {
            "month": random.choice(months),
            "year": random.choice([2023, 2024]),
            "account": str(random.randint(1000, 9999)),
            "beginning": beginning,
            "deposits": deposits,
            "withdrawals": withdrawals,
            "ending": beginning + deposits - withdrawals,
            "interest": random.uniform(5, 50),
            "opening": beginning,
            "num_deposits": random.randint(5, 15),
            "num_atm": random.randint(3, 10),
            "num_checks": random.randint(2, 8),
            "fees": random.uniform(10, 35),
            "closing": beginning + deposits - withdrawals,
            "prev": beginning,
            "current": beginning + deposits - withdrawals,
            "rate": round(random.uniform(0.5, 4.5), 2)
        }
        
    elif doc_type == "investment_report":
        portfolio = random.randint(100_000, 5_000_000)
        stock_pct = random.randint(40, 70)
        bond_pct = random.randint(20, 40)
        values = {
            "quarter": random.randint(1, 4),
            "year": random.choice([2023, 2024]),
            "month": random.choice(months),
            "portfolio": portfolio,
            "stocks": int(portfolio * stock_pct / 100),
            "bonds": int(portfolio * bond_pct / 100),
            "cash": int(portfolio * (100 - stock_pct - bond_pct) / 100),
            "stock_pct": stock_pct,
            "bond_pct": bond_pct,
            "return_pct": round(random.uniform(-5, 15), 2),
            "ytd_pct": round(random.uniform(-3, 20), 2),
            "equities": int(portfolio * 0.6),
            "fixed_income": int(portfolio * 0.3),
            "alternatives": int(portfolio * 0.1),
            "total": portfolio,
            "monthly_return": round(random.uniform(-2, 3), 2),
            "dividends": random.randint(1000, 10000),
            "gains": random.randint(5000, 50000),
            "beginning": int(portfolio * 0.9),
            "contributions": random.randint(5000, 50000),
            "withdrawals": random.randint(0, 20000),
            "market_change": random.randint(-50000, 100000),
            "ending": portfolio,
            "total_return": round(random.uniform(-5, 18), 2),
            "benchmark": round(random.uniform(-3, 15), 2)
        }
        
    elif doc_type == "utility_bill":
        values = {
            "month": random.choice(months),
            "year": random.choice([2023, 2024]),
            "address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}, {random.choice(['San Francisco', 'New York', 'Chicago', 'Boston', 'Seattle'])}, {random.choice(['CA', 'NY', 'IL', 'MA', 'WA'])} {random.randint(10000, 99999)}",
            "account": str(random.randint(100000, 999999)),
            "kwh": random.randint(300, 1500),
            "rate": random.uniform(0.10, 0.30),
            "service": random.uniform(10, 25),
            "total": random.uniform(80, 400),
            "due_date": (datetime.now() + timedelta(days=random.randint(10, 30))).strftime("%B %d, %Y"),
            "name": client_name,
            "therms": random.randint(20, 150),
            "delivery": random.uniform(20, 60),
            "supply": random.uniform(30, 90),
            "tax": random.uniform(5, 20),
            "gallons": random.randint(3000, 15000),
            "water": random.uniform(40, 100),
            "sewer": random.uniform(30, 80),
            "period": f"{random.choice(months)} 1-30, {random.choice([2023, 2024])}"
        }
        
    elif doc_type == "mortgage_statement":
        principal = random.randint(200_000, 800_000)
        rate = random.uniform(3.0, 6.5)
        values = {
            "month": random.choice(months),
            "year": random.choice([2023, 2024]),
            "loan": str(random.randint(100000000, 999999999)),
            "address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}, {random.choice(['San Francisco', 'New York', 'Chicago', 'Boston', 'Seattle'])}, {random.choice(['CA', 'NY', 'IL', 'MA', 'WA'])} {random.randint(10000, 99999)}",
            "principal": principal,
            "payment": int((principal * (rate/100/12)) / (1 - (1 + rate/100/12)**(-360))),
            "principal_paid": random.uniform(500, 2000),
            "interest_paid": random.uniform(1000, 4000),
            "escrow": random.randint(5000, 15000),
            "rate": round(rate, 2),
            "account": str(random.randint(100000000, 999999999)),
            "original": int(principal * 1.2),
            "balance": principal,
            "p": random.uniform(500, 2000),
            "i": random.uniform(1000, 4000),
            "t": random.uniform(200, 800),
            "ins": random.uniform(100, 400),
            "num_payments": random.randint(1, 12)
        }
        
    elif doc_type == "insurance_policy":
        values = {
            "policy": str(random.randint(1000000, 9999999)),
            "name": client_name,
            "coverage": random.randint(100_000, 5_000_000),
            "policy_type": random.choice(["Term Life", "Whole Life", "Universal Life"]),
            "premium": random.randint(500, 15000),
            "beneficiaries": random.choice(["Spouse", "Children", "Estate", "Trust"]),
            "effective": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%B %d, %Y"),
            "renewal": (datetime.now() + timedelta(days=random.randint(180, 365))).strftime("%B %d, %Y"),
            "address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}, {random.choice(['San Francisco', 'New York', 'Chicago', 'Boston', 'Seattle'])}, {random.choice(['CA', 'NY', 'IL', 'MA', 'WA'])} {random.randint(10000, 99999)}",
            "deductible": random.randint(500, 5000),
            "liability": random.randint(100_000, 1_000_000),
            "expiration": (datetime.now() + timedelta(days=random.randint(180, 365))).strftime("%B %d, %Y"),
            "coverage_type": random.choice(["Comprehensive", "HDHP", "PPO", "HMO", "EPO"]),
            "oop_max": random.randint(3000, 10000),
            "copay": random.choice(["$20", "$30", "$40", "$50"]),
            "coinsurance": random.choice([10, 20, 30])
        }
        
    elif doc_type == "estate_document":
        values = {
            "name": client_name,
            "date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%B %d, %Y"),
            "beneficiaries": random.choice(["Spouse and children", "Children only", "Charitable organizations", "Trust"]),
            "executor": random.choice(["Spouse", "Adult child", "Attorney", "Trust company"]),
            "assets": random.randint(500_000, 10_000_000),
            "successor": random.choice(["Adult child", "Sibling", "Attorney", "Trust company"]),
            "agent": random.choice(["Spouse", "Adult child", "Sibling"]),
            "effective": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%B %d, %Y")
        }
        
    elif doc_type == "loan_document":
        amount = random.randint(10_000, 500_000)
        rate = random.uniform(4.0, 12.0)
        term = random.choice([12, 24, 36, 48, 60])
        monthly_payment = (amount * (rate/100/12)) / (1 - (1 + rate/100/12)**(-term))
        values = {
            "name": client_name,
            "amount": amount,
            "rate": round(rate, 2),
            "term": term,
            "payment": round(monthly_payment, 2),
            "purpose": random.choice(["Auto purchase", "Home improvement", "Debt consolidation", "Business investment", "Education"]),
            "origination": (datetime.now() - timedelta(days=random.randint(30, 180))).strftime("%B %d, %Y"),
            "maturity": (datetime.now() + timedelta(days=term * 30)).strftime("%B %d, %Y"),
            "month": random.choice(months),
            "year": random.choice([2023, 2024]),
            "loan": str(random.randint(100000000, 999999999)),
            "vehicle": random.choice(["2023 Honda Accord", "2022 Toyota Camry", "2024 BMW 3 Series", "2023 Tesla Model 3"]),
            "original": amount,
            "balance": int(amount * random.uniform(0.3, 0.9)),
            "remaining": random.randint(6, term - 6),
            "payoff": int(amount * random.uniform(0.3, 0.9)),
            "loan_type": random.choice(["Federal Direct", "Private", "Stafford", "Parent PLUS"]),
            "forbearance": random.choice(["Active", "Inactive", "Pending"]),
            "plan": random.choice(["Standard", "Income-driven", "Extended", "Graduated"])
        }
        
    elif doc_type == "retirement_statement":
        balance = random.randint(50_000, 2_000_000)
        values = {
            "quarter": random.randint(1, 4),
            "year": random.choice([2023, 2024]),
            "month": random.choice(months),
            "name": client_name,
            "employer": random.choice(["Tech Corp", "Financial Services Inc", "Healthcare Systems", "Manufacturing Co"]),
            "balance": balance,
            "employee": random.randint(5000, 25000),
            "match": random.randint(2500, 15000),
            "allocation": random.choice(["60% Stocks, 30% Bonds, 10% Cash", "80% Stocks, 20% Bonds", "50% Stocks, 40% Bonds, 10% Real Estate"]),
            "vested": int(balance * random.uniform(0.8, 1.0)),
            "account": str(random.randint(100000000, 999999999)),
            "type": random.choice(["Traditional", "Roth", "SEP"]),
            "beginning": int(balance * 0.95),
            "contributions": random.randint(5000, 25000),
            "earnings": random.randint(-10000, 50000),
            "ending": balance,
            "ytd": round(random.uniform(-5, 15), 2),
            "years": random.randint(5, 30),
            "vested_pct": random.randint(80, 100),
            "age": random.randint(55, 70),
            "benefit": random.randint(2000, 8000),
            "survivor": random.randint(1500, 6000),
            "early_age": random.randint(55, 62)
        }
        
    content = template.format(**values)
    
    # Generate appropriate titles
    titles = {
        "tax_return": f"Tax Return {values.get('year', 2024)}",
        "bank_statement": f"Bank Statement - {values.get('month', 'January')} {values.get('year', 2024)}",
        "investment_report": f"Investment Portfolio Report Q{values.get('quarter', 1)} {values.get('year', 2024)}",
        "utility_bill": f"Utility Bill - {values.get('month', 'January')} {values.get('year', 2024)}",
        "mortgage_statement": f"Mortgage Statement - {values.get('month', 'January')} {values.get('year', 2024)}",
        "insurance_policy": f"Insurance Policy #{values.get('policy', 'N/A')}",
        "estate_document": "Estate Planning Document",
        "loan_document": "Loan Agreement",
        "retirement_statement": f"Retirement Account Statement - {values.get('month', 'Q1')} {values.get('year', 2024)}"
    }
    
    return {
        "title": titles.get(doc_type, f"{doc_type.replace('_', ' ').title()} Document"),
        "content": content
    }


def generate_test_data(num_clients: int = 100, docs_per_client_range: tuple = (10, 50)) -> List[Dict]:
    """Generate complete test dataset"""
    print(f"Generating {num_clients} clients with {docs_per_client_range[0]}-{docs_per_client_range[1]} documents each...")
    
    clients_data = []
    
    # Determine wealth distribution
    for i in range(num_clients):
        # Weighted random selection of wealth tier
        tier = random.choices(
            list(WEALTH_TIERS.keys()),
            weights=[WEALTH_TIERS[t]["weight"] for t in WEALTH_TIERS.keys()]
        )[0]
        
        client = generate_client(tier)
        client_name = f"{client['first_name']} {client['last_name']}"
        
        # Generate documents for this client
        num_docs = random.randint(*docs_per_client_range)
        documents = []
        
        # Weight document types by likelihood
        doc_type_weights = {
            "bank_statement": 25,
            "investment_report": 20,
            "tax_return": 15,
            "utility_bill": 15,
            "mortgage_statement": 10,
            "insurance_policy": 5,
            "retirement_statement": 5,
            "loan_document": 3,
            "estate_document": 2
        }
        
        for _ in range(num_docs):
            doc_type = random.choices(
                list(doc_type_weights.keys()),
                weights=list(doc_type_weights.values())
            )[0]
            
            documents.append(generate_document(client_name, doc_type))
        
        clients_data.append({
            "client": client,
            "documents": documents
        })
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_clients} clients...")
    
    print(f"✓ Generated {num_clients} clients with {sum(len(c['documents']) for c in clients_data)} total documents")
    return clients_data


def save_test_data(data: List[Dict], filename: str = "test_data.json"):
    """Save generated data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved test data to {filename}")


if __name__ == "__main__":
    # Generate different dataset sizes
    
    # Small dataset (for quick testing)
    small_data = generate_test_data(num_clients=10, docs_per_client_range=(5, 15))
    save_test_data(small_data, "test_data_small.json")
    
    # Medium dataset (realistic)
    medium_data = generate_test_data(num_clients=100, docs_per_client_range=(10, 50))
    save_test_data(medium_data, "test_data_medium.json")
    
    # Large dataset (stress test)
    # large_data = generate_test_data(num_clients=1000, docs_per_client_range=(20, 100))
    # save_test_data(large_data, "test_data_large.json")
    
    print("\n✓ Test data generation complete!")
    print("\nDataset sizes:")
    print(f"  Small: {len(small_data)} clients, {sum(len(c['documents']) for c in small_data)} documents")
    print(f"  Medium: {len(medium_data)} clients, {sum(len(c['documents']) for c in medium_data)} documents")