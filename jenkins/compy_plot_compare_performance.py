import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys

date_str = datetime.today().strftime('%Y-%m-%d')

resolution = sys.argv[1]

# Load data from CSV file into a DataFrame
eamxx_df = pd.read_csv('/qfs/projects/eagles/litz372/performance_data/eamxx_performance_' + resolution + '.csv', header=None, names=['date', 'throughput'])
mam4xx_df = pd.read_csv('/qfs/projects/eagles/litz372/performance_data/mam4xx_performance_' + resolution + '.csv', header=None, names=['date', 'throughput'])

# Convert date column to datetime type
eamxx_df['date'] = pd.to_datetime(eamxx_df['date'])
mam4xx_df['date'] = pd.to_datetime(mam4xx_df['date'])

print(eamxx_df)
print(mam4xx_df)

# Plot the data using matplotlib
plt.figure(figsize=(10, 5))
plt.plot(eamxx_df['date'], eamxx_df['throughput'], marker='o')
plt.plot(mam4xx_df['date'], mam4xx_df['throughput'], marker='^')
plt.title('Model Throughput Over Time')
plt.xlabel('Date')
plt.ylabel('Throughput (simulated_years/day)')
plt.xticks(rotation=45)
plt.grid(True)
plt.legend(['EAMxx default', 'EAMxx+MAM4xx'])
test_specs = "Machine: compy (CPU)\nResolution: " + resolution + "\nLength: 5 time steps\nEAMxx Compset: F2010-SCREAMv1\nMAM4xx Compset: F2010-EAMxx-MAM4xx"
plt.figtext(.95, .5, test_specs, ha="left")
plt.savefig('/qfs/projects/eagles/litz372/performance_data/performance_comp_' + date_str + '_' + resolution + '.png', bbox_inches='tight')