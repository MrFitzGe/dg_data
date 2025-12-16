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
    from loguru import logger


@app.cell(hide_code=True)
def _():
    # Configure the app
    mo.md("""
    # Disc Golf League Analysis 🥏📊
    """)
    return


@app.cell(hide_code=True)
def upload_data_files():
    # File upload cell
    csv_file = mo.ui.file(
        label="Upload UDisc CSV file(s)",
        multiple=True
    )
    mo.md(f"""
    ## Upload Data
    Please upload your rounds data.<br> Should be a UDisc CSV export: {csv_file}
    """)
    return (csv_file,)


@app.cell(hide_code=True)
def read_preproc_data(csv_file):
    # Process uploaded data
    # Transform the data into long format for time series analysis
    static_cols = ["PlayerName", "CourseName", "LayoutName", "StartDate", "EndDate"]
    drop_cols = []
    start_end_date_cols = ["StartDate", "EndDate"]

    if csv_file.value is not None and len(csv_file.value) > 0:
        # Read each CSV file and concatenate them
        dfs = []
        for file_info in csv_file.value:
            df = pl.read_csv(file_info.contents, try_parse_dates=True)
            dfs.append(df)

        # Concatenate all dataframes vertically
        df_clean = pl.concat(dfs)
    else:
        logger.error("File upload format not recognized. Please check your .csv file.")

    mo.vstack([
        mo.md("Data Used"),
        mo.ui.dataframe(df_clean)
    ])
    return (df_clean,)


@app.cell
def clean_data(df_clean):
    # check data is comparable Course and layout
    if df_clean["CourseName"].n_unique() > 1 or df_clean["LayoutName"].n_unique() > 1:
        logger.warning("Course or Layout differ in the data set! Results may not be fair comparison.")

    # clean the date times
    def clean_date_duration(df: pl.DataFrame | pl.LazyFrame, start_col: str = "StartDate", end_col: str ="EndDate") -> pl.DataFrame | pl.LazyFrame:
        return df.with_columns(
            pl.col(start_col).cast(pl.Date).alias("Date"),
            (pl.col(end_col) - pl.col(start_col)).dt.total_minutes().alias("RoundDuration")
        ).drop(start_col, end_col)

    # Clean the dataframe with proper null handling and do some basic long formatting
    df_preprocessed = (
        clean_date_duration(df_clean)
        .rename({"+/-":"Score"})
        .with_columns(
            Attendance = pl.len().over("PlayerName")
        )
    )
    df_long = df_preprocessed.filter(
            pl.col("Score").is_not_null()
        )
    return df_long, df_preprocessed


@app.cell(hide_code=True)
def _(df_long):
    # Player selector for detailed charts
    players = mo.ui.multiselect(
        options=df_long['PlayerName'].unique(),  # Will be replaced dynamically
        label="Select Player(s) to Highlight:",
        value=df_long['PlayerName'].unique(),
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
    filtered_df = df_long.filter(pl.col("PlayerName").is_in(selected_players))

    # Base chart
    base = alt.Chart(filtered_df).encode(
        x=alt.X("Date:T", title="Date")
    )

    # Highlight area for selected player(s)
    area = base.mark_area(opacity=0.3).encode(
        y=alt.Y("Score:Q", title="Score (Relative to Par)"), color="PlayerName:N"
    )

    # Line for scores
    lines = base.mark_line(point=True).encode(
        y=alt.Y("Score:Q", title="Score (Relative to Par)"),
        color="PlayerName:N",
        tooltip=["PlayerName", "Date:T", "Score:Q"],
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
            color="PlayerName:N",
            tooltip=["PlayerName", "Date:T", "Score:Q", "Relative Score to Player Avg:Q"],
        )
    )

    # Add average score lines
    avg_lines = (
        alt.Chart(df_with_stats)
        .mark_rule(strokeDash=[5, 5], opacity=0.3)
        .encode(
            y=alt.Y('Avg Score:Q', title='Score (Relative to Par)'),
            color="PlayerName:N",
            tooltip=["PlayerName:N", 'Avg Score:Q', "Rounds Played:N"]
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
def _(df_long, player_stats):
    # Attendance bar chart
    global_avg = round(df_long['Attendance'].mean(), 2)

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
            y=alt.Y("PlayerName:N", sort="-x", title="Player Name"),
            x=alt.X("Rounds Played:Q", title="Number of Rounds"),
            color="Rounds Played:Q",
            tooltip=["PlayerName:N", "Rounds Played:Q"],
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
                "PlayerName:N", 
                sort=alt.EncodingSortField(
                 field='Score',
                 op='mean',
                 order='ascending'
                ),
                title="Player Name"
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
                "PlayerName:N",
                alt.Tooltip("mean(Score):Q", title="Avg Score"),
                alt.Tooltip("stdev(Score):Q", title="Std Dev")
            ],
        )
    )

    bar = alt.Chart(filtered_df).mark_bar(cornerRadius=8, height=7).encode(
        x=alt.X('min(Score):Q', scale=alt.Scale(domain=[-18, 40]), title='Score (Relative to Par)'),
        x2='max(Score):Q',
        y=alt.Y(
            "PlayerName:N", 
            sort=alt.EncodingSortField(
                 field='Score',
                 op='mean',
                 order='ascending'
             ),
            title="Player Name"
        ),
    )

    text_min = alt.Chart(filtered_df).mark_text(align='right', color="white", dx=-5).encode(
        x='min(Score):Q',
        y=alt.Y(
            "PlayerName:N", 
            sort=alt.EncodingSortField(
                 field='Score',
                 op='mean',
                 order='ascending'
             ),
            title="Player Name"
        ),
        text='min(Score):Q'
    )

    text_max = alt.Chart(filtered_df).mark_text(align='left', color="grey", dx=5).encode(
        x='max(Score):Q',
        y=alt.Y(
            "PlayerName:N", 
            sort=alt.EncodingSortField(
                 field='Score',
                 op='mean',
                 order='ascending'
             ),
            title="Player Name"
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
            color="PlayerName:N",
            tooltip=["PlayerName", "Date:T", "Relative Score to Player Avg:Q", "Score:Q", "Avg Score:Q", "Std Dev:Q"],
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
    player_stats = filtered_df.group_by("PlayerName").agg(
        [
            pl.mean("Score").alias("Avg Score"),
            pl.std("Score").alias("Std Dev"),
            pl.count("Score").alias("Rounds Played"),
            pl.min("Score").alias("Best Score"),
            pl.max("Score").alias("Worst Score"),
        ]
    ).with_columns(cs.numeric().round(2))

    # Join with original attendance data for consistency
    df_with_stats = filtered_df.join(player_stats, on="PlayerName", how="left")

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


@app.cell
def _(df_preprocessed):
    # Get hole-by-hole data
    by_hole_df = (
        df_preprocessed
        .unpivot(
            index="PlayerName",
            on=cs.starts_with("Hole"),
            value_name="ShotsThrown",
            variable_name="Hole#" 
        ).with_columns(
            pl.col("Hole#").str.replace("Hole", "").cast(pl.Int16)
        )
    )
    # Separate par data and player data
    par_data = by_hole_df.filter(pl.col("PlayerName") == "Par")
    player_data = by_hole_df.filter(pl.col("PlayerName") != "Par")

    # Join player scores with par for each hole
    hole_analysis = ( 
        player_data
        .join(
            par_data.select(["Hole#", "ShotsThrown"]).rename({"ShotsThrown": "Par"}),
            on="Hole#",
            how="left"
        ).with_columns([
            (pl.col("ShotsThrown") - pl.col("Par")).alias("Score_vs_Par")
        ])
        .sort("Hole#")
    )
    # Calculate hole difficulty statistics
    hole_difficulty = ( 
        hole_analysis
        .group_by("Hole#")
        .agg([
            pl.mean("Score_vs_Par").alias("Avg_Score_vs_Par"),
            pl.count("PlayerName").alias("Total_Players"),
            pl.max("Score_vs_Par").alias("Worst_Score_vs_Par"),
            pl.min("Score_vs_Par").alias("Best_Score_vs_Par"),
            pl.std("Score_vs_Par").alias("Std_Dev")
        ])
        .with_columns(cs.numeric().round(2))
        .sort("Avg_Score_vs_Par")
    )
    mo.vstack([
        mo.md("## Hole Difficulty Analysis"),
        mo.ui.dataframe(hole_difficulty)
    ])
    return by_hole_df, hole_analysis, hole_difficulty


@app.cell
def _(hole_analysis):
    # Calculate each player's performance on each hole relative to par
    player_hole_performance = hole_analysis.group_by(["PlayerName", "Hole#"]).agg([
        pl.mean("Score_vs_Par").alias("Avg_Score_vs_Par"),
        pl.count("ShotsThrown").alias("Rounds_Played"),
        pl.min("Score_vs_Par").alias("Best_Score_vs_Par"),
        pl.max("Score_vs_Par").alias("Worst_Score_vs_Par")
    ]).sort(["PlayerName", "Hole#"])

    # Find best and worst holes for each player
    player_best_holes = player_hole_performance.group_by("PlayerName").agg([
        pl.min("Avg_Score_vs_Par").alias("Best_Hole_Performance"),
        pl.col("Hole#").filter(pl.col("Avg_Score_vs_Par") == pl.min("Avg_Score_vs_Par")).alias("Best_Hole")
    ])

    player_worst_holes = player_hole_performance.group_by("PlayerName").agg([
        pl.max("Avg_Score_vs_Par").alias("Worst_Hole_Performance"),
        pl.col("Hole#").filter(pl.col("Avg_Score_vs_Par") == pl.max("Avg_Score_vs_Par")).alias("Worst_Hole")
    ])

    # Combine best and worst hole analysis
    player_extremes = player_best_holes.join(
        player_worst_holes, 
        on="PlayerName", 
        how="left"
    ).with_columns([
        cs.numeric().round(2)
    ])

    mo.vstack([
        mo.md("## Player Best & Worst Holes"),
        mo.ui.dataframe(player_extremes)
    ])
    return (player_hole_performance,)


@app.cell
def _(by_hole_df):
    by_hole_df
    return


@app.cell
def _(hole_difficulty):
    # Create hole difficulty visualization
    hole_chart = (
        alt.Chart(hole_difficulty)
        .mark_bar()
        .encode(
            x=alt.X("Hole#:N", title="Hole Number", sort=alt.SortField("Avg_Score_vs_Par")),
            y=alt.Y("Avg_Score_vs_Par:Q", title="Average Score vs Par"),
            color=alt.Color("Avg_Score_vs_Par:Q", 
                           scale=alt.Scale(scheme="redyellowgreen", domain=[-1, 2], reverse=True),
                           title="Difficulty"),
            tooltip=[
                "Hole#:N",
                alt.Tooltip("Avg_Score_vs_Par:Q", title="Avg Score vs Par"),
                alt.Tooltip("Best_Score_vs_Par:Q", title="Best Score vs Par"),
                alt.Tooltip("Worst_Score_vs_Par:Q", title="Worst Score vs Par"),
                "Total_Players:Q"
            ]
        )
        .properties(
            title="Hole Difficulty (Easiest to Hardest)",
            width=700,
            height=400
        )
    )

    hole_chart
    return


@app.cell
def _(player_hole_performance):
    # Create heatmap of player performance by hole
    heatmap_data = player_hole_performance.filter(pl.col("Rounds_Played") >= 1)  # Only holes with data

    player_heatmap = (
        alt.Chart(heatmap_data)
        .mark_rect()
        .encode(
            x=alt.X("Hole#:N", title="Hole Number"),
            y=alt.Y("PlayerName:N", title="PlayerName"),
            color=alt.Color("Avg_Score_vs_Par:Q", 
                           scale=alt.Scale(scheme="redyellowgreen", domain=[-2, 3], reverse=True),
                           title="Avg Score vs Par"),
            tooltip=[
                "PlayerName:N",
                "Hole#:N",
                alt.Tooltip("Avg_Score_vs_Par:Q", title="Avg Score vs Par"),
                alt.Tooltip("Rounds_Played:Q", title="Rounds Played")
            ]
        )
        .properties(
            title="Player Performance by Hole (Heatmap)",
            width=700,
            height=400
        )
    )

    player_heatmap
    return


if __name__ == "__main__":
    app.run()
