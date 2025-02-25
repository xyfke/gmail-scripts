# import os tools and pyPDF2 extractor
import os
from PyPDF2 import PdfReader, PdfWriter, PdfFileReader

if __name__ == '__main__':

    # Windows python - keep spaces in path 
    path = "outputs/"

    dir_list = os.listdir(path)
    log = open("name_ssn.csv", "a")

    name_ssn = {}

    for f in dir_list:
        in_file = PdfReader(open(path + f, "rb"))
        pageObj = in_file.pages[0]

        v = pageObj.extract_text().split("\n")
        ssn = v[42].split(".")[1]

        name = f.split(" W2")[0]

        if (name not in name_ssn) or (name_ssn[name] != ssn):
            name_ssn[name] = ssn
            print("{}\t{}".format(name, ssn), file=log)

    log.close()