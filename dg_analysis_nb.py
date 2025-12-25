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
    # 🥏 Disc Golf League Analysis 📊
    """).center()
    return


@app.cell(hide_code=True)
def upload_data_files():
    # File upload cell
    csv_file = mo.ui.file(
        label="Upload UDisc CSV file(s)",
        multiple=True
    )
    mo.md(f"""
    ## Step 1. Upload Data<br>
    Please upload your rounds data to begin.<br> 
    Should be a UDisc CSV export: {csv_file}
    """)
    return (csv_file,)


@app.cell(hide_code=True)
def read_preproc_data(csv_file):
    mo.stop(len(csv_file.value) == 0, mo.md("... upload data to analyze"))

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
        mo.stop("File upload format not recognized. Please check your .csv file.")


    mo.accordion({
        "Check Data Uploaded":
        mo.ui.dataframe(df_clean)
    })
    return (df_clean,)


@app.cell
def clean_data(csv_file, df_clean):
    mo.stop(len(csv_file.value) == 0)

    # check data is comparable Course and layout
    if df_clean["CourseName"].n_unique() > 1 or df_clean["LayoutName"].n_unique() > 1:
        print("Course or Layout differ in the data set! Results may not be fair comparison.")

    # clean the date times
    def clean_date_duration(df: pl.DataFrame | pl.LazyFrame, start_col: str = "StartDate", end_col: str ="EndDate") -> pl.DataFrame | pl.LazyFrame:
        return df.with_columns(
            pl.col(start_col).cast(pl.Date).alias("Date"),
            (pl.col(end_col) - pl.col(start_col)).dt.total_minutes().alias("Round Duration (min)")
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

    mo.accordion({
        "Data Cleaning Steps":
        mo.md("""
        The uploaded data above is cleaned and processed before the analysis below. The cleaning steps include:
        * check for multiple layouts or courses
        * converts the start datetime and end datetime to separate Date and Round Duration columns
        * renames the +/- column as 'Score'
        * counts the number of rounds played for each player in the data ('Attendance')
        """)
    })
    return df_long, df_preprocessed


@app.cell(hide_code=True)
def _(df_long):
    # Player selector for detailed charts
    players = mo.ui.multiselect(
        options=df_long['PlayerName'].unique(),  # Will be replaced dynamically
        label="Select Player(s):",
        value=df_long['PlayerName'].unique(),
    )

    courses = mo.ui.multiselect(
        options=df_long['CourseName'].unique(),  # Will be replaced dynamically
        label="Select Course(s):",
        value=df_long['CourseName'].unique(),
    )

    layouts = mo.ui.multiselect(
        options=df_long['LayoutName'].unique(),  # Will be replaced dynamically
        label="Select Layout(s):",
        value=df_long['LayoutName'].unique(),
    )

    mo.vstack([
        mo.md("## Step 2. Select the data to use for analysis:"),
        mo.hstack([players, courses, layouts])
    ])

    return courses, layouts, players


@app.cell(hide_code=True)
def _(courses, layouts, players):
    mo.hstack([
        mo.vstack([
            mo.md("Selected Players"),
            players.value
        ]), 
        mo.vstack([
            mo.md("Selected Courses"),
            courses.value
        ]),
        mo.vstack([
            mo.md("Selected Layouts"),
            layouts.value
        ]),
    ])
    return


@app.cell
def filter_data(courses, df_long, layouts, players):
    # Filter data
    filtered_df = df_long.filter(
        pl.col("PlayerName").is_in(players.value),
        pl.col("CourseName").is_in(courses.value), 
        pl.col("LayoutName").is_in(layouts.value)
    )
    return (filtered_df,)


@app.cell
def base_chart():
    # Create chart base theme
    alt.theme.enable('urbaninstitute')

    # Resuable chart components
    date_axis=alt.X(
        "Date:T",
        title="Date",
        axis=alt.Axis(
            format="%b %d, %Y",
            labelAngle=-45,
            labelFontSize=11
        )
    )
    return (date_axis,)


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
        [(pl.col("Score") - pl.col("Avg Score")).round(1).alias("Relative Score to Player Avg")]
    )
    return df_with_stats, player_stats


@app.cell
def _(
    by_hole_stats,
    df_with_stats,
    perf_over_time_plots,
    player_stats_by_hole,
    score_attend_plots,
):
    tabs = mo.ui.tabs({
        "Data": mo.vstack([
        mo.md("## <br>Selected Player Data & Stats<br>"),
        df_with_stats.select(~cs.starts_with("Hole"))
    ]),
        "League Ranks: Score & Attendance": score_attend_plots,
        "Performance over Time": perf_over_time_plots,
        "Hole-by-Hole Analysis": mo.vstack([by_hole_stats, mo.md("-------------"), player_stats_by_hole])
    })

    mo.vstack([
        mo.md("""
        ## Step 3. Analysis
        Click the tabs below for different stats and analyses
        <br>
        <br>
        """), 
        tabs
    ])
    return


@app.cell
def score_distro_plot(filtered_df):
    # Score distribution plots
    ## Bar with point layered on top

    _mean_points = (
        alt.Chart(filtered_df)
        .mark_point(filled=True, size=100)
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
                scale=alt.Scale(scheme="redyellowgreen", reverse=True),
                title="Avg Score"
            ),
            tooltip=[
                "PlayerName:N",
                alt.Tooltip("min(Score):Q", title="Best Score"),
                alt.Tooltip("max(Score):Q", title="Worst Score"),            
                alt.Tooltip("mean(Score):Q", title="Avg Score", format=".2f"),
                alt.Tooltip("stdev(Score):Q", title="Std Dev", format=".2f")
            ],
        )
    )

    _bar = ( 
        alt.Chart(filtered_df)
        .mark_bar(cornerRadius=8, height=7)
        .encode(
            x=alt.X('min(Score):Q', scale=alt.Scale(domain=[-18, 40]), title='Best Score'),
            x2=alt.X('max(Score):Q', scale=alt.Scale(domain=[-18, 40]), title='Worst Score'),
            y=alt.Y(
                "PlayerName:N", 
                sort=alt.EncodingSortField(
                     field='Score',
                     op='mean',
                     order='ascending'
                 ),
                title="Player Name"
            ),
            tooltip=[
                "PlayerName:N",
                alt.Tooltip("min(Score):Q", title="Best Score"),
                alt.Tooltip("max(Score):Q", title="Worst Score"),            
                alt.Tooltip("mean(Score):Q", title="Avg Score", format=".2f"),
                alt.Tooltip("stdev(Score):Q", title="Std Dev", format=".2f")
            ],
        )
    )

    _text_min = alt.Chart(filtered_df).mark_text(align='right', color="black", dx=-5).encode(
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

    _text_max = alt.Chart(filtered_df).mark_text(align='left', color="black", dx=5).encode(
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

    avg_score_bars = (_bar + _text_min + _text_max + _mean_points).properties(
        title=alt.Title(text='Lowest, Avg, & Highest Round Score by Player', 
        subtitle='Scores relative to Par'),
        width=800,
        height=400
    )
    return (avg_score_bars,)


@app.cell
def _(df_long, player_stats):
    # Attendance bar chart
    global_avg = round(df_long['Attendance'].mean(), 2)

    _rule = alt.Chart().mark_rule(
        color="black",
        size=3
    ).encode(
        x=alt.X(datum=global_avg)
    )

    _label = _rule.mark_text(
        x="width",
        dx=4,
        align="left",
        baseline="bottom",
        text=f"Avg Attendance = {global_avg}", 
        color="black"
    )

    player_attendance = (
        alt.Chart(player_stats)
        .mark_bar()
        .encode(
            y=alt.Y("PlayerName:N", sort="-x", title="Player Name"),
            x=alt.X("Rounds Played:Q", scale=alt.Scale(round=True), title="Number of Rounds", axis=alt.Axis(format="d")),
            color="Rounds Played:Q",
            tooltip=["PlayerName:N", "Rounds Played:Q"],
        )
    )

    attend_chart = (player_attendance + _rule + _label).properties(title="League Attendance", width=800, height=500)
    return (attend_chart,)


@app.cell
def _(hole_analysis):
    _bar = (
        alt.Chart(hole_analysis)
            .mark_bar()
            .encode(
            x=alt.X(
                'count(Hole Outcome):Q',
                stack="normalize",
                title="Outcome of Holes Played"
            ),
            y='PlayerName:N',
            color=alt.Color(
                'Hole Outcome:N',
                scale=alt.Scale(
                    domain=['Over Par', 'Par', 'Under Par'],
                    range=['orangered', 'silver', 'green']
                )
            )
        )
    )

    _text = ( 
        alt.Chart(hole_analysis)
            .mark_text(dx=-15, dy=3, color='white')
            .encode(
                x=alt.X('count(Hole Outcome):Q', stack='normalize'),
                y=alt.Y('PlayerName:N'),
                detail='Hole Outcome:N',
                text=alt.Text('count(Hole Outcome):Q')
            )
    )


    player_hole_outcomes_plot = (_bar + _text).properties(
        title=alt.Title(text='Player Bird | Par | Bogey Rate', 
        subtitle='Under Par counts eagles, aces, birdies; Over Par counts anything bogey+'),
        width=800,
        height=400
    )
    return (player_hole_outcomes_plot,)


@app.cell
def _(attend_chart, avg_score_bars, filtered_df, player_hole_outcomes_plot):
    score_attend_plots = mo.vstack([
        mo.md("""
        ## <br>Score & Attendance

        * Best round so far:
        """),
        filtered_df.filter(pl.col("Score") == pl.col("Score").min()).select("PlayerName", "Score", "RoundRating", "Date"), 
        mo.md(f"""<br>
        * Average round rating: {round(filtered_df["RoundRating"].mean())} 
        <br>"""),
        mo.md("""
        <br> 
        * Most attendance so far: 
        <br>
        """),
        filtered_df.filter(pl.col("Attendance") == pl.col("Attendance").max()).select("PlayerName", "Attendance").unique(),
        mo.md(f"<br>* Average round duration: {round(filtered_df["Round Duration (min)"].mean())}  minutes"),
        mo.md("### Graphs"),
        mo.ui.altair_chart(avg_score_bars),
        mo.ui.altair_chart(player_hole_outcomes_plot),
        mo.md("---------------------"),
        mo.ui.altair_chart(attend_chart),
    ])
    return (score_attend_plots,)


@app.cell
def _(df_with_stats, line_chart, relative_chart):
    perf_over_time_plots = mo.vstack([
        mo.md("""
        ## <br>Performance Over Time
        Track how players performed in each round.

        * Most improved so far:  
        """),
        df_with_stats.filter((pl.col("Best Score") - pl.col("Worst Score")) == (pl.col("Best Score") - pl.col("Worst Score")).min()).select(pl.col("PlayerName"), (pl.col("Best Score") - pl.col("Worst Score")).alias("Score Improvement")).unique(),
        mo.md("<br>"),
        mo.ui.altair_chart(line_chart), 
        mo.md("<br>"),
        mo.md("""### Relative Performance
        Shows how players performed compared to their personal average score each round.<br>
        Each player's average is 0. Each round is scored relative to their average.<br>
        Ideally, this should trend downwards as you improve over time.
        """),
        mo.ui.altair_chart(relative_chart),
    ])
    return (perf_over_time_plots,)


@app.cell
def time_series_plot(date_axis, filtered_df):
    # Calculate daily averages for all players
    daily_avg = (
        filtered_df.group_by("Date")
        .agg(
            [
                pl.mean("Score").round(2).alias("Daily Avg Score"),
                pl.count("Score").alias("Total Rounds"),
            ]
        )
        .sort("Date")
    )

    # Calculate cumulative average for each player
    player_cumulative = filtered_df.sort("Date", descending=False).select(
        pl.col("Date"),
        pl.col("PlayerName"),
        pl.col("Score"),
        cum_avg=(pl.col("Score").cum_sum() / pl.arange(1, pl.len() + 1)).over("PlayerName"),
    )

    # Base chart for daily averages
    daily_avg_bars = (
        alt.Chart(daily_avg)
        .mark_bar(opacity=0.7, color="blue", width=25)
        .encode(
            x=date_axis,
            y=alt.Y("Daily Avg Score:Q", title="Score (Relative to Par)"),
            tooltip=[
                "Date:T",
                alt.Tooltip("Daily Avg Score:Q", format=".2f", title="Daily Average Score"),
                "Total Rounds:Q",
            ],
        )
    )


    daily_avg_trend = (
        alt.Chart(daily_avg)
        .mark_line(
            opacity=0.5,
            color="blue",
        )
        .encode(
            x=date_axis,
            y=alt.Y("Daily Avg Score:Q", title="Score (Relative to Par)"),
        )
    )


    # Player scores as circles
    player_scores = (
        alt.Chart(player_cumulative)
        .mark_circle(filled=True, opacity=0.4)
        .encode(
            x=date_axis,
            y=alt.Y("Score:Q", title="Score (Relative to Par)"),
            xOffset="jitter:Q",
            color="PlayerName:N",
            tooltip=[
                "PlayerName:N",
                "Date:T",
                "Score:Q",
                alt.Tooltip("cum_avg:Q", format=".2f", title="Player's Cumulative Average"),
            ],
        ).transform_calculate(
            # Generate uniform jitter
            jitter='random()'
        )
    )

    # Combine all layers
    line_chart = (
        (daily_avg_bars + daily_avg_trend + player_scores)
        .resolve_scale(y="shared")
        .properties(
            title=alt.TitleParams(
                "Player Performance Over Time",
                subtitle="Blue bars show avg score of all rounds that day (to account for weather conditions), circles show individual scores, line shows trend over time",
            ),
            width=800,
            height=500,
        )
    )
    return (line_chart,)


@app.cell
def player_rel_perf_plot(date_axis, df_with_stats):
    # Relative performance chart
    yrule = alt.Chart().mark_rule(strokeDash=[12, 6], size=2).encode(y=alt.datum(0))

    label = yrule.mark_text(
        x="width", dx=-2, align="right", baseline="bottom", text="Player's Avg."
    )

    player_performance_over_time = (
        alt.Chart(df_with_stats)
        .mark_line(point=True, strokeWidth=2)
        .encode(
            x=date_axis,
            y=alt.Y(
                "Relative Score to Player Avg:Q",
                title="Performance (Relative to Player Average)",
            ),
            color="PlayerName:N",
            tooltip=[
                "PlayerName",
                "Date:T",
                "Relative Score to Player Avg:Q",
                "Score:Q",
                "Avg Score:Q",
                "Std Dev:Q",
            ],
        )
    )

    relative_chart = (player_performance_over_time + yrule + label).properties(
        title=alt.TitleParams(
            "Performance Relative to Player Average",
            subtitle="Each Player's Avg Score is 0. The y-axis shows round scores as difference from each player's average.",
        ),
        width=800,
        height=500,
    )
    return (relative_chart,)


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
    par_data = by_hole_df.filter(pl.col("PlayerName") == "Par").unique()
    hole_analysis = ( 
        by_hole_df
        .filter(pl.col("PlayerName") != "Par")
        .join(
            par_data.select(["Hole#", "ShotsThrown"]).rename({"ShotsThrown": "Par"}),
            on="Hole#",
            how="left"
        ).with_columns(
            (pl.col("ShotsThrown") - pl.col("Par")).alias("Score_vs_Par"),
        )
        .with_columns(
            (pl.when(pl.col("Score_vs_Par") < 0)
                .then(pl.lit("Under Par"))
                .otherwise(
                    pl.when(pl.col("Score_vs_Par") > 0)
                    .then(pl.lit("Over Par"))
                    .otherwise(pl.lit("Par"))
                )
            ).alias("Hole Outcome")
        )
        .sort("Hole#")
    )
    return (hole_analysis,)


@app.cell
def _(hole_analysis, hole_outcomes_plot):
    # Calculate hole difficulty statistics
    hole_difficulty = ( 
        hole_analysis
        .group_by("Hole#")
        .agg([
            pl.mean("Score_vs_Par").round(2).alias("Avg_Score_vs_Par"),
            pl.count("PlayerName").alias("Total_Players"),
            pl.max("Score_vs_Par").alias("Worst_Score_vs_Par"),
            pl.min("Score_vs_Par").alias("Best_Score_vs_Par"),
            pl.std("Score_vs_Par").round(2).alias("Std_Dev")
        ])
        .with_columns(cs.numeric().round(2))
        .sort("Avg_Score_vs_Par")
    )

    # Create hole difficulty visualization
    _mean_points = (
        alt.Chart(hole_difficulty)
        .mark_point(filled=True, size=80)
        .encode(
            y=alt.Y("Hole#:N", title="Hole Number", sort=alt.SortField("Avg_Score_vs_Par")),
            x=alt.X("Avg_Score_vs_Par:Q", title="Score vs Par"),
            color=alt.Color("Avg_Score_vs_Par:Q", 
                           scale=alt.Scale(scheme="redyellowgreen", domain=[-2, 2], reverse=True),
                           title="Score vs Par"),
            tooltip=[
                "Hole#:N",
                alt.Tooltip("Avg_Score_vs_Par:Q", title="Avg Score vs Par", format=".2f"),
                alt.Tooltip("Best_Score_vs_Par:Q", title="Best Score vs Par"),
                alt.Tooltip("Worst_Score_vs_Par:Q", title="Worst Score vs Par"),
                "Total_Players:Q"
            ]
        )
    )

    _error_bars = ( 
        alt.Chart(hole_analysis)
            .mark_errorbar(color="blue", opacity=0.8, ticks=True)
            .encode(
              x=alt.X('Score_vs_Par:Q', scale=alt.Scale(zero=False), title="Score vs Par"),
              y=alt.Y(
                  "Hole#:N", 
                    sort=alt.EncodingSortField(
                         field='Avg_Score_vs_Par',
                         order='ascending'
                     ),
                    title="Hole Number"
                ),
            )
    )

    hole_chart = (_error_bars + _mean_points).properties(
        title=alt.Title(text='Hole Difficulty', 
        subtitle='Scores relative to Par'),
        width=800,
        height=500
    )


    # Output
    by_hole_stats = mo.vstack([
        mo.md("## <br>Hole Difficulty Analysis"),
        hole_difficulty,
        mo.md("### Graphs"), 
        hole_outcomes_plot,
        hole_chart,
    ])
    return by_hole_stats, hole_difficulty


@app.cell
def _(hole_analysis, hole_difficulty):
    # Calculate each player's performance on each hole relative to par
    player_hole_performance = hole_analysis.group_by(["PlayerName", "Hole#"]).agg([
        pl.mean("Score_vs_Par").round(2).alias("Avg_Score_vs_Par"),
        pl.std("Score_vs_Par").round(2).alias("SD_Score_vs_Par"),
        pl.len().alias("Rounds_Played"),
        pl.min("Score_vs_Par").alias("Best_Score_vs_Par"),
        pl.max("Score_vs_Par").alias("Worst_Score_vs_Par")
    ]).sort(["PlayerName", "Hole#"])

    # Find best and worst holes for each player
    player_best_holes = player_hole_performance.group_by("PlayerName").agg([
        pl.min("Avg_Score_vs_Par").alias("Best_Hole_Performance"),
        pl.col("Hole#").filter(pl.col("Avg_Score_vs_Par") == pl.min("Avg_Score_vs_Par")).alias("Best_Holes")
    ])

    player_worst_holes = player_hole_performance.group_by("PlayerName").agg([
        pl.max("Avg_Score_vs_Par").alias("Worst_Hole_Performance"),
        pl.col("Hole#").filter(pl.col("Avg_Score_vs_Par") == pl.max("Avg_Score_vs_Par")).alias("Nemesis_Holes")
    ])

    # Combine best and worst hole analysis
    player_extremes = player_best_holes.join(
        player_worst_holes, 
        on="PlayerName", 
        how="left"
    ).with_columns([
        cs.numeric().round(2)
    ])

    # Create heatmap of player performance by hole
    heatmap_data = ( 
        player_hole_performance
            .filter(pl.col("Rounds_Played") >= 1)  # Only holes with data
            .join(
                hole_difficulty.select("Hole#", "Avg_Score_vs_Par").rename({"Avg_Score_vs_Par":"Hole_Avg_vs_Par"}),
                how="left", 
                on="Hole#"
            )
    )

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
                alt.Tooltip("Avg_Score_vs_Par:Q", title="Player's Avg Score vs Par"),
                alt.Tooltip("Hole_Avg_vs_Par:Q", title="Hole's Avg Score vs. Par (all players)"),
                alt.Tooltip("Rounds_Played:Q", title="Rounds Played")
            ]
        )
        .properties(
            title="Player Performance by Hole (Heatmap)",
            width=800,
            height=500
        )
    )

    player_stats_by_hole = mo.vstack([
        mo.md("## <br>Each Player's Best & Nemesis Holes"),
        player_extremes,
        mo.md("### Graphs"),
        player_heatmap      
    ])
    return (player_stats_by_hole,)


@app.cell
def _(hole_analysis):
    _bar = (
        alt.Chart(hole_analysis)
            .mark_bar()
            .encode(
            x=alt.X(
                'count(Hole Outcome):Q',
                stack="normalize",
                title="Outcome of Holes Played"
            ),
            y=alt.Y('Hole#:N', title="Hole Number"),
            color=alt.Color(
                'Hole Outcome:N',
                scale=alt.Scale(
                    domain=['Over Par', 'Par', 'Under Par'],
                    range=['orangered', 'silver', 'green']
                )
            )
        )
    )

    _text = ( 
        alt.Chart(hole_analysis)
            .mark_text(dx=-15, dy=3, color='white')
            .encode(
                x=alt.X('count(Hole Outcome):Q', stack='normalize'),
                y=alt.Y('Hole#:N', title="Hole Number"),
                detail='Hole Outcome:N',
                text=alt.Text('count(Hole Outcome):Q')
            )
    )


    hole_outcomes_plot = (_bar + _text).properties(
        title=alt.Title(text='Hole Bird | Par | Bogey Rate', 
        subtitle='Under Par counts eagles, aces, birdies; Over Par counts anything bogey+'),
        width=800,
        height=400
    )
    return (hole_outcomes_plot,)


if __name__ == "__main__":
    app.run()
