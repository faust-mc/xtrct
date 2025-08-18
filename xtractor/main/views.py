from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import render
from .models import  Type, FormObject, HeaderObjects, RowObjects, FieldObject
from .forms import TypeForm, FormObjectForm, HeaderObjectsForm, RowObjectsForm, FieldObjectForm
import json

def login(request):
    
    return render(request, 'login.html')



def index(request):
    
    return render(request, 'index.html')

    
    
def template_config(request):
    
    return render(request, 'config.html')



def extractor(request):
    
    return render(request, 'extractor.html')



def submit_form_ajax(request):
    if request.method == 'POST':
            field_list = request.POST.getlist('field_list[]')
            form_title = request.POST.get('form_title')
            
            table_data = dict(request.POST)  # convert QueryDict to dict for easier view

            # print("Form Title:", form_title)
            # print("Field List:", field_list)
            # print("Full Data:", table_data)
            
            # Process the data
            return JsonResponse({"Form Title" : form_title,"Field List": field_list,"Table Data" : table_data})
        
            return JsonResponse({'status': 'success', 'message': 'Valid request method'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



def sample(request):
    
    return render(request, 'sample.html')

# def template_config(request):
#     # if this is a POST request we need to process the form data
#     if request.method == "POST":
#         # create a form instance and populate it with data from the request:
#         typeform = TypeForm(request.POST, prefix='type')
#         formobjectform = FormObjectForm(request.POST, prefix='formobject')
#         headerobjectsform = HeaderObjectsForm(request.POST, prefix='headerobjects')
#         rowobjectsform = RowObjectsForm(request.POST, prefix='rowobjects')
#         fieldobjectform = FieldObjectForm(request.POST, prefix='fieldobject')
        
#         if 'submit_TypeForm' in request.POST:
#             if(typeform.is_valid()):
#                 #process type form
#                 type = typeform.save(commit=False) # Don't save yet
#                 typeform.save()  # Save type                
#         elif 'submit_FormObject' in request.POST:
#             if(formobjectform.is_valid()):
#                 #process form object
#                 formobject = formobjectform.save()  # Save form   
#         elif 'submit_HeaderObjects' in request.POST:    
#             if(headerobjectsform.is_valid()):
#                 #process form object 
#                 headerobjects = headerobjectsform.save()  # Save header   
#         elif 'submit_RowObjects' in request.POST:    
#             if(rowobjectsform.is_valid()):   
#                 #process form object
#                 rowobjects = rowobjectsform.save()  # Save row  
#         elif 'submit_FieldObject' in request.POST:    
#             if(fieldobjectform.is_valid()):   
#                 #process form object 
#                 fieldobject = fieldobjectform.save()  # Save row  
#     else :
#         typeform = TypeForm(prefix='type')
#         formobjectform = FormObjectForm(prefix='formobject')
#         headerobjectsform = HeaderObjectsForm(prefix='headerobjects')
#         rowobjectsform = RowObjectsForm(prefix='rowobjects')
#         fieldobjectform = FieldObjectForm(prefix='fieldobject')
   
#     return render(request, 'config.html', {'typeform': typeform, 'formobjectform': formobjectform,  'headerobjectsform': headerobjectsform,  'rowobjectsform': rowobjectsform,  'fieldobjectform': fieldobjectform})



   





@csrf_exempt
def ocr_result_view(request):
    form_name = FormName.objects.get(name="Samp")
    # EGG QUANTITY RECEIVED FORM
    # Samp
    # Form Name
    print(form_name)
    # with open("main/samp3json.json") as f:
    with open("main/samp6.json") as f:
        ocr_data = json.load(f)
    lines = [] #line of texts extracted
    for block in ocr_data["readResult"]["blocks"]:
        for line in block["lines"]:
            center = get_center(line["boundingPolygon"])
            lines.append({
                "text": line["text"],
                "center": center,
                "bbox": line["boundingPolygon"]
            })

    # === EXTRA TOTALS ===
    
    fields_to_find = list(
        FormObject.objects
        .filter(form_name=form_name, type=2)
        .values_list('title', flat=True)  # change 'title' to the correct field name
    )

    extra_totals = {}

    for field in fields_to_find:
        reject_anchor_y = None
        for line in lines:
            text_upper = line["text"]
            if text_upper.startswith(field):
                rest = text_upper[len(field):].strip()
                if rest:
                    extra_totals[field] = rest
                else:
                    label_x, label_y = line["center"]
                    candidates = [c for c in lines if c != line and c["center"][0] > label_x and abs(c["center"][1] - label_y) < 10]
                    if candidates:
                        candidates.sort(key=lambda c: c["center"][0])
                        extra_totals[field] = candidates[0]["text"]
                    else:
                        extra_totals[field] = "N/A"
                break
    
    tables = []
    table_name = list(
        FormObject.objects
        .filter(form_name=form_name, type=1)
        .values_list('title', flat=True)  # change 'title' to the correct field name
    )
    print(table_name)
    print()
    # table_name = ["05-01-25"]
    # table_name = ["04- 30 -25"]
    
    # table_name = ["COLLECTED GOOD EGGS"]
    for t in table_name:
        #table_name = "COLLECTED REJECT EGGS"

        table = FormObject.objects.get(title=t)
     
        


        reject_anchor_y = None

           
        for line in lines:

            if line["text"] == table.title:
                reject_anchor_x, reject_anchor_y = line["center"]
                break

        #header_names = ["QUANTITY", "TOTAL"]

        header_names = list(
            HeaderObjects.objects
            .filter(form_object=table)
            .exclude(header_type="label")
            .values_list('header_name', flat=True)
        )

        header_x_positions = {}

        if reject_anchor_y is not None:
            closest_headers = {}

            for line in lines:
                text = line["text"]
                cx, cy = line["center"]

                # Only consider lines below the table title (with margin)
                if cy <= reject_anchor_y + 5:
                    continue

                if text in header_names:
                    vertical_distance = cy - reject_anchor_y
                    horizontal_distance = abs(cx - reject_anchor_x)

                    # Option 1: Euclidean distance
                    total_distance = (vertical_distance ** 2 + horizontal_distance ** 2) ** 0.5

                    # Option 2: Weighted sum (tune weights as needed)
                    # total_distance = vertical_distance + 0.5 * horizontal_distance

                    # Choose the closest header based on combined distance
                    if (
                        text not in closest_headers or
                        total_distance < closest_headers[text]["total_distance"]
                    ):
                        closest_headers[text] = {
                            "cx": cx,
                            "cy": cy,
                            "total_distance": total_distance,
                            "line": line
                        }

            # Extract final x-positions
            for text, info in closest_headers.items():
                header_x_positions[text] = info["cx"]
                


       

        #row_names = ['SUPER JUMBO', 'JUMBO', 'EXTRA LARGE', 'LARGE', 'MEDIUM', 'SMALL', "EXTRA SMALL", 'PEWEE']

        row_names = list(
            RowObjects.objects
            .filter(form_object=table)
            .values_list('row_name', flat=True)
        )

        reject_table = {}

        for field in row_names:
            for line in lines:
                if (
                    field == line["text"]
                    and line["center"][0] < reject_anchor_x  # within 100px horizontally of table name
                    and line["center"][1] > reject_anchor_y  # ensure it's below the title
                ):

                    field_y = line["center"][1]
                    label_x = line["center"][0]
                    same_row = [l for l in lines if abs(l["center"][1] - field_y) < 15.6 and l["center"][0] > label_x + 5]

                
                    # print(same_row)
                    field_values = {}

                    for col in header_names:
                        col_x = header_x_positions.get(col)
                        if col_x is None:
                            print("n/a")
                            field_values[col] = "N/A"
                            continue

                        # Get the bbox for this header
                        # Get the bbox from the closest matching header (already filtered correctly)
                        header_info = closest_headers.get(col)
                        if not header_info:
                            field_values[col] = "N/A"
                            continue

                        header_bbox = header_info["line"]["bbox"]

                        
                        # Find matches within same row that horizontally overlap with the header bbox
                        matches = [l for l in same_row if is_same_column(header_bbox, l["bbox"])]
                        # print(matches)
                        # Choose the one closest in X to the expected header position
                        closest = min(matches, key=lambda l: abs(l["center"][0] - col_x), default=None)

                        field_values[col] = closest["text"] if closest else "N/A"

                    reject_table[field] = field_values
                    break
                print(reject_table)
        tables.append({t:reject_table})
    return JsonResponse({
        "extracted_table": tables,
        "extracted_fields": extra_totals
    }, json_dumps_params={"indent": 2})





@csrf_exempt
def quantity_graded_eggs(request):
    with open("main/2nd img res.json") as f:
        ocr_data = json.load(f)

    def get_center(bbox):
        xs = [p["x"] for p in bbox]
        ys = [p["y"] for p in bbox]
        return (sum(xs) / 4, sum(ys) / 4)

    headers = [
        "JUMBO", "XLARGE", "LARGE", "MEDIUM", "SMALL", "XSMALL", "PEEWEE",
        "CRACKED", "DIRTY", "SHELL ONLY", "SOFT SHELL", "SPOILED", "ASSORTED", "S-JUMBO"
    ]

    lines = []
    for block in ocr_data["readResult"]["blocks"]:
        for line in block["lines"]:
            center = get_center(line["boundingPolygon"])
            lines.append({
                "text": line["text"].strip(),
                "center": center,
                "bbox": line["boundingPolygon"]
            })

    results = {}
    y_tolerance = 10

    for line in lines:

        label = line["text"].upper()
        if label in headers:
            label_x, label_y = line["center"]

            #find closest item to the right and roughly same y
            right_candidates = [
                l for l in lines
                if l["center"][0] > label_x and abs(l["center"][1] - label_y) <= y_tolerance
            ]
            right_candidates.sort(key=lambda l: l["center"][0])  # sort by x distance

            if right_candidates:
                results[label] = right_candidates[0]["text"]
            else:
                results[label] = None

    return JsonResponse(results)





def extract_table_rows_from_file(request):
    with open("main/samp4json.json") as f:
        ocr_data = json.load(f)


    lines = []
    for block in ocr_data["readResult"]["blocks"]:
        for line in block["lines"]:
            center = get_center(line["boundingPolygon"])
            lines.append({
                "text": line["text"].strip(),
                "center": center,
                "bbox": line["boundingPolygon"]
            })


    header = next((line for line in lines if "COLLECTED GOOD EGGS" in line["text"].upper()), None)
    if not header:
        print("Header 'COLLECTED GOOD EGGS' not found.")
        return []

    _, header_y = header["center"]
    column_lines = [line for line in lines if line["center"][1] > header_y + 10]

    from collections import defaultdict
    rows_dict = defaultdict(list)
    for line in column_lines:
        y_bucket = round(line["center"][1] / 10) * 10  # bucket by y to group rows
        rows_dict[y_bucket].append(line)

    sorted_rows = []
    for y in sorted(rows_dict):
        row_items = sorted(rows_dict[y], key=lambda l: l["center"][0])  # sort by x (left to right)
        if len(row_items) >= 3:
            sorted_rows.append({
                "size": row_items[0]["text"],
                "description": row_items[1]["text"],
                "total": row_items[2]["text"]
            })


    for row in sorted_rows:
        print(row)

    return JsonResponse(sorted_rows, safe=False)

#extract_table_by_headers2
# def extract_table_by_headers2(request):
#     # table_name = "Business Name/Style ANDOKS LITSON CORPORATION Payment Terms: July 07, 2025"
#     table_name = "EPP PRODUCTION LOT-BATCHCODE REPORT"
#     # table_name = "Customer Id: $09-145"
#     # table_name = "Table 1 Title"

#     # expected_headers = ["Part Number", "Description", "UOM", "Delivered"]
#     # expected_headers = ["Part Number", "Description", "Transferred", "\"Transferred", "Received", "Returned", "Retumed"]
#     expected_headers = ["PACKER","PROD'N DATE", "HOUSE NUMBER", "MOTHER SKU", "INPUT (PCS)", "TRANSFORMATION", "TOTAL OTY"]
#     # expected_headers = ["Header 1", "Header 2", "Header 3", "Header 4", "Header 5"]
    

#     # with open("main/samp9.json") as f:
#     # with open("main/samp8b.json") as f:
#     with open("main/samp5.json") as f:
#     # with open("main/samp10.json") as f:
#         ocr_data = json.load(f)

#     lines = []
#     for block in ocr_data["readResult"]["blocks"]:
#         for line in block["lines"]:
#             center = get_center(line["boundingPolygon"])
#             lines.append({
#                 "text": line["text"].strip(),
#                 "center": center,
#                 "bbox": line["boundingPolygon"]
#             })

#     table_title = table_name.strip().upper()
#     expected_headers = [h.strip().upper() for h in expected_headers]


#     anchor_y = None
#     for line in lines:
#         if line["text"].strip().upper() == table_title:
#             _, anchor_y = line["center"]
#             break
#     if anchor_y is None:
#         return {"error": "Table title not found"}

#     headers_in_doc = {}
#     for line in lines:
#         text = line["text"].strip().upper()
#         cx, cy = line["center"]
#         if abs(cy - anchor_y) < 100 and text in expected_headers:
#             headers_in_doc[text] = cx
#             print(cy)
#     print(headers_in_doc)
#     if len(headers_in_doc) < len(expected_headers):

#         return {"error": "Some headers not found below title"}


#     extracted_rows = []
#     row_lines = [line for line in lines if line["center"][1] > anchor_y + 50]

#     used_rows = set()
    
#     stop_text = "BAWAL MAG IWAN NG CRATES"

#     for line in row_lines:
#         row_y = line["center"][1]

#         # STOP if the special line is detected
#         if line["text"].strip().upper() == stop_text.upper():
#             break

#         if any(abs(row_y - y) < 20 for y in used_rows):
#             continue

#         same_row = [l for l in row_lines if abs(l["center"][1] - row_y) < 10]

#         # Also stop if the special text is found anywhere in this row
#         if any(stop_text.upper() in l["text"].strip().upper() for l in same_row):
#             break

#         used_rows.add(row_y)

#         row_data = {}
#         for header in expected_headers:
#             col_x = headers_in_doc.get(header)
#             if col_x is None:
#                 row_data[header] = "N/A"
#                 continue

#             header_bbox = next(line["bbox"] for line in lines if line["text"].strip().upper() == header)
#             matches = [l for l in same_row if is_same_column(header_bbox, l["bbox"])]
#             closest = min(matches, key=lambda l: abs(l["center"][0] - col_x), default=None)
#             row_data[header] = closest["text"] if closest else "N/A"

#         extracted_rows.append(row_data)


#     return JsonResponse(extracted_rows, safe=False)



def extract_table_by_headers2(request):
    # table_name = "Customer Id: $09-111"
    table_name = "Customer Id: $09-145"
    # table_name = "Business Name/Style ANDOKS LITSON CORPORATION Payment Terms: July 07, 2025"
    # table_name = "EPP PRODUCTION LOT-BATCHCODE REPORT"
    expected_headers = ["Part Number", "Description", "Transferred", "\"Transferred", "Received", "Returned", "Retumed"]
    # expected_headers = ["Part Number", "Description", "UOM", "Delivered"]
    # expected_headers = ["PACKER","PROD'N DATE", "HOUSE NUMBER", "MOTHER SKU", "INPUT (PCS)", "TRANSFORMATION", "-", "SALLE ORDER", "UOM","TOTAL OTY","DIRTY (PCS)",]

    with open("main/samp9.json") as f:
    # with open("main/samp8b.json") as f:
    # with open("main/samp5.json") as f:
    # with open("main/samp10.json") as f:
    # with open("main/samp11.json") as f:
        ocr_data = json.load(f)

    lines = []
    for block in ocr_data["readResult"]["blocks"]:
        for line in block["lines"]:
            center = get_center(line["boundingPolygon"])
            lines.append({
                "text": line["text"].strip(),
                "center": center,
                "bbox": line["boundingPolygon"]
            })

    table_title = table_name.strip().upper()
    expected_headers_upper = [h.strip().upper() for h in expected_headers]

    # Find table title Y
    anchor_y = None
    for line in lines:
        if line["text"].strip().upper() == table_title:
            _, anchor_y = line["center"]
            break
    if anchor_y is None:
        return {"error": "Table title not found"}

    # Find headers in the document
    headers_in_doc = {}
    header_y_positions = []
    for line in lines:
        text = line["text"].strip().upper()
        cx, cy = line["center"]
        if cy > anchor_y and text in expected_headers_upper:
            headers_in_doc[text] = cx
            header_y_positions.append(cy)

    # Warn if some headers are missing but do not stop execution
    found_headers = list(headers_in_doc.keys())
    missing_headers = [h for h in expected_headers_upper if h not in found_headers]
    if missing_headers:
        print(f"⚠ Missing headers: {missing_headers}")
    if not headers_in_doc:
        return {"error": "No matching headers found below title"}

    # Dynamic start position
    if header_y_positions:
        start_y = max(header_y_positions) + 5
    else:
        start_y = anchor_y + 50

    extracted_rows = []
    row_lines = [line for line in lines if line["center"][1] > start_y]

    used_rows = set()
    stop_text = "BAWAL MAG IWAN NG CRATES"

    for line in row_lines:
        row_y = line["center"][1]

        # STOP if the special line is detected
        if line["text"].strip().upper() == stop_text.upper():
            break

        if any(abs(row_y - y) < 20 for y in used_rows):
            continue

        same_row = [l for l in row_lines if abs(l["center"][1] - row_y) < 13.5]

        # Also stop if the special text is found anywhere in this row
        if any(stop_text.upper() in l["text"].strip().upper() for l in same_row):
            break

        used_rows.add(row_y)

        row_data = {}
        for header_text_upper, col_x in headers_in_doc.items():
            # Use the original header casing from expected_headers
            original_header = next((h for h in expected_headers if h.strip().upper() == header_text_upper), header_text_upper)
            header_bbox = next(line["bbox"] for line in lines if line["text"].strip().upper() == header_text_upper)
            matches = [l for l in same_row if is_same_column(header_bbox, l["bbox"])]
            closest = min(matches, key=lambda l: abs(l["center"][0] - col_x), default=None)
            row_data[original_header] = closest["text"] if closest else "N/A"

        extracted_rows.append(row_data)


    return extracted_rows


