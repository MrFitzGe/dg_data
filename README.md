# Disc Golf League Analysis 🥏📊

An interactive web application for analyzing Disc Golf League performance over time. Built with [Marimo](https://marimo.io/) for creating reactive notebooks that can be deployed as web apps.

## Features

- **📈 Interactive Visualizations**: Track player performance with time series charts, score distributions, and attendance metrics
- **📁 CSV Upload**: Simply upload your league data CSV file - no coding required
- **👥 Player Comparison**: Select specific players to highlight and compare performance. See League leaders and trending/improving players quickly.
- **📊 Multiple Chart Types**: 
  - Score trends over time with personal averages
  - Attendance tracking
  - Score distribution (min/max/average)
  - Relative performance vs personal averages


## Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) for fast Python package management

### Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd dg-data
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Run the application:
```bash
uv run marimo run dg_analysis_nb.py
```

4. Open your browser to the URL shown in the terminal (typically `http://localhost:2718`)

## Data Format

The application supports **UDisc CSV export format** directly! Simply export your round to .csv in UDisc and upload it immediately.

### UDisc Export Format

Export your round data from UDisc and upload the CSV file. The format includes:

| PlayerName | CourseName | LayoutName | StartDate | EndDate | Total | +/- | RoundRating | Hole1 | Hole2 | ... | Hole18 |
|------------|------------|------------|-----------|---------|-------|-----|-------------|--------|--------|-----|--------|
| Sean Fitz | Croydon Disc Golf | Glow Up 18 | 2025-12-12 1908 | 2025-12-12 2126 | 50 | -4 | 190 | 3 | 2 | ... | 5 |

### Data Requirements:
- **PlayerName**: Player identifier
- **Total**: Total score for the round
- **+/-**: Score relative to par (negative = under par, positive = over par)
- **RoundRating**: UDisc round rating
- **Hole1-Hole18**: Individual hole scores
- **StartDate/EndDate**: Round timestamps

## Usage

1. **Upload Data**: Click "Upload your UDisc CSV file" and select your UDisc export file
2. **Select Players**: Use the multiselect dropdown to choose which players to analyze
3. **Explore Visualizations**: 
   - View score trends over time
   - Compare attendance across players
   - Analyze score distributions and consistency
   - Track relative performance improvements
   - View round ratings and hole-by-hole analysis

## Technical Details

### Built With
- **[Marimo](https://marimo.io/)**: Reactive Python notebooks that run as web apps
- **[Polars](https://pola.rs/)**: Fast DataFrame library for data processing
- **[Altair](https://altair-viz.github.io/)**: For interactive plotting

### Project Structure
```
dg-data/
├── dg_analysis_nb.py   # Main marimo notebook application
├── pyproject.toml      # Project dependencies and metadata
├── uv.lock             # Locked dependency versions
├── Data/               # Sample data files
│   ├── Glow Standings.csv
│   └── 2025-12-121908-CroydonDiscGolf-GlowUp18-UDisc.csv
└── README.md           # This file
```

### Key Features Implementation
- **Data Processing**: Converts wide-format CSV to long-format for time series analysis
- **Interactive Filtering**: Dynamic player selection updates all visualizations
- **Statistical Calculations**: Computes averages, standard deviations, and relative performance metrics for each player
- **League-wise Rankings**: Compare performance and attendance across all players instantly

## Development

### Adding New Features
The application is built as a marimo notebook, making it easy to modify:
1. Edit `dg_analysis_nb.py` directly or run `marimo edit dg_analysis_nb.py` for the notebook interface
2. Add new cells for additional analysis or visualizations
3. Use marimo's reactive features to create interactive elements

### Sample Data
The `Data/UDisc/` directory contains example UDisc CSV export files you can use for testing:
- Multiple UDisc export files for testing multi-round analysis
- `2025-12-121908-CroydonDiscGolf-GlowUp18-UDisc.csv`: Example UDisc export format

## Deployment

### Local Development
```bash
uv run marimo run dg_analysis_nb.py
```

### Production Deployment
Marimo notebooks can be deployed as static web applications or served via various hosting platforms. See the [marimo deployment documentation](https://docs.marimo.io/guides/deploying/) for options.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test with sample data
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is open source and available under the Apache 2.0 License.

## Support

If you encounter issues or have questions:
- Check the sample data format in the `Data/UDisc/` directory
- Ensure your CSV is a direct export from UDisc
- Verify your CSV contains the expected columns (PlayerName, Total, +/-, RoundRating, etc.)

## What's New

✅ **UDisc CSV Export Support**: Directly upload UDisc exports with hole-by-hole data and round ratings
✅ **Enhanced Analytics**: Round ratings, hole-by-hole analysis, and more detailed statistics
✅ **Multi-file Support**: Upload multiple UDisc export files for comprehensive league analysis


---
