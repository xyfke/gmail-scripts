if __name__ == "__main__":

    emp_file = open("inputs/results.txt", "r", encoding="utf-16")
    hash_set = set()
    result = open("outputs/uniq_emp.txt", "a")

    for l in emp_file:
        emp = l.strip().split("W2")[0]
        hash_set.add(emp)

    for emp in hash_set:
        print(emp, file=result)

    emp_file.close()
    result.close()
    