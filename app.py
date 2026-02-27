import streamlit as st
import pandas as pd
import plotly.express as px
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor

# Athena connection using Streamlit secrets
def get_athena_connection():
    return connect(
        aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"],
        s3_staging_dir=st.secrets["aws"]["s3_staging_dir"],
        region_name=st.secrets["aws"]["region"],
        work_group=st.secrets["aws"]["workgroup"],
        cursor_class=PandasCursor
    )

# Query Athena with caching
def run_athena_query(query):
    @st.cache_data(show_spinner=False)
    def _query(q):
        with get_athena_connection() as conn:
            return pd.read_sql(q, conn)
    return _query(query)

st.set_page_config(
    page_title="Olympic Games Data Lake Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Olympic Games Data Lake Dashboard")

# Sidebar filters
def sidebar_filters():
    season = st.sidebar.selectbox("Season", ["All", "Summer", "Winter"])
    year_range = st.sidebar.slider("Year Range", 1896, 2024, (1896, 2024), step=4)
    return season, year_range

season_filter, year_range = sidebar_filters()

# Tabs for visualizations
tabs = st.tabs([
    "Total Medals by Country",
    "Gender Participation Over Time",
    "GDP vs Medal Performance",
    "Population-Normalized Medal Count",
    "Sport Evolution Over Decades",
    "Enriched Medals Explorer"
])

# 1. Total Medals by Country
with tabs[0]:
    st.header("Total Medals by Country (Both Seasons)")
    query = '''
    SELECT Code, Season, COUNT(*) as total_medals,
        SUM(CASE WHEN Medal = 'Gold' THEN 1 ELSE 0 END) as gold,
        SUM(CASE WHEN Medal = 'Silver' THEN 1 ELSE 0 END) as silver,
        SUM(CASE WHEN Medal = 'Bronze' THEN 1 ELSE 0 END) as bronze
    FROM olympic_db.processed_events
    GROUP BY Code, Season
    ORDER BY total_medals DESC
    LIMIT 25;
    '''
    df = run_athena_query(query)
    if season_filter != "All":
        df = df[df["Season"] == season_filter]
    if df.empty:
        st.info("No data available for the selected filter.")
    else:
        fig = px.bar(
            df,
            y="Code",
            x=["gold", "silver", "bronze"],
            orientation="h",
            title="Top 25 Countries by Total Medals",
            labels={"value": "Medals", "Code": "Country Code"},
            color_discrete_map={"gold": "#FFD700", "silver": "#C0C0C0", "bronze": "#CD7F32"}
        )
        st.plotly_chart(fig, use_container_width=True)

# 2. Gender Participation Over Time
with tabs[1]:
    st.header("Gender Participation Over Time")
    query = '''
    SELECT Year, Season, Gender, COUNT(DISTINCT Athlete) as athlete_count
    FROM olympic_db.processed_events
    GROUP BY Year, Season, Gender
    ORDER BY Year, Season;
    '''
    df = run_athena_query(query)
    if season_filter != "All":
        df = df[df["Season"] == season_filter]
    df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
    if df.empty:
        st.info("No data available for the selected filter.")
    else:
        fig = px.line(
            df,
            x="Year",
            y="athlete_count",
            color="Gender",
            title="Gender Participation Over Time",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

# 3. GDP vs Medal Performance
with tabs[2]:
    st.header("GDP vs Medal Performance")
    query = '''
    SELECT c.Country, c.Code, c.gdp_per_capita, COUNT(*) as total_medals
    FROM olympic_db.processed_events e
    JOIN olympic_db.processed_countries c ON e.Code = c.Code
    GROUP BY c.Country, c.Code, c.gdp_per_capita
    ORDER BY total_medals DESC
    LIMIT 30;
    '''
    df = run_athena_query(query)
    if df.empty:
        st.info("No data available.")
    else:
        fig = px.scatter(
            df,
            x="gdp_per_capita",
            y="total_medals",
            hover_name="Country",
            text="Code",
            title="GDP per Capita vs Total Medals"
        )
        st.plotly_chart(fig, use_container_width=True)

# 4. Population-Normalized Medal Count
with tabs[3]:
    st.header("Population-Normalized Medal Count")
    query = '''
    SELECT c.Country, c.Code, c.Population, COUNT(*) as total_medals,
        ROUND(COUNT(*) * 1000000.0 / c.Population, 2) as medals_per_million
    FROM olympic_db.processed_events e
    JOIN olympic_db.processed_countries c ON e.Code = c.Code
    WHERE c.Population > 0
    GROUP BY c.Country, c.Code, c.Population
    ORDER BY medals_per_million DESC
    LIMIT 25;
    '''
    df = run_athena_query(query)
    if df.empty:
        st.info("No data available.")
    else:
        fig = px.bar(
            df,
            y="Country",
            x="medals_per_million",
            orientation="h",
            title="Top 25 Countries by Medals per Million Population"
        )
        st.plotly_chart(fig, use_container_width=True)

# 5. Sport Evolution Over Decades
with tabs[4]:
    st.header("Sport Evolution Over Decades")
    query = '''
    SELECT Sport, MIN(Year) as first_appeared, MAX(Year) as last_appeared,
        COUNT(DISTINCT Year) as editions, COUNT(DISTINCT Discipline) as disciplines
    FROM olympic_db.processed_events
    GROUP BY Sport
    ORDER BY first_appeared;
    '''
    df = run_athena_query(query)
    if df.empty:
        st.info("No data available.")
    else:
        fig = px.timeline(
            df,
            x_start="first_appeared",
            x_end="last_appeared",
            y="Sport",
            color="editions",
            title="Sport Evolution Over Decades"
        )
        st.plotly_chart(fig, use_container_width=True)

# 6. Enriched Medals Explorer
with tabs[5]:
    st.header("Enriched Medals Explorer")
    query = '''
    SELECT e.*, c.Country as country_name, c.Population, c.gdp_per_capita
    FROM olympic_db.processed_events e
    LEFT JOIN olympic_db.processed_countries c ON e.Code = c.Code;
    '''
    df = run_athena_query(query)
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        season = st.selectbox("Season", ["All"] + sorted(df["Season"].dropna().unique().tolist()))
    with col2:
        sport = st.selectbox("Sport", ["All"] + sorted(df["Sport"].dropna().unique().tolist()))
    with col3:
        medal = st.selectbox("Medal", ["All"] + sorted(df["Medal"].dropna().unique().tolist()))
    with col4:
        country = st.selectbox("Country", ["All"] + sorted(df["country_name"].dropna().unique().tolist()))
    if season != "All":
        df = df[df["Season"] == season]
    if sport != "All":
        df = df[df["Sport"] == sport]
    if medal != "All":
        df = df[df["Medal"] == medal]
    if country != "All":
        df = df[df["country_name"] == country]
    st.dataframe(df, use_container_width=True)
