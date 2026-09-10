import argparse
import matplotlib.pyplot as plt
import sys

def parse_args(argv):
  parser = argparse.ArgumentParser(description='Plot EAMxx-MAM4xx performance data')
  parser.add_argument('-i', '--input', metavar='r', type=ascii, nargs='+',
                     help='input performance comp graph')

  parser.add_argument('-o', '--output', metavar='m', type=ascii, nargs='+',
                     help='html output dash graph')

  args = vars(parser.parse_args())

  input_graph = args["input"][0].strip("'""'")
  output_graph = args["output"][0].strip("'""'")

  return input_graph, output_graph 

input_graph, output_graph = parse_args(sys.argv[1:])

# Append the image to the HTML file
html_content = f'<img src="{input_graph}" alt="comparison between EAMxx and EAMxx+MAM4xx">\n'
with open(f'{output_graph}', "a") as html_file:
    html_file.write(html_content)

# Display the HTML file path
print(f"HTML file generated: {output_graph}")
