import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import streamlit as st

data = pd.read_csv("data/all_track_artist.csv")
data_top = pd.read_csv("data/chart_filter_release.csv")

# Changing "chart_week" for data format
data["chart_week"] = pd.to_datetime(data["chart_week"])
data_top["chart_week"] = pd.to_datetime(data_top["chart_week"], errors="coerce")


# Creatiing the year
data_top["year"] = data_top["chart_week"].dt.year

#Setting page
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded")


#Dashbord title
st.title ("Top 10 Tracks")
st.subheader ("Tracks with longest apperance on the chart from 2018 to 2024")

#Sidebar
select_year= st.sidebar.selectbox("Select Year:", sorted(data_top["year"].unique()))



top_10_tracks = (
    data_top[data_top["year"] == select_year]
    .groupby("name")["chart_week"]
    .count()
    .reset_index()
    .sort_values(by="chart_week", ascending=False)
    .head(10)
)

select_track = st.sidebar.selectbox("Select Track:", top_10_tracks["name"].unique())

select_track_artist = data[data["name_x"] == select_track][["name_y", "popularity", "followers"]].drop_duplicates()

#Filter data for selected track
selected_data = data[data["name_x"] == select_track].iloc[0]
top_10_select = data_top[data_top["year"] == select_year]


# Create columns for dashboard
col1, col2 = st.columns([1,3], gap='medium')

#Column 1: Artist Info + Explicit

with col1:
    #Artist Info
    st.write(f"**<span style='font-size: 24px;'>Track Info</span>**", unsafe_allow_html=True)

    st.dataframe(
        select_track_artist.rename(columns = {"name_y": "Arist","popularity": "Popularity", "followers": "Followers"}),
        hide_index = True,
        use_container_width=True
    )

    #Explicit info
    #explicit = "Yes" if selected_data["explicit"] == True else "No"
    #st.write(f"**Is Track Explicit:** {'Yes' if selected_data['explicit'] else 'No'}")

    #Top 10 tracks list
    top_10_year = data_top.groupby(["year", "name"])["chart_week"].count().sort_values(ascending=False).reset_index()

    selet_year_data = top_10_year[top_10_year["year"] == select_year]
    selet_year_data = selet_year_data.head(10)

    selet_year_data['year'] = selet_year_data['year'].astype(str)
    selet_year_data = selet_year_data.drop(columns=["year"])

    # Display the Table
    st.write(f"**<span style='font-size: 24px;'>Top 10 Tracks for {select_year}</span>**", unsafe_allow_html=True)
    st.dataframe(
        selet_year_data.rename(columns = {"chart_week": "# of Weeks"}),
        hide_index=True,
        height=None,
        use_container_width=True
    )

#Coumn 2: Line Charts + KPI's

with col2:
    #Line chart
    data_perf = data.groupby(["name_x","chart_week"])["list_position"].mean()
    data_perf = data_perf.to_frame().reset_index()
    selected_performance = data_perf[data_perf["name_x"] == select_track]

    fig_perf = px.line(
        selected_performance,
        x = "chart_week",
        y = "list_position",
        title = f"Performance of {select_track}",
        labels = {"chart_week": "Chart Week", "list_position": "List Positoin"},
        markers = True 
    )

    # Updating color and size of markers 
    fig_perf.update_traces(
        line=dict(color="darkblue", width=3),  
        marker=dict(size=8)
    )

    fig_perf.update_layout(
        yaxis=dict(autorange='reversed', title='List Position'),
        xaxis_title = "Chart Week",
        yaxis_title = "List Position",
        template = "plotly_white",
        title_font=dict(size=16)
    )

    st.plotly_chart(fig_perf, use_container_width=True)

    # KPI's : dancebility, tempo, energy, valence
    st.write(f"**<span style='font-size: 24px;'>Audio Features of {select_track}</span>**", unsafe_allow_html=True)

    kpi_data = {
        'Danceability': selected_data['danceability'],
        'Tempo': selected_data['tempo'],
        'Energy': selected_data['energy'],
        'Valence': selected_data['valence'],
        'Loudness': selected_data['loudness'],
        'Speechiness': selected_data['speechiness']
    }

    kpi_cols = st.columns([1,1,1,1,1,1])

    for idx, (kpi,value) in enumerate(kpi_data.items()):
        with kpi_cols[idx]:
            st.metric(kpi, round(value,2))


# ARON'S CODE STARTS HERE
st.markdown("---")
st.write(f"**<span style='font-size: 24px;'>Moodboard of Tracks by Release Year and Audio Features</span>**", unsafe_allow_html=True)

# Sidebar Filters for Scatter Plot
selected_metric = st.sidebar.selectbox(
    "Select Audio Feature:", ["tempo", "danceability", "energy", "valence", "loudness", "speechiness"]
)

# Filter data for scatter plot by selected year
scatter_data = data_top[data_top["year"] == select_year]

# Group data by track name and year
scatter_data_mean = (
    scatter_data.groupby(["name", "year"], as_index=False)
    .agg({
        selected_metric: "mean",  # Mean of the selected metric
        "list_position": "mean"  # Mean list position
    })
)

# Indicate whether a track is the selected one
scatter_data_mean["is_selected"] = scatter_data_mean["name"] == select_track

# Create scatter plot with the aggregated data
fig_scatter = px.scatter(
    scatter_data_mean,
    x=selected_metric,
    y="list_position",
    size=[max(scatter_data_mean["list_position"]) - lp + 1 for lp in scatter_data_mean["list_position"]],
    color=selected_metric,
    hover_name="name",
    title=f"{selected_metric.capitalize()} Distribution for Tracks in {select_year}",
    labels={"list_position": "Mean Chart Position", selected_metric: selected_metric.capitalize()},
    color_continuous_scale="Plasma",
)
# Highlight the selected track's mean position
selected_track_data = scatter_data_mean[scatter_data_mean["is_selected"]]

fig_scatter.add_scatter(
    x=selected_track_data[selected_metric],
    y=selected_track_data["list_position"],
    mode="markers",
    marker=dict(
        size=20,  
        color="black", 
        symbol="circle"  
    ),
    name=f"{select_track}",
)

# Ensure the black marker is on top
fig_scatter.update_traces(marker=dict(opacity=0.5), selector=dict(mode="markers"))
fig_scatter.data[-1].update(marker=dict(opacity=1))  

# Customize scatter plot layout
fig_scatter.update_layout(
    xaxis_title=selected_metric.capitalize(),
    yaxis_title="Mean Chart Position",
    yaxis=dict(autorange="reversed", title="Mean Chart Position"),
    template="simple_white",
    title_font=dict(size=16),
)

# Display scatter plot
st.plotly_chart(fig_scatter, use_container_width=True)
# ARON'S CODE ENDS HERE

#Pusing text down
st.sidebar.markdown("<br>"*14, unsafe_allow_html=True)
st.sidebar.markdown(
    "**Data Sources:**<br>"
    "1. Billboard Top 50 weekly charts (2000-2024)<br>"
    "2. Spotify API",
    unsafe_allow_html=True
)
