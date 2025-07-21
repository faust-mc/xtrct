from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json

#return render(request, 'pdf_list.html', {'documents': documents})
def config(request):
    return render(request, 'config.html')

@csrf_exempt
def ocr_result_view(request):
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

    # === COLLECTED GOOD EGGS ===
    quantity_x = total_x = None
    target_x = target_y = None

    for line in lines:
        text_upper = line["text"].strip().upper()
        if "QUANTITY" in text_upper:
            quantity_x = line["center"][0]
        if "COLLECTED GOOD EGGS" in text_upper:
            target_x, target_y = line["center"]

    min_distance = float("inf")
    for line in lines:
        text_upper = line["text"].strip().upper()
        cx, cy = line["center"]
        if "TOTAL" in text_upper and cx > target_x and cy > target_y:
            distance = ((cx - target_x)**2 + (cy - target_y)**2)**0.5
            if distance < min_distance:
                min_distance = distance
                total_x = cx

    if quantity_x is None or total_x is None:
        return JsonResponse({"error": "QUANTITY or TOTAL column not found"}, status=400)

    labels_to_find = ['SUPER JUMBO', 'JUMBO', 'EXTRA LARGE', 'LARGE', 'MEDIUM', 'SMALL', "EXTRA SMALL", 'PEWEE']
    label_value_pairs = {}

    for label in labels_to_find:
        for line in lines:
            if label == line["text"].strip().upper():
                label_x, label_y = line["center"]
                same_row = [c for c in lines if abs(c["center"][1] - label_y) < 10]
                closest_quantity = closest_total = None
                min_q_dist = min_t_dist = float("inf")

                for candidate in same_row:
                    if candidate == line:
                        continue
                    cx = candidate["center"][0]
                    q_dist = abs(cx - quantity_x)
                    t_dist = abs(cx - total_x)
                    if q_dist < min_q_dist:
                        min_q_dist = q_dist
                        closest_quantity = candidate
                    if t_dist < min_t_dist:
                        min_t_dist = t_dist
                        closest_total = candidate

                label_value_pairs[label] = {
                    "quantity": closest_quantity["text"] if closest_quantity else "N/A",
                    "total": closest_total["text"] if closest_total else "N/A"
                }
                break

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
        if line["text"].strip().upper() == "COLLECTED REJECT EGGS":
            _, reject_anchor_y = line["center"]
            break

    reject_headers = ["ACCUMULATOR", "CANDLING", "TAKE AWAY", "BYPASS", "TOTAL"]
    header_x_positions = {}
    if reject_anchor_y is not None:
        for line in lines:
            text = line["text"].strip().upper()
            cx, cy = line["center"]
            if text in reject_headers and abs(cy - reject_anchor_y) < 100:
                header_x_positions[text] = cx

    reject_fields = ["SLIGHTLY DIRTY", "DIRTY MANURE", "DIRTY YOLK", "DIRTY GREASE", "DIRTY BLOOD", "DEFORMED", "PULLETS", "BLOODSPOT", "MEATSPOT", "SPOILED EGGS", "SOFT SHELL"]
    reject_table = {}

    for field in reject_fields:
        for line in lines:
            if field == line["text"].strip().upper():
                field_y = line["center"][1]
                print(f"{field_y} {field}")
                same_row = [l for l in lines if abs(l["center"][1] - field_y) < 10]
                field_values = {}
                for col in reject_headers:
                    col_x = header_x_positions.get(col)
                    if col_x is None:
                        continue
                    closest = min(same_row, key=lambda l: abs(l["center"][0] - col_x), default=None)
                    dist = abs(closest["center"][0] - col_x) if closest else float("inf")
                    field_values[col] = closest["text"] if closest and dist < 10 else "N/A"
                reject_table[field] = field_values
                break

    # === BREAKAGES ===
    breakages_anchor_y = None
    for line in lines:
        if line["text"].strip().upper() == "BREAKAGES":
            _, breakages_anchor_y = line["center"]
            break

    breakages_headers = ["CONVEYOR", "ACCUMULATOR", "MULTI-DRUM", "CANDLING", "TRANSFER", "BRIDGE", "DROP SET", "TAKE AWAY", "BY-PASS", "TOTAL"]
    breakage_header_x_positions = {}
    if breakages_anchor_y is not None:
        for line in lines:
            text = line["text"].strip().upper()
            cx, cy = line["center"]
            if text in breakages_headers and abs(cy - breakages_anchor_y) < 100:
                breakage_header_x_positions[text] = cx

    breakages_fields = ["HAIRLINES", "GOOD CRACKED", "SEMI CRACKED", "OVER CRACKED", "SHELL ONLY"]
    breakages_table = {}

    for field in breakages_fields:
        found_line = None
        for i, line in enumerate(lines):
            text1 = line["text"].strip().upper()
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                text2 = next_line["text"].strip().upper()
                x1, y1 = line["center"]
                x2, y2 = next_line["center"]
                if abs(x1 - x2) < 20 and 0 < abs(y2 - y1) < 20:
                    combined = f"{text1} {text2}"
                    if field == combined:
                        found_line = {"text": combined, "center": ((x1 + x2) / 2, (y1 + y2) / 2)}
                        break
            if text1 == field:
                found_line = line
                break

        if not found_line:
            continue

        field_y = found_line["center"][1]
        same_row = [l for l in lines if abs(l["center"][1] - field_y) < 10]
        field_values = {}
        for col in breakages_headers:
            col_x = breakage_header_x_positions.get(col)
            if col_x is None:
                continue
            closest = min(same_row, key=lambda l: abs(l["center"][0] - col_x), default=None)
            dist = abs(closest["center"][0] - col_x) if closest else float("inf")
            field_values[col] = closest["text"] if closest and dist < 10 else "N/A"
        breakages_table[field] = field_values

    #Return All Extracted Info as JSON
    # return JsonResponse({
    #     "collected_good_eggs": label_value_pairs,
    #     "extra_totals": extra_totals,
    #     "reject_eggs": reject_table,
    #     "breakages": breakages_table
    # }, json_dumps_params={"indent": 2})

    response = {
        "collected_good_eggs": label_value_pairs,
        "extra_totals": extra_totals,
        "reject_eggs": reject_table,
        "breakages": breakages_table
    }

    return render(request, 'ocr_result.html' , {'response' : response })

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
        print(line)
        print()
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
