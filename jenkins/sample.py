import matplotlib.pyplot as plt
import os

date_str = datetime.today().strftime('%Y-%m-%d')

resolution, machine, eamxx_compset, mam4xx_compset, destination, simulation_length = parse_args(sys.argv[1:])

# Load data from CSV file into a DataFrame
eamxx_df = pd.read_csv(destination + '/eamxx_performance_' + resolution + '.csv', header=None, names=['date', 'throughput', 'model_cost'])
mam4xx_df = pd.read_csv(destination + '/mam4xx_performance_' + resolution + '.csv', header=None, names=['date', 'throughput', 'model_cost'])
eamxx_atm_df = pd.read_csv(destination + '/eamxx_atm_time_' + resolution + '.csv', header=None, names=['date', 'run_time', 'sec_mday', 'myears_wday'])
mam4xx_atm_df = pd.read_csv(destination + '/mam4xx_atm_time_' + resolution + '.csv', header=None, names=['date', 'run_time', 'sec_mday', 'myears_wday'])

# Convert date column to datetime type
eamxx_df['date'] = pd.to_datetime(eamxx_df['date'])
mam4xx_df['date'] = pd.to_datetime(mam4xx_df['date'])
eamxx_atm_df['date'] = pd.to_datetime(eamxx_atm_df['date'])
mam4xx_atm_df['date'] = pd.to_datetime(mam4xx_atm_df['date'])

print(eamxx_df)
print(mam4xx_df)
print(eamxx_atm_df)
print(mam4xx_atm_df)

mam4xx_avg_cost = str(mam4xx_df.loc[:, 'model_cost'].mean())
eamxx_avg_cost = str(eamxx_df.loc[:, 'model_cost'].mean())

# 2. Create the figure and a grid of subplots
# (2 rows, 1 column)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10))

# Plot the data using matplotlib
ax1.plot(eamxx_df['date'], eamxx_df['throughput'], marker='o')
ax1.plot(mam4xx_df['date'], mam4xx_df['throughput'], marker='^')
title_machine = machine.upper()
title_res = resolution.upper()
display_title = title_machine + " " + title_res
ax1.set_title(display_title)
ax1.set_xlabel('Date')
ax1.set_ylabel('Simulated Years Per Wall-Clock Day (SYPD)')
ax1.xticks(rotation=45)
ax1.grid(True)
ax1.legend(['F2010-SCREAMv1', 'F2010-EAMxx-MAM4xx'])
test_specs = "Machine: " + machine + "\nResolution: " + resolution + "\nSimulation Length: " + simulation_length +  "\nEAMxx Compset: " + eamxx_compset + "\nMAM4xx Compset: " + mam4xx_compset + "\nMAM4xx Average Model Cost: " + mam4xx_avg_cost + "\nEAMxx Average Model Cost: " + eamxx_avg_cost
ax1.figtext(.95, .5, test_specs, ha="left")


# 4. Plot on the second subplot (ax2)
ax2.plot(eamxx_atm_df['date'], eamxx_atm_df['run_time'], label='EAMxx run time seconds', color='green', marker='^')
ax2.plot(eamxx_atm_df['date'], eamxx_atm_df['sec_mday'], label='EAMxx sec_mday', color='red', marker='^')
ax2.plot(eamxx_atm_df['date'], eamxx_atm_df['myears_wday'], label='EAMxx myears wday', color='blue', marker='^')
ax2.plot(mam4xx_atm_df['date'], mam4xx_atm_df['run_time'], label='MAM4xx run time seconds', color='green', marker='o')
ax2.plot(mam4xx_atm_df['date'], mam4xx_atm_df['sec_mday'], label='MAM4xx sec_mday', color='red', marker='o')
ax2.plot(mam4xx_atm_df['date'], mam4xx_atm_df['myears_wday'], label='MAM4xx myears wday', color='blue', marker='o')
ax2.set_title('Timing')
ax2.set_xlabel('Time')
ax2.set_ylabel('Value B')
ax2.legend()
ax2.grid(True)

# 5. Adjust layout so titles/labels don't overlap
plt.tight_layout()
# Save the plot
plt.savefig(destination + '/performance_comp_' + date_str + '_' + resolution + '_' + simulation_length + '.png', bbox_inches='tight')

# 6. Show the plot
plt.savefig("/global/cfs/projectdirs/e3sm/www/litz372/sample.png")

os.chmod("/global/cfs/projectdirs/e3sm/www/litz372/sample.png", 0o664)
