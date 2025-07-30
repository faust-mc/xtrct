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
    table_name = "COLLECTED GOOD EGGS"
    table_name = "COLLECTED REJECT EGGS"

    table = FormObject.objects.get(title=table_name)
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

    # === Step 1: Locate "COLLECTED GOOD EGGS" ===


    # === EXTRA TOTALS ===
    TOTAL_COUNT_TO_FIND = ['MOBA COUNT:', 'ACTUAL COUNT:', 'GOOD EGGS:', 'SD EGGS:', 'REJECT EGGS:', "DATE:",  "START:", "END:", "HOUSE/S:", "SPEED:"]
    extra_totals = {}

    for TOTAL_COUNT in TOTAL_COUNT_TO_FIND:
        for line in lines:
            text_upper = line["text"].strip().upper()
            if text_upper.startswith(TOTAL_COUNT):
                rest = text_upper[len(TOTAL_COUNT):].strip()
                if rest:
                    extra_totals[TOTAL_COUNT] = rest
                else:
                    label_x, label_y = line["center"]
                    candidates = [c for c in lines if c != line and c["center"][0] > label_x and abs(c["center"][1] - label_y) < 10]
                    if candidates:
                        candidates.sort(key=lambda c: c["center"][0])
                        extra_totals[TOTAL_COUNT] = candidates[0]["text"]
                    else:
                        extra_totals[TOTAL_COUNT] = "N/A"
                break

    # === COLLECTED REJECT EGGS ===
    reject_anchor_y = None
    for line in lines:
        print(line)
        print()
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

    row_names = ['SUPER JUMBO', 'JUMBO', 'EXTRA LARGE', 'LARGE', 'MEDIUM', 'SMALL', "EXTRA SMALL", 'PEWEE']

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
                #print(f"{field_y} {field}")
                same_row = [l for l in lines if abs(l["center"][1] - field_y) < 10]
                print(same_row)
                print()
                field_values = {}
                #print(same_row)
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



    # ✅ Return All Extracted Info as JSON
    return JsonResponse({

        "extracted_totals": extra_totals,
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

    # Normalize and upper-case the headers
    results = {}
    y_tolerance = 10

    for line in lines:

        label = line["text"].upper()
        if label in headers:
            label_x, label_y = line["center"]

            # Find closest item to the right and roughly same y
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

    # Step 1: Flatten all lines and compute center
    lines = []
    for block in ocr_data["readResult"]["blocks"]:
        for line in block["lines"]:
            center = get_center(line["boundingPolygon"])
            lines.append({
                "text": line["text"].strip(),
                "center": center,
                "bbox": line["boundingPolygon"]
            })

    # Step 2: Locate "COLLECTED GOOD EGGS" header and determine reference y position and x range
    header = next((line for line in lines if "COLLECTED GOOD EGGS" in line["text"].upper()), None)
    if not header:
        print("Header 'COLLECTED GOOD EGGS' not found.")
        return []

    _, header_y = header["center"]
    column_lines = [line for line in lines if line["center"][1] > header_y + 10]  # +10 to skip header itself

    # Step 3: Sort by y-center to group rows
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

    # Step 4: Output
    for row in sorted_rows:
        print(row)

    return sorted_rows





