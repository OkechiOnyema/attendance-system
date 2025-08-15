import csv

def load_courses_from_csv(filepath):
    courses = []
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)[0].replace('"', '').split(',')
        for row in reader:
            clean_row = row[0].replace('"', '').split(',')
            courses.append({
                'code': clean_row[0].strip(),
                'title': clean_row[1].strip()
            })
    return courses