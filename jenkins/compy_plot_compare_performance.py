import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import argparse

def parse_args(argv):
  parser = argparse.ArgumentParser(description='Plot EAMxx-MAM4xx performance data')
  parser.add_argument('-r', '--resolution', metavar='r', type=ascii, nargs='+',
                     help='Resolution of the model')

  parser.add_argument('-m', '--machine', metavar='m', type=ascii, nargs='+',
                     help='Cluster this simulation was run on')

  parser.add_argument('-e', '--eamxx_compset', metavar='e', type=ascii, nargs='+',
                     help='EAMxx default simulation\'s compset')

  parser.add_argument('-x', '--mam4xx_compset', metavar='x', type=ascii, nargs='+',
                     help='EAMxx+MAM4xx simulation\'s compset')

  parser.add_argument('-d', '--destination', metavar='d', type=ascii, nargs='+',
                     help='Destination to save plot')

  parser.add_argument('-t', '--timestep', metavar='t', type=ascii, nargs='+',
                     help='How many timesteps the simulations ran for')

  args = vars(parser.parse_args())
  
  resolution = args["resolution"][0].strip("'""'")
  machine = args["machine"][0].strip("'""'")
  eamxx_compset = args["eamxx_compset"][0].strip("'""'")
  mam4xx_compset = args["mam4xx_compset"][0].strip("'""'")
  destination = args["destination"][0].strip("'""'")
  timestep = args["timestep"][0].strip("'""'")

  return resolution, machine, eamxx_compset, mam4xx_compset, destination, timestep

date_str = datetime.today().strftime('%Y-%m-%d')

resolution, machine, eamxx_compset, mam4xx_compset, destination, timestep = parse_args(sys.argv[1:])

# Load data from CSV file into a DataFrame
eamxx_df = pd.read_csv(destination + '/eamxx_performance_' + resolution + '.csv', header=None, names=['date', 'throughput', 'model_cost'])
mam4xx_df = pd.read_csv(destination + '/mam4xx_performance_' + resolution + '.csv', header=None, names=['date', 'throughput', 'model_cost'])

# Convert date column to datetime type
eamxx_df['date'] = pd.to_datetime(eamxx_df['date'])
mam4xx_df['date'] = pd.to_datetime(mam4xx_df['date'])

print(eamxx_df)
print(mam4xx_df)

mam4xx_avg_cost = str(mam4xx_df.loc[:, 'model_cost'].mean())
eamxx_avg_cost = str(eamxx_df.loc[:, 'model_cost'].mean())
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
test_specs = "Machine: " + machine + "\nResolution: " + resolution + "\nLength: " + timestep +  " time steps\nEAMxx Compset: " + eamxx_compset + "\nMAM4xx Compset: " + mam4xx_compset + "\nMAM4xx Average Model Cost: " + mam4xx_avg_cost + "\nEAMxx Average Model Cost: " + eamxx_avg_cost
plt.figtext(.95, .5, test_specs, ha="left")
plt.savefig(destination + '/performance_comp_' + date_str + '_' + resolution + '.png', bbox_inches='tight')
