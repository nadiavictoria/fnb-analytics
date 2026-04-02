import pandas as pd

# Run script to remove unnecessary columns from csv
input_file = "cleaned_restaurant.csv" #CHANGE THIS
output_file = "final_restaurant.csv" #CHANGE THIS

df = pd.read_csv(input_file)

columns_to_drop = ['name', 'category', 'address'] #CHANGE THIS
df_cleaned = df.drop(columns=columns_to_drop, errors='ignore')
df_cleaned.to_csv(output_file, index=False)

print(f"Success! Removed columns: {columns_to_drop}")
print(f"New file saved as: {output_file}")