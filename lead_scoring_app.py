import streamlit as st
import os
import json
from groq import Groq

# Page config 
st.set_page_config(
    page_title="AI Lead Scorer",
    page_icon="!$$!!",
    layout="centered"
)

# Custom CSS 
st.markdown("""
<style>
    .score-box {
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 1rem 0;
    }
    .hot  { background: #fff3cd; border: 2px solid #ffc107; color: #856404; }
    .warm { background: #d1ecf1; border: 2px solid #17a2b8; color: #0c5460; }
    .cold { background: #f8d7da; border: 2px solid #dc3545; color: #721c24; }
    .score-num { font-size: 3rem; font-weight: 700; }
    .tier-label { font-size: 1.2rem; font-weight: 600; margin-top: 0.3rem; }
    .stTextArea textarea { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# Header 
st.title("AI Lead Scoring Tool")
st.markdown("*Powered by gpt-oss-120b | Built for CRM & Sales teams*")
st.divider()

# Sidebar: API Key 
    st.header("Configuration")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Get a free key at console.groq.com"
    )
    st.markdown("---")
    st.markdown("**About this tool**")
    st.markdown(
        "Enter lead details and receive an AI-generated score (0–100), "
        "tier classification, reasoning, and recommended next actions."

    )
    st.markdown("---")
    st.markdown("Built by **Jovial DAlmeida**")
    st.markdown("MSc Business Analytics · Dublin")
    st.markdown("[GitHub](https://github.com/JovialAlmeida) · [LinkedIn](https://linkedin.com/in/joviald)")

# Lead Input Form 
st.subheader("Lead Information")

col1, col2 = st.columns(2)

with col1:
    company_name = st.text_input("Company Name", placeholder="e.g. D'Almeidas' grp")
    industry = st.selectbox("Industry", [
        "Technology", "Finance", "Healthcare", "Retail / E-commerce",
        "Manufacturing", "Education", "Real Estate", "Other"
    ])
    company_size    = st.selectbox("Company Size", [
        "1–10 (Startup)", "11–50 (Small)", "51–200 (Mid-Market)",
        "201–1000 (Growth)", "1000+ (Enterprise)"
    ])
    annual_revenue  = st.selectbox("Annual Revenue (EUR)", [
        "Under €1M", "€1M–€10M", "€10M–€50M", "€50M-€100M", "€100M+"
    ])

with col2:
    contact_name    = st.text_input("Contact Name", placeholder="e.g. Jovial")
    job_title       = st.text_input("Job Title", placeholder="e.g. Head of Sales")
    engagement      = st.selectbox("Engagement Level", [
        "Cold (no prior contact)",
        "Warm (opened emails / attended webinar)",
        "Hot (booked a demo / requested a call)",
        "Existing customer (upsell / cross-sell)"
    ])
    budget_signal   = st.selectbox("Budget Signal", [
        "No signal", "Mentioned budget range", "Confirmed budget approved",
        "Currently evaluating competitors"
    ])

pain_points = st.text_area(
    "Known Pain Points / Notes",
    placeholder="e.g. Struggling with manual CRM data entry, wants to automate lead tracking, mentioned Q3 deadline...",
    height=100
)

timeline = st.selectbox("Purchase Timeline", [
    "No timeline given", "6–12 months", "3–6 months",
    "Within 3 months", "Immediate / urgent need"
])

# Score Button 
st.divider()
score_btn = st.button("Score This Lead", use_container_width=True, type="primary")

# Scoring Logic
if score_btn:
    if not api_key:
        st.error("Please enter your Groq API key in the sidebar.")
        st.stop()

    if not company_name or not contact_name:
        st.warning("Please fill in at least the Company Name and Contact Name.")
        st.stop()

    lead_summary = f"""
    Company: {company_name}
    Industry: {industry}
    Company Size: {company_size}
    Annual Revenue: {annual_revenue}
    Contact: {contact_name} ({job_title})
    Engagement Level: {engagement}
    Budget Signal: {budget_signal}
    Purchase Timeline: {timeline}
    Pain Points / Notes: {pain_points if pain_points else 'None provided'}
    """

    prompt = f"""
You are a senior B2B sales analyst. Analyse the following lead and return ONLY a valid JSON object — no markdown, no explanation outside the JSON.

Lead details:
{lead_summary}

Return exactly this JSON structure:
{{
  "score": <integer 0-100>,
  "tier": "<Hot | Warm | Cold>",
  "summary": "<2-sentence summary of why this score was given>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "risks": ["<risk 1>", "<risk 2>"],
  "next_actions": ["<action 1>", "<action 2>", "<action 3>"],
  "crm_note": "<one sentence ready to paste into a CRM record>"
}}

Scoring guide:
- 75–100 = Hot: strong buying signals, budget confirmed, senior decision-maker, short timeline
- 40–74  = Warm: some engagement, potential fit, needs nurturing
- 0–39   = Cold: poor fit, no engagement, no budget signal
"""

    with st.spinner("Analysing lead with AI..."):
        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            raw = response.choices[0].message.content.strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            result = json.loads(raw)
            
    # Exception Handling
        except json.JSONDecodeError:
            st.error("AI returned an unexpected format. Please try again.")
            st.code(raw)
            st.stop()
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    # Results 
    st.subheader("Lead Score Results")

    score = result.get("score", 0)
    tier  = result.get("tier", "Cold")
    css_class = "hot" if tier == "Hot" else ("warm" if tier == "Warm" else "cold")
    emoji = "🔥" if tier == "Hot" else ("☀️" if tier == "Warm" else "❄️")

    st.markdown(f"""
    <div class="score-box {css_class}">
        <div class="score-num">{score}/100</div>
        <div class="tier-label">{emoji} {tier} Lead</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Summary:** {result.get('summary', '')}")

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Strengths**")
        for s in result.get("strengths", []):
            st.markdown(f"- {s}")

    with col_b:
        st.markdown("**Risks**")
        for r in result.get("risks", []):
            st.markdown(f"- {r}")

    st.divider()
    st.markdown("**Recommended Next Actions**")
    for i, action in enumerate(result.get("next_actions", []), 1):
        st.markdown(f"{i}. {action}")

    st.divider()
    st.markdown("**CRM Note (ready to copy)**")
    st.code(result.get("crm_note", ""), language=None)

    # Raw JSON expander
    with st.expander("View raw JSON response"):
        st.json(result)
