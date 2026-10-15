import csv
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup as bs

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import UpFile
from .models import Documents


def clean_unicode(text):
    """Remove hidden Unicode directional marks inserted by WhatsApp Web."""
    if not text:
        return ""
    return re.sub(r"[\u200e\u200f\u202a-\u202e]", "", text)


def extract_contacts_from_html(file_content, country_filter="all", prefix="ZG"):
    """
    Resilient multi-strategy phone number extractor for WhatsApp Web exports.
    Handles Nigerian numbers (+234 and local 080/090/070/081/091),
    plus international numbers, while deduplicating and cleaning.
    """
    soup = bs(file_content, "lxml")
    candidate_texts = []

    # Strategy 1: Find any span with a comma-separated title attribute
    for span in soup.find_all("span", title=True):
        title = clean_unicode(span["title"])
        if "," in title and ("+" in title or any(char.isdigit() for char in title)):
            candidate_texts.append(title)

    # Strategy 2: Check selectable-text copyable-text elements
    for span in soup.find_all(class_=re.compile(r"selectable-text.*copyable-text")):
        text = clean_unicode(span.get_text())
        if "," in text and ("+" in text or any(char.isdigit() for char in text)):
            candidate_texts.append(text)

    # Strategy 3: Check elements with data-testid or header elements
    for elem in soup.find_all(attrs={"data-testid": re.compile(r"chat-title|conversation-info|group")}):
        text = clean_unicode(elem.get_text())
        if "," in text:
            candidate_texts.append(text)

    # Pick the candidate string with the most content
    if candidate_texts:
        chosen_text = max(candidate_texts, key=len)
        raw_items = chosen_text.split(",")
    else:
        # Fallback to scanning all text in document
        raw_items = clean_unicode(soup.get_text()).split("\n")

    contacts = []
    seen = set()

    for raw in raw_items:
        # Strip spaces, hyphens, parentheses, and directional marks
        cleaned = re.sub(r"[\s\-\(\)]", "", clean_unicode(raw)).strip()
        if not cleaned or cleaned.lower() == "you":
            continue

        num = None
        cc = "234"

        # Case A: Standard Nigerian format (+234 801...)
        if cleaned.startswith("+234"):
            num = cleaned[4:]
            cc = "234"
        # Case B: Nigerian format with 234 prefix without plus (234801...)
        elif cleaned.startswith("234") and len(cleaned) == 13:
            num = cleaned[3:]
            cc = "234"
        # Case C: Nigerian local format (0801..., 0901..., 0701..., 0811..., 0911...)
        elif cleaned.startswith("0") and len(cleaned) == 11 and cleaned[1] in "789":
            num = cleaned[1:]
            cc = "234"
        # Case D: Other international numbers (+1..., +44..., etc.)
        elif cleaned.startswith("+"):
            digits = cleaned[1:]
            # 1-digit country codes: +1 (US/CA)
            if digits.startswith("1") and len(digits) == 11:
                cc = "1"
                num = digits[1:]
            elif digits.startswith("7") and len(digits) == 11:
                cc = "7"
                num = digits[1:]
            else:
                # 3-digit country codes
                found_3 = False
                for p3 in ["234", "233", "254", "256", "255", "250", "237", "225", "221", "229", "228", "212", "213", "216", "218", "249", "251", "260", "263", "267", "268", "264", "265", "353", "351", "352", "354", "358", "370", "371", "372", "380", "381", "385", "386", "387", "389", "420", "421", "501", "502", "503", "504", "505", "506", "507", "509", "591", "592", "593", "595", "597", "598", "673", "855", "856", "880", "961", "962", "963", "964", "965", "966", "967", "968", "971", "972", "973", "974", "975", "976", "977"]:
                    if digits.startswith(p3) and len(digits) > len(p3):
                        cc = p3
                        num = digits[len(p3):]
                        found_3 = True
                        break
                # 2-digit country codes (+44, +33, +49, +91, +86, etc.)
                if not found_3 and len(digits) >= 8:
                    cc = digits[:2]
                    num = digits[2:]
        else:
            # Fallback regex search for embedded phone numbers inside the item
            embedded = re.search(r"(\+?\d{10,15})", cleaned)
            if embedded:
                cand = embedded.group(1)
                if cand.startswith("+234"):
                    num = cand[4:]
                    cc = "234"
                elif cand.startswith("0") and len(cand) == 11 and cand[1] in "789":
                    num = cand[1:]
                    cc = "234"
                elif cand.startswith("+"):
                    cand_digits = cand[1:]
                    if cand_digits.startswith("1") and len(cand_digits) == 11:
                        cc = "1"
                        num = cand_digits[1:]
                    elif len(cand_digits) >= 8:
                        cc = cand_digits[:2]
                        num = cand_digits[2:]

        # Apply country filter if selected
        if country_filter == "234" and cc != "234":
            continue

        # Clean non-digits from national number
        if num:
            num = re.sub(r"\D", "", num)
            if len(num) >= 7 and num not in seen:
                seen.add(num)
                contacts.append((num, cc))

    return contacts


def home_view(request):
    total_docs = Documents.objects.count()
    return render(request, "home.html", {"total_docs": total_docs})


def extract_view(request):
    if request.method == "POST":
        form = UpFile(request.POST, request.FILES)
        if form.is_valid():
            prefix = form.cleaned_data.get("contact_prefix") or "ZG"
            prefix = prefix.strip().replace(" ", "_")
            country_filter = form.cleaned_data.get("country_filter") or "all"

            # Save the uploaded document
            doc_obj = form.save()
            myid = doc_obj.id

            csv_file_name = f"{prefix}_{myid}.csv"
            doc_obj.name = csv_file_name
            doc_obj.save()

            # Resolve file path on disk
            try:
                if hasattr(doc_obj.documents, "path") and os.path.exists(doc_obj.documents.path):
                    file_path = doc_obj.documents.path
                else:
                    file_path = os.path.join(settings.BASE_DIR, doc_obj.documents.name)

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_content = f.read()
            except Exception as e:
                messages.error(request, f"Error reading uploaded file: {e}")
                return render(request, "extract.html", {"form": form})

            # Extract contacts
            contacts = extract_contacts_from_html(file_content, country_filter=country_filter, prefix=prefix)

            if not contacts:
                messages.warning(
                    request,
                    "No phone numbers could be detected in this file. "
                    "Make sure you saved the WhatsApp Web page while the group participant list was visible.",
                )
                return render(request, "extract.html", {"form": form})

            # Ensure media export directory exists
            export_dir = os.path.join(settings.MEDIA_ROOT, "exports")
            os.makedirs(export_dir, exist_ok=True)
            csv_path = os.path.join(export_dir, csv_file_name)

            # Write formatted CSV: <number_without_country_code>,<prefix><count>,<country_code>
            preview_rows = []
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                for index, (phone_num, cc) in enumerate(contacts, start=1):
                    contact_label = f"{prefix}{index}"
                    writer.writerow([phone_num, contact_label, cc])
                    if index <= 10:
                        preview_rows.append({
                            "index": index,
                            "phone": phone_num,
                            "label": contact_label,
                            "country_code": cc,
                            "full_number": f"+{cc}{phone_num}",
                        })

            # Store extraction meta in session
            request.session["new_id"] = myid
            request.session["contacts_count"] = len(contacts)
            request.session["contacts_preview"] = preview_rows
            request.session["contact_prefix"] = prefix

            messages.success(request, f"Successfully extracted {len(contacts)} contacts!")
            return HttpResponseRedirect(reverse("success"))
    else:
        form = UpFile()

    return render(request, "extract.html", {"form": form})


def success_view(request):
    doc_id = request.session.get("new_id")
    if not doc_id:
        return redirect("home")

    doc = get_object_or_404(Documents, id=doc_id)
    contacts_count = request.session.get("contacts_count", 0)
    preview_rows = request.session.get("contacts_preview", [])
    prefix = request.session.get("contact_prefix", "ZG")

    # If preview wasn't in session, read from file
    if not preview_rows:
        csv_path = os.path.join(settings.MEDIA_ROOT, "exports", doc.name)
        if not os.path.exists(csv_path):
            csv_path = os.path.join(settings.BASE_DIR, "static", "documents", "ext", doc.name)

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if len(row) >= 3:
                        count += 1
                        if len(preview_rows) < 10:
                            preview_rows.append({
                                "index": count,
                                "phone": row[0],
                                "label": row[1],
                                "country_code": row[2],
                                "full_number": f"+{row[2]}{row[0]}",
                            })
                contacts_count = count

    download_url = reverse("download", args=[doc.id])

    context = {
        "obj": doc,
        "contacts_count": contacts_count,
        "preview_rows": preview_rows,
        "download_url": download_url,
        "prefix": prefix,
    }
    return render(request, "successful.html", context)


def download_view(request, doc_id):
    """Safely serves the generated CSV file as an attachment download."""
    doc = get_object_or_404(Documents, id=doc_id)

    # Check media exports first, then legacy static path
    csv_path = os.path.join(settings.MEDIA_ROOT, "exports", doc.name)
    if not os.path.exists(csv_path):
        csv_path = os.path.join(settings.BASE_DIR, "static", "documents", "ext", doc.name)

    if not os.path.exists(csv_path):
        raise Http404("CSV file not found.")

    response = FileResponse(
        open(csv_path, "rb"),
        as_attachment=True,
        filename=doc.name,
        content_type="text/csv",
    )
    return response


def sender_view(request):
    """WhatsApp sender feature preview / dashboard."""
    return render(request, "sender.html", {})