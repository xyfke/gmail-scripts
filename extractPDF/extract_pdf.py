"""
--------------------------------------------------------------------------
This piece of code extracts specific pages in a PDF file and creates a 
new PDF of those requested pages.
--------------------------------------------------------------------------
"""

# import os tools and pyPDF2 extractor
import os
from PyPDF2 import PdfReader, PdfWriter

if __name__ == '__main__':

    # Windows python - keep spaces in path 
    path = "C:/Users/Accounting Admin/Documents/Paycheck City W2/Regenerated/"

    output_path = "../data/w2-EIN/outputs/pdfs/"

    dir_list = os.listdir(path)
    pages = [3,4,5,6]


    # loop through the files
    for f in dir_list:
        pdf_file_path = path + f
        if os.path.isfile(pdf_file_path):

            file_base_name = pdf_file_path.replace('.pdf', '')
            pdf = PdfReader(pdf_file_path)

            pdfWriter = PdfWriter()

            for page_num in pages:
                pdfWriter.add_page(pdf.pages[page_num])

            with open(os.path.realpath(output_path + f), 'wb') as out_file:
                pdfWriter.write(out_file)
                out_file.close()

            print("Finish: {}".format(f))
