"""
a Python script that generates a CSV file with 200 high school student records, including a binary gender column and 
embedded patterns: females show GPA improvement over time, while males do not. After the script, you'll find a 
rationale for how each column can be processed with statistical tests.
"""

import pandas as pd
import numpy as np

np.random.seed(42)  # For reproducibility

N = 200
first_names_male = ["Alex", "Ben", "Chris", "David", "Ethan", "Frank", "George", "Henry", "Ivan", "Jack"]
first_names_female = ["Alice", "Beth", "Cathy", "Diana", "Eva", "Fiona", "Grace", "Hannah", "Ivy", "Julia"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Martinez", "Lee"]

# Gender assignment
genders = np.random.choice(["Male", "Female"], size=N)

names = []
for g in genders:
    if g == "Male":
        names.append(np.random.choice(first_names_male) + " " + np.random.choice(last_names))
    else:
        names.append(np.random.choice(first_names_female) + " " + np.random.choice(last_names))

ages = np.random.randint(14, 19, size=N)
current_grades = np.random.choice([9, 10, 11, 12], size=N)
fav_classes = np.random.choice(["Math", "Biology", "History", "English", "Art", "Physics"], size=N)
homerooms = np.random.choice(["Room A", "Room B", "Room C", "Room D"], size=N)
# Generate right-skewed distributions for lates and absences
# Using a combination of Poisson distributions to create longer tails
num_lates = np.random.poisson(5, size=N) + np.random.poisson(3, size=N)  # Mean ~8
num_absences = np.random.poisson(2, size=N) + np.random.poisson(1, size=N)  # Mean ~3
extracurricular_hrs = np.clip(np.random.normal(5, 2, N), 0, 20)
sports_participation = np.random.choice([True, False], size=N)
standardized_test = np.clip(np.random.normal(80, 10, N), 60, 100)
lunch_type = np.random.choice(["Free", "Reduced", "Full"], size=N, p=[0.2, 0.3, 0.5])
iep_status = np.random.choice([True, False], size=N, p=[0.1, 0.9])
parent_edu = np.random.choice(["High School", "Bachelor's", "Master's"], size=N, p=[0.4, 0.4, 0.2])

# GPA pattern: Females improve, males don't
gpa_2022 = np.clip(np.random.normal(3.0, 0.5, N), 1.5, 4.0)
gpa_2023 = []
for i in range(N):
    if genders[i] == "Female":
        gpa_2023.append(np.clip(gpa_2022[i] + np.random.normal(0.15, 0.15), 1.5, 4.0))
    else:
        gpa_2023.append(np.clip(gpa_2022[i] + np.random.normal(0.00, 0.15), 1.5, 4.0))

school_year = [2023] * N

df = pd.DataFrame({
    "student_id": [f"S{str(i+1).zfill(3)}" for i in range(N)],
    "name": names,
    "gender": genders,
    "age": ages,
    "current_grade": current_grades,
    "gpa_2022": np.round(gpa_2022, 2),
    "gpa_2023": np.round(gpa_2023, 2),
    "fav_class": fav_classes,
    "homeroom": homerooms,
    "num_lates": num_lates,
    "num_absences": num_absences,
    "extracurricular_hrs": np.round(extracurricular_hrs, 1),
    "sports_participation": sports_participation,
    "standardized_test": np.round(standardized_test, 0),
    "lunch_type": lunch_type,
    "iep_status": iep_status,
    "parent_edu": parent_edu,
    "school_year": school_year
})

df.to_csv("high_school_students.csv", index=False)
