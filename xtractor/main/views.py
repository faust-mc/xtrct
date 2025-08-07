from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import  ComponentType, FormObject, HeaderObjects, RowObjects, FieldObject
import math




def is_same_column_1(header_bbox, cell_bbox, x_tolerance=10):
    # Get left and right boundaries for header and cell
    header_xs = [p["x"] for p in header_bbox]
    cell_xs = [p["x"] for p in cell_bbox]

    header_left = min(header_xs)
    header_right = max(header_xs)

    cell_left = min(cell_xs)
    cell_right = max(cell_xs)

    # Check horizontal overlap
    return not (cell_right < header_left - x_tolerance or cell_left > header_right + x_tolerance)


def is_same_column(header_bbox, cell_bbox):
    header_xs = [p["x"] for p in header_bbox]
    cell_xs = [p["x"] for p in cell_bbox]

    header_left = min(header_xs)
    header_right = max(header_xs)

    cell_left = min(cell_xs)
    cell_right = max(cell_xs)

    # Check if the cell box overlaps with the header box
    horizontal_overlap = not (cell_right < header_left or cell_left > header_right)

    return horizontal_overlap





def get_center(bbox):
    xs = [p["x"] for p in bbox]
    ys = [p["y"] for p in bbox]
    return (sum(xs) / 4, sum(ys) / 4)




@csrf_exempt
def ocr_result_view(request):

    # table_name = ["COLLECTED REJECT EGGS"]
    # table_name = ["04- 30 -25"]
    table_name = ["COLLECTED GOOD EGGS"]
    for t in table_name:
        #table_name = "COLLECTED REJECT EGGS"

        table = FormObject.objects.get(title=t)
        print(table)
        with open("main/samp3json.json") as f:
        # with open("main/samp3json.json") as f:
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


        reject_anchor_y = None

           
        for line in lines:

            if line["text"].strip().upper() == table.title:
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
            closest_headers = {}  # To store the closest line for each header

            for line in lines:
                text = line["text"].strip().upper()
                cx, cy = line["center"]

                # Only consider lines strictly below the table title (with margin)
                if cy <= reject_anchor_y + 5:
                    continue

                if text in header_names:
                    vertical_distance = cy - reject_anchor_y

                    # Check if it's the closest header match (vertically) so far
                    if text not in closest_headers or vertical_distance < closest_headers[text]["distance"]:
                        closest_headers[text] = {
                            "cx": cx,
                            "cy": cy,
                            "distance": vertical_distance,
                            "line": line
                        }

            # Now extract x-positions from closest_headers
            for text, info in closest_headers.items():
                header_x_positions[text] = info["cx"]
                print(info["line"])


        print(header_x_positions)

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
                    same_row = [l for l in lines if abs(l["center"][1] - field_y) < 15]
                    # print(same_row)
                    field_values = {}

                    for col in header_names:
                        col_x = header_x_positions.get(col)
                        if col_x is None:
                            field_values[col] = "N/A"
                            continue

                        # Get the bbox for this header
                        header_bbox = next(
                            (l["bbox"] for l in lines if l["text"].strip().upper() == col),
                            None
                        )
                        if not header_bbox:
                            field_values[col] = "N/A"
                            continue

                        # Find matches within same row that horizontally overlap with the header bbox
                        matches = [l for l in same_row if is_same_column_1(header_bbox, l["bbox"], x_tolerance=12)]

                        # Choose the one closest in X to the expected header position
                        closest = min(matches, key=lambda l: abs(l["center"][0] - col_x), default=None)

                        field_values[col] = closest["text"] if closest else "N/A"

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
def extract_table_by_headers2(request):
    table_name = "Business Name/Style ANDOKS LITSON CORPORATION Payment Terms: July 07, 2025"
    # table_name = "EPP PRODUCTION LOT-BATCHCODE REPORT"
    # table_name = "Customer Id: $09-145"

    expected_headers = ["Part Number", "Description", "UOM", "Delivered", "Delivered"]
    # expected_headers = ["Part Number", "Description", "Transferred", "\"Transferred", "Received", "Returned", "Retumed"]
    # expected_headers = ["PACKER","PROD'N DATE", "HOUSE NUMBER", "MOTHER SKU", "INPUT (PCS)", "TRANSFORMATION", "TOTAL OTY"]

    # Preprocess lines

    # with open("main/samp9.json") as f:
    with open("main/samp8b.json") as f:
    # with open("main/samp5.json") as f:
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
            print(cy)
    print(headers_in_doc)
    if len(headers_in_doc) < len(expected_headers):

        return {"error": "Some headers not found below title"}


    extracted_rows = []
    row_lines = [line for line in lines if line["center"][1] > anchor_y + 80]

    used_rows = set()
    
    for line in row_lines:
        row_y = line["center"][1]
        if any(abs(row_y - y) < 20 for y in used_rows):
            print(line)
            print(row_y)
            continue
        same_row = [l for l in row_lines if abs(l["center"][1] - row_y) < 10]
        for x in same_row:
            print(x)
            print("------------------------------------")
            print()
        used_rows.add(row_y)

        row_data = {}
        for header in expected_headers:
            col_x = headers_in_doc.get(header)
            if col_x is None:
                row_data[header] = "N/A"
                continue
            header_bbox = next(line["bbox"] for line in lines if line["text"].strip().upper() == header)

            matches = [l for l in same_row if is_same_column(header_bbox, l["bbox"])]
            closest = min(matches, key=lambda l: abs(l["center"][0] - col_x), default=None)

            row_data[header] = closest["text"] if closest else "N/A"



        extracted_rows.append(row_data)

    return JsonResponse(extracted_rows, safe=False)
