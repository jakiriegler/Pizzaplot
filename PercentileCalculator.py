import pandas as pd
import math
import streamlit as st
from scipy import stats
from mplsoccer import PyPizza

st.set_page_config(layout="wide")

# Custom CSS to reduce spacing and font sizes
st.markdown("""
    <style>
    .small-font {
        font-size:14px !important;
    }
    .stSelectbox > div > div {
        padding-top: 0px;
        padding-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

# Reduce title and subheader font sizes
st.markdown("<h1 style='font-size: 24px;'>Percentile Ranks</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='font-size: 18px;'>Filter to any team/player to see</h2>", unsafe_allow_html=True)

# Create two columns for the selectboxes
col1, col2 = st.columns(2)

with col1:
    seasons = ["2024-2025", "2023-2024", "2022-2023"]
    season = st.selectbox("Select a Season", seasons, index=0, key="season")

    df = pd.read_csv(f"Data Fbref/{season}/Top 5.csv")

    League = st.selectbox("Select a league", df['League'].sort_values().unique(), index=0, key="league")

    Position = st.selectbox("Select a position", ["FW", "MF", "DF"], index=0, key="position")

with col2:
    Minutes = st.selectbox("Select a minimum of minutes played", [100, 500, 1000, 1500], index=0, key="minutes")
    Squad = st.selectbox("Select a team", df[df['League']==League]['Squad'].sort_values().unique(), index=1, key="squad")

    df_filtered = df[df["90s"] >= Minutes/90]

    if df_filtered.empty:
        st.warning(f"No players found who played at least {Minutes} minutes. Please adjust your filter.")
        st.stop()

    filtered_players = df_filtered[
        (df_filtered['Squad'] == Squad if Squad else True) &
        ((df_filtered['Position Primary'] == Position) | (df_filtered['Position Secondary'] == Position) if Position else True)
    ]['Player'].sort_values().unique()

    if len(filtered_players) == 0:
        st.warning(f"No players found in the selected Squad/Position who played at least {Minutes} minutes. Please adjust your filters.")
        st.stop()

    Player = st.selectbox("Select a player", filtered_players, index=0, key="player")
    
# The rest of your code remains unchanged
player_minutes = int(df_filtered[df_filtered['Player'] == Player]['90s'].values[0] * 90)

df = df_filtered[(df_filtered["Position Primary"]==Position) | (df_filtered["Position Secondary"]==Position)]

per_90 = st.checkbox('Display stats per 90 minutes', value=True)

if per_90:
    minutes_played = df['90s']  # Adjust column name if different
    for col in ['Assists', 'G+A', 'Goals without Penalties',
       'Yellow Cards', 'Red Cards', 'xAssistedGoals', 'npxG+xAG',
       'Prog. Carries', 'Prog. Passes', 'Progressive Passes received', 'Goals',
       'Shots', 'Shots on Target',
       'xG', 'npxG',
       'Passes played',
       'Progressive Pass Distance', 'Short Passes Completed',
       'Medium Passes Completed',
       'Long Passes Completed',
       'xA',
       'Key Passes', 'Passes into final 1/3', 'Passes into Penalty Area',
       'Crosses into Penalty Area', 'Through Balls', 'Crosses',
       'Shot Creating Actions', 'Goal Creating Actions', 'Tackles',
       'Tackles Won', 'Tackles in Defensive 3rd', 'Tackles in Midfield',
       'Tackles in Attacking 3rd', 'Dribblers Tackled', 'Dribbles Challenged',
       'Blocks', 'Shots Blocked', 'Interceptions',
       'Tackles + Int', 'Clearances', 'Errors leading to shots', 'Touches',
       'Touches own PA', 'Touches in Def. 1/3', 'Touches in Midfield',
       'Touches in Final 1/3', 'Touches Opp. PA', 'Take-Ons Attempted',
       'Take-Ons Completed',
       'Carries', 'Progressive Carries Distance',
       'Carries into final 1/3', 'Carries into Penalty Area', 'Dispossesed',
       'Fouls Committed', 'Fouls drawn', 'Offsides', 'Ball Recoveries',
       'Aerials won']:  # Add or remove columns as needed
            if col in df.columns:
                df[col] = df[col] / minutes_played




df = df[df['League']==League]



position_columns = {
    'FW': ['Goals', 'Assists', 'Shots', 'Shots on Target', 'npxG', 'Key Passes', 'Touches in Final 1/3', 'Touches Opp. PA', 
           'Take-Ons Completed', '% Successful Take-Ons', 'Carries into Penalty Area', 'Ball Recoveries', 'Aerials won', '% Aerials won', 'npxG per Shot', 'Fouls drawn'],
    'MF': ['Assists', 'Prog. Carries', 'Prog. Passes', 'Shots', 'xG', 'Pass %', 'xA', 
           'Key Passes', 'Passes into final 1/3', 'Tackles Won', 'Tackles + Int', 'Take-Ons Completed', 
           '% Successful Take-Ons', 'Carries into final 1/3', 'Ball Recoveries', 'Fouls drawn', 'Fouls Committed'],
    'DF': ['Assists', 'Yellow Cards', 'Prog. Carries', 'Prog. Passes', 'npxG', 'Pass %', '% Long Passes Completed', 'Passes into final 1/3',
           'Tackles Won', 'Shots Blocked', 'Tackles + Int', 'Clearances', 'Fouls Committed', 'Ball Recoveries', 'Aerials won', '% Aerials won']
}

df = df[['Player'] + position_columns.get(Position, [])]

params = df.columns[1:].tolist()

negate_columns = ['Yellow Cards', 'Fouls Committed']  # Add more columns as needed




def calculate_percentile(Player, df, params):
    player_data = df[df["Player"] == Player]
    if player_data.empty:
        st.warning("Please select a player to generate the visualization.")
        return None, None, None
    
    percentiles = []
    absolute_values = []
    ranks = []
    for param in params:
        value = player_data.iloc[0][param]
        percentile = math.floor(stats.percentileofscore(df[param], value))
        
        if param in negate_columns:
            percentile = 100 - percentile
            rank = df[param].rank(ascending=True).loc[player_data.index[0]]
        else:
            rank = df[param].rank(ascending=False).loc[player_data.index[0]]
        
        percentiles.append(percentile)
        absolute_values.append(value)
        ranks.append(int(rank))
    
    return percentiles, absolute_values, ranks




values, absolute_values, ranks = calculate_percentile(Player, df, params)


if values and Player:
    # Create parameter labels with absolute values and ranks
    param_labels = [f"{param}\n({abs_val:.2f})\nRank: {rank}" for param, abs_val, rank in zip(params, absolute_values, ranks)]

    st.markdown(f"<h3 style='text-align: center;'>{Player} | {League} | {Position} | {player_minutes} Minutes played</h3>", unsafe_allow_html=True)

    baker = PyPizza(
        params=param_labels,  # Use the new parameter labels
        background_color="#000000",
        straight_line_color="#FFFFFF",
        straight_line_lw=1,
        last_circle_lw=0,
        other_circle_lw=4,
        inner_circle_size=10
    )

    fig, ax = baker.make_pizza(
        values,
        figsize=(12, 12),  # Increased figure size further
        color_blank_space="same",
        slice_colors=["#1A78CF"] * len(params),
        value_colors=["#FFFFFF"] * len(params),
        value_bck_colors=["#1A78CF"] * len(params),
        blank_alpha=0.4,
        param_location=110,  # Moved param labels outward more
        kwargs_slices=dict(edgecolor="#F2F2F2", zorder=2, linewidth=2),
        kwargs_params=dict(color="#FFFFFF", fontsize=9, va="center"),  # Reduced font size further
        kwargs_values=dict(color="#FFFFFF", fontsize=12, zorder=3, 
                           bbox=dict(edgecolor="#FFFFFF", facecolor="cornflowerblue", boxstyle="round, pad=0.2", lw=1))
    )

    # We're not adding any additional text here

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.pyplot(fig)

    # Center the text using markdown with HTML and CSS
    st.markdown(f"<p style='text-align: center;'>Compared to other {Position} | {League} | {season} season | Min. {Minutes} minutes played</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Datasource: fbref.com</p>", unsafe_allow_html=True)
