import pandas as pd

company = pd.read_csv("data/metadata/company_master.csv")
research = pd.read_csv("data/metadata/research_universe.csv")

print("Company Master Columns:")
print(company.columns.tolist())

print("\nResearch Universe Columns:")
print(research.columns.tolist())