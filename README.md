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

Your CSV file should follow this format:

| Team Name | 24.10. | 01.11. | 07.11. | 15.11. | 21.11. | 28.11. | 12.12. | Best round | Attendance |
|-----------|--------|--------|--------|--------|--------|--------|--------|------------|------------|
| Player A  | 2      | 3      | X      | 1      |        |        |        | -1         | 4          |
| Player B  | 1      | X      | 2      | 0      |        |        |        | 0          | 4          |

### Data Requirements:
- **Team Name**: Player identifier
- **Date columns**: Format `DD.MM.` (e.g., `24.10.` for October 24th)
- **Scores**: Integer values relative to par (negative = under par, positive = over par)
- **Missing data**: Use `X`, `x`, `N/A`, `-`, or better yet, just leave empty for rounds not played
- **Best round**: Optional column with player's best (lowest) score
- **Attendance**: Optional column with number of rounds played

## Usage

1. **Upload Data**: Click "Upload your Glow League CSV file" and select your data file
2. **Select Players**: Use the multiselect dropdown to choose which players to analyze
3. **Explore Visualizations**: 
   - View score trends over time
   - Compare attendance across players
   - Analyze score distributions and consistency
   - Track relative performance improvements

## Technical Details

### Built With
- **[Marimo](https://marimo.io/)**: Reactive Python notebooks that run as web apps
- **[Polars](https://pola.rs/)**: Fast DataFrame library for data processing
- **[Altair](https://altair-viz.github.io/)**: Declarative statistical visualization
- **[NumPy](https://numpy.org/)**: Numerical computing

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
- **Null Handling**: Gracefully handles missing data (X, N/A, empty cells)
- **Date Parsing**: Automatically parses date columns and assigns current year
- **Interactive Filtering**: Dynamic player selection updates all visualizations
- **Statistical Calculations**: Computes averages, standard deviations, and relative performance metrics

## Development

### Adding New Features
The application is built as a marimo notebook, making it easy to modify:
1. Edit `dg_analysis_nb.py` directly or run `marimo edit dg_analysis_nb.py` for the notebook interface
2. Add new cells for additional analysis or visualizations
3. Use marimo's reactive features to create interactive elements

### Sample Data
The `Data/` directory contains example CSV files you can use for testing:
- `Glow Standings.csv`: Basic league standings format
- `2025-12-121908-CroydonDiscGolf-GlowUp18-UDisc.csv`: UDisc export format

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

This project is open source and available under the MIT License.

## Support

If you encounter issues or have questions:
- Check the sample data format in the `Data/` directory
- Ensure your CSV follows the expected column naming convention
- Verify date columns use the `DD.MM.` format with trailing dots and leading zeroes

## TODO

* Use the csv file output from UDisc export directly to provide more data and consistent data fields.
* Auto-detect the UDisc format
* Add a method for automatically aggregating data from multiple rounds (e.g. point to a directory full of files instead of a file)
---
