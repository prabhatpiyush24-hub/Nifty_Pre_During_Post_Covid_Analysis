import pandas as pd

# Load metadata
company_master = pd.read_csv("data/metadata/company_master.csv")

print("=" * 60)
print("COMPANY MASTER")
print("=" * 60)

print(f"Total companies : {len(company_master)}")

# Show unique values in Eligible
print("\nEligible values:")
print(company_master["Eligible"].value_counts(dropna=False))

# Filter eligible companies
eligible = company_master[company_master["Eligible"] == True].copy()

print("\nEligible companies:", len(eligible))

print("\nFirst 10 eligible symbols:")
print(eligible["Symbol"].head(10).tolist())