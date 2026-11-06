import streamlit as st
import pymupdf
import pandas as pd
from collections import defaultdict
from io import BytesIO

# ==========================================
# Streamlit Page Setup
# ==========================================

st.set_page_config(
    page_title="Drawing Revision Extractor",
    layout="wide"
)

st.title("📄 Drawing Revision Extractor")

uploaded_file = st.file_uploader(
    "Upload Drawing PDF",
    type=["pdf"]
)

# ==========================================
# Helper Function
# ==========================================

def compress_pages(pages):

    if not pages:
        return ""

    pages = sorted(pages)

    ranges = []

    start = pages[0]
    end = pages[0]

    for p in pages[1:]:

        if p == end + 1:
            end = p

        else:

            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")

            start = end = p

    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")

    return ", ".join(ranges)


# ==========================================
# Main Program
# ==========================================

if uploaded_file:

    pdf = pymupdf.open(
        stream=uploaded_file.read(),
        filetype="pdf"
    )

    grouped = defaultdict(list)

    page_results = []

    progress = st.progress(0)

    for page_no, page in enumerate(pdf, start=1):

        words = page.get_text("words")

        width = page.rect.width
        height = page.rect.height

        bottom_words = []

        for w in words:

            x0 = w[0]
            y0 = w[1]
            text = w[4]

            # Bottom-right title block area
            if (
                x0 > width * 0.75
                and y0 > height * 0.95
            ):
                bottom_words.append(
                    (x0, y0, text)
                )

        revision = "UNKNOWN"
        drawing_no = "UNKNOWN"

        if bottom_words:

            # Sort left to right
            bottom_words.sort(
                key=lambda x: x[0]
            )

            texts = [x[2] for x in bottom_words]

            # Revision = rightmost item
            revision = texts[-1]

            # Drawing Number
            # Look for text containing /
            drawing_candidates = [
                t for t in texts
                if "/" in t
            ]

            if drawing_candidates:
                drawing_no = drawing_candidates[-1]

        grouped[revision].append(page_no)

        page_results.append(
            {
                "Page": page_no,
                "Drawing No": drawing_no,
                "Revision": revision
            }
        )

        progress.progress(
            page_no / len(pdf)
        )

    st.success(
        f"Successfully processed {len(pdf)} pages"
    )

    # ==========================================
    # Revision Summary
    # ==========================================

    st.subheader("Revision Summary")

    summary_data = []

    for rev in sorted(grouped.keys()):

        pages = grouped[rev]

        page_string = compress_pages(pages)

        summary_data.append(
            {
                "Revision": rev,
                "Pages": page_string
            }
        )

        st.write(
            f"**{rev}** : P.{page_string}"
        )

    st.divider()

    # ==========================================
    # Tables
    # ==========================================

    col1, col2 = st.columns(2)

    page_df = pd.DataFrame(
        page_results
    )

    summary_df = pd.DataFrame(
        summary_data
    )

    with col1:

        st.subheader(
            "Page Details"
        )

        st.dataframe(
            page_df,
            use_container_width=True
        )

    with col2:

        st.subheader(
            "Revision Summary Table"
        )

        st.dataframe(
            summary_df,
            use_container_width=True
        )

    # ==========================================
    # Excel Export
    # ==========================================

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        page_df.to_excel(
            writer,
            sheet_name="Page Details",
            index=False
        )

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

    st.download_button(
        label="📥 Download Excel Report",
        data=output.getvalue(),
        file_name="revision_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )