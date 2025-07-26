# Universal File Converter - Automated Testing Guide

## 🚀 Step-by-Step Testing Instructions

This guide will help you run the automated test suite for the Universal File Converter and generate a beautiful summary report of all conversions.

---

## 1. **Activate Your Python Virtual Environment**

```bash
source venv/bin/activate
```

---

## 2. **Start the API Server**

Make sure your API server is running:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. **Run the Automated Test Suite**

This will:
- Set up a variety of test files (DOCX, PDF, XLSX, PPTX, images, etc.)
- Convert each file to all supported formats
- Check if tables, images, and text are preserved
- Generate detailed reports

Run the following command:

```bash
python automated_test_suite.py
```

Generate the PDF summary

```bash
python generate_summary_pdf.py
```

---

## 4. **View the Test Results**

After the test suite completes, you will find the following in the `test_outputs/` directory:

- `test_report_YYYYMMDD_HHMMSS.json` — Full detailed results (machine-readable)
- `test_summary_YYYYMMDD_HHMMSS.csv` — Spreadsheet summary
- `test_report_YYYYMMDD_HHMMSS.html` — Beautiful HTML report
- `summaryReport.pdf` — **Beautiful PDF summary report** (see below)

---

## 5. **About `summaryReport.pdf`**

This PDF is a visually appealing, well-organized summary of your test run. It includes:

- **Overall Summary**: Total tests, successes, failures, and success rate
- **Conversion Table**: For each conversion:
    - Input file name
    - Output file name
    - Source file type
    - Output file type
    - Conversion status (Success/Fail)
    - Error message (if any)
    - Content preservation (tables/images/text)
    - Conversion method used (LibreOffice, fallback, etc.)
    - Time taken for each conversion
- **Recommendations**: Suggestions for improving conversion quality
- **Color-coded status**: Green for success, red for failure
- **Easy to scan**: Clean layout, clear headings, and summary statistics

---

## 6. **Example Table in `summaryReport.pdf`**

| Input File                | Output File                        | Source Type | Output Type | Status   | Method      | Content Preserved | Error/Warning |
|--------------------------|-------------------------------------|-------------|-------------|----------|-------------|------------------|--------------|
| document_with_tables.docx | document_with_tables.pdf            | DOCX        | PDF         | Success  | libreoffice | Yes              |              |
| pdf_with_tables.pdf      | pdf_with_tables.docx                | PDF         | DOCX        | Success  | fallback    | Yes              |              |
| simple_document.docx     | simple_document.pdf                 | DOCX        | PDF         | Success  | libreoffice | Yes              |              |
| ...                      | ...                                 | ...         | ...         | ...      | ...         | ...              | ...          |

---

## 7. **Ignore Test Artifacts in Git**

Add the following to your `.gitignore` to avoid committing test files and reports:

```
test_files/
test_outputs/
summaryReport.pdf
```

---

## 8. **Generating the PDF Summary Report**

After the test suite runs, you can generate `summaryReport.pdf` from the CSV or JSON summary using a script or tool (e.g., Python with `reportlab` or `pandas` + `matplotlib` + `pdfkit`).

**Example command:**
```bash
python generate_summary_pdf.py
```

This script will:
- Read the latest CSV/JSON summary
- Create a beautiful PDF with all results, tables, and charts
- Save it as `summaryReport.pdf` in your project root

---

## 9. **Review and Share**

- Open `summaryReport.pdf` to review all results visually
- Share the PDF with your team or stakeholders for a quick overview of conversion quality

---

**Happy Testing!** 🎉 