import statistics

def getSpansByPage(listOfBlockByPage, excludeNonText=True):
  spansByPage = []
  for page in listOfBlockByPage:
    spans = []
    for blk in page:
      if excludeNonText:
        if blk['type'] != 0 or len(blk['lines']) == 0: continue
      spans.extend([span for line in blk['lines'] for span in line['spans']])

    spansByPage.append(spans)
  return spansByPage


def keepFromTitle(spans):
    largestFont = max(spans, key = lambda span: span['size'])['size']

    for i in range(len(spans)):
        span = spans[i]
        font = span['size']
        if font == largestFont:
            spans = spans[i:]
            break

    #print(f"removed {b4-len(block_font)} lines")
    return spans

# Find the index of blocks that are Headers
def find_header_spans(span_lst):
    dict_header_spans = {}
    # Split between even & odd pages
    for page in [1,2]:
        spans = []
        for span in range(0,len(span_lst[page])):
            try:
                is_similar = (re.sub(r'[0-9]','',span_lst[page][span]['text']).strip() == re.sub(r'[0-9]','',span_lst[page+2][span]['text']).strip())
                if is_similar:
                    spans.append(span)
                else:
                    if page == 2:
                        dict_header_spans['Odd'] = spans
                    else:
                        dict_header_spans['Even'] = spans
                    break
            except IndexError as e:
                print(e)
    return dict_header_spans



# Find the index of blocks that are Footers
def find_footer_spans(span_lst):
    dict_footer_spans = {}
    for page in [1,2]:
        spans = []
        for span in range(-1,-len(span_lst[page]),-1):
            try:
                is_similar = (re.sub(r'[0-9]','',span_lst[page][span]['text']).strip() == re.sub(r'[0-9]','',span_lst[page+2][span]['text']).strip())
                if is_similar:
                    spans.append(span)
                else:
                    if page == 2:
                        dict_footer_spans['Odd'] = spans
                    else:
                        dict_footer_spans['Even'] = spans
                    break
            except IndexError as e:
                print(e)
    
    return dict_footer_spans


def remove_header_helper(span_lst,headers,page,oddEven):
    if len(headers[oddEven]) != 0:
        return span_lst[page][headers[oddEven][-1]+1:]
    else:
        return span_lst[page]

def remove_footer_helper(span_lst,footers,page,oddEven):
    if len(footers[oddEven]) != 0:
        return span_lst[page][0:footers[oddEven][-1]:1]
    else:
        return span_lst[page]

def remove_header_footer_firstPage(firstPage,secondPage):
    left_border = min([span['bbox'][0] for span in secondPage])
    right_border = max([span['bbox'][2] for span in secondPage])
    bottom_border = max([span['bbox'][3] for span in secondPage])

    for span in range(-1,-len(firstPage),-1):
        bbox = firstPage[span]['bbox']
        if bbox[2] < left_border or bbox[0] > right_border or bbox[1] > bottom_border:
            continue
        else:
            if span == -1:
                return firstPage
            else:
                return firstPage[0:span+1:1] 
        

# Remove Headers and Footers
def remove_header_footer(span_lst,headers,footers,referenceRemoved):
    for page in range(1, len(span_lst)):
        if page == len(span_lst) - 1 and referenceRemoved:
            if page % 2 == 0:
                span_lst[page] = remove_header_helper(span_lst,headers,page,'Odd')
            else:
                span_lst[page] = remove_header_helper(span_lst,headers,page,'Even')
        else:
            if page % 2 == 0:
                span_lst[page] = remove_header_helper(span_lst,headers,page,'Odd')
                span_lst[page] = remove_footer_helper(span_lst,footers,page,'Odd')
            else:
                span_lst[page] = remove_header_helper(span_lst,headers,page,'Even')
                span_lst[page] = remove_footer_helper(span_lst,footers,page,'Even')

    span_lst[0] = remove_header_footer_firstPage(span_lst[0],span_lst[1])

    return span_lst



# Remove Headers and Footers
def remove_header_footer_size(span_lst):
    for page in range(0,len(span_lst)):
        sizes = [span['size'] for span in span_lst[page]]
        text_size = statistics.mode(sizes)
        
        header_span = 0
        for span in range(0,len(sizes)):
            if span < text_size:
                header_span += 1
            else:
                break
                
        footer_span = None
        
        for span in range(-1,-len(sizes),-1):
            if sizes[span] != text_size:
                footer_span = span
            else:
                break

        if footer_span == None:
            span_lst[page] = span_lst[page][header_span:]
        else:
            span_lst[page] = span_lst[page][header_span:footer_span:1]
    
    return span_lst

