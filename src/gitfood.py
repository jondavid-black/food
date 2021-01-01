import sys
import csv
from m2r import convert

def processTocRow(section, level, title, content):
    #print(f'\tSection: {section} Heading Level: {level} Title: {title} Content File: {content}')
    output = ""

    if (len(title) > 0):
        # Add section heading
        output += ('#' * level) + " " + title + "\n"

    convertToRst = len(content) == 0 or content.endswith(".md")

    # Process content (if present)
    if (len(content) > 0):
        reader = open(content, encoding="utf8")
        try:
            # strip off any Jekyll metadata at the top of the file
            inMetadata = False
            for line in reader.readlines():
                if (line.strip() == "---"):
                    inMetadata = not inMetadata
                    continue
                if (not inMetadata):
                    if (line.startswith("#")):
                        # make sure heading level is correct-ish
                        output += ('#' * level) + line + "\n"
                    else:
                        # append line to output
                        output += line
        finally:
            reader.close()

    rst = ""
    if (convertToRst):
        rst = convert(output)
    else:
        rst = output

    # add a page break    
    rst += "\n.. raw:: pdf\n   \n   PageBreak\n"
    print(rst)

with open(sys.argv[1]) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            # print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            processTocRow(row[0].strip(), int(row[1].strip()), row[2].strip(), row[3].strip())
            line_count += 1
   # print(f'Processed {line_count} lines.')


    
