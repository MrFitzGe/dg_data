import altair as alt

# dg_custom color scheme for score-based coloring
score_color_scale = alt.Scale(
    domain=[-5, -2, 0, 2, 5, 10],
    range=["#2ecc71", "#27ae60", "#f39c12", "#e67e22", "#e74c3c", "#c0392b"],
    name="score_colors",
)

# Enhanced tooltip formatting
dg_custom_tooltip = [
    alt.Tooltip("PlayerName:N", title="Player"),
    alt.Tooltip("Date:T", title="Date", format="%b %d, %Y"),
    alt.Tooltip("Score:Q", title="Score vs Par", format="+.1f"),
    alt.Tooltip("CourseName:N", title="Course"),
    alt.Tooltip("LayoutName:N", title="Layout"),
]


# dg_custom title styling
def create_dg_custom_title(main_title, subtitle=""):
    return alt.TitleParams(
        text=main_title,
        subtitle=subtitle,
        fontSize=18,
        fontWeight="bold",
        color="#2c3e50",
        anchor="middle",
        subtitleFontSize=14,
        subtitleColor="#7f8c8d",
        subtitleFontWeight="normal",
    )


# Enhanced axis configuration
dg_custom_axis = alt.Axis(
    labelFontSize=11,
    titleFontSize=13,
    labelColor="#666666",
    titleColor="#333333",
    grid=True,
    gridColor="#e0e0e0",
    gridOpacity=0.2,
    tickColor="#666666",
    domainColor="#666666",
)

# dg_custom legend configuration
dg_custom_legend = alt.Legend(
    titleFontSize=12,
    labelFontSize=11,
    titleFontWeight="bold",
    titleColor="#333333",
    labelColor="#666666",
    orient="right",
    padding=10,
)
