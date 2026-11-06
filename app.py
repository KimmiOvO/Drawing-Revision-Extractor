import streamlit as st
import pymupdf
import pandas as pd
from collections import defaultdict
from io import BytesIO

st.set_page_config(
    page_title="Drawing Revision Extractor",
    layout="wide"
)

st.title("📄 Drawing Revision Extractor")

uploaded_file = st.file_uploader(
    "Upload Drawing PDF",
    type=["pdf"]
)

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

        candidates = []

        for w in words:

            x0 = w[0]
            y0 = w[1]
            text = w[4]

            # YOUR WORKING LOGIC
            if x0 > width * 0.95 and y0 > height * 0.95:
                candidates.append((x0, y0, text))

        if candidates:

            candidates.sort(
                key=lambda x: (x[1], x[0])
            )

            revision = candidates[-1][2]

        else:
            revision = "UNKNOWN"

        grouped[revision].append(page_no)

        page_results.append(
            {
                "Page": page_no,
                "Revision": revision
            }
        )

        progress.progress(
            page_no / len(pdf)
        )

    st.success(
        f"Successfully processed {len(pdf)} pages"
    )

    st.subheader("Revision Summary")

    summary_data = []

    for rev, pages in grouped.items():

        page_string = ",".join(
            map(str, pages)
        )

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

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Page Details")

        page_df = pd.DataFrame(
            page_results
        )

        st.dataframe(
            page_df,
            use_container_width=True
        )

    with col2:
        st.subheader("Revision Summary Table")

        summary_df = pd.DataFrame(
            summary_data
        )

        st.dataframe(
            summary_df,
            use_container_width=True
        )

    # Excel Export

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
