import json
import subprocess   # enables use of command-line functions in python
import re           # support for regular expressions
import argparse     # to run the script from the command line
import os


### index.txt ###
# Function for counting all 0s in bval file and writing the index numbers into "index-txt" (one line per index nr)
def process_file_block1(bvalfile):
    with open(bvalfile, 'r') as bval_file:
        counter = 1
        with open(index_file_path, 'w') as index_file:
            for line in bval_file:
                numbers = line.split()
                for number in numbers:
                    if number == '0':
                        index_file.write(str(counter) + '\n')
                        counter += 1

# Function for second part of "index.txt"; keep index number for every non-0 until a new 0 comes up
def process_file_block2(bvalfile):
    with open(bvalfile, 'r') as bval_file, open(index_file_path, 'a') as index_file:
        counter = 0
        for line in bval_file:
            numbers = line.split()
            for number in numbers:
                if number == '0':
                    counter += 1
                    index_file.write(str(counter) + '\n')
                else:
                    index_file.write(str(counter) + '\n')


### acqparams.txt ###
# Function to extract the numbers from lines in json file
# that start with ""PhaseEncodingSteps"" or ""DerivedVendorReportedEchoSpacing""
def extract_values(json_data, key1, key2):
    values = {key1: None, key2: None}
    for line in json_data:
        if f'"{key1}"' in line:  # fstring because of quotes in the file
            _, value = line.replace(',', '').strip().split(":")
            values[key1] = float(value)
        elif f'"{key2}"' in line:
            _, value = line.replace(',', '').strip().split(":")
            values[key2] = float(value)

    return values

# Function to extract number of 0s, non-os and total number of values from bval file
def count_numbers(bval_file):
    with open(bval_file, 'r') as file:
        content = file.read()

    # Split content into a list of integers
    numbers = list(map(int, content.split()))

    # Count occurrences of each number
    counts = {}
    for num in numbers:
        counts[num] = counts.get(num, 0) + 1

    # Count the number of "0"s and non-"0"s
    zero_count = counts.get(0, 0)
    non_zero_count = len(numbers) - zero_count

    return counts, zero_count, non_zero_count

# Function to extract the number of volumes from nifti file using the command line function 'fslinfo'
def number_of_volumes(niftifile):
    # Run the fslinfo command and capture the output
    result = subprocess.run(['fslinfo', niftifile], capture_output=True, text=True)

    # Use regular expression to find the number of volumes
    # r' prefix: raw string (commonly used for regular expressions in python)
    # dim4: literal match for the characters "dim4" in the string
    # \s: matches zero or more whitespace characters
    # ([\d]+): capturing group that matches one or more digits (\d)
    # parentheses () are used to capture the matched digits so that they can be extracted later
    match = re.search(r'dim4\s+([\d]+)', result.stdout)
    if match:
        volume_count = int(match.group(1))
        return volume_count

    # Return None if number of volumes is not found
    return None


### Argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process files.')
    parser.add_argument('--bval', help='Path to bval file')
    parser.add_argument('--json', help='Path to json file')
    parser.add_argument('--nii', help='Path to nifti file')
    parser.add_argument('--output_dir', help='Directory for output files', default='.')
    args = parser.parse_args()

    bvalfile = args.bval
    jsonfile = args.json
    niftifile = args.nii
    output_dir = args.output_dir

    index_file_path = os.path.join(output_dir, 'index.txt')
    acqparams_file_path = os.path.join(output_dir, 'acqparams.txt')

    process_file_block1(bvalfile)
    process_file_block2(bvalfile)

    with open(jsonfile, 'r') as file:
        data = file.readlines()

    key1 = 'PhaseEncodingSteps'
    key2 = 'DerivedVendorReportedEchoSpacing'
    result = extract_values(data, key1, key2)

    if result[key1] is not None and result[key2] is not None:
        expression_result = round(result[key2] * (result[key1] - 1), 3)
    else:
        print("One or both keys for column 4 not found")

    _, zero_count, _ = count_numbers(bvalfile)
    num_volumes = number_of_volumes(niftifile)

    positive_line = f'0 1 0 {expression_result}\n'
    negative_line = f'0 -1 0 {expression_result}\n'

    with open(acqparams_file_path, 'w') as params_file:
        for i in range(zero_count):
            params_file.write(positive_line)
        for i in range(num_volumes):
            params_file.write(negative_line)