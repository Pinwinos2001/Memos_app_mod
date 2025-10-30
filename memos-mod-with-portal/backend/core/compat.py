# Optional imports that may be unavailable in Linux/Dev environments

try:
    from docx2pdf import convert as docx2pdf_convert  # type: ignore
except Exception:  # pragma: no cover
    docx2pdf_convert = None

try:
    import win32com.client as win32  # type: ignore
except Exception:  # pragma: no cover
    win32 = None

try:
    import pythoncom  # type: ignore
except Exception:  # pragma: no cover
    pythoncom = None