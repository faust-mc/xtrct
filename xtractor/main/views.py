from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import  Type, FormObject, HeaderObjects, RowObjects, FieldObject
from .forms import TypeForm, FormObjectForm, HeaderObjectsForm, RowObjectsForm, FieldObjectForm
import json




def template_config(request):
    # if this is a POST request we need to process the form data
    if request.method == "POST":
        # create a form instance and populate it with data from the request:
        typeform = TypeForm(request.POST, prefix='type')
        formobjectform = FormObjectForm(request.POST, prefix='formobject')
        headerobjectsform = HeaderObjectsForm(request.POST, prefix='headerobjects')
        rowobjectsform = RowObjectsForm(request.POST, prefix='rowobjects')
        fieldobjectform = FieldObjectForm(request.POST, prefix='fieldobject')
        
        
        if 'submit_TypeForm' in request.POST:
            if(typeform.is_valid()):
                #process type form
                type = typeform.save(commit=False) # Don't save yet
                typeform.save()  # Save type                
        elif 'submit_FormObject' in request.POST:
            if(formobjectform.is_valid()):
                #process form object
                formobject = formobjectform.save()  # Save form   
        elif 'submit_HeaderObjects' in request.POST:    
            if(headerobjectsform.is_valid()):
                #process form object 
                headerobjects = headerobjectsform.save()  # Save header   
        elif 'submit_RowObjects' in request.POST:    
            if(rowobjectsform.is_valid()):   
                #process form object
                rowobjects = rowobjectsform.save()  # Save row  
        elif 'submit_FieldObject' in request.POST:    
            if(fieldobjectform.is_valid()):   
                #process form object 
                fieldobject = fieldobjectform.save()  # Save row  
    else :
        typeform = TypeForm(prefix='type')
        formobjectform = FormObjectForm(prefix='formobject')
        headerobjectsform = HeaderObjectsForm(prefix='headerobjects')
        rowobjectsform = RowObjectsForm(prefix='rowobjects')
        fieldobjectform = FieldObjectForm(prefix='fieldobject')
   
    return render(request, 'config.html', {'typeform': typeform, 'formobjectform': formobjectform,  'headerobjectsform': headerobjectsform,  'rowobjectsform': rowobjectsform,  'fieldobjectform': fieldobjectform})



   









@csrf_exempt
def ocr_result_view(request):

    table_name = ["COLLECTED GOOD EGGS", "COLLECTED REJECT EGGS"]
    for t in table_name:
        #table_name = "COLLECTED REJECT EGGS"

        table = FormObject.objects.get(title=t)
        print(table)
        with open("main/samp3json.json") as f:
            ocr_data = json.load(f)

        def get_center(bbox):
            xs = [p["x"] for p in bbox]
            ys = [p["y"] for p in bbox]
            return (sum(xs) / 4, sum(ys) / 4)

        lines = []
        for block in ocr_data["readResult"]["blocks"]:
            for line in block["lines"]:
                center = get_center(line["boundingPolygon"])
                lines.append({
                    "text": line["text"],
                    "center": center,
                    "bbox": line["boundingPolygon"]
                })


        reject_anchor_y = None
        for line in lines:

            if line["text"].strip().upper() == table.title:
                _, reject_anchor_y = line["center"]
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
            for line in lines:

                text = line["text"].strip().upper()
                cx, cy = line["center"]
                if text in header_names and abs(cy - reject_anchor_y) < 100:
                    header_x_positions[text] = cx

        #row_names = ['SUPER JUMBO', 'JUMBO', 'EXTRA LARGE', 'LARGE', 'MEDIUM', 'SMALL', "EXTRA SMALL", 'PEWEE']

        row_names = list(
            RowObjects.objects
            .filter(form_object=table)
            .values_list('row_name', flat=True)
        )

        reject_table = {}

        for field in row_names:
            for line in lines:
                if field == line["text"].strip().upper():
                    field_y = line["center"][1]
                    same_row = [l for l in lines if abs(l["center"][1] - field_y) < 10]

                    field_values = {}

                    for col in header_names:
                        col_x = header_x_positions.get(col)
                        #print(col_x)
                        if col_x is None:
                            continue
                        closest = min(same_row, key=lambda l: abs(l["center"][0] - col_x), default=None)
                        #print(closest)
                        dist = abs(closest["center"][0] - col_x) if closest else float("inf")
                        field_values[col] = closest["text"] if closest and dist < 90 else "N/A"
                    reject_table[field] = field_values
                    break

        return JsonResponse({
            "extracted_table": reject_table,
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




def get_center(bbox):
    xs = [p["x"] for p in bbox]
    ys = [p["y"] for p in bbox]
    return (sum(xs) / 4, sum(ys) / 4)

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

    return sorted_rows

#extract_table_by_headers2

def extract_table_by_headers2():
    table_name = "EPP PRODUCTION LOT-BATCHCODE REPORT"

    expected_headers = ["PROD'N DATE", "HOUSE NUMBER", "MOTHER SKU", "INPUT (PCS)", "TRANSFORMATION"]
    def get_center(bbox):
        xs = [p["x"] for p in bbox]
        ys = [p["y"] for p in bbox]
        return (sum(xs) / 4, sum(ys) / 4)

    # Preprocess lines

    with open("main/samp5.json") as f:
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
    expected_headers = [h.strip().upper() for h in expected_headers]


    anchor_y = None
    for line in lines:
        if line["text"].strip().upper() == table_title:
            _, anchor_y = line["center"]
            break
    if anchor_y is None:
        return {"error": "Table title not found"}


    headers_in_doc = {}
    for line in lines:
        text = line["text"].strip().upper()
        cx, cy = line["center"]
        if abs(cy - anchor_y) < 100 and text in expected_headers:
            headers_in_doc[text] = cx

    if len(headers_in_doc) < len(expected_headers):
        return {"error": "Some headers not found below title"}


    extracted_rows = []
    row_lines = [line for line in lines if line["center"][1] > anchor_y + 100]

    used_rows = set()
    for line in row_lines:
        row_y = line["center"][1]
        if any(abs(row_y - y) < 10 for y in used_rows):
            continue
        same_row = [l for l in row_lines if abs(l["center"][1] - row_y) < 10]
        used_rows.add(row_y)

        row_data = {}
        for header in expected_headers:
            col_x = headers_in_doc.get(header)
            if col_x is None:
                row_data[header] = "N/A"
                continue
            closest = min(same_row, key=lambda l: abs(l["center"][0] - col_x), default=None)
            dist = abs(closest["center"][0] - col_x) if closest else float("inf")
            row_data[header] = closest["text"] if closest and dist < 20 else "N/A"


        extracted_rows.append(row_data)

    return extracted_rows

