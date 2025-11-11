# PhonePe Transaction Analysis Dashboard
# A simplified and refined Streamlit application for analyzing PhonePe transaction data

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import json

# ========================
# CONFIGURATION
# ========================
st.set_page_config(
    page_title="PhonePe Transaction Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================
# DATABASE CONNECTION
# ========================
@st.cache_resource                        #cache the database engine to avoid reconnecting on every function call
def get_database_engine():
    """Create database connection with error handling."""
    try:
        engine = create_engine("mysql+mysqlconnector://root:12345@localhost:3306/phonepe_db")
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# ========================
# DATA LOADING FUNCTIONS
# ========================
@st.cache_data                         #cache the geojson data to avoid reloading on every function call
def load_geojson_data():
    """Load and process GeoJSON data with Odisha fix."""
    try:
        with open("Indian_States.geojson", "r") as f:
            geojson_data = json.load(f)
        
        # Process state names and fix Odisha mapping
        for feature in geojson_data["features"]:                                    #ITERATE THROUGH EACH FEATURE
            if "properties" not in feature:
                feature["properties"] = {}                                          # Ensure properties key exists empty
            
            state_name = feature["properties"].get("NAME_1", "")                    # Get state name
            if isinstance(state_name, str):
                # Standardize state name
                standardized_name = state_name.lower().strip()
                
                # Hardcoded fix for Odisha
                if standardized_name == "orissa":
                    standardized_name = "odisha"
                
                feature["properties"]["State_Name"] = standardized_name
            else:
                feature["properties"]["State_Name"] = ""
        
        return geojson_data
    except Exception as e:
        st.error(f"Failed to load GeoJSON data: {e}")
        return {"type": "FeatureCollection", "features": []}

@st.cache_data
def load_table_data(table_name):
    """Load data from database table with state name standardization."""
    engine = get_database_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, engine)
        
        # Standardize state names if States column exists
        if "States" in df.columns:
            df["States"] = df["States"].str.lower().str.strip()
            
            # Apply state name mappings including Odisha fix
            state_mappings = {
                "andaman and nicobar": "andaman & nicobar islands",
                "dadra and nagar haveli and daman and diu": "dadra & nagar haveli & daman & diu",
                "orissa": "odisha"  # Hardcoded Odisha fix
            }
            df["States"] = df["States"].replace(state_mappings)
            
            # Rename States column to State for consistency
            df.rename(columns={"States": "State"}, inplace=True)
        
        return df
    except Exception as e:
        st.error(f"Failed to load data from {table_name}: {e}")
        return pd.DataFrame()

# ========================
# DATA LOADING
# ========================
@st.cache_data
def load_all_data():
    """Load all required data tables."""
    tables = {
        "agg_transaction": "aggregated_transaction",
        "agg_insurance": "aggregated_insurance", 
        "agg_user": "aggregated_user",
        "map_transaction": "map_transaction",
        "map_insurance": "map_insurance",
        "map_user": "map_user",
        "top_transaction": "top_transaction",
        "top_insurance": "top_insurance",
        "top_user": "top_user"
    }
    
    data = {}
    for key, table_name in tables.items():
        data[key] = load_table_data(table_name)
    
    return data

# ========================
# VISUALIZATION FUNCTIONS
# ========================
def create_choropleth_map(df, value_col, title, color_scale="Viridis", value_suffix=""):
    """Create a standardized choropleth map."""
    if df.empty:
        st.warning("No data available for the map.")
        return None
    
    fig = go.Figure(data=go.Choropleth(
        geojson=geojson_data,
        featureidkey="properties.State_Name",
        locationmode="geojson-id",
        locations=df["State"],
        z=df[value_col],
        colorscale=color_scale,
        marker_line_color="white",
        marker_line_width=1.5,
        colorbar=dict(title=f"{value_col.replace('_', ' ').title()} ({value_suffix})")
    ))
    
    fig.update_geos(
        visible=False,
        projection=dict(type="conic conformal", parallels=[12.47, 35.17], rotation={"lat": 24, "lon": 80}),
        lonaxis={"range": [68, 98]},
        lataxis={"range": [6, 38]}
    )
    
    fig.update_layout(
        title=title,
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        height=600
    )
    
    return fig

def create_pie_chart(df, values_col, names_col, title):
    """Create a standardized pie chart."""
    if df.empty:
        st.warning("No data available for the chart.")
        return None
    
    fig = px.pie(df, values=values_col, names=names_col, title=title, hole=0.4)
    fig.update_layout(height=400)
    return fig

def create_bar_chart(df, x_col, y_col, title, text_auto=True):
    """Create a standardized bar chart."""
    if df.empty:
        st.warning("No data available for the chart.")
        return None
    
    fig = px.bar(df, x=x_col, y=y_col, title=title, text_auto=text_auto, color=x_col)
    fig.update_layout(height=400, xaxis_title=x_col.replace('_', ' ').title(), 
                     yaxis_title=y_col.replace('_', ' ').title())
    return fig

# ========================
# MAIN APPLICATION
# ========================

# Load all data
data = load_all_data()
geojson_data = load_geojson_data()

# Sidebar Navigation
st.sidebar.title("PhonePe Transactions")
st.sidebar.markdown("### Navigate through different analysis sections")
page = st.sidebar.radio("Select Section", ["📊 Dashboard", "🔍 Case Studies"])

# ========================
# HOME PAGE / DASHBOARD
# ========================
if page == "📊 Dashboard":
    st.title("📱 PhonePe Transaction Analysis Dashboard")
    st.markdown("""
    ## Welcome to PhonePe Transaction Insights
    
    Explore India's digital payment landscape through comprehensive transaction analysis. 
    This dashboard provides insights into:
    
    - **💳 Transaction Patterns**: Volume and amount trends across states and time periods
    - **📱 User Engagement**: Device preferences and app usage analytics  
    - **🛡️ Insurance Growth**: Insurance transaction analysis and market penetration
    - **📈 Market Expansion**: Identify high-potential regions for business growth
    
    Navigate to **Case Studies** for detailed business analysis scenarios.
    """)

    # Quick Statistics
    st.subheader("📈 Quick Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_transactions = data["agg_transaction"]["Transaction_count"].sum() if not data["agg_transaction"].empty else 0
        st.metric("Total Transactions", f"{total_transactions / 1e9:.1f}B")
    
    with col2:
        total_amount = data["agg_transaction"]["Transaction_amount"].sum() if not data["agg_transaction"].empty else 0
        st.metric("Total Amount", f"₹{total_amount / 1e12:.1f}T")
    
    with col3:
        total_users = data["top_user"]["Registered_Users"].sum() if not data["top_user"].empty else 0
        st.metric("Registered Users", f"{total_users / 1e6:.1f}M")
        
    with col4:
        total_insurance = data["agg_insurance"]["Insurance_amount"].sum() if not data["agg_insurance"].empty else 0
        st.metric("Insurance Amount", f"₹{total_insurance / 1e9:.1f}B")

    # Main Dashboard Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗺️ Transaction Heatmap")
        if not data["agg_transaction"].empty:
            latest_year = data["agg_transaction"]["Years"].max()
            latest_quarter = data["agg_transaction"][data["agg_transaction"]["Years"] == latest_year]["Quarter"].max()
            
            filtered_df = data["agg_transaction"][
                (data["agg_transaction"]["Years"] == latest_year) & 
                (data["agg_transaction"]["Quarter"] == latest_quarter)
            ].groupby("State").agg({
                "Transaction_amount": "sum",
                "Transaction_count": "sum"
            }).reset_index()
            
            filtered_df["Amount_M"] = filtered_df["Transaction_amount"] / 1e6
            
            fig = create_choropleth_map(
                filtered_df, 
                "Amount_M", 
                f"Transaction Amount - {latest_year} Q{latest_quarter}",
                "Viridis",
                "₹M"
            )
            if fig:
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Transaction Trend")
        if not data["agg_transaction"].empty:
            trend_data = data["agg_transaction"].groupby(["Years", "Quarter"])["Transaction_amount"].sum().reset_index()
            trend_data["Period"] = trend_data["Years"].astype(str) + " Q" + trend_data["Quarter"].astype(str)
            
            fig = px.line(
                trend_data, 
                x="Period", 
                y="Transaction_amount",
                title="Transaction Amount Over Time",
                markers=True
            )
            fig.update_layout(
                height=600,
                xaxis_title="Time Period",
                yaxis_title="Transaction Amount (₹)",
                yaxis=dict(tickformat=".2e")
            )
            st.plotly_chart(fig, use_container_width=True)

# ========================
# CASE STUDIES PAGE
# ========================
# ========================
# CASE STUDIES PAGE
# ========================
elif page == "🔍 Case Studies":
    st.title("🔍 Business Case Studies")
    
    case_study = st.sidebar.selectbox("Select Case Study", [
        "💳 Transaction Dynamics Analysis",
        "📱 Device Usage & User Engagement", 
        "🛡️ Insurance Market Analysis",
        "🎯 Market Expansion Strategy",
        "👥 User Growth Analysis"
    ])

    # ------------------------------------------------------------------
    # CASE STUDY 1: TRANSACTION DYNAMICS
    # ------------------------------------------------------------------
    if case_study == "💳 Transaction Dynamics Analysis":
        st.header("💳 Transaction Dynamics Analysis")
        st.markdown("**Objective:** Explore how transaction count, amount, and type vary across time and states for strategic planning.")
        
        col1, col2 = st.columns(2)
        with col1:
            years = sorted(data["agg_transaction"]["Years"].unique())
            selected_year = st.selectbox("Select Year", years, key="td_year")
        with col2:
            quarters = sorted(data["agg_transaction"][data["agg_transaction"]["Years"] == selected_year]["Quarter"].unique())
            selected_quarter = st.selectbox("Select Quarter", quarters, key="td_quarter")
        
        filtered = data["agg_transaction"][
            (data["agg_transaction"]["Years"] == selected_year) & 
            (data["agg_transaction"]["Quarter"] == selected_quarter)
        ]
        if filtered.empty:
            st.warning("No transaction data for selected period.")
        else:
            # 1️⃣ State-wise Heatmap
            state_summary = filtered.groupby("State", as_index=False)["Transaction_amount"].sum()
            state_summary["Amount_M"] = state_summary["Transaction_amount"] / 1e6
            st.subheader("1️⃣ State-wise Transaction Heatmap")
            fig = create_choropleth_map(state_summary, "Amount_M", f"Transaction Heatmap - {selected_year} Q{selected_quarter}", "Blues", "₹M")
            st.plotly_chart(fig, use_container_width=True)

            # 2️⃣ Top 10 States
            st.subheader("2️⃣ Top 10 States by Transaction Amount")
            top10 = state_summary.nlargest(10, "Transaction_amount")
            fig = create_bar_chart(top10, "State", "Amount_M", "Top 10 States (₹M)")
            st.plotly_chart(fig, use_container_width=True)

            # 3️⃣ Payment Type Distribution
            st.subheader("3️⃣ Payment Type Distribution")
            pay_type = filtered.groupby("Transaction_type")["Transaction_count"].sum().reset_index()
            fig = create_pie_chart(pay_type, "Transaction_count", "Transaction_type", "Transaction Count by Type")
            st.plotly_chart(fig, use_container_width=True)

            # 4️⃣ Yearly Growth Trend
            st.subheader("4️⃣ Yearly Growth Trend")
            growth = data["agg_transaction"].groupby("Years")["Transaction_amount"].sum().reset_index()
            fig = px.line(growth, x="Years", y="Transaction_amount", title="Yearly Transaction Growth", markers=True)
            st.plotly_chart(fig, use_container_width=True)

            # 5️⃣ Average Transaction Value
            st.subheader("5️⃣ Average Transaction Value per Transaction")
            avg_val = filtered.groupby("State").apply(lambda x: (x["Transaction_amount"].sum() / x["Transaction_count"].sum())).reset_index(name="Avg_Value")
            fig = create_bar_chart(avg_val.nlargest(10, "Avg_Value"), "State", "Avg_Value", "Top 10 Avg Transaction Value (₹)")
            st.plotly_chart(fig, use_container_width=True)
    # ------------------------------------------------------------------
    # CASE STUDY 2: DEVICE USAGE & USER ENGAGEMENT (SIMPLE & CONSISTENT)
    # ------------------------------------------------------------------
        # ------------------------------------------------------------------
    # CASE STUDY 2: DEVICE USAGE & USER ENGAGEMENT (NO REGISTERED_USERS)
    # ------------------------------------------------------------------
    elif case_study == "📱 Device Usage & User Engagement":
        st.header("📱 Device Usage & User Engagement")
        st.markdown("**Objective:** Analyze user engagement based on device brands and app usage patterns across regions.**")

        # Dropdown filters for Year and Quarter
        years = sorted(data["agg_user"]["Years"].unique())
        selected_year = st.selectbox("Select Year", years, key="du_year")

        quarters = sorted(data["agg_user"][data["agg_user"]["Years"] == selected_year]["Quarter"].unique())
        selected_quarter = st.selectbox("Select Quarter", quarters, key="du_quarter")

        # Filter data for selected year and quarter
        user_df = data["agg_user"][
            (data["agg_user"]["Years"] == selected_year) & 
            (data["agg_user"]["Quarter"] == selected_quarter)
        ]
        map_df = data["map_user"][
            (data["map_user"]["Years"] == selected_year) & 
            (data["map_user"]["Quarter"] == selected_quarter)
        ]

        # Check if data is available
        if user_df.empty or map_df.empty:
            st.warning("No user data available for the selected period.")
        else:
            # 1️⃣ Top 10 Device Brands by Count
            st.subheader("📱 Top 10 Device Brands by Transaction_count")
            brand_data = (
                user_df.groupby("Brands")["Transaction_count"].sum()
                .reset_index()
                .sort_values(by="Transaction_count", ascending=False)
                .head(10)
            )
            fig1 = px.bar(
                brand_data,
                x="Brands",
                y="Transaction_count",
                text_auto=True,
                color="Brands",
                title=f"Top 10 Device Brands - {selected_year} Q{selected_quarter}"
            )
            st.plotly_chart(fig1, use_container_width=True)

            # 2️⃣ Top 10 States by App Opens
            st.subheader("🌍 Top 10 States by App Opens")
            state_usage = (
                map_df.groupby("State")["AppOpens"].sum()
                .reset_index()
                .sort_values(by="AppOpens", ascending=False)
                .head(10)
            )
            fig2 = px.bar(
                state_usage,
                x="State",
                y="AppOpens",
                text_auto=True,
                color="State",
                title=f"Top 10 States by App Opens - {selected_year} Q{selected_quarter}"
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # 3️⃣ Pie Chart: Share of Device Usage by State
            st.subheader("🥧 Share of Device Usage by State")
            state_device_share = (
                user_df.groupby("State")["Transaction_count"]
                .sum()
                .reset_index()
                .sort_values(by="Transaction_count", ascending=False)
                .head(10)
            )
            fig3 = px.pie(
                state_device_share,
                values="Transaction_count",
                names="State",
                title=f"Top 10 States by Share of Total Device Usage - {selected_year} Q{selected_quarter}",
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig3.update_traces(textinfo='percent+label', pull=[0.05]*len(state_device_share))
            st.plotly_chart(fig3, use_container_width=True)

    # ------------------------------------------------------------------
    # CASE STUDY 3: INSURANCE MARKET ANALYSIS
    # ------------------------------------------------------------------
    elif case_study == "🛡️ Insurance Market Analysis":
        st.header("🛡️ Insurance Market Analysis")
        st.markdown("**Objective:** Track the growth and penetration of insurance transactions across India.")
        
        years = sorted(data["agg_insurance"]["Years"].unique())
        year = st.selectbox("Select Year", years, key="ins_year")
        quarters = sorted(data["agg_insurance"][data["agg_insurance"]["Years"] == year]["Quarter"].unique())
        quarter = st.selectbox("Select Quarter", quarters, key="ins_quarter")
        
        ins = data["agg_insurance"][(data["agg_insurance"]["Years"] == year) & (data["agg_insurance"]["Quarter"] == quarter)]
        if ins.empty:
            st.warning("No insurance data available.")
        else:
            # 1️⃣ Heatmap
            state_ins = ins.groupby("State", as_index=False)["Insurance_amount"].sum()
            state_ins["Amount_M"] = state_ins["Insurance_amount"] / 1e6
            fig = create_choropleth_map(state_ins, "Amount_M", f"Insurance - {year} Q{quarter}", "Oranges", "₹M")
            st.plotly_chart(fig, use_container_width=True)

            # 2️⃣ Top 10 States
            top10 = state_ins.nlargest(10, "Insurance_amount")
            fig = create_bar_chart(top10, "State", "Amount_M", "Top States by Insurance (₹M)")
            st.plotly_chart(fig, use_container_width=True)

            # 3️⃣ Quarterly Growth
            trend = data["agg_insurance"][data["agg_insurance"]["Years"] == year].groupby("Quarter")["Insurance_amount"].sum().reset_index()
            fig = px.line(trend, x="Quarter", y="Insurance_amount", title="Quarterly Insurance Growth", markers=True)
            st.plotly_chart(fig, use_container_width=True)

            # 4️⃣ Average Insurance per Policy
            ins["Avg_Policy_Value"] = ins["Insurance_amount"] / (ins["Insurance_count"] + 1)
            avg_policy = ins.groupby("State")["Avg_Policy_Value"].mean().nlargest(10).reset_index()
            fig = create_bar_chart(avg_policy, "State", "Avg_Policy_Value", "Average Policy Value by State")
            st.plotly_chart(fig, use_container_width=True)

            # 5️⃣ Year-on-Year Comparison
            yearly = data["agg_insurance"].groupby("Years")["Insurance_amount"].sum().reset_index()
            fig = px.line(yearly, x="Years", y="Insurance_amount", title="Year-on-Year Insurance Growth", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # CASE STUDY 4: MARKET EXPANSION STRATEGY
    # ------------------------------------------------------------------
    elif case_study == "🎯 Market Expansion Strategy":
        st.header("🎯 Market Expansion Strategy")
        st.markdown("**Objective:** Identify states with highest market potential based on transaction and growth metrics.")
        
        years = sorted(data["map_transaction"]["Years"].unique())
        year = st.selectbox("Select Year", years, key="exp_year")
        quarters = sorted(data["map_transaction"][data["map_transaction"]["Years"] == year]["Quarter"].unique())
        quarter = st.selectbox("Select Quarter", quarters, key="exp_quarter")
        
        exp = data["map_transaction"][(data["map_transaction"]["Years"] == year) & (data["map_transaction"]["Quarter"] == quarter)]
        if exp.empty:
            st.warning("No transaction mapping data available.")
        else:
            exp_summary = exp.groupby("State", as_index=False).agg({"Transaction_amount": "sum", "Transaction_count": "sum"})
            exp_summary["Amount_M"] = exp_summary["Transaction_amount"] / 1e6

            # 1️⃣ Heatmap
            fig = create_choropleth_map(exp_summary, "Amount_M", f"Market Penetration - {year} Q{quarter}", "Reds", "₹M")
            st.plotly_chart(fig, use_container_width=True)

            # 2️⃣ Growth Potential
            exp_summary["Growth_Score"] = (exp_summary["Transaction_amount"] / exp_summary["Transaction_count"]).fillna(0)
            fig = create_bar_chart(exp_summary.nlargest(10, "Growth_Score"), "State", "Growth_Score", "Top 10 Growth Potential States")
            st.plotly_chart(fig, use_container_width=True)

            # 3️⃣ High-Density States
            high_density = exp_summary.nlargest(10, "Transaction_count")
            fig = create_bar_chart(high_density, "State", "Transaction_count", "Top States by Transaction Density")
            st.plotly_chart(fig, use_container_width=True)

            # 4️⃣ Yearly Volume Trend
            trend = data["map_transaction"].groupby("Years")["Transaction_amount"].sum().reset_index()
            fig = px.line(trend, x="Years", y="Transaction_amount", title="Yearly Market Volume Trend", markers=True)
            st.plotly_chart(fig, use_container_width=True)

            # 5️⃣ Correlation Scatter
            fig = px.scatter(exp_summary, x="Transaction_count", y="Transaction_amount", text="State", title="Correlation: Count vs Amount")
            st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # CASE STUDY 5: USER GROWTH ANALYSIS
    # ------------------------------------------------------------------
    elif case_study == "👥 User Growth Analysis":
        st.header("👥 User Growth Analysis")
        st.markdown("**Objective:** Explore how user registration and engagement evolve across states and quarters.")
        
        years = sorted(data["map_user"]["Years"].unique())
        year = st.selectbox("Select Year", years, key="usr_year")
        quarters = sorted(data["map_user"][data["map_user"]["Years"] == year]["Quarter"].unique())
        quarter = st.selectbox("Select Quarter", quarters, key="usr_quarter")
        
        user = data["map_user"][(data["map_user"]["Years"] == year) & (data["map_user"]["Quarter"] == quarter)]
        if user.empty:
            st.warning("No user data available.")
        else:
            user_sum = user.groupby("State", as_index=False).agg({"RegisteredUsers": "sum", "AppOpens": "sum"})
            user_sum["Users_K"] = user_sum["RegisteredUsers"] / 1e3

            # 1️⃣ User Distribution Heatmap
            fig = create_choropleth_map(user_sum, "Users_K", f"Registered Users - {year} Q{quarter}", "Purples", "K Users")
            st.plotly_chart(fig, use_container_width=True)

            # 2️⃣ Engagement Rate
            user_sum["Engagement_Rate"] = user_sum["AppOpens"] / (user_sum["RegisteredUsers"] + 1)
            top_eng = user_sum.nlargest(10, "Engagement_Rate")
            fig = create_bar_chart(top_eng, "State", "Engagement_Rate", "Top 10 States by Engagement Rate")
            st.plotly_chart(fig, use_container_width=True)

            # 3️⃣ Quarterly Growth
            q_growth = data["map_user"][data["map_user"]["Years"] == year].groupby("Quarter")["RegisteredUsers"].sum().reset_index()
            fig = px.line(q_growth, x="Quarter", y="RegisteredUsers", title="Quarterly User Growth", markers=True)
            st.plotly_chart(fig, use_container_width=True)

            # 4️⃣ Top Districts by Users
            district_users = user.groupby("District")["RegisteredUsers"].sum().nlargest(10).reset_index()
            fig = create_bar_chart(district_users, "District", "RegisteredUsers", "Top Districts by Registered Users")
            st.plotly_chart(fig, use_container_width=True)

            # 5️⃣ Correlation Scatter
            fig = px.scatter(user_sum, x="RegisteredUsers", y="AppOpens", text="State", title="Correlation: App Opens vs Registered Users")
            st.plotly_chart(fig, use_container_width=True)

# ========================
# FOOTER
# ========================
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    **PhonePe Transaction Dashboard**
    
    This dashboard analyzes PhonePe transaction data to provide insights for business decision making.
    
    **Data Sources**: PhonePe Pulse GitHub Repository
    **Technology Stack**: Streamlit, Plotly, Pandas, MySQL
    """
)
