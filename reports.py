"""
TERRA Report Generator
Produces PDF ESG reports using fpdf2.
Falls back to a structured bytes object if fpdf2 not installed.
"""
from datetime import datetime
import io


class ReportGenerator:

    def generate_pdf(self, user, results, title, frameworks,
                     period, auditor_note="",
                     include_roadmap=True, include_credits=True) -> bytes:
        """Return PDF as bytes for st.download_button."""
        try:
            from fpdf import FPDF
            return self._build_fpdf(user, results, title, frameworks,
                                    period, auditor_note,
                                    include_roadmap, include_credits)
        except ImportError:
            return self._build_text_fallback(user, results, title, frameworks, period)

    def _build_fpdf(self, user, results, title, frameworks,
                    period, auditor_note, include_roadmap, include_credits) -> bytes:
        from fpdf import FPDF

        GREEN = (59, 109, 17)
        DARK  = (30, 30, 30)
        GREY  = (120, 120, 120)
        LIGHT = (245, 249, 240)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # ── Cover header ──────────────────────────────────────────
        pdf.set_fill_color(*GREEN)
        pdf.rect(0, 0, 210, 38, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_xy(15, 8)
        pdf.cell(0, 10, "TERRA", ln=False)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_xy(15, 20)
        pdf.cell(0, 6, "Carbon Intelligence Platform", ln=True)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_xy(15, 28)
        pdf.cell(0, 6, f"Powered by TERRA · terra-carbon.io · {datetime.now().strftime('%d %B %Y')}")

        # ── Report title ──────────────────────────────────────────
        pdf.ln(18)
        pdf.set_text_color(*DARK)
        pdf.set_font("Helvetica", "B", 16)
        pdf.multi_cell(0, 9, title)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*GREY)
        pdf.cell(0, 6, f"Reporting period: {period}", ln=True)
        pdf.cell(0, 6, f"Organisation: {user['org']}", ln=True)
        if frameworks:
            pdf.cell(0, 6, f"Frameworks: {', '.join(frameworks)}", ln=True)

        # ── Executive summary ─────────────────────────────────────
        pdf.ln(5)
        pdf.set_fill_color(*LIGHT)
        pdf.set_text_color(*DARK)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Executive Summary", ln=True, fill=True)
        pdf.set_font("Helvetica", "", 10)
        if auditor_note:
            pdf.multi_cell(0, 6, auditor_note)
            pdf.ln(3)

        esg = results['esg']
        grade = "A" if esg>=80 else "B" if esg>=65 else "C" if esg>=50 else "D"
        summary = (
            f"{user['org']} reports total GHG emissions of {results['total']:,.1f} tCO2e "
            f"for the period {period}. The organisation achieves an ESG Climate Score of "
            f"{esg}/100 (Grade {grade}). Emissions intensity is {results['per_emp']:.1f} "
            f"tCO2e per full-time employee, compared to a global average of 8.5 tCO2e."
        )
        pdf.multi_cell(0, 6, summary)

        # ── Key metrics table ─────────────────────────────────────
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "GHG Inventory Summary", ln=True)
        pdf.set_font("Helvetica", "", 10)

        rows = [
            ("Scope 1 — Direct emissions",    f"{results['scope1']:.1f} tCO2e"),
            ("Scope 2 — Purchased electricity",f"{results['scope2']:.1f} tCO2e"),
            ("Scope 3 — Value chain",          f"{results['scope3']:.1f} tCO2e"),
            ("TOTAL GHG (Scope 1+2+3)",        f"{results['total']:,.1f} tCO2e"),
            ("Intensity (per employee)",       f"{results['per_emp']:.1f} tCO2e/FTE"),
            ("Grid emission factor",           f"{results['grid_f']} kgCO2e/kWh ({results['country']})"),
            ("ESG Climate Score",              f"{results['esg']}/100 — Grade {grade}"),
        ]

        col1_w, col2_w = 120, 60
        fill = False
        for label, value in rows:
            pdf.set_fill_color(248, 252, 244) if fill else pdf.set_fill_color(255,255,255)
            pdf.cell(col1_w, 7, label, border=1, fill=True)
            pdf.cell(col2_w, 7, value, border=1, fill=True, ln=True)
            fill = not fill

        # ── Methodology note ──────────────────────────────────────
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Methodology", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREY)
        methodology = (
            "Emission factors sourced from: IPCC Sixth Assessment Report (AR6, 2021), "
            "IEA Emission Factors 2023, Kenya Power Grid Emission Factor (KPLC, 2023: "
            f"0.233 kgCO2e/kWh for Kenya), and the GHG Protocol Corporate Standard. "
            "Scope 3 categories include: business travel (Category 6), "
            "purchased goods & services (Category 1), waste generated in operations "
            "(Category 5), and employee commuting (Category 7). "
            "This report was prepared using the TERRA Carbon Intelligence Platform and "
            "is intended for internal management and voluntary disclosure purposes. "
            "For regulated reporting, third-party verification is recommended."
        )
        pdf.multi_cell(0, 5, methodology)

        # ── Legal footer ──────────────────────────────────────────
        pdf.ln(5)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(160, 160, 160)
        footer = (
            f"This report was generated by TERRA Carbon Intelligence Platform on "
            f"{datetime.now().strftime('%d %B %Y %H:%M')} UTC. "
            f"TERRA is a product of Terra Climate Technologies Ltd, Nairobi, Kenya. "
            f"© {datetime.now().year} Terra Climate Technologies Ltd. All rights reserved. "
            f"Data accuracy is the responsibility of {user['org']}. "
            f"TERRA is not liable for decisions made based on this report."
        )
        pdf.multi_cell(0, 5, footer)

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    def _build_text_fallback(self, user, results, title, frameworks, period) -> bytes:
        """Plain-text fallback when fpdf2 is not installed."""
        now = datetime.now().strftime("%d %B %Y %H:%M")
        lines = [
            "TERRA CARBON INTELLIGENCE PLATFORM",
            "=" * 60,
            title,
            f"Organisation: {user['org']}",
            f"Period: {period}",
            f"Generated: {now} UTC",
            f"Frameworks: {', '.join(frameworks) if frameworks else 'GRI Standards'}",
            "",
            "GHG INVENTORY SUMMARY",
            "-" * 40,
            f"Scope 1 (Direct):         {results['scope1']:.1f} tCO2e",
            f"Scope 2 (Electricity):    {results['scope2']:.1f} tCO2e",
            f"Scope 3 (Value chain):    {results['scope3']:.1f} tCO2e",
            f"TOTAL:                    {results['total']:,.1f} tCO2e/year",
            f"Per employee:             {results['per_emp']:.1f} tCO2e/FTE",
            f"ESG Climate Score:        {results['esg']}/100",
            "",
            "DISCLAIMER",
            "-" * 40,
            "This report was prepared using the TERRA Carbon Intelligence Platform.",
            "Emission factors sourced from IPCC AR6 (2021) and IEA 2023.",
            "For regulated reporting, third-party verification is recommended.",
            f"(c) {datetime.now().year} Terra Climate Technologies Ltd, Nairobi, Kenya.",
        ]
        return "\n".join(lines).encode("utf-8")