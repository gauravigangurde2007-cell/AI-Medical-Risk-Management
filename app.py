import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date

DB_NAME = "risk_management.db"

st.set_page_config(
    page_title="AI Medical Risk Management",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            patient_data TEXT NOT NULL,
            ai_confidence INTEGER NOT NULL,
            human_review TEXT NOT NULL,
            bias_testing TEXT NOT NULL,
            explainability TEXT NOT NULL,
            authentication TEXT NOT NULL,
            average_score REAL NOT NULL,
            overall_level TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS risk_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            risk TEXT NOT NULL,
            category TEXT NOT NULL,
            likelihood INTEGER NOT NULL,
            impact INTEGER NOT NULL,
            risk_score INTEGER NOT NULL,
            severity TEXT NOT NULL,
            mitigation TEXT NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS risk_treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            risk TEXT NOT NULL,
            category TEXT NOT NULL,
            initial_score INTEGER NOT NULL,
            initial_severity TEXT NOT NULL,
            treatment_strategy TEXT NOT NULL,
            control TEXT NOT NULL,
            owner TEXT NOT NULL,
            status TEXT NOT NULL,
            target_date TEXT NOT NULL,
            residual_likelihood INTEGER NOT NULL,
            residual_impact INTEGER NOT NULL,
            residual_score INTEGER NOT NULL,
            residual_severity TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def log_action(action, details):
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (timestamp, action, details) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, details),
    )
    conn.commit()
    conn.close()


initialize_database()

# ============================================================
# RISK ENGINE
# ============================================================

RISK_CATALOG = [
    ("Incorrect AI prediction", "Healthcare", 5, 5),
    ("Patient data privacy breach", "Technical / Ethical", 5, 5),
    ("Bias in training data", "Ethical", 4, 5),
    ("Lack of explainability", "Ethical", 3, 4),
    ("Model hallucination or unsupported output", "Technical", 4, 5),
    ("Unauthorized access", "Technical", 4, 5),
    ("System downtime", "Technical", 3, 3),
    ("Wrong treatment recommendation", "Healthcare", 5, 5),
]


def risk_level(score):
    if score >= 15:
        return "Critical"
    if score >= 10:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def mitigation(risk_name):
    actions = {
        "Incorrect AI prediction":
            "Require doctor or human verification, confidence thresholds, validated datasets and continuous monitoring.",
        "Patient data privacy breach":
            "Use encryption, role-based access control, data minimization and secure audit logs.",
        "Bias in training data":
            "Use diverse datasets, fairness testing, subgroup evaluation and periodic bias audits.",
        "Lack of explainability":
            "Provide interpretable reasons, model documentation and an explainability layer.",
        "Model hallucination or unsupported output":
            "Use validated models, constrained outputs, confidence checks and human review.",
        "Unauthorized access":
            "Implement authentication, authorization, session security and least-privilege access.",
        "System downtime":
            "Use backups, health monitoring, failover procedures and incident response plans.",
        "Wrong treatment recommendation":
            "Do not automate treatment decisions. Require approval from a qualified medical professional.",
    }
    return actions.get(risk_name, "Define an appropriate preventive and corrective control.")


def calculate_risks(patient_data, ai_confidence, human_review,
                     bias_testing, explainability, authentication):
    rows = []

    for name, category, likelihood, impact in RISK_CATALOG:
        adjusted_likelihood = likelihood

        if name == "Incorrect AI prediction" and ai_confidence < 80:
            adjusted_likelihood = min(5, adjusted_likelihood + 1)

        if name == "Patient data privacy breach" and patient_data in ["High", "Very High"]:
            adjusted_likelihood = min(5, adjusted_likelihood + 1)

        if name == "Bias in training data" and bias_testing == "No":
            adjusted_likelihood = min(5, adjusted_likelihood + 1)

        if name == "Lack of explainability" and explainability == "No":
            adjusted_likelihood = min(5, adjusted_likelihood + 1)

        if name in ["Incorrect AI prediction", "Wrong treatment recommendation"] and human_review == "Not Available":
            adjusted_likelihood = min(5, adjusted_likelihood + 1)

        if name == "Unauthorized access" and authentication == "No":
            adjusted_likelihood = min(5, adjusted_likelihood + 1)

        score = adjusted_likelihood * impact

        rows.append({
            "Risk": name,
            "Category": category,
            "Likelihood": adjusted_likelihood,
            "Impact": impact,
            "Risk Score": score,
            "Severity": risk_level(score),
            "Recommended Mitigation": mitigation(name),
        })

    return pd.DataFrame(rows)

# ============================================================
# DATABASE HELPERS
# ============================================================

def save_assessment(df, patient_data, ai_confidence, human_review,
                    bias_testing, explainability, authentication):
    average_score = float(df["Risk Score"].mean())
    overall_level = risk_level(average_score)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO assessments
        (timestamp, patient_data, ai_confidence, human_review,
         bias_testing, explainability, authentication,
         average_score, overall_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, patient_data, ai_confidence, human_review,
        bias_testing, explainability, authentication,
        average_score, overall_level,
    ))

    assessment_id = cur.lastrowid

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO risk_results
            (assessment_id, risk, category, likelihood, impact,
             risk_score, severity, mitigation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id,
            row["Risk"],
            row["Category"],
            int(row["Likelihood"]),
            int(row["Impact"]),
            int(row["Risk Score"]),
            row["Severity"],
            row["Recommended Mitigation"],
        ))

    conn.commit()
    conn.close()

    log_action(
        "Assessment Saved",
        f"Assessment #{assessment_id} saved with overall level {overall_level}.",
    )

    return assessment_id


def load_assessment_history():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            id AS "Assessment ID",
            timestamp AS "Date and Time",
            patient_data AS "Data Sensitivity",
            ai_confidence AS "AI Confidence",
            human_review AS "Human Review",
            average_score AS "Average Score",
            overall_level AS "Overall Level"
        FROM assessments
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def save_treatment(row, strategy, control, owner, status,
                   target_date, residual_likelihood, residual_impact):
    residual_score = residual_likelihood * residual_impact
    residual_severity = risk_level(residual_score)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO risk_treatments
        (risk, category, initial_score, initial_severity,
         treatment_strategy, control, owner, status, target_date,
         residual_likelihood, residual_impact, residual_score,
         residual_severity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["Risk"],
        row["Category"],
        int(row["Risk Score"]),
        row["Severity"],
        strategy,
        control,
        owner,
        status,
        str(target_date),
        residual_likelihood,
        residual_impact,
        residual_score,
        residual_severity,
        created_at,
    ))

    treatment_id = cur.lastrowid
    conn.commit()
    conn.close()

    log_action(
        "Risk Treatment Created",
        f"Treatment #{treatment_id} created for {row['Risk']}.",
    )

    return treatment_id


def load_treatments():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            id AS "Treatment ID",
            risk AS "Risk",
            category AS "Category",
            initial_score AS "Initial Score",
            initial_severity AS "Initial Severity",
            treatment_strategy AS "Treatment",
            control AS "Control",
            owner AS "Owner",
            status AS "Status",
            target_date AS "Target Date",
            residual_likelihood AS "Residual Likelihood",
            residual_impact AS "Residual Impact",
            residual_score AS "Residual Score",
            residual_severity AS "Residual Severity",
            created_at AS "Created At"
        FROM risk_treatments
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def load_audit_log():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT
            id AS "ID",
            timestamp AS "Date and Time",
            action AS "Action",
            details AS "Details"
        FROM audit_log
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🛡️ Risk Management")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Risk Assessment",
        "Risk Register",
        "Risk Treatment",
        "Risk Matrix",
        "Assessment History",
        "Governance & Safety",
        "Audit Log",
        "About Project",
    ],
)

st.sidebar.divider()
st.sidebar.caption("SEP CIAP Micro Project")
st.sidebar.caption("SDG 3 - Good Health and Well-Being")

st.sidebar.subheader("System Inputs")

patient_data = st.sidebar.selectbox(
    "Patient data sensitivity",
    ["Low", "Medium", "High", "Very High"],
    index=3,
    key="patient_data",
)

ai_confidence = st.sidebar.slider(
    "AI model confidence (%)",
    0,
    100,
    72,
    key="ai_confidence",
)

human_review = st.sidebar.selectbox(
    "Human / Doctor verification",
    ["Available", "Not Available"],
    key="human_review",
)

bias_testing = st.sidebar.selectbox(
    "Bias testing performed",
    ["Yes", "No"],
    key="bias_testing",
)

explainability = st.sidebar.selectbox(
    "Explainability available",
    ["Yes", "No"],
    key="explainability",
)

authentication = st.sidebar.selectbox(
    "Strong authentication",
    ["Yes", "No"],
    key="authentication",
)

df = calculate_risks(
    patient_data,
    ai_confidence,
    human_review,
    bias_testing,
    explainability,
    authentication,
)

critical = int((df["Severity"] == "Critical").sum())
high = int((df["Severity"] == "High").sum())
medium = int((df["Severity"] == "Medium").sum())
low = int((df["Severity"] == "Low").sum())
average_score = float(df["Risk Score"].mean())
overall_level = risk_level(average_score)

# ============================================================
# HEADER
# ============================================================

st.title("AI Medical Diagnosis Risk Management Framework")
st.caption("Software Engineering Practices | CIAP Micro Project | SDG 3")

st.warning(
    "Educational prototype only. This system does not provide medical diagnosis "
    "or treatment advice. It demonstrates risk assessment and governance for an "
    "AI-based medical diagnosis system."
)

# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":
    st.header("📊 Risk Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Critical Risks", critical)
    c2.metric("High Risks", high)
    c3.metric("Medium Risks", medium)
    c4.metric("Low Risks", low)

    st.subheader("Overall Risk Assessment")
    st.progress(min(average_score / 25, 1.0))

    c1, c2 = st.columns(2)
    c1.metric("Average Risk Score", f"{average_score:.2f} / 25")
    c2.metric("Overall Risk Level", overall_level)

    treatments = load_treatments()

    if treatments.empty:
        open_count = 0
        implemented_count = 0
        avg_residual = 0
    else:
        open_count = int((treatments["Status"] != "Implemented").sum())
        implemented_count = int((treatments["Status"] == "Implemented").sum())
        avg_residual = float(treatments["Residual Score"].mean())

    st.subheader("Risk Treatment Status")

    t1, t2, t3 = st.columns(3)
    t1.metric("Open Treatments", open_count)
    t2.metric("Implemented Controls", implemented_count)
    t3.metric("Average Residual Risk", f"{avg_residual:.2f}" if not treatments.empty else "N/A")

    st.subheader("Quick Actions")

    a1, a2 = st.columns(2)

    with a1:
        if st.button("💾 Save Current Assessment", use_container_width=True):
            assessment_id = save_assessment(
                df, patient_data, ai_confidence, human_review,
                bias_testing, explainability, authentication,
            )
            st.success(f"Assessment #{assessment_id} saved successfully.")

    with a2:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Risk Register",
            data=csv_data,
            file_name="risk_register_assessment.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ============================================================
# RISK ASSESSMENT
# ============================================================

elif page == "Risk Assessment":
    st.header("⚠️ Risk Assessment")

    st.write("Risk is calculated using:")
    st.code("Risk Score = Likelihood × Impact", language="text")

    st.dataframe(
        df[["Risk", "Category", "Likelihood", "Impact", "Risk Score", "Severity"]],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Current System Configuration")

    config_df = pd.DataFrame({
        "Parameter": [
            "Patient data sensitivity",
            "AI model confidence",
            "Human verification",
            "Bias testing",
            "Explainability",
            "Strong authentication",
        ],
        "Current Value": [
            patient_data,
            f"{ai_confidence}%",
            human_review,
            bias_testing,
            explainability,
            authentication,
        ],
    })

    st.table(config_df)

    if st.button("💾 Save Assessment"):
        assessment_id = save_assessment(
            df, patient_data, ai_confidence, human_review,
            bias_testing, explainability, authentication,
        )
        st.success(f"Assessment #{assessment_id} saved to SQLite.")

# ============================================================
# RISK REGISTER
# ============================================================

elif page == "Risk Register":
    st.header("📋 Risk Register")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Mitigation Plan")

    for _, row in df.sort_values("Risk Score", ascending=False).iterrows():
        with st.expander(
            f"{row['Severity']} - {row['Risk']} "
            f"(Score: {row['Risk Score']}/25)"
        ):
            st.write(f"**Category:** {row['Category']}")
            st.write(f"**Likelihood:** {row['Likelihood']}/5")
            st.write(f"**Impact:** {row['Impact']}/5")
            st.write(f"**Risk Score:** {row['Risk Score']}/25")
            st.write(f"**Recommended Mitigation:** {row['Recommended Mitigation']}")

# ============================================================
# RISK TREATMENT
# ============================================================

elif page == "Risk Treatment":
    st.header("🛠️ Risk Treatment Management")

    st.write(
        "Convert identified risks into actionable treatment plans and "
        "evaluate the expected residual risk after mitigation."
    )

    selected_risk = st.selectbox(
        "Select a risk",
        df["Risk"].tolist(),
    )

    selected_row = df[df["Risk"] == selected_risk].iloc[0]

    st.info(
        f"Initial risk: **{selected_row['Risk Score']}/25 - "
        f"{selected_row['Severity']}**"
    )

    strategy = st.selectbox(
        "Treatment strategy",
        ["Avoid", "Mitigate", "Transfer", "Accept"],
    )

    default_control = selected_row["Recommended Mitigation"]

    control = st.text_area(
        "Control / mitigation action",
        value=default_control,
    )

    owner = st.text_input(
        "Responsible owner",
        value="Security / Project Team",
    )

    status = st.selectbox(
        "Treatment status",
        ["Not Started", "In Progress", "Implemented", "Under Review"],
    )

    target_date = st.date_input(
        "Target completion date",
        value=date.today(),
    )

    st.subheader("Residual Risk")

    st.write(
        "Estimate the likelihood and impact after the proposed control."
    )

    residual_likelihood = st.slider(
        "Residual likelihood",
        1,
        5,
        max(1, min(5, int(selected_row["Likelihood"]) - 1)),
    )

    residual_impact = st.slider(
        "Residual impact",
        1,
        5,
        int(selected_row["Impact"]),
    )

    residual_score = residual_likelihood * residual_impact
    residual_severity = risk_level(residual_score)

    r1, r2 = st.columns(2)
    r1.metric("Residual Score", f"{residual_score} / 25")
    r2.metric("Residual Severity", residual_severity)

    if residual_score < int(selected_row["Risk Score"]):
        st.success("The proposed treatment reduces the calculated risk.")
    elif residual_score == int(selected_row["Risk Score"]):
        st.warning("Residual risk is unchanged. Consider strengthening the control.")
    else:
        st.error("Residual risk is higher than the initial risk. Review the treatment.")

    if st.button("✅ Save Risk Treatment", use_container_width=True):
        if not owner.strip():
            st.error("Please enter a responsible owner.")
        elif not control.strip():
            st.error("Please enter a mitigation control.")
        else:
            treatment_id = save_treatment(
                selected_row,
                strategy,
                control,
                owner.strip(),
                status,
                target_date,
                residual_likelihood,
                residual_impact,
            )
            st.success(f"Risk Treatment #{treatment_id} saved successfully.")

    st.divider()
    st.subheader("Existing Treatment Plans")

    treatment_df = load_treatments()

    if treatment_df.empty:
        st.info("No treatment plans saved yet.")
    else:
        st.dataframe(
            treatment_df,
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# RISK MATRIX
# ============================================================

elif page == "Risk Matrix":
    st.header("🧩 5 × 5 Risk Matrix")

    matrix = []

    for likelihood in range(5, 0, -1):
        row = {"Likelihood": likelihood}

        for impact in range(1, 6):
            score = likelihood * impact
            row[f"Impact {impact}"] = f"{risk_level(score)} ({score})"

        matrix.append(row)

    matrix_df = pd.DataFrame(matrix)

    def style_risk(value):
        if isinstance(value, str):
            if value.startswith("Critical"):
                return "background-color: #8B0000; color: white;"
            if value.startswith("High"):
                return "background-color: #D97706; color: white;"
            if value.startswith("Medium"):
                return "background-color: #EAB308; color: black;"
            if value.startswith("Low"):
                return "background-color: #16A34A; color: white;"
        return ""

    styled = matrix_df.style.map(
        style_risk,
        subset=["Impact 1", "Impact 2", "Impact 3", "Impact 4", "Impact 5"],
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.subheader("Current Risk Positions")

    st.dataframe(
        df[["Risk", "Likelihood", "Impact", "Risk Score", "Severity"]],
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# ASSESSMENT HISTORY
# ============================================================

elif page == "Assessment History":
    st.header("📝 Assessment History")

    history = load_assessment_history()

    if history.empty:
        st.info("No saved assessments yet.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)

        st.metric("Total Saved Assessments", len(history))

# ============================================================
# GOVERNANCE
# ============================================================

elif page == "Governance & Safety":
    st.header("🔐 Governance and Safety")

    checks = {
        "Human verification for medical decisions": human_review == "Available",
        "Patient data protection considered": patient_data in ["High", "Very High"],
        "Bias testing": bias_testing == "Yes",
        "Explainability": explainability == "Yes",
        "Strong authentication": authentication == "Yes",
        "AI confidence threshold": ai_confidence >= 80,
    }

    governance_df = pd.DataFrame([
        {
            "Control": control,
            "Status": "PASS" if status else "ACTION REQUIRED",
        }
        for control, status in checks.items()
    ])

    st.dataframe(
        governance_df,
        use_container_width=True,
        hide_index=True,
    )

    passed = sum(checks.values())
    total = len(checks)

    st.metric("Governance Controls Passed", f"{passed} / {total}")

    if passed == total:
        st.success("All configured governance checks passed.")
    else:
        st.warning(f"{total - passed} governance control(s) require attention.")

    st.subheader("Key Principles")

    st.markdown("""
    - **Human oversight:** Medical decisions should not rely solely on AI.
    - **Privacy:** Patient information must be protected.
    - **Fairness:** Training data should be evaluated for bias.
    - **Explainability:** Important AI outputs should be understandable.
    - **Security:** Access should be restricted to authorized users.
    - **Reliability:** The system should handle failures and downtime safely.
    """)

# ============================================================
# AUDIT LOG
# ============================================================

elif page == "Audit Log":
    st.header("📑 Audit Log")

    log_df = load_audit_log()

    if log_df.empty:
        st.info("No audit events recorded yet.")
    else:
        st.dataframe(
            log_df,
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# ABOUT
# ============================================================

elif page == "About Project":
    st.header("ℹ️ About the Project")

    st.subheader("Project Title")
    st.write(
        "Risk Management Framework for an AI-Based Medical Diagnosis Prototype"
    )

    st.subheader("Course")
    st.write("Software Engineering Practices (SEP)")

    st.subheader("SDG Alignment")
    st.write("SDG 3 - Good Health and Well-Being")

    st.subheader("Objective")
    st.write(
        "Identify, evaluate and mitigate technical, ethical and healthcare "
        "risks associated with AI-based medical diagnosis software."
    )

    st.subheader("Major Modules")

    modules = pd.DataFrame({
        "Module": [
            "Risk Identification",
            "Risk Scoring",
            "Risk Classification",
            "Risk Mitigation",
            "Risk Treatment",
            "Residual Risk",
            "Risk Matrix",
            "Assessment History",
            "Audit Logging",
        ],
        "Purpose": [
            "Identify potential system risks.",
            "Calculate likelihood multiplied by impact.",
            "Classify risks by severity.",
            "Recommend suitable controls.",
            "Assign treatment strategy and ownership.",
            "Evaluate risk remaining after treatment.",
            "Visualize likelihood and impact.",
            "Store previous assessments.",
            "Maintain an activity record.",
        ],
    })

    st.dataframe(
        modules,
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "This is an academic software-engineering prototype and is not "
        "intended for real-world clinical use."
    )
