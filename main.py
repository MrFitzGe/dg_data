import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")

with app.setup:
    import marimo as mo
    import polars as pl
    import polars.selectors as cs
    import altair as alt
    import numpy as np
    from datetime import datetime


@app.cell(hide_code=True)
def _():
    # Configure the app
    mo.md("""
    # Disc Golf League Analysis
    """)
    return


@app.cell(hide_code=True)
def _():
    # File upload cell
    csv_file = mo.ui.file(
        label="Upload your Glow League CSV file",
        filetypes=[".csv"]
    )
    mo.md(f"""
    ## Upload Data
    Please upload your league data CSV file: {csv_file}
    """)
    return (csv_file,)


@app.cell(hide_code=True)
def _(csv_file):
    # Process uploaded data
    # Transform the data into long format for time series analysis
    static_cols = ["Team Name"]
    drop_cols = ["Best round", "Attendance"]

    if csv_file.value is not None and len(csv_file.value) > 0:
        df_raw = pl.read_csv(csv_file.value[0].contents)
        # Clean column names (remove any extra spaces)
        df_clean = df_raw.rename({col: col.strip() for col in df_raw.columns})
        # Identify date columns (MM.DD format)
        # First ensure date columns are properly identified and filtered
        date_cols = [col for col in df_clean.columns if col not in static_cols + drop_cols]
        # Replace placeholder strings with nulls in date columns
        df_clean = df_clean.with_columns([
            pl.col(col).cast(pl.Utf8).str.replace_many(
                ["X", "x", "N/A", "-", ""],
                ["", "", "", "", ""]
            ).cast(pl.Int64, strict=False)
            for col in date_cols
        ])
    else:
        # Sample data for demonstration
        sample_data = {
            "Team Name": ["Player A", "Player B", "Player C", "Player D"],
            "01.04": [2, 3, "X", 1],
            "08.04": [1, "X", 2, 0],
            "15.04": [0, 2, 3, -1],
            "22.04": [3, 1, "X", 2],
            "29.04": ["X", 0, 1, 1],
            "Best Round": [-1, 0, 1, -1],
            "Attendance": [4, 4, 4, 5],
        }
        df_clean = pl.DataFrame(sample_data, strict=False)
        # Replace placeholder strings with nulls in date columns
        date_cols = ["01.04", "08.04", "15.04", "22.04", "29.04"]
        df_clean = df_clean.with_columns([
            pl.col(col).cast(pl.Utf8).str.replace_many(
                ["X", "x", "N/A", "-", ""],
                ["", "", "", "", ""]
            ).cast(pl.Int64, strict=False)
            for col in date_cols
        ])

    mo.vstack([
        mo.md("Data Used"),
        mo.ui.dataframe(df_clean)
    ])

    return date_cols, df_clean, drop_cols, static_cols


@app.cell(hide_code=True)
def _(date_cols, df_clean, drop_cols, static_cols):
    # Clean the dataframe with proper null handling and do some basic long formatting
    df_long = (
        df_clean
        .drop(drop_cols)
        .unpivot(
            index=static_cols,
            on=date_cols,
            variable_name="Date",
            value_name="Score",
        )
        .filter(
            pl.col("Score").is_not_null()
        )
        .with_columns(
            pl.col("Date")
            .str.strptime(pl.Date, format="%d.%m.", strict=False)  # match the trailing dot
            .dt.replace(year=2025)                  # force year 2025
        )
    )
    return (df_long,)


@app.cell(hide_code=True)
def _(df_long):
    # Player selector for detailed charts
    players = mo.ui.multiselect(
        options=df_long['Team Name'].unique(),  # Will be replaced dynamically
        label="Select Player(s) to Highlight:",
        value=df_long['Team Name'].unique(),
    )
    players
    return (players,)


@app.cell(hide_code=True)
def _(players):
    mo.vstack([
        mo.md("Selected Players"),
        players.value
    ])
    return


@app.cell
def _(df_long, players):
    # Create detail chart highlighting selected players
    selected_players = players.value

    # Filter data
    filtered_df = df_long.filter(pl.col("Team Name").is_in(selected_players))

    # Base chart
    base = alt.Chart(filtered_df).encode(
        x=alt.X("Date:T", title="Date")
    )

    # Highlight area for selected player(s)
    area = base.mark_area(opacity=0.3).encode(
        y=alt.Y("Score:Q", title="Score (Relative to Par)"), color="Team Name:N"
    )

    # Line for scores
    lines = base.mark_line(point=True).encode(
        y=alt.Y("Score:Q", title="Score (Relative to Par)"),
        color="Team Name:N",
        tooltip=["Team Name", "Date:T", "Score:Q"],
    )
    return filtered_df, lines


@app.cell
def _(df_with_stats, lines):
    # Time series line chart showing scores over time
    line_chart = (
        alt.Chart(df_with_stats)
        .mark_line(point=True)
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Score:Q", title="Score (Relative to Par)"),
            color="Team Name:N",
            tooltip=["Team Name", "Date:T", "Score:Q", "Relative Score to Player Avg:Q"],
        )
    )

    # Add average score lines
    avg_lines = (
        alt.Chart(df_with_stats)
        .mark_rule(strokeDash=[5, 5], opacity=0.3)
        .encode(
            y=alt.Y('Avg Score:Q', title='Score (Relative to Par)'),
            color="Team Name:N",
            tooltip=["Team Name:N", 'Avg Score:Q', "Rounds Played:N"]
        )
    )

    line_chart = (lines + avg_lines).resolve_scale(
        y='shared'
    ).properties(
        title=alt.TitleParams(
            'Player Scores Over Time with Averages',
            subtitle='Solid lines show individual performance, dashed lines show player averages'
        ),
        width=750, height=500
    )

    return (line_chart,)


@app.cell
def _(df_clean, player_stats):
    # Attendance bar chart
    global_avg = round(df_clean['Attendance'].mean(), 2)

    rule = alt.Chart().mark_rule(
        color="white",
        size=3
    ).encode(
        x=alt.X(datum=global_avg)
    )

    label = rule.mark_text(
        x="width",
        dx=4,
        align="left",
        baseline="bottom",
        text=f"Avg Attendance = {global_avg}", 
        color="white"
    )

    player_attendance = (
        alt.Chart(player_stats)
        .mark_bar()
        .encode(
            y=alt.Y("Team Name:N", sort="-x", title="Player"),
            x=alt.X("Rounds Played:Q", title="Number of Rounds"),
            color="Rounds Played:Q",
            tooltip=["Team Name:N", "Rounds Played:Q"],
        )
    )

    attend_chart = (player_attendance + rule + label).properties(title="League Attendance", width=750, height=300)
    return (attend_chart,)


@app.cell
def _(filtered_df):
    # Score distribution plots
    ## Bar with point layered on top

    mean_points = (
        alt.Chart(filtered_df)
        .mark_point(filled=True, size=60)
        .encode(
            y=alt.Y(
                "Team Name:N", 
                sort="-x",
                title="Player"
            ),
            x=alt.X(
                "Score:Q",
                aggregate="mean",
                title="Average Score (Relative to Par)"
            ),
            color=alt.Color(
                "mean(Score):Q",
                scale=alt.Scale(scheme="redblue", reverse=True),
                title="Avg Score"
            ),
            tooltip=[
                "Team Name:N",
                alt.Tooltip("mean(Score):Q", title="Avg Score"),
                alt.Tooltip("stdev(Score):Q", title="Std Dev")
            ],
        )
    )

    bar = alt.Chart(filtered_df).mark_bar(cornerRadius=8, height=7).encode(
        x=alt.X('min(Score):Q', scale=alt.Scale(domain=[-18, 40]), title='Score (Relative to Par)'),
        x2='max(Score):Q',
        y=alt.Y(
            "Team Name:N", 
            sort="-x",
            title="Player"
        ),
    )

    text_min = alt.Chart(filtered_df).mark_text(align='right', color="white", dx=-5).encode(
        x='min(Score):Q',
        y=alt.Y(
            "Team Name:N", 
            sort="-x",
            title="Player"
        ),
        text='min(Score):Q'
    )

    text_max = alt.Chart(filtered_df).mark_text(align='left', color="grey", dx=5).encode(
        x='max(Score):Q',
        y=alt.Y(
            "Team Name:N", 
            sort="-x",
            title="Player"
        ),
        text='max(Score):Q'
    )

    avg_score_bars = (bar + text_min + text_max + mean_points).properties(
        title=alt.Title(text='Avg, min, max Score by Player', 
        subtitle='Scores relative to Par'),
        width=750,
        height=300
    )
    return (avg_score_bars,)


@app.cell
def _(df_with_stats):

    # Relative performance chart
    relative_chart = (
        alt.Chart(df_with_stats)
        .mark_line(point=True)
        .encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y(
                "Relative Score to Player Avg:Q",
                title="Performance (Relative to Player Average)",
            ),
            color="Team Name:N",
            tooltip=["Team Name", "Date:T", "Relative Score to Player Avg:Q", "Score:Q", "Avg Score:Q", "Std Dev:Q"],
        )
        .properties(
            title="Performance Relative to Player Average",
            width=700,
            height=400,
        )
    )

    return (relative_chart,)


@app.cell(hide_code=True)
def _():
    # Summary statistics section
    mo.md("""
    ## Statistics

    Key metrics about the league performance:
    - Date: the day the round was scored
    - Score: score relative to par at the end of the round
    - Avg score: average across all rounds for that player
    - Standard deviation: shows consistency (lower = more consistent)
    - Rounds Played: redundant total number of rounds scored
    - Best Score: best (lowest) recorded score
    - Worst Score: worst (highest) recorded score
    - Relative Score to Player's Avg.: how many strokes better or worse was that days round to the player's avg score
    """)
    return


@app.cell(hide_code=True)
def _(filtered_df):
    # Calculate player statistics
    player_stats = filtered_df.group_by("Team Name").agg(
        [
            pl.mean("Score").alias("Avg Score"),
            pl.std("Score").alias("Std Dev"),
            pl.count("Score").alias("Rounds Played"),
            pl.min("Score").alias("Best Score"),
            pl.max("Score").alias("Worst Score"),
        ]
    ).with_columns(cs.numeric().round(2))

    # Join with original attendance data for consistency
    df_with_stats = filtered_df.join(player_stats, on="Team Name", how="left")

    # Calculate performance relative to player's average
    df_with_stats = df_with_stats.with_columns(
        [(pl.col("Score") - pl.col("Avg Score")).alias("Relative Score to Player Avg")]
    )

    mo.vstack([
        mo.md("## Highlighted Player Data & Stats"),
        df_with_stats
    ])


    return df_with_stats, player_stats


@app.cell
def _(attend_chart, avg_score_bars):
    # Output all visualizations
    mo.vstack([
        mo.md("""
    ## Score & Attendance
    """), 
        mo.ui.altair_chart(avg_score_bars),
        mo.ui.altair_chart(attend_chart)
    ])
    return


@app.cell
def _(line_chart):
    mo.vstack([
        mo.md("""
        ## Performance Over Time
        Track how players performed in each round.
        """),
        mo.ui.altair_chart(line_chart)
    ])
    return


@app.cell
def _(relative_chart):
    mo.vstack([
        mo.md("""### Relative Performance
        Shows how players performed compared to their personal averages over time.<br>
        Ideally, this should trend downwards as you improve.
        """),
        mo.ui.altair_chart(relative_chart),
    ])
    return


if __name__ == "__main__":
    app.run()
