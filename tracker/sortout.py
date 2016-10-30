# Sorting the Output


def sortOutput(name):
	line_map = {}
	line = None
	skip = True
	first_line = None
	with open(name) as f:
		line = f.readlines()
	for i in line:
		if skip == True:
			first_line = i
			skip = False
			continue
		else:			
			a=i.split()
			line_map[int(a[0])]=i
	writeOutput(line_map, first_line)

def writeOutput(line_map, first_line):
	text_sorted_file = open("images/SortOutput.txt", "w")
	sorted(line_map)
	text_sorted_file.write(first_line)
	for key in line_map:
		text_sorted_file.write(line_map[key])
	text_sorted_file.close()
