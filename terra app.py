"""
╔══════════════════════════════════════════════════════════════════╗
  T E R R A  ·  Carbon Intelligence Platform  v1.0.0
  © 2025 Terra Climate Technologies Ltd · Nairobi, Kenya
  Run:  streamlit run terra_app.py
╚══════════════════════════════════════════════════════════════════╝
"""
import streamlit as st
import sys, os
from datetime import datetime
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(__file__))

from terra.db       import Database
from terra.auth     import Auth
from terra.security import Security
from terra.engine   import CarbonEngine
from terra.reports  import ReportGenerator
from terra.ui       import UI
from terra.policy   import TERMS_OF_SERVICE, PRIVACY_POLICY

st.set_page_config(
    page_title="TERRA · Carbon Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help":     "mailto:support@terra-carbon.io",
        "Report a bug": "mailto:security@terra-carbon.io",
        "About":        "TERRA Carbon Intelligence Platform v1.0.0\n© 2025 Terra Climate Technologies Ltd.",
    },
)

UI.inject_security_meta()
UI.inject_global_styles()

db      = Database()
auth    = Auth(db)
sec     = Security()
engine  = CarbonEngine()
reports = ReportGenerator()

# ── Session defaults ─────────────────────────────────────────────
for k, v in {
    "user": None, "page": "landing",
    "calc_results": None, "login_attempts": 0, "locked_until": 0
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Demo user seed ────────────────────────────────────────────────
def ensure_demo():
    if not db.get_user_by_email("demo@terra-carbon.io"):
        auth.register(
            name="Demo User", email="demo@terra-carbon.io",
            password="Terra2025Demo!", org="Terra Demo Corp",
            plan="business", agreed_terms=True,
            agreed_privacy=True, marketing=False
        )

ensure_demo()

# ════════════════════════════════════════════════════════════════
#  ROUTER
# ════════════════════════════════════════════════════════════════
def route():
    u = st.session_state.user
    p = st.session_state.page
    if u is None:
        if p == "register": page_register()
        elif p == "policy": page_policy()
        else:               page_landing()
    else:
        page_dashboard()

def go(page):
    st.session_state.page = page
    st.rerun()

def do_logout():
    st.session_state.user         = None
    st.session_state.calc_results = None
    st.session_state.page         = "landing"
    st.rerun()

# ════════════════════════════════════════════════════════════════
#  LANDING
# ════════════════════════════════════════════════════════════════
def page_landing():
    UI.render_topbar(user=None)
    _, c, _ = st.columns([1, 1.5, 1])
    with c:
        st.markdown("""
        <div style='text-align:center;padding:2rem 0 1.5rem;'>
          <div style='font-size:2.8rem;margin-bottom:.4rem;'>🌍</div>
          <h1 style='font-size:2.2rem;font-weight:700;letter-spacing:-1px;margin-bottom:.3rem;'>TERRA</h1>
          <p style='font-size:1rem;color:var(--text-muted);margin-bottom:1.8rem;'>
            Carbon Intelligence Platform · Built for African & global SMEs
          </p>
        </div>
        """, unsafe_allow_html=True)

        tab_l, tab_d = st.tabs(["Sign In", "Demo"])
        with tab_l:
            with st.form("login"):
                email = st.text_input("Email", placeholder="you@company.com")
                pwd   = st.text_input("Password", type="password")
                sub   = st.form_submit_button("Sign In →", use_container_width=True)
            if sub:
                ok, msg = sec.check_rate_limit(
                    st.session_state.login_attempts,
                    st.session_state.locked_until)
                if not ok:
                    st.error(msg)
                else:
                    ec = sec.sanitise_email(email)
                    if not ec:
                        st.error("Enter a valid email.")
                    else:
                        user = auth.login(ec, pwd)
                        if user:
                            st.session_state.user           = user
                            st.session_state.login_attempts = 0
                            st.rerun()
                        else:
                            st.session_state.login_attempts += 1
                            rem = max(0, 5 - st.session_state.login_attempts)
                            if rem == 0:
                                import time
                                st.session_state.locked_until = time.time() + 300
                                st.error("Account locked 5 minutes — too many failures.")
                            else:
                                st.error(f"Invalid credentials. {rem} attempt(s) left.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create free account", use_container_width=True, key="go_reg"):
                go("register")

        with tab_d:
            st.info("**demo@terra-carbon.io** · **Terra2025Demo!**")
            if st.button("Launch demo →", use_container_width=True):
                user = auth.login("demo@terra-carbon.io", "Terra2025Demo!")
                if user:
                    st.session_state.user = user
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    for col,(icon,title,body) in zip([c1,c2,c3,c4],[
        ("📊","Carbon Calculator","Scope 1+2+3 · 11 IPCC emission factors"),
        ("🗺️","Reduction Roadmap","7 prioritised actions · ROI ranked"),
        ("🌿","Carbon Credits","Verified African + global offset projects"),
        ("📄","ESG Reports","GRI, TCFD, CSRD, Kenya Carbon Act aligned"),
    ]):
        with col:
            st.markdown(f"""
            <div style='background:var(--card-bg);border:1px solid var(--border);
                 border-radius:12px;padding:1.1rem;text-align:center;min-height:120px;'>
              <div style='font-size:1.5rem;margin-bottom:.4rem;'>{icon}</div>
              <div style='font-weight:600;font-size:.88rem;margin-bottom:.25rem;'>{title}</div>
              <div style='font-size:.78rem;color:var(--text-muted);line-height:1.5;'>{body}</div>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
#  REGISTRATION
# ════════════════════════════════════════════════════════════════
def page_register():
    UI.render_topbar(user=None)
    _, c, _ = st.columns([0.5, 2, 0.5])
    with c:
        st.markdown("## Create your TERRA account")
        st.markdown("*14-day free trial on all plans. No credit card required.*")
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("register", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1: name  = st.text_input("Full name *",         placeholder="Jane Mwangi")
            with c2: org   = st.text_input("Organisation *",       placeholder="Mwangi Logistics Ltd")
            email   = st.text_input("Work email *",                placeholder="jane@company.com")
            c3, c4  = st.columns(2)
            with c3: pwd   = st.text_input("Password *",  type="password",
                                            help="Min 8 chars · 1 number · 1 symbol")
            with c4: pwd2  = st.text_input("Confirm password *", type="password")
            plan    = st.selectbox("Plan *", ["starter","business","enterprise"],
                                   format_func=lambda x:{
                                       "starter":   "Starter — $49/month",
                                       "business":  "Business — $149/month (most popular)",
                                       "enterprise":"Enterprise — $299/month"
                                   }[x], index=1)

            st.markdown("---")
            st.markdown("**Policy agreements (required)**")

            col_t, col_p = st.columns(2)
            show_t = col_t.form_submit_button("📋 Read Terms of Service")
            show_p = col_p.form_submit_button("🔒 Read Privacy Policy")
            if show_t or show_p:
                st.session_state.page = "policy"
                st.rerun()

            ag_terms   = st.checkbox("✅ I agree to the **Terms of Service**")
            ag_privacy = st.checkbox(
                "✅ I agree to the **Privacy Policy** and understand my data is "
                "processed in compliance with Kenya Data Protection Act 2019")
            ag_age     = st.checkbox(
                "✅ I am 18+ and authorised to bind my organisation to these Terms")
            marketing  = st.checkbox(
                "📧 Send me carbon reduction tips and product updates (optional)", value=True)

            submitted = st.form_submit_button(
                "Create Account & Start Free Trial →", use_container_width=True)

        if submitted:
            errs = []
            n2  = sec.sanitise_text(name, 100)
            o2  = sec.sanitise_text(org, 200)
            e2  = sec.sanitise_email(email)
            if not n2:        errs.append("Full name required.")
            if not o2:        errs.append("Organisation required.")
            if not e2:        errs.append("Valid work email required.")
            if not ag_terms:  errs.append("You must agree to the Terms of Service.")
            if not ag_privacy:errs.append("You must agree to the Privacy Policy.")
            if not ag_age:    errs.append("You must confirm you are 18+ and authorised.")
            pw_ok, pw_msg = sec.validate_password(pwd)
            if not pw_ok:     errs.append(pw_msg)
            if pwd != pwd2:   errs.append("Passwords do not match.")
            for e in errs:    st.error(e)
            if not errs:
                ok, msg = auth.register(
                    name=n2, email=e2, password=pwd, org=o2,
                    plan=plan, agreed_terms=True, agreed_privacy=True,
                    marketing=marketing)
                if ok:
                    user = auth.login(e2, pwd)
                    if user:
                        st.session_state.user = user
                        st.success("Welcome to TERRA!")
                        st.rerun()
                else:
                    st.error(msg)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Sign In"):
            go("landing")

# ════════════════════════════════════════════════════════════════
#  POLICY
# ════════════════════════════════════════════════════════════════
def page_policy():
    UI.render_topbar(user=None)
    t1, t2 = st.tabs(["📋 Terms of Service", "🔒 Privacy Policy"])
    with t1: st.markdown(TERMS_OF_SERVICE)
    with t2: st.markdown(PRIVACY_POLICY)
    if st.button("← Back"):
        go("register")

# ════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════
def page_dashboard():
    user = st.session_state.user
    UI.render_topbar(user=user, on_logout=do_logout)

    with st.sidebar:
        st.markdown(f"""
        <div style='padding:.25rem 0 .75rem;'>
          <div style='font-size:.75rem;color:var(--text-muted);'>Signed in as</div>
          <div style='font-weight:600;font-size:.95rem;'>{user['name']}</div>
          <div style='font-size:.8rem;color:var(--text-muted);'>{user['org']}</div>
          <span style='background:var(--green-light);color:var(--green-dark);
                font-size:.68rem;padding:2px 10px;border-radius:20px;font-weight:600;
                display:inline-block;margin-top:.4rem;'>{user['plan'].upper()}</span>
        </div>""", unsafe_allow_html=True)
        st.markdown("---")
        nav = st.radio("Nav", [
            "🏠 Dashboard", "📊 Carbon Calculator",
            "🗺️ Reduction Roadmap", "🌿 Carbon Credits",
            "📄 ESG Reports", "⚙️ Settings"
        ], label_visibility="collapsed")
        st.markdown("---")
        r = st.session_state.calc_results
        st.markdown(f"""
        <div style='font-size:.75rem;color:var(--text-muted);line-height:2;'>
          <div>ESG Score: <b>{r['esg'] if r else '—'}/100</b></div>
          <div>Total: <b>{r['total']:,.0f} tCO₂e</b></div>
          <div>🔒 Encrypted · ✅ GDPR</div>
        </div>""" if r else """
        <div style='font-size:.75rem;color:var(--text-muted);'>
          Run calculator to see stats
        </div>""", unsafe_allow_html=True)

    pages = {
        "🏠 Dashboard":         render_home,
        "📊 Carbon Calculator": render_calculator,
        "🗺️ Reduction Roadmap": render_roadmap,
        "🌿 Carbon Credits":    render_credits,
        "📄 ESG Reports":       render_reports,
        "⚙️ Settings":          render_settings,
    }
    pages[nav](user)


# ════════════════════════════════════════════════════════════════
#  HOME
# ════════════════════════════════════════════════════════════════
def render_home(user):
    st.markdown(f"## Good day, {user['name'].split()[0]} 👋")
    st.caption(f"{user['org']} · Carbon Intelligence Dashboard · {datetime.now().strftime('%d %B %Y')}")
    st.markdown("<br>", unsafe_allow_html=True)
    r = st.session_state.calc_results

    c1,c2,c3,c4 = st.columns(4)
    UI.metric_card(c1,"Total Emissions",
                   f"{r['total']:,.1f}" if r else "—","tCO₂e/yr",
                   delta="▲ Above avg" if r and r['per_emp']>8.5 else "▼ Below avg" if r else None,
                   good=r['per_emp']<=8.5 if r else True)
    UI.metric_card(c2,"ESG Score",
                   str(r['esg']) if r else "—","/ 100",
                   delta="Grade A" if r and r['esg']>=80 else "Grade B" if r and r['esg']>=65 else "Grade C" if r else None,
                   good=r['esg']>=65 if r else True)
    UI.metric_card(c3,"Per Employee",
                   f"{r['per_emp']:.1f}" if r else "—","tCO₂e",
                   delta="vs avg 8.5 t", good=r['per_emp']<=8.5 if r else True)
    UI.metric_card(c4,"Plan",user['plan'].title(),"",delta="Active ✓",good=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if not r:
        st.info("👆 Go to **Carbon Calculator** to calculate your first footprint — takes 2 minutes.")
        return

    ca, cb = st.columns([1.4,1])
    with ca:
        st.markdown("### Emissions breakdown")
        fig = go.Figure(go.Pie(
            labels=list(r['breakdown'].keys()),
            values=list(r['breakdown'].values()),
            hole=0.55,
            marker_colors=["#3B6D11","#639922","#97C459","#BA7517","#534AB7"],
            textinfo="label+percent", textfont_size=12,
        ))
        fig.update_layout(showlegend=False,margin=dict(t=10,b=10,l=10,r=10),
                          height=260,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    with cb:
        st.markdown("### Scope summary")
        for scope, val, pct in [
            ("Scope 1 — Direct", r['scope1'], r['scope1']/max(r['total'],.1)*100),
            ("Scope 2 — Energy", r['scope2'], r['scope2']/max(r['total'],.1)*100),
            ("Scope 3 — Chain",  r['scope3'], r['scope3']/max(r['total'],.1)*100),
        ]:
            st.markdown(f"""
            <div style='margin-bottom:.7rem;'>
              <div style='display:flex;justify-content:space-between;font-size:.85rem;margin-bottom:3px;'>
                <span>{scope}</span><span style='font-weight:600;'>{val:.1f} t ({pct:.0f}%)</span>
              </div>
              <div style='background:var(--border);height:6px;border-radius:3px;overflow:hidden;'>
                <div style='background:var(--green-mid);height:100%;width:{pct:.1f}%;'></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:var(--green-light);border-radius:10px;padding:.9rem;
             text-align:center;margin-top:.5rem;'>
          <div style='font-size:.75rem;color:var(--green-dark);font-weight:600;'>ESG SCORE</div>
          <div style='font-size:2.2rem;font-weight:700;color:var(--green-dark);'>{r['esg']}</div>
          <div style='font-size:.8rem;color:var(--green-dark);'>{r['esg_msg']}</div>
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  CALCULATOR
# ════════════════════════════════════════════════════════════════
def render_calculator(user):
    st.markdown("## Carbon Calculator")
    st.caption("Enter your operational data. All values are encrypted and never shared.")

    ci, cr = st.columns([1.1, 1])
    with ci:
        st.markdown("#### Scope 1 — Direct emissions")
        gas      = st.number_input("Natural gas (m³/month)",       0.0,500000.0, 300.0, 10.0)
        diesel   = st.number_input("Diesel / fuel oil (L/month)",   0.0,500000.0, 500.0, 10.0)
        fleet_km = st.number_input("Fleet vehicles (km/month)",     0.0,5000000.0,8000.0,100.0)
        refrigerant=st.number_input("Refrigerant leakage (kgCO₂e/yr)",0.0,50000.0,50.0,5.0)

        st.markdown("#### Scope 2 — Purchased energy")
        elec     = st.number_input("Electricity (kWh/month)",       0.0,10000000.0,2500.0,100.0)
        steam    = st.number_input("District heating (MWh/month)",  0.0,10000.0,   0.0,  1.0)

        st.markdown("#### Scope 3 — Value chain")
        flights  = st.number_input("Business flights (hrs/year)",   0.0,10000.0,   40.0,  5.0)
        supply   = st.number_input("Supply chain spend ($K/month)", 0.0,100000.0,150.0, 10.0)
        waste    = st.number_input("Waste (tonnes/month)",          0.0,10000.0,    2.0,  0.1)
        commute  = st.number_input("Commute (km/day × employees)",  0.0,1000000.0, 450.0,10.0)

        st.markdown("#### Organisation")
        employees= st.number_input("Employees", 1, 100000, 45, 1)
        country  = st.selectbox("Country / grid", [
            "Kenya","Nigeria","South Africa","Ghana","Ethiopia",
            "United Kingdom","Germany","France","United States","India","Other"])

    inputs = dict(gas=gas, diesel=diesel, fleet_km=fleet_km, refrigerant=refrigerant,
                  elec=elec, steam=steam, flights=flights, supply=supply, waste=waste,
                  commute=commute, employees=employees, country=country)
    r = engine.calculate(inputs)
    st.session_state.calc_results = r
    db.save_calculation(user['id'], inputs, r)

    with cr:
        st.markdown("#### Your carbon footprint")
        esg_c = "#3B6D11" if r['esg']>=70 else "#BA7517" if r['esg']>=50 else "#D85A30"
        grade = "A" if r['esg']>=80 else "B" if r['esg']>=65 else "C" if r['esg']>=50 else "D"
        st.markdown(f"""
        <div style='background:var(--green-light);border:2px solid var(--green-mid);
             border-radius:14px;padding:1.5rem;text-align:center;margin-bottom:1rem;'>
          <div style='font-size:.75rem;color:var(--green-dark);font-weight:600;
               text-transform:uppercase;letter-spacing:.05em;margin-bottom:.3rem;'>
            Total Annual Emissions
          </div>
          <div style='font-size:3rem;font-weight:700;color:var(--green-dark);line-height:1;'>
            {r['total']:,.1f}
          </div>
          <div style='color:var(--green-dark);'>tCO₂e / year</div>
        </div>""", unsafe_allow_html=True)

        for scope, val, pct in [
            ("Scope 1 — Direct",      r['scope1'], r['scope1']/max(r['total'],.1)*100),
            ("Scope 2 — Energy",      r['scope2'], r['scope2']/max(r['total'],.1)*100),
            ("Scope 3 — Value chain", r['scope3'], r['scope3']/max(r['total'],.1)*100),
        ]:
            st.markdown(f"""
            <div style='margin-bottom:.55rem;'>
              <div style='display:flex;justify-content:space-between;font-size:.82rem;margin-bottom:2px;'>
                <span>{scope}</span><span style='font-weight:600;'>{val:.1f} t ({pct:.0f}%)</span>
              </div>
              <div style='background:var(--border);height:5px;border-radius:3px;overflow:hidden;'>
                <div style='background:var(--green-mid);height:100%;width:{pct:.1f}%;'></div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='background:var(--card-bg);border:1px solid var(--border);border-radius:12px;
             padding:1.1rem;text-align:center;margin-top:.75rem;'>
          <div style='font-size:.72rem;color:var(--text-muted);text-transform:uppercase;
               letter-spacing:.05em;margin-bottom:.3rem;'>ESG Climate Score</div>
          <div style='font-size:2.8rem;font-weight:700;color:{esg_c};line-height:1;'>
            {r['esg']}
          </div>
          <div style='font-size:.9rem;color:{esg_c};font-weight:600;'>Grade {grade}</div>
          <div style='background:var(--border);height:7px;border-radius:4px;overflow:hidden;margin:.6rem 0;'>
            <div style='background:{esg_c};height:100%;width:{r['esg']}%;'></div>
          </div>
          <div style='font-size:.78rem;color:var(--text-muted);'>{r['esg_msg']}</div>
        </div>
        <div style='background:var(--card-bg);border:1px solid var(--border);
             border-radius:8px;padding:.75rem 1rem;margin-top:.6rem;
             display:flex;justify-content:space-between;align-items:center;'>
          <span style='color:var(--text-muted);font-size:.82rem;'>Per employee intensity</span>
          <span style='font-weight:700;font-size:1.05rem;
                color:{"#3B6D11" if r["per_emp"]<=8.5 else "#D85A30"};'>
            {r['per_emp']:.1f} tCO₂e
          </span>
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  ROADMAP
# ════════════════════════════════════════════════════════════════
def render_roadmap(user):
    st.markdown("## Reduction Roadmap")
    r = st.session_state.calc_results
    if not r:
        st.warning("Run the Carbon Calculator first.")
        return
    actions = engine.get_roadmap(r)
    total   = r['total']

    ca, cb = st.columns([1.2, 1])
    with ca:
        st.markdown(f"Baseline: **{total:,.1f} tCO₂e/yr** — actions ranked by CO₂ saved per $ invested")
        for i, a in enumerate(actions):
            rc = "#3B6D11" if a['roi']>10 else "#BA7517" if a['roi']>3 else "#888"
            diff = {"Easy":"🟢 Easy","Medium":"🟡 Medium","Hard":"🔴 Hard"}[a['difficulty']]
            st.markdown(f"""
            <div style='background:var(--card-bg);border:1px solid var(--border);
                 border-radius:10px;padding:.9rem 1.1rem;margin-bottom:.5rem;
                 border-left:4px solid {rc};'>
              <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div style='flex:1;'>
                  <div style='font-weight:600;font-size:.92rem;margin-bottom:.15rem;'>
                    {i+1}. {a['title']}
                  </div>
                  <div style='font-size:.78rem;color:var(--text-muted);margin-bottom:.3rem;'>
                    {a['description']} · {diff}
                  </div>
                  <div style='display:flex;gap:1rem;font-size:.75rem;'>
                    <span style='color:{rc};font-weight:600;'>↓ {a['reduction_pct']}% emissions</span>
                    <span style='color:#3B6D11;'>💰 Saves ${a['annual_saving']:,.0f}/yr</span>
                    <span style='color:var(--text-muted);'>ROI {a['roi']:.1f}×</span>
                  </div>
                </div>
                <div style='text-align:right;min-width:72px;'>
                  <div style='font-size:1.15rem;font-weight:700;color:{rc};'>{a['co2_saved']:.0f} t</div>
                  <div style='font-size:.68rem;color:var(--text-muted);'>CO₂ saved/yr</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    with cb:
        st.markdown("#### 5-year trajectory")
        years = [2025,2026,2027,2028,2029,2030]
        bau   = [round(total*(1+i*.035)) for i in range(len(years))]
        terra = [round(total*(.85**i))   for i in range(len(years))]
        fig   = go.Figure()
        fig.add_trace(go.Scatter(x=years,y=bau,  name="Business as usual",
            line=dict(color="#E24B4A",width=2),fill='tozeroy',fillcolor='rgba(226,75,74,0.06)'))
        fig.add_trace(go.Scatter(x=years,y=terra, name="With TERRA",
            line=dict(color="#3B6D11",width=2.5),fill='tozeroy',fillcolor='rgba(59,109,17,0.08)'))
        fig.add_trace(go.Scatter(x=years,y=[0]*len(years),name="Net zero",
            line=dict(color="#1D9E75",width=1.5,dash='dash'),mode='lines'))
        fig.update_layout(height=260,margin=dict(t=5,b=5,l=0,r=0),
            paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(size=10),bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)",title="tCO₂e/yr"))
        st.plotly_chart(fig,use_container_width=True)

        total_red = sum(a['co2_saved'] for a in actions)
        total_sav = sum(a['annual_saving'] for a in actions)
        st.markdown(f"""
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:.6rem;margin-top:.4rem;'>
          <div style='background:var(--green-light);border-radius:10px;padding:.9rem;text-align:center;'>
            <div style='font-size:1.6rem;font-weight:700;color:var(--green-dark);'>
              {round(total_red/max(total,.1)*100)}%
            </div>
            <div style='font-size:.72rem;color:var(--green-dark);font-weight:500;'>Achievable reduction</div>
          </div>
          <div style='background:#EAF3DE;border-radius:10px;padding:.9rem;text-align:center;'>
            <div style='font-size:1.6rem;font-weight:700;color:#27500A;'>${total_sav:,.0f}</div>
            <div style='font-size:.72rem;color:#27500A;font-weight:500;'>Annual cost savings</div>
          </div>
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  CARBON CREDITS
# ════════════════════════════════════════════════════════════════
def render_credits(user):
    st.markdown("## Carbon Credit Marketplace")
    st.caption("Verified offsets from African and global projects. Transparent pricing.")
    r = st.session_state.calc_results
    residual = r['total']*0.35 if r else 500.0

    cc, cm = st.columns([1,1.2])
    with cc:
        st.markdown("#### Offset calculator")
        price  = st.slider("Carbon price ($/tCO₂e)", 5, 150, 18)
        offset = st.slider("% to offset", 0, 100, 60, 5)
        tonnes = round(residual*offset/100,1); cost=round(tonnes*price)
        st.markdown(f"""
        <div style='background:var(--card-bg);border:1px solid var(--border);
             border-radius:12px;padding:1.1rem;'>
          {"".join([f"<div style='display:flex;justify-content:space-between;padding:.35rem 0;border-bottom:1px solid var(--border);font-size:.88rem;'><span style='color:var(--text-muted);'>{k}</span><span style='font-weight:500;'>{v}</span></div>" for k,v in [("Residual emissions",f"{residual:.1f} tCO₂e"),("Tonnes to offset",f"{tonnes} t"),("Credits needed",f"{int(tonnes)}"),]])}
          <div style='display:flex;justify-content:space-between;padding:.5rem 0;font-size:.95rem;font-weight:700;'>
            <span>Annual cost</span><span style='color:#3B6D11;'>${cost:,}</span>
          </div>
        </div>""", unsafe_allow_html=True)

    with cm:
        st.markdown("#### Available projects")
        for p in [
            ("Nairobi Reforestation",  "🇰🇪 Kenya",    11, "VCS+CCBS", 8500,  95),
            ("Turkana Wind Farm",      "🇰🇪 Kenya",    14, "Gold Std", 22000, 92),
            ("Cookstoves East Africa", "🇹🇿 Tanzania",  8, "CDM",      45000, 88),
            ("Mangrove Blue Carbon",   "🇲🇿 Mozambique",22,"VCS",      3200,  97),
            ("Solar Mini-Grids",       "🇺🇬 Uganda",   12, "Gold Std", 18000, 90),
            ("Direct Air Capture",     "🌍 Global",   180, "Puro.earth",500,  99),
        ]:
            name,country,price2,cert,avail,qual = p
            qc = "#3B6D11" if qual>=95 else "#639922" if qual>=88 else "#BA7517"
            st.markdown(f"""
            <div style='background:var(--card-bg);border:1px solid var(--border);
                 border-radius:9px;padding:.8rem .95rem;margin-bottom:.4rem;
                 display:flex;align-items:center;gap:.8rem;'>
              <div style='flex:1;'>
                <div style='font-weight:600;font-size:.87rem;'>{name}</div>
                <div style='font-size:.72rem;color:var(--text-muted);'>
                  {country} · {cert} · {avail:,} credits</div>
              </div>
              <div style='text-align:right;'>
                <div style='font-size:1rem;font-weight:700;color:#3B6D11;'>${price2}/t</div>
                <div style='font-size:.68rem;font-weight:600;color:{qc};'>{qual}% quality</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.info("💡 Enterprise clients get bulk pricing and forward contracts. Upgrade in Settings.")


# ════════════════════════════════════════════════════════════════
#  REPORTS
# ════════════════════════════════════════════════════════════════
def render_reports(user):
    st.markdown("## ESG Reports")
    st.caption("Regulatory-aligned reports for investors, auditors, and government bodies.")
    r = st.session_state.calc_results
    if not r:
        st.warning("Run the Carbon Calculator first.")
        return

    cl, cr = st.columns([1, 1.2])
    with cl:
        st.markdown("#### Report settings")
        title_in    = st.text_input("Title", value=f"{user['org']} — ESG Climate Report 2025")
        frameworks  = st.multiselect("Frameworks",
                          ["GRI Standards","TCFD","CSRD","GHG Protocol","Kenya Carbon Act"],
                          default=["GRI Standards","TCFD"])
        period      = st.selectbox("Period", ["January–December 2025","April 2024–March 2025"])
        note        = st.text_area("Executive summary (optional)", height=70)
        inc_road    = st.checkbox("Include reduction roadmap", True)
        inc_cred    = st.checkbox("Include carbon offset summary", True)

        if st.button("📥 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Generating your ESG report..."):
                pdf_bytes = reports.generate_pdf(
                    user=user, results=r, title=title_in,
                    frameworks=frameworks, period=period,
                    auditor_note=note,
                    include_roadmap=inc_road, include_credits=inc_cred)
            st.download_button(
                "⬇ Download PDF",
                data=pdf_bytes,
                file_name=f"TERRA_ESG_{user['org'].replace(' ','_')}_2025.pdf",
                mime="application/pdf",
                use_container_width=True)
            db.log_event(user['id'], "REPORT_GENERATED")
            st.success("Report ready!")

    with cr:
        st.markdown("#### Report preview")
        grade = "A" if r['esg']>=80 else "B" if r['esg']>=65 else "C" if r['esg']>=50 else "D"
        st.markdown(f"""
        <div style='background:var(--card-bg);border:1px solid var(--border);
             border-radius:12px;padding:1.4rem;font-family:Georgia,serif;'>
          <div style='display:flex;align-items:center;gap:.7rem;margin-bottom:1.2rem;
               padding-bottom:.9rem;border-bottom:2px solid #3B6D11;'>
            <span style='font-size:1.6rem;'>🌍</span>
            <div>
              <div style='font-size:1rem;font-weight:700;'>TERRA</div>
              <div style='font-size:.72rem;color:var(--text-muted);'>Carbon Intelligence Platform</div>
            </div>
          </div>
          <div style='font-size:.95rem;font-weight:700;margin-bottom:.2rem;'>{title_in}</div>
          <div style='font-size:.78rem;color:var(--text-muted);margin-bottom:.9rem;'>
            {period} · {datetime.now().strftime('%d %B %Y')}
          </div>
          {"".join([f"<div style='display:flex;justify-content:space-between;padding:.35rem 0;border-bottom:1px solid var(--border);font-size:.82rem;'><span style='color:var(--text-muted);'>{k}</span><span style='font-weight:500;color:{\"#3B6D11\" if good else \"#D85A30\"};'>{v}</span></div>" for k,v,good in [
              ("Total GHG (Scope 1+2+3)",  f"{r['total']:,.1f} tCO₂e", r['total']<1000),
              ("Scope 1",                   f"{r['scope1']:.1f} tCO₂e", True),
              ("Scope 2",                   f"{r['scope2']:.1f} tCO₂e", True),
              ("Scope 3",                   f"{r['scope3']:.1f} tCO₂e", True),
              ("Intensity (per employee)",  f"{r['per_emp']:.1f} tCO₂e/FTE", r['per_emp']<=8.5),
              ("ESG Score",                 f"{r['esg']}/100 · Grade {grade}", r['esg']>=65),
              ("Paris alignment",           "On track ✓" if r['esg']>=65 else "Action required", r['esg']>=65),
          ]])}
          <div style='margin-top:.9rem;padding:.6rem .8rem;background:var(--green-light);
               border-radius:7px;font-size:.75rem;color:var(--green-dark);'>
            Frameworks: {", ".join(frameworks) if frameworks else "GRI Standards"}
          </div>
          <div style='margin-top:.8rem;font-size:.68rem;color:var(--text-muted);'>
            © {datetime.now().year} Terra Climate Technologies Ltd.
            Data provided by {user['org']}. For guidance purposes only.
          </div>
        </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  SETTINGS
# ════════════════════════════════════════════════════════════════
def render_settings(user):
    st.markdown("## Account Settings")
    t1, t2, t3 = st.tabs(["Profile", "Security", "Data & Privacy"])

    with t1:
        with st.form("profile"):
            st.text_input("Name",         value=user['name'])
            st.text_input("Organisation", value=user['org'])
            st.text_input("Email",        value=user['email'], disabled=True,
                          help="Contact support to change your email.")
            st.selectbox("Industry", ["Technology","Logistics","Retail",
                                      "Manufacturing","Finance","Agriculture","Other"])
            st.selectbox("Country", ["Kenya","Nigeria","South Africa","Ghana",
                                     "United Kingdom","Germany","Other"])
            if st.form_submit_button("Save"):
                st.success("Profile saved.")

    with t2:
        st.markdown("#### Change password")
        with st.form("chpwd"):
            cur  = st.text_input("Current password",     type="password")
            new1 = st.text_input("New password",         type="password")
            new2 = st.text_input("Confirm new password", type="password")
            if st.form_submit_button("Update password"):
                if not auth.verify_password(user['id'], cur):
                    st.error("Current password incorrect.")
                elif new1 != new2:
                    st.error("Passwords don't match.")
                else:
                    ok, msg = sec.validate_password(new1)
                    if not ok: st.error(msg)
                    else:
                        auth.change_password(user['id'], new1)
                        st.success("Password updated.")
        st.markdown("""
        #### Security notes
        - Passwords are hashed with **bcrypt (cost 12)** — never stored in plain text
        - All queries use parameterised SQL — protected against injection
        - Sessions use Streamlit's encrypted cookie store
        - Authentication is rate-limited (5 attempts, 5-min lockout)
        """)

    with t3:
        st.markdown("#### Your data rights")
        st.markdown("""
        Under the **Kenya Data Protection Act 2019** and GDPR principles:

        | Right | Action |
        |-------|--------|
        **Access** | Download all your data below |
        **Rectification** | Edit your profile above |
        **Erasure** | Delete account below |
        **Portability** | Export JSON below |
        **Objection** | Unsubscribe from emails in profile |
        """)
        c1,c2 = st.columns(2)
        with c1:
            if st.button("📦 Export my data", use_container_width=True):
                import json
                data = db.export_user_data(user['id'])
                st.download_button("⬇ Download JSON", data=json.dumps(data,indent=2,default=str),
                    file_name=f"terra_export_{user['id']}.json", mime="application/json")
        with c2:
            if st.button("🗑️ Delete account", use_container_width=True):
                st.warning("This permanently deletes your account and all data.")
                if st.checkbox("I confirm — delete my account permanently"):
                    db.delete_user(user['id'])
                    do_logout()
        st.markdown("---")
        if st.button("📋 View full policies"):
            go("policy")


# ════════════════════════════════════════════════════════════════
#  ENTRY
# ════════════════════════════════════════════════════════════════
route()