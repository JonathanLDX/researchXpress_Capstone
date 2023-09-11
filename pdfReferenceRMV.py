import argparse
import fitz
from pdfUtils import find_Reference, remove_reference
from customExceptions import CannotFindReference
from removeHeadersFooters import getSpansByPage, remove_header_footer, keepFromTitle, find_header_spans, find_footer_spans, remove_header_footer_size


def main(pdf_file_name):
    '''takes in a pdf file path and outputs a new pdf with reference removed. 
    Throws an exception if there is no reference detected'''
    try:
        doc = fitz.open(pdf_file_name)

        pgNo, _, reference_blks = find_Reference(doc)
        output_doc = remove_reference(doc, reference_blks, pgNo)

    except CannotFindReference as e:
        print(f"{e} -- output is just a copy of source")
        output_doc = (doc,None)
        
    if output_doc[1] == None or output_doc[1] + 1 == output_doc[0].page_count:
        pgNo = output_doc[0].page_count
    else:
        pgNo = output_doc[1] + 1

    doc = output_doc[0]
    txtpgs = [pg.get_textpage() for pg in doc]
    txtpgs = txtpgs[0:pgNo]

    blocksDictByPage = [tp.extractDICT()['blocks'] for tp in txtpgs]
    spansByPage = getSpansByPage(blocksDictByPage)

    pageOne = spansByPage[0]
    pageOne = keepFromTitle(pageOne)
    spansByPage[0] = pageOne

    if len(spansByPage) >= 6:
        referenceRemoved = (output_doc[1] != None)
        headers = find_header_spans(spansByPage)
        footers = find_footer_spans(spansByPage)
        spansByPage = remove_header_footer(spansByPage,headers,footers,referenceRemoved)
    else:
        spansByPage = remove_header_footer_size(spansByPage)
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Takes in a pdf file and splits it into sections")
    parser.add_argument("--fp", type=str, help="source-file-path")

    args = parser.parse_args()
    main(args.fp)
