import matplotlib.pyplot as plt
import numpy as np

# Data
years_alpha = [2000, 2005, 2010, 2020]
pop_alpha = [50000, 60000, 65000, 80000]

years_beta = [2000, 2008, 2015, 2020]
pop_beta = [30000, 40000, 50000, 55000]

years_gamma = [2000, 2004, 2012, 2018]
pop_gamma = [20000, 25000, 35000, 45000]

# Combine all years for bar positions
all_years = sorted(set(years_alpha + years_beta + years_gamma))
x = np.arange(len(all_years))

# Width of each bar
width = 0.25

# Create population arrays aligned with all_years (fill 0 if no data for that year)
pop_alpha_aligned = [pop_alpha[years_alpha.index(year)] if year in years_alpha else 0 for year in all_years]
pop_beta_aligned = [pop_beta[years_beta.index(year)] if year in years_beta else 0 for year in all_years]
pop_gamma_aligned = [pop_gamma[years_gamma.index(year)] if year in years_gamma else 0 for year in all_years]

# Plot bar chart
plt.figure(figsize=(10, 6))
plt.bar(x - width, pop_alpha_aligned, width=width, label='Alpha')
plt.bar(x, pop_beta_aligned, width=width, label='Beta')
plt.bar(x + width, pop_gamma_aligned, width=width, label='Gamma')

# Customize chart
plt.title('Population Growth Over Time')
plt.xlabel('Year')
plt.ylabel('Population')
plt.xticks(x, all_years)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.show()