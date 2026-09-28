import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Industrial Supply Chain Procurement Optimizer",
    layout="wide",
)

st.title("Industrial Distribution & MRO Procurement Engine")
st.caption(
    "Multi-vendor stock locator, margin protector, and lead-time optimizer"
)


# 1. Load Data
@st.cache_data
def load_data():
    return pd.read_csv("inventory.csv")


df = load_data()

# 2. Sidebar Filters
st.sidebar.header("Procurement Search Filters")
categories = ["All"] + sorted(df["Category"].unique().tolist())
selected_cat = st.sidebar.selectbox("Filter by Category", categories)

search_term = st.sidebar.text_input(
    "Search Description or SKU", ""
).strip()
max_lead = st.sidebar.slider("Max Acceptable Lead Time (Days)", 1, 30, 14)

# 3. Filter Logic
filtered = df.copy()
if selected_cat != "All":
    filtered = filtered[filtered["Category"] == selected_cat]
if search_term:
    filtered = filtered[
        filtered["Description"].str.contains(search_term, case=False)
        | filtered["SKU"].str.contains(search_term, case=False)
    ]
filtered = filtered[filtered["Lead_Time_Days"] <= max_lead]

# 4. Ghost Inventory & Margin Calculation
filtered["Gross_Margin_%"] = (
    (filtered["List_Price"] - filtered["Unit_Cost"])
    / filtered["List_Price"]
    * 100
).round(1)
# Ghost inventory flag: stock < 5 AND reliability score < 0.75
filtered["Ghost_Risk"] = filtered.apply(
    lambda r: (
        "High Risk"
        if (r["Stock_Qty"] <= 5 and r["Reliability_Score"] < 0.75)
        else "Verified"
    ),
    axis=1,
)

# 5. Top KPI Metrics
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("SKUs Monitored", len(df["SKU"].unique()))
kpi2.metric("Active Vendors", len(df["Vendor"].unique()))
kpi3.metric("Available Options", len(filtered))
high_risk_count = len(filtered[filtered["Ghost_Risk"] == "High Risk"])
kpi4.metric("Flagged Stock Risks", high_risk_count)

st.markdown("---")

# 6. Comparison Table
st.subheader("Vendor Availability Matrix")


def highlight_risk(val):
    color = "#ffcccc" if val == "High Risk" else "#ccffcc"
    return f"background-color: {color}; color: black;"


st.dataframe(
    filtered[
        [
            "SKU",
            "Description",
            "Vendor",
            "Unit_Cost",
            "List_Price",
            "Gross_Margin_%",
            "Stock_Qty",
            "Lead_Time_Days",
            "Ghost_Risk",
        ]
    ].style.applymap(highlight_risk, subset=["Ghost_Risk"]),
    use_container_width=True,
)

# 7. Optimal Sourcing Decision Engine
st.subheader("Optimal Order Recommendation")
if not filtered.empty:
    verified_stock = filtered[filtered["Ghost_Risk"] == "Verified"]
    if not verified_stock.empty:
        best_cost = verified_stock.loc[verified_stock["Unit_Cost"].idxmin()]
        fastest_delivery = verified_stock.loc[
            verified_stock["Lead_Time_Days"].idxmin()
        ]

        rec1, rec2 = st.columns(2)
        with rec1:
            st.success(f"**Lowest Unit Cost Option:** {best_cost['Vendor']}")
            st.write(f"Cost: **${best_cost['Unit_Cost']:,.2f}** per unit")
            st.write(f"Lead Time: **{best_cost['Lead_Time_Days']} days**")
            st.write(f"Gross Margin: **{best_cost['Gross_Margin_%']}%**")

        with rec2:
            st.info(
                f"**Fastest Delivery Option:** {fastest_delivery['Vendor']}"
            )
            st.write(
                f"Cost: **${fastest_delivery['Unit_Cost']:,.2f}** per unit"
            )
            st.write(
                f"Lead Time: **{fastest_delivery['Lead_Time_Days']} days**"
            )
            st.write(f"Gross Margin: **{fastest_delivery['Gross_Margin_%']}%**")
    else:
        st.warning(
            "All available suppliers have high risk of ghost inventory. Extend lead time filter."
        )
else:
    st.write("No matching parts found.")
