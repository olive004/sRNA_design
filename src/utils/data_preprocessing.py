import csv


def txt_to_csv(input_file: str, output_file: str):
    """ GCG """

    # Open the input and output files
    with open(input_file, 'r') as txt_file, open(output_file, 'w', newline='') as csv_file:
        # Create a CSV writer
        csv_writer = csv.writer(csv_file, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Write the header row to the CSV file
        header = next(txt_file).strip().split('\t')
        csv_writer.writerow(header)

        # Process the rest of the lines in the text file
        for line in txt_file:
            # Split the line by tab character
            data = line.strip().split('\t')
            # Write the data to the CSV file
            csv_writer.writerow(data)

    print("Conversion complete. CSV file saved as", output_file)
