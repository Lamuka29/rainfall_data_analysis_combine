import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import calendar
import io
import streamlit as st
import xlrd
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Rainfall Analysis",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ Rainfall Data Analysis")
st.caption("Pemprosesan, Quality Control dan Analisis Data Hujan Harian")
# ============================================================
# MONTHS
# ============================================================
months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]
# ============================================================
# GRAPH SETTINGS
# ============================================================
RAINFALL_MIN = 0
RAINFALL_MAX = 500
# ============================================================
# FIGURE SIZE
# ============================================================
FIG_WIDTH = 14
FIG_HEIGHT = 9
# ============================================================
# FILE UPLOAD
# ============================================================
uploaded_files = st.file_uploader("📁 Upload Excel file data hujan mengikut stesen AAWS",
    type=["xlsx", "xls"],
    accept_multiple_files=True)

if not uploaded_files:
    st.info("Sila upload sekurang-kurangnya satu fail Excel.")
    st.markdown(
        """
        **Format data yang diperlukan:**
        - Sheet dinamakan mengikut tahun, contoh `2016`, `2017`, ..., `2025`
        - Header berada pada baris ke-7 Excel
        - Column A = `hari`
        - Column B:M = `Jan` hingga `Dec`
        """
    )
    st.stop()
# ============================================================
# DETECT AVAILABLE YEARS
# ============================================================
def get_available_years(uploaded_file):

    try:
        file_bytes = uploaded_file.getvalue()
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

        if file_ext == ".xls":
            engine = "xlrd"
        else:
            engine = "openpyxl"

        excel_file = pd.ExcelFile(io.BytesIO(file_bytes),engine=engine)
        available_years = []

        for sheet in excel_file.sheet_names:
            try:
                year = int(str(sheet).strip())
                if 1900 <= year <= 2100:
                    available_years.append(year)

            except:
                continue

        return sorted(set(available_years))

    except Exception:

        return []
# ============================================================
# DETECT YEARS FROM ALL UPLOADED FILES
# ============================================================
all_available_years = set()

file_years = {}

for uploaded_file in uploaded_files:
    detected_years = get_available_years(uploaded_file)

    file_years[uploaded_file.name] = detected_years
    all_available_years.update(detected_years)

all_available_years = sorted(all_available_years)
# ============================================================
# TAHUN CLIMATOLOGY
# ============================================================
st.sidebar.subheader("📅 Climatology Period")

START_YEAR = st.sidebar.selectbox(
    "Start Year",
    all_available_years,
    index=0
)

END_YEAR = st.sidebar.selectbox(
    "End Year",
    all_available_years,
    index=len(all_available_years) - 1
)

if START_YEAR > END_YEAR:
    st.sidebar.error("Start Year mesti lebih kecil atau sama dengan End Year.")
    st.stop()

years = range(int(START_YEAR),int(END_YEAR) + 1)

YEAR_RANGE_TEXT = (f"{int(START_YEAR)}–{int(END_YEAR)}")
# ============================================================
# SIDEBAR SETTINGS
# ============================================================
st.sidebar.header("⚙️ Analysis Settings")

# ============================================================
# WMO MISSING DATA RULE
# ============================================================
st.sidebar.subheader("WMO Missing Data Rule")

MAX_MISSING_DAYS = st.sidebar.number_input(
    "Maximum missing days",
    min_value=0,
    max_value=31,
    value=10,
    step=1,
    help=("Bulan ditolak jika bilangan missing days melebihi nilai ini. Default 10 bermaksud >=11 missing days ditolak.")
)

MAX_CONSECUTIVE_MISSING = st.sidebar.number_input(
    "Maximum consecutive missing days",
    min_value=1,
    max_value=31,
    value=4,
    step=1,
    help=("Bulan ditolak jika terdapat missing days berturut-turut melebihi nilai ini. Default 4 bermaksud >=5 berturut-turut ditolak.")
)
# ============================================================
# RAINFALL THRESHOLDS
# ============================================================
st.sidebar.subheader("🌧️ Rainfall Threshold")

VALID_MIN = 0.0

WET_DAY_MIN = st.sidebar.number_input(
    "Wet day threshold (mm)",
    min_value=0.0,
    value=0.1,
    step=0.01
)

SUSPECT_RAINFALL = st.sidebar.number_input(
    "Suspect threshold (mm)",
    min_value=0.0,
    value=150.0,
    step=10.0
)

EXTREME_RAINFALL = st.sidebar.number_input(
    "Extreme threshold (mm)",
    min_value=0.0,
    value=250.0,
    step=10.0
)
# ============================================================
# PLOT SETTINGS - USER BOLEH UBAH
# ============================================================
st.sidebar.header("🎨 Plot Settings")

# ============================================================
# BACKGROUND
# ============================================================
BG_COLOR = st.sidebar.color_picker(
    "Background Graf",
    "#FFFFFF"
)
# ============================================================
# DEFAULT BAR COLORS - MONTHLY RAINFALL
# ============================================================
default_colors = [
    "#4682B4",  # Jan
    "#87CEEB",  # Feb
    "#3CB371",  # Mar
    "#32CD32",  # Apr
    "#FFD700",  # May
    "#FFA500",  # Jun
    "#FF7F50",  # Jul
    "#FF6347",  # Aug
    "#9370DB",  # Sep
    "#DA70D6",  # Oct
    "#6A5ACD",  # Nov
    "#008080"   # Dec
]
# ============================================================
# SESSION STATE
# ============================================================
if "bar_colors" not in st.session_state:
    st.session_state.bar_colors = default_colors.copy()

if "max_daily_color" not in st.session_state:
    st.session_state.max_daily_color = "#FF6347"

if "wet_days_color" not in st.session_state:
    st.session_state.wet_days_color = "#3CB371"

if "std_color" not in st.session_state:
    st.session_state.std_color = "#9370DB"

if "hist_color" not in st.session_state:
    st.session_state.hist_color = "#4682B4"
# ============================================================
# SELECT BAR CHART
# ============================================================
chart_options = ["Bar + Line",]

selected_chart = st.sidebar.selectbox("Select Bar Chart",chart_options)
# ============================================================
# MONTHLY RAINFALL
# ============================================================
if selected_chart == "Monthly Rainfall":
    selected_month = st.sidebar.selectbox("Select Month",months)
    selected_index = months.index(selected_month)

    st.session_state.bar_colors[
        selected_index
    ] = st.sidebar.color_picker(
        f"{selected_month} Bar Colour",
        st.session_state.bar_colors[selected_index]
    )
# ============================================================
# MEAN LINE
# ============================================================
LINE_COLOR = st.sidebar.color_picker(
    "Mean Line",
    "#000000"
)
# ============================================================
# MINIMUM
# ============================================================
MIN_COLOR = st.sidebar.color_picker(
    "Minimum",
    "#008000"
)
# ============================================================
# MAXIMUM
# ============================================================
MAX_COLOR = st.sidebar.color_picker(
    "Maximum",
    "#FF0000"
)
# ============================================================
# CHECK AVAILABLE YEARS
# ============================================================
if not all_available_years:
    st.error("❌ Tiada sheet tahun yang sah dijumpai dalam fail Excel.")
    st.stop()

# ============================================================
# FUNCTION
# MAXIMUM CONSECUTIVE MISSING
# ============================================================
def max_consecutive_missing(values):
    is_missing = values.isna()
    max_missing = 0
    current_missing = 0

    for missing in is_missing:
        
        if missing:
            current_missing += 1

            if current_missing > max_missing:
                max_missing = current_missing

        else:
            current_missing = 0

    return max_missing
# ============================================================
# FUNCTION
# READ YEAR SHEET
# ============================================================
def read_year_sheet(uploaded_file, year):

    try:
        file_bytes = uploaded_file.getvalue()

        file_ext = os.path.splitext(
            uploaded_file.name
        )[1].lower()
        
        if file_ext == ".xls":
            engine = "xlrd"
        elif file_ext == ".xlsx":
            engine = "openpyxl"
        else:
            return None, "Format fail tidak disokong."

        df = pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name=str(year),
            header=6,
            engine=engine
        )

    except Exception as e:
        return None, str(e)

    if df is None or df.empty:
        return None, "Sheet kosong."
    # --------------------------------------------------------
    # Ambil 13 column pertama
    # --------------------------------------------------------
    if df.shape[1] < 13:

        return None, (
            f"Bilangan column tidak mencukupi "
            f"({df.shape[1]} column dikesan). "
            f"Minimum 13 column diperlukan."
        )

    df = df.iloc[:, :13].copy()

    df.columns = [
        "hari",
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    # --------------------------------------------------------
    # Convert day
    # --------------------------------------------------------
    df["hari"] = pd.to_numeric(
        df["hari"],
        errors="coerce"
    )

    df = df[
        df["hari"].between(1, 31)
    ].copy()
    # --------------------------------------------------------
    # Convert rainfall
    # --------------------------------------------------------
    for month in months:

        df[month] = pd.to_numeric(
            df[month],
            errors="coerce"
        )

        # Negative = invalid
        df.loc[
            df[month] < VALID_MIN,
            month
        ] = np.nan

    df["Year"] = int(year)

    return df, None
# ============================================================
# FUNCTION
# ANALYZE ONE FILE
# ============================================================
def analyze_file(uploaded_file):

    file_name = os.path.splitext(
        uploaded_file.name
    )[0]

    original_file_name = uploaded_file.name

    daily_results = []
    read_errors = []    
    # ========================================================
    # READ ALL YEARS
    # ========================================================
    for year in years:

        df, error = read_year_sheet(
            uploaded_file,
            year
        )

        if df is not None:
            daily_results.append(df)

        else:
            read_errors.append({
                "Year": int(year),
                "Error": error
            })
    # ========================================================
    # CHECK DATA
    # ========================================================
    if len(daily_results) == 0:

        return {
            "success": False,
            "file_name": file_name,
            "original_file_name": original_file_name,
            "error": "Tiada sheet tahun berjaya dibaca."
        }
    # ========================================================
    # COMBINE DATA
    # ========================================================
    all_daily = pd.concat(
        daily_results,
        ignore_index=True
    )
    # ========================================================
    # QUALITY CONTROL
    # ========================================================
    for month in months:

        all_daily.loc[
            all_daily[month] < VALID_MIN,
            month
        ] = np.nan
    # ========================================================
    # SUSPECT & EXTREME
    # ========================================================
    suspect_records = []
    extreme_records = []

    for _, row in all_daily.iterrows():
        year = int(row["Year"])
        day = int(row["hari"])

        for month in months:
            value = row[month]

            if pd.isna(value):
                continue

            if value > EXTREME_RAINFALL:
                extreme_records.append({
                    "Year": year,
                    "Day": day,
                    "Month": month,
                    "Rainfall (mm)": value,
                    "Status": "EXTREME - DOUBLE CHECK"
                })

            elif value > SUSPECT_RAINFALL:
                suspect_records.append({
                    "Year": year,
                    "Day": day,
                    "Month": month,
                    "Rainfall (mm)": value,
                    "Status": "SUSPECT - SEMAK"
                })

    suspect_df = pd.DataFrame(
        suspect_records,
        columns=[
            "Year",
            "Day",
            "Month",
            "Rainfall (mm)",
            "Status"
        ]
    )

    extreme_df = pd.DataFrame(
        extreme_records,
        columns=[
            "Year",
            "Day",
            "Month",
            "Rainfall (mm)",
            "Status"
        ]
    )
    # ========================================================
    # YEARLY MONTHLY TOTAL
    # ========================================================
    available_years = sorted(
        all_daily["Year"].unique()
    )

    yearly_monthly_total = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=float
    )

    monthly_missing_count = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=float
    )

    monthly_valid_count = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=float
    )

    monthly_max_consecutive_missing = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=float
    )

    monthly_qc_status = pd.DataFrame(
        index=available_years,
        columns=months,
        dtype=object
    )
    # ========================================================
    # LOOP YEAR & MONTH
    # ========================================================
    for year in available_years:
        year_data = all_daily[all_daily["Year"] == year]

        for month in months:
            month_index = (months.index(month) + 1)

            days_expected = calendar.monthrange(
                int(year),
                month_index
            )[1]

            values = (
                year_data[month]
                .iloc[:days_expected]
                .copy()
            )

            valid_values = values[
                values.notna() &
                (values >= VALID_MIN)
            ]

            valid_count = len(valid_values)
            missing_count = (days_expected - valid_count)
            max_consecutive = (max_consecutive_missing(values))

            monthly_valid_count.loc[year,month] = valid_count
            monthly_missing_count.loc[year,month] = missing_count
            monthly_max_consecutive_missing.loc[year,month] = max_consecutive
            # ------------------------------------------------
            # ACCEPT / REJECT
            # Default:
            # >10 missing = reject
            # >=5 consecutive = reject
            # ------------------------------------------------
            if (
                missing_count <= MAX_MISSING_DAYS
                and
                max_consecutive <= MAX_CONSECUTIVE_MISSING
            ):

                yearly_monthly_total.loc[year,month] = valid_values.sum()
                monthly_qc_status.loc[year,month] = "ACCEPT"

            else:
                yearly_monthly_total.loc[year,month] = np.nan

                if missing_count > MAX_MISSING_DAYS:
                    monthly_qc_status.loc[year,month] = (f"REJECT: >{MAX_MISSING_DAYS} MISSING")

                elif (max_consecutive >MAX_CONSECUTIVE_MISSING):
                    monthly_qc_status.loc[year,month
                    ] = (f"REJECT: {MAX_CONSECUTIVE_MISSING} CONSECUTIVE MISSING")

                else:
                    monthly_qc_status.loc[year,month] = "REJECT"
    # ========================================================
    # CLIMATOLOGICAL MONTHLY MEAN
    # ========================================================
    mean_monthly_total = (
        yearly_monthly_total
        .mean(
            axis=0,
            skipna=True
        )
        .reindex(months)
    )
    # ========================================================
    # YEARLY TOTAL
    # ========================================================
    yearly_total = (
        yearly_monthly_total
        .sum(
            axis=1,
            min_count=1
        )
    )
    # ========================================================
    # RETURN RESULTS
    # ========================================================
    return {
        "success": True,
        "file_name":file_name,
        "original_file_name":original_file_name,
        "all_daily":all_daily,
        "yearly_monthly_total":yearly_monthly_total,
        "monthly_missing_count":monthly_missing_count,
        "monthly_valid_count":monthly_valid_count,
        "monthly_max_consecutive_missing":monthly_max_consecutive_missing,
        "monthly_qc_status":monthly_qc_status,
        "mean_monthly_total":mean_monthly_total,
        "yearly_total":yearly_total,
        "suspect_df":suspect_df,
        "extreme_df":extreme_df,
        "read_errors":read_errors
    }
# ============================================================
# PROCESS ALL UPLOADED FILES
# ============================================================
with st.spinner(
    "⏳ Sedang memproses semua fail Excel..."
):

    results = []
    progress_bar = st.progress(0)

    for i, uploaded_file in enumerate(
        uploaded_files
    ):

        result = analyze_file(
            uploaded_file
        )

        results.append(result)

        progress_bar.progress(
            int(
                ((i + 1) /
                 len(uploaded_files)) * 100
            )
        )

    progress_bar.empty()

# ============================================================
# CHECK RESULTS
# ============================================================
successful_results = [
    result
    for result in results
    if result.get("success", False)
]

failed_results = [
    result
    for result in results
    if not result.get("success", False)
]
# ============================================================
# TARGET YEAR
# ============================================================
available_years = sorted(
    set(
        year
        for result in successful_results
        for year in result["all_daily"]["Year"].dropna().unique()
    )
)

target_year = st.sidebar.selectbox(
    "📅 Target Year",
    available_years,
    index=len(available_years) - 1,
    key="target_year"
)

target_year = int(target_year)
# ============================================================
# TARGET YEAR ANALYSIS
# ============================================================
for result in successful_results:
    all_daily = result["all_daily"]
    yearly_monthly_total = (result["yearly_monthly_total"])
    mean_monthly_total = (result["mean_monthly_total"])
    # --------------------------------------------------------
    # TARGET YEAR MONTHLY TOTAL
    # --------------------------------------------------------
    if target_year in yearly_monthly_total.index:
        rainfall_target = (yearly_monthly_total.loc[target_year].reindex(months))

    else:
        rainfall_target = pd.Series(np.nan,index=months)
    # --------------------------------------------------------
    # ANOMALY
    # --------------------------------------------------------
    anomaly_percent = ((rainfall_target - mean_monthly_total)/ mean_monthly_total) * 100
    anomaly_percent[mean_monthly_total == 0] = np.nan
    # --------------------------------------------------------
    # MIN / MAX TARGET YEAR
    # --------------------------------------------------------
    valid_target = rainfall_target.dropna()

    if len(valid_target) > 0:
        min_target_month = valid_target.idxmin()
        min_target_value = valid_target.min()

        max_target_month = valid_target.idxmax()
        max_target_value = valid_target.max()

    else:
        min_target_month = None
        min_target_value = None
        max_target_month = None
        max_target_value = None
    # --------------------------------------------------------
    # MIN / MAX MEAN
    # --------------------------------------------------------
    valid_mean = mean_monthly_total.dropna()

    if len(valid_mean) > 0:
        min_mean_month = valid_mean.idxmin()
        min_mean_value = valid_mean.min()

        max_mean_month = valid_mean.idxmax()
        max_mean_value = valid_mean.max()

    else:
        min_mean_month = None
        min_mean_value = None
        max_mean_month = None
        max_mean_value = None
    # ========================================================
    # SAVE INTO RESULT
    # ========================================================
    result["rainfall_target"] = rainfall_target
    result["anomaly_percent"] = anomaly_percent

    result["min_target_month"] = min_target_month
    result["min_target_value"] = min_target_value
    result["max_target_month"] = max_target_month
    result["max_target_value"] = max_target_value

    result["min_mean_month"] = min_mean_month
    result["min_mean_value"] = min_mean_value
    result["max_mean_month"] = max_mean_month
    result["max_mean_value"] = max_mean_value
# ============================================================
# DAILY STATISTICS FOR TARGET YEAR
# ============================================================
for result in successful_results:

    all_daily = result["all_daily"]

    target_data = all_daily[
        all_daily["Year"] == target_year
    ].copy()

    median_daily = []
    std_daily = []
    max_daily = []
    min_daily = []
    wet_days = []
    valid_data_percent = []
    suspect_count = []
    extreme_count = []

    # ========================================================
    # RAINFALL CATEGORY
    # ========================================================
    category_labels = [
        "Slight Rain (1.0–10.0 mm)",
        "Moderate Rain (>10.0–30.0 mm)",
        "Heavy Rain (>30.0–60.0 mm)",
        "Very Heavy Rain (>60 mm)"
    ]

    # ========================================================
    # MONTHLY DAILY STATISTICS
    # ========================================================
    for month in months:

        month_index = months.index(month) + 1

        days_expected = calendar.monthrange(
            target_year,
            month_index
        )[1]

        raw_values = (
            target_data[month]
            .iloc[:days_expected]
            .copy()
        )

        # ----------------------------------------------------
        # QC
        # ----------------------------------------------------
        qc_values = raw_values[
            raw_values.notna() &
            (raw_values >= VALID_MIN)
        ]

        # ----------------------------------------------------
        # WET DAYS
        # ----------------------------------------------------
        values = qc_values[
            qc_values >= WET_DAY_MIN
        ]

        # ----------------------------------------------------
        # VALID DATA %
        # ----------------------------------------------------
        valid_count = len(qc_values)

        percent = (
            valid_count /
            days_expected
        ) * 100

        valid_data_percent.append(percent)

        # ----------------------------------------------------
        # MEDIAN
        # ----------------------------------------------------
        if len(values) > 0:
            median_daily.append(
                values.median()
            )
        else:
            median_daily.append(np.nan)

        # ----------------------------------------------------
        # STANDARD DEVIATION
        # ----------------------------------------------------
        if len(values) > 1:
            std_daily.append(
                values.std()
            )
        else:
            std_daily.append(np.nan)

        # ----------------------------------------------------
        # MAXIMUM
        # ----------------------------------------------------
        if len(values) > 0:
            max_daily.append(
                values.max()
            )
        else:
            max_daily.append(np.nan)

        # ----------------------------------------------------
        # MINIMUM
        # ----------------------------------------------------
        if len(values) > 0:
            min_daily.append(
                values.min()
            )
        else:
            min_daily.append(np.nan)

        # ----------------------------------------------------
        # WET DAYS
        # ----------------------------------------------------
        wet_days.append(
            (qc_values >= WET_DAY_MIN).sum()
        )

        # ----------------------------------------------------
        # SUSPECT
        # ----------------------------------------------------
        suspect_count.append(
            (values > SUSPECT_RAINFALL).sum()
        )

        # ----------------------------------------------------
        # EXTREME
        # ----------------------------------------------------
        extreme_count.append(
            (values > EXTREME_RAINFALL).sum()
        )

    # ========================================================
    # ANALYSIS TABLE
    # ========================================================
    analysis_table = pd.DataFrame({
        "Month": months,
        "Median": median_daily,
        "Std Dev": std_daily,
        "Maximum": max_daily,
        "Minimum": min_daily,
        "Wet Days": wet_days,
        "Valid Data (%)": valid_data_percent,
        "Suspect": suspect_count,
        "Extreme": extreme_count
    })

    # ========================================================
    # HISTOGRAM VALUES
    # ========================================================
    hist_values = target_data[
        months
    ].stack()

    hist_values = hist_values[
        hist_values.notna() &
        (hist_values >= VALID_MIN)
    ]

    # ========================================================
    # RAINFALL CATEGORY
    # ========================================================
    all_values = target_data[
        months
    ].stack()

    all_values = all_values[
        all_values.notna() &
        (all_values >= VALID_MIN)
    ]

    category_values = [
        (
            (all_values >= 1) &
            (all_values <= 10)
        ).sum(),

        (
            (all_values > 10) &
            (all_values <= 30)
        ).sum(),

        (
            (all_values > 30) &
            (all_values <= 60)
        ).sum(),

        (all_values > 60).sum()
    ]

    # ========================================================
    # SAVE INTO RESULT
    # ========================================================
    result["median_daily"] = median_daily
    result["std_daily"] = std_daily
    result["max_daily"] = max_daily
    result["min_daily"] = min_daily
    result["wet_days"] = wet_days
    result["valid_data_percent"] = valid_data_percent
    result["suspect_count"] = suspect_count
    result["extreme_count"] = extreme_count

    result["analysis_table"] = analysis_table
    result["hist_values"] = hist_values
    result["category_values"] = category_values
    result["category_labels"] = category_labels
# ============================================================
# FILE SUMMARY
# ============================================================
st.success(
    f"✅ {len(successful_results)} daripada "
    f"{len(uploaded_files)} fail berjaya dianalisis."
)

if failed_results:
    st.warning(
        f"⚠️ {len(failed_results)} fail tidak berjaya dianalisis."
    )

    for result in failed_results:
        st.error(
            f"{result.get('original_file_name', 'Unknown')}: "
            f"{result.get('error', 'Unknown error')}"
        )

if not successful_results:
    st.stop()
# ============================================================
# STATION SELECTION
# ============================================================
station_options = [
    result["file_name"]
    for result in successful_results
]

selected_station = st.sidebar.selectbox(
    "📍 Select Station",
    station_options,
    key="main_station"
)

# ============================================================
# FILTER DISPLAY RESULT
# ============================================================
display_results = [
    result
    for result in successful_results
    if result["file_name"] in selected_station
]

if not selected_station:
    st.warning("Sila pilih sekurang-kurangnya satu stesen.")
    st.stop()
# ============================================================
# GLOBAL AUTO Y-AXIS
# ============================================================
global_max_total = 0
global_max_mean = 0

max_total_file = None
max_total_month = None

max_mean_file = None
max_mean_month = None

for result in successful_results:
    rainfall_target = result["rainfall_target"]
    
    mean_monthly_total = result["mean_monthly_total"]

    if rainfall_target.notna().any():
        local_max = rainfall_target.max()

        if local_max > global_max_total:
            global_max_total = local_max

            max_total_file = result["original_file_name"]

            max_total_month = (rainfall_target.idxmax())

    if mean_monthly_total.notna().any():
        local_max = mean_monthly_total.max()

        if local_max > global_max_mean:
            global_max_mean = local_max

            max_mean_file = result["original_file_name"]
            max_mean_month = (mean_monthly_total.idxmax())

selected_max = max(
    global_max_total,
    global_max_mean
)

if selected_max > 0:
    RAINFALL_MAX = (int(selected_max / 100) + 1) * 100

else:
    RAINFALL_MAX = 100

# ============================================================
# GLOBAL SUMMARY
# ============================================================
st.subheader("📌 Overall Analysis Summary")

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    st.metric(
        "Files Analysed",
        len(successful_results)
    )

with summary_col2:
    st.metric(
        "Target Year",
        target_year
    )

with summary_col3:
    st.metric(
        "Auto Y-Axis Maximum",
        f"{RAINFALL_MAX:.0f} mm"
    )

# ============================================================
# GLOBAL AUTO Y-AXIS INFORMATION
# ============================================================
with st.expander(
    "🔎 Auto Y-Axis Information"
):

    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Maximum Target-Year Monthly Total**")
        st.write(f"Value: {global_max_total:.2f} mm")
        st.write(f"File: {max_total_file}")
        st.write(f"Month: {max_total_month}")

    with col2:
        st.write("**Maximum Climatological Monthly Mean**")
        st.write(f"Value: {global_max_mean:.2f} mm")
        st.write(f"File: {max_mean_file}")
        st.write(f"Month: {max_mean_month}")
# ============================================================
# MAIN TABS
# ============================================================
main_tabs = st.tabs([
    "📅 Target Year (Selected Station)",
    "📊 All Years (Selected Station)",
    "🔄 Station Comparison (All years data)"
])

with main_tabs[0]:
    # ============================================================
    # DISPLAY EACH FILE
    # ============================================================
    for result in display_results:
        file_name = result["file_name"]
        original_file_name = result["original_file_name"]
        all_daily = result["all_daily"]

        target_data = all_daily[
            all_daily["Year"] == target_year
        ].copy()
    
        yearly_monthly_total = result["yearly_monthly_total"]
        monthly_missing_count = result["monthly_missing_count"]
        monthly_valid_count = result["monthly_valid_count"]
        monthly_max_consecutive_missing = result["monthly_max_consecutive_missing"]
        monthly_qc_status = result["monthly_qc_status"]
        rainfall_target = result["rainfall_target"]
        mean_monthly_total = result["mean_monthly_total"]
        anomaly_percent = result["anomaly_percent"]
        min_target_month = result["min_target_month"]
        min_target_value = result["min_target_value"]
        max_target_month = result["max_target_month"]
        max_target_value = result["max_target_value"]
        min_mean_month = result["min_mean_month"]
        min_mean_value = result["min_mean_value"]
        max_mean_month = result["max_mean_month"]
        max_mean_value = result["max_mean_value"]
        median_daily = result["median_daily"]
        std_daily = result["std_daily"]
        max_daily = result["max_daily"]
        min_daily = result["min_daily"]
        wet_days = result["wet_days"]
        valid_data_percent = result["valid_data_percent"]
        analysis_table = result["analysis_table"]
        suspect_df = result["suspect_df"]
        extreme_df = result["extreme_df"]
        hist_values = result["hist_values"]
        category_values = result["category_values"]
        category_labels = result["category_labels"]
        read_errors = result["read_errors"]
        
        # ========================================================
        # FILE HEADER
        # ========================================================
        st.divider()
    
        st.header(f"📁 {original_file_name}")
        # ========================================================
        # READ ERROR
        # ========================================================
        if read_errors:
    
            with st.expander("⚠️ Sheet yang tidak berjaya dibaca"):
                error_df = pd.DataFrame(read_errors)
    
                st.dataframe(error_df,use_container_width=True,hide_index=True)
        # ========================================================
        # BASIC METRICS
        # ========================================================
        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            if (
                min_target_month is not None
                and min_target_value is not None
            ):
    
                st.metric(
                    f"Minimum {target_year}",
                    f"{min_target_value:.2f} mm",
                    min_target_month
                )
    
            else:
                st.metric(
                    f"Minimum {target_year}",
                    "N.A."
                )
    
        with col2:
            if (
                max_target_month is not None
                and max_target_value is not None
            ):
    
                st.metric(
                    f"Maximum {target_year}",
                    f"{max_target_value:.2f} mm",
                    max_target_month
                )
    
            else:
                st.metric(
                    f"Maximum {target_year}",
                    "N.A."
                )
    
        with col3:
            if (
                min_mean_month is not None
                and min_mean_value is not None
            ):

                st.metric(
                    "Minimum Mean",
                    f"{min_mean_value:.2f} mm",
                    min_mean_month
                )
    
            else:
                st.metric(
                    "Minimum Mean",
                    "N.A."
                )
    
        with col4:
            if (
                max_mean_month is not None
                and max_mean_value is not None
            ):
    
                st.metric(
                    "Maximum Mean",
                    f"{max_mean_value:.2f} mm",
                    max_mean_month
                )
    
            else:
                st.metric(
                    "Maximum Mean",
                    "N.A."
                )

        # ========================================================
        # YEARS AVAILABLE
        # ========================================================
        years_available = (
            all_daily["Year"]
            .dropna()
            .nunique()
        )
        # ========================================================
        # QC SUMMARY
        # ========================================================
        qc_col1, qc_col2, qc_col3 = st.columns(3)
    
        with qc_col1:
            st.metric("Suspect Records",len(suspect_df))
    
        with qc_col2:
            st.metric("Extreme Records",len(extreme_df))
    
        with qc_col3:
            st.metric("Valid Daily Records",int((all_daily[months].notna().sum().sum())))
# ===========================================================
# main tab 1
# ===========================================================
with main_tabs[0]:
    tabs = st.tabs([
        "📊 Bar + Line",
        "🔥 Heatmap",
        "📉 Anomaly",
        "📋 Statistics",
        "📈 Max Daily",
        "🌧️ Wet Days",
        "📐 Standard Deviation",
        "📊 Histogram",
        "🥧 Rainfall Category",
        "📦 Boxplot",
        "⚠️ QC"
    ])
    # ========================================================
    # TAB 1 BAR + LINE
    # ========================================================
    with tabs[0]:
        st.subheader(
            f"Monthly Rainfall {target_year} vs "
            f"Mean Monthly Rainfall {YEAR_RANGE_TEXT}"
        )

        x = np.arange(
            len(months)
        )

        fig, ax = plt.subplots(
            figsize=(
                FIG_WIDTH,
                FIG_HEIGHT
            )
        )

        bg_color = BG_COLOR
        
        fig.patch.set_facecolor(
            bg_color
        )

        ax.set_facecolor(
            bg_color
        )

        ax.bar(
            x,
            rainfall_target.values,
            width=0.60,
            color=st.session_state.bar_colors,
            edgecolor="black",
            linewidth=0.8,
            label=(
                f"Total Rainfall {target_year}"
            )
        )

        ax.plot(
            x,
            mean_monthly_total.values,
            color=LINE_COLOR,
            marker="o",
            linewidth=2.5,
            markersize=7,
            label=(
                f"Mean Monthly Rainfall "
                f"{YEAR_RANGE_TEXT}"
            )
        )
        # ----------------------------------------------------
        # Mean labels
        # ----------------------------------------------------
        for i, value in enumerate(
            mean_monthly_total.values
        ):

            if pd.notna(value):
                ax.annotate(
                    f"{value:.1f}",
                    (
                        i,
                        value
                    ),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=11,
                    fontweight="bold"
                )
        # ----------------------------------------------------
        # Minimum
        # ----------------------------------------------------
        if min_target_month is not None:
            min_index = months.index(
                min_target_month
            )

            ax.scatter(
                min_index,
                min_target_value,
                s=50,
                color=MIN_COLOR,
                edgecolor="black",
                linewidth=1,
                zorder=5,
                label=(
                    f"Minimum {target_year}: "
                    f"{min_target_month} "
                    f"({min_target_value:.1f} mm)"
                )
            )
        # ----------------------------------------------------
        # Maximum
        # ----------------------------------------------------
        if max_target_month is not None:
            max_index = months.index(
                max_target_month
            )

            ax.scatter(
                max_index,
                max_target_value,
                s=50,
                color=MAX_COLOR,
                edgecolor="black",
                linewidth=1,
                zorder=5,
                label=(
                    f"Maximum {target_year}: "
                    f"{max_target_month} "
                    f"({max_target_value:.1f} mm)"
                )
            )

        ax.set_title(
            f"{file_name}\n"
            f"Monthly Rainfall {target_year} vs "
            f"Mean Monthly Rainfall {YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Month",
            fontsize=12
        )

        ax.set_ylabel(
            "Rainfall (mm)",
            fontsize=12
        )

        ax.set_xticks(x)
        ax.set_xticklabels(months)

        ax.set_ylim(
            RAINFALL_MIN,
            RAINFALL_MAX
        )

        ax.grid(
            True,
            axis="y",
            linestyle="--",
            alpha=0.4
        )

        ax.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=9
        )

        plt.tight_layout()

        st.pyplot(fig,use_container_width=True)

        img_buffer = io.BytesIO()
        
        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        img_buffer.seek(0)
        
        st.download_button(
            "📥 Download Plot PNG",
            data=img_buffer.getvalue(),
            file_name=f"{selected_station}_target_year_{target_year}.png",
            mime="image/png",
            key=f"download_monthly_rainfall_{selected_station}_{target_year}"
        )

        # ========================================================
        # TABLE DATA
        # ========================================================
        
        plot_table = pd.DataFrame({
            "Month": months,
            f"Total Rainfall {target_year} (mm)":
                rainfall_target.values,
            f"Mean Rainfall {YEAR_RANGE_TEXT} (mm)":
                mean_monthly_total.values,
            "Anomaly (%)":
                anomaly_percent.values
        })
        
        plot_table = plot_table.round(2)
        
        st.dataframe(
            plot_table,
            use_container_width=True,
            hide_index=True
        )
        
        csv = (
            plot_table
            .to_csv(index=False)
            .encode("utf-8")
        )
        
        st.download_button(
            "📥 Download Table CSV",
            data=csv,
            file_name=(
                f"{selected_station}_monthly_rainfall_"
                f"{target_year}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_monthly_rainfall_table_"
                f"{selected_station}_{target_year}"
            )
        )
        
        plt.close(fig)
    # ========================================================
    # TAB 2 HEATMAP
        # ========================================================
    with tabs[1]:
        st.subheader(
            f"Monthly Total Rainfall Heatmap "
            f"{YEAR_RANGE_TEXT}"
        )

        heatmap_data = (
            yearly_monthly_total
            .reindex(columns=months)
        )

        fig, ax = plt.subplots(
            figsize=(14, 8)
        )

        bg_color = BG_COLOR

        fig.patch.set_facecolor(
            bg_color
        )

        ax.set_facecolor(
            bg_color
        )

        plot_data = heatmap_data.copy()

        valid_values = plot_data.values[
            ~pd.isna(
                plot_data.values
            )
        ]

        if len(valid_values) > 0:
            vmin = valid_values.min()
            vmax = valid_values.max()

            if vmin == vmax:
                vmax = vmin + 1

        else:
            vmin = 0
            vmax = 1

        im = ax.imshow(
            plot_data.values,
            aspect="auto",
            cmap="YlGnBu",
            vmin=vmin,
            vmax=vmax
        )

        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months)
        ax.set_yticks(range(len(plot_data.index)))
        ax.set_yticklabels(plot_data.index.astype(str))

        # Grid
        ax.set_xticks(
            [
                i - 0.5
                for i in range(
                    len(months) + 1
                )
            ],
            minor=True
        )

        ax.set_yticks(
            [
                i - 0.5
                for i in range(
                    len(plot_data.index) + 1
                )
            ],
            minor=True
        )

        ax.grid(
            which="minor",
            color="white",
            linestyle="-",
            linewidth=1
        )

        ax.tick_params(
            which="minor",
            bottom=False,
            left=False
        )

        # Values
        for i in range(len(plot_data.index)):

            for j in range(len(months)):
                value = plot_data.iloc[i,j]

                if pd.notna(value):
                    ax.text(j,i,f"{value:.0f}",ha="center",va="center",fontsize=7)

                else:
                    ax.add_patch(
                        plt.Rectangle((j - 0.5,i - 0.5),
                            1,1,facecolor="lightgray",edgecolor="white",linewidth=1)
                    )

                    ax.text(j,i,"N.A.",ha="center",va="center",fontsize=7)

        cbar = fig.colorbar(im,ax=ax)
        cbar.set_label("Total Rainfall (mm)",fontsize=11)

        ax.set_title(
            f"{file_name}\n"
            f"Monthly Total Rainfall Heatmap, "
            f"{YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel("Month",fontsize=12)
        ax.set_ylabel("Year",fontsize=12)
        
        plt.tight_layout()

        st.pyplot(fig,use_container_width=True)

        img_buffer = io.BytesIO()
        
        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        img_buffer.seek(0)
        
        st.download_button(
            "📥 Download Plot PNG",
            data=img_buffer.getvalue(),
            file_name=f"{selected_station}_target_year_{target_year}.png",
            mime="image/png",
            key=f"download_heatmap_{selected_station}_{target_year}"
        )

        # ========================================================
        # TABLE DATA
        # ========================================================
        
        heatmap_table = (
            heatmap_data
            .reset_index()
        )
        
        heatmap_table = heatmap_table.round(2)
        
        st.dataframe(
            heatmap_table,
            use_container_width=True,
            hide_index=True
        )
        
        csv = (
            heatmap_table
            .to_csv(index=False)
            .encode("utf-8")
        )
        
        st.download_button(
            "📥 Download Table CSV",
            data=csv,
            file_name=(
                f"{selected_station}_rainfall_heatmap_"
                f"{YEAR_RANGE_TEXT}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_heatmap_table_"
                f"{selected_station}_{YEAR_RANGE_TEXT}"
            )
        )
        
        plt.close(fig)
    # ========================================================
    # TAB 3
    # ANOMALY
    # ========================================================
    with tabs[2]:

        st.subheader(
            f"Rainfall Anomaly {target_year} "
            f"Relative to Mean {YEAR_RANGE_TEXT}"
        )

        fig, ax = plt.subplots(figsize=(14, 8))

        bg_color = BG_COLOR

        fig.patch.set_facecolor(bg_color)

        ax.set_facecolor(bg_color)

        anomaly_colors = []

        for value in anomaly_percent.values:
            if pd.isna(value):
                anomaly_colors.append("lightgray")

            elif value >= 0:
                anomaly_colors.append("steelblue")

            else:
                anomaly_colors.append("darkorange")

        bars = ax.bar(x,anomaly_percent.values,width=0.60,color=anomaly_colors,edgecolor="black",linewidth=0.8)

        ax.axhline(0,color="black",linewidth=1)

        for bar, value in zip(bars,anomaly_percent.values):

            if pd.notna(value):
                if value >= 0:
                    offset = 4
                    vertical = "bottom"

                else:
                    offset = -12
                    vertical = "top"

                ax.annotate(f"{value:.1f}%",(bar.get_x()+ bar.get_width() / 2,value),
                    xytext=(0, offset),
                    textcoords="offset points",
                    ha="center",
                    va=vertical,
                    fontsize=8
                )

        ax.set_title(
            f"{file_name}\n"
            f"Rainfall Anomaly {target_year} "
            f"Relative to Mean {YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel("Month",fontsize=12)
        ax.set_ylabel("Anomaly (%)",fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(months)
        ax.grid(True,axis="y",linestyle="--",alpha=0.4)

        plt.tight_layout()

        st.pyplot(fig,use_container_width=True)

        img_buffer = io.BytesIO()
        
        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        img_buffer.seek(0)
        
        st.download_button(
            "📥 Download Plot PNG",
            data=img_buffer.getvalue(),
            file_name=f"{selected_station}_target_year_{target_year}.png",
            mime="image/png",
            key=f"download_anomaly_{selected_station}_{target_year}"
        )
        # ========================================================
        # TABLE DATA
        # ========================================================
        
        anomaly_table = pd.DataFrame({
            "Month": months,
            f"Total Rainfall {target_year} (mm)":
                rainfall_target.values,
            f"Mean Rainfall {YEAR_RANGE_TEXT} (mm)":
                mean_monthly_total.values,
            "Anomaly (%)":
                anomaly_percent.values
        })
        
        anomaly_table = anomaly_table.round(2)
        
        st.dataframe(
            anomaly_table,
            use_container_width=True,
            hide_index=True
        )
        
        csv = (
            anomaly_table
            .to_csv(index=False)
            .encode("utf-8")
        )
        
        st.download_button(
            "📥 Download Table CSV",
            data=csv,
            file_name=(
                f"{selected_station}_rainfall_anomaly_"
                f"{target_year}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_anomaly_table_"
                f"{selected_station}_{target_year}"
            )
        )
        
        plt.close(fig)
    # ========================================================
    # TAB 4
    # STATISTICS
    # ========================================================
    with tabs[3]:

        st.subheader("📋 Rainfall Statistical Analysis")

        display_table = (analysis_table.copy())
        numeric_columns = (display_table.columns[
                display_table.columns != "Month"
            ])

        for column in numeric_columns:
            display_table[column] = pd.to_numeric(
                display_table[column],
                errors="coerce"
            ).round(2)

        st.dataframe(display_table,use_container_width=True,hide_index=True)
        csv = (
            analysis_table
            .round(2)
            .to_csv()
            .encode("utf-8")
        )
        
        st.download_button(
            "📥 Download Table CSV",
            data=csv,
            file_name=f"{selected_station}_analysis_{target_year}.csv",
            mime="text/csv",
            key=f"download_statistics_{selected_station}_{target_year}"
        )
    # ========================================================
    # TAB 5
    # MAX DAILY RAINFALL
    # ========================================================
    with tabs[4]:

        st.subheader(
            f"Maximum Daily Rainfall by Month - "
            f"{target_year}"
        )

        fig, ax = plt.subplots(figsize=(14, 8))
        bg_color = BG_COLOR
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        bars = ax.bar(
            x,
            max_daily,
            width=0.60,
            color=st.session_state.max_daily_color,
            edgecolor="black",
            linewidth=0.8
        )

        for bar, value in zip(bars,max_daily):

            if pd.notna(value):
                ax.annotate(f"{value:.1f}",
                    (
                        bar.get_x()
                        + bar.get_width() / 2,
                        value
                    ),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    fontsize=10,
                    fontweight="bold"
                )

        ax.set_title(
            f"{file_name}\n"
            f"Maximum Daily Rainfall by Month - "
            f"{target_year}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel("Month",fontsize=12)
        ax.set_ylabel("Maximum Daily Rainfall (mm)",fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(months)

        ax.grid(True,axis="y",linestyle="--",alpha=0.4)

        plt.tight_layout()

        st.pyplot(fig,use_container_width=True)

        img_buffer = io.BytesIO()

        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        img_buffer.seek(0)
        
        st.download_button(
            "📥 Download Plot PNG",
            data=img_buffer.getvalue(),
            file_name=f"{selected_station}_target_year_{target_year}.png",
            mime="image/png",
            key=f"download_Max_rainfall_{selected_station}_{target_year}"
        )
        # ========================================================
        # TABLE DATA
        # ========================================================
        
        max_daily_table = pd.DataFrame({
            "Month": months,
            "Maximum Daily Rainfall (mm)": list(max_daily)
        })
        
        max_daily_table = max_daily_table.round(2)
        
        st.dataframe(
            max_daily_table,
            use_container_width=True,
            hide_index=True
        )
        
        csv = (
            max_daily_table
            .to_csv(index=False)
            .encode("utf-8")
        )
        
        st.download_button(
            "📥 Download Table CSV",
            data=csv,
            file_name=(
                f"{selected_station}_maximum_daily_rainfall_"
                f"{target_year}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_max_daily_table_"
                f"{selected_station}_{target_year}"
            )
        )

        plt.close(fig)
    # ========================================================
    # TAB 6
    # WET DAYS
    # ========================================================
    with tabs[5]:

        st.subheader(
            f"Number of Wet Days "
            f"{target_year}"
        )

        fig, ax = plt.subplots(figsize=(14, 8))
        bg_color = BG_COLOR

        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        bars = ax.bar(x,wet_days,width=0.60,color="steelblue",edgecolor="black",linewidth=0.8)

        for bar, value in zip(bars,wet_days):

            if pd.notna(value):
                ax.annotate(
                    f"{int(value)}",
                    (
                        bar.get_x()
                        + bar.get_width() / 2,
                        value
                    ),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    fontsize=10,
                    fontweight="bold"
                )

        ax.set_title(
            f"{file_name}\n"
            f"Number of Wet Days "
            f"{target_year}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel("Month",fontsize=12)
        ax.set_ylabel("Number of Wet Days",fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(months)

        ax.grid(True,axis="y",linestyle="--",alpha=0.4)

        plt.tight_layout()

        st.pyplot(fig,use_container_width=True)

        img_buffer = io.BytesIO()
        
        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        img_buffer.seek(0)
        
        st.download_button(
            "📥 Download Plot PNG",
            data=img_buffer.getvalue(),
            file_name=f"{selected_station}_target_year_{target_year}.png",
            mime="image/png",
            key=f"download_Wet_days_{selected_station}_{target_year}"
        )
        # ========================================================
        # TABLE DATA
        # ========================================================
        
        wet_days_table = pd.DataFrame({
            "Month": months,
            "Number of Wet Days": list(wet_days)
        })
        
        st.dataframe(
            wet_days_table,
            use_container_width=True,
            hide_index=True
        )
        
        csv = (
            wet_days_table
            .to_csv(index=False)
            .encode("utf-8")
        )
        
        st.download_button(
            "📥 Download Table CSV",
            data=csv,
            file_name=(
                f"{selected_station}_wet_days_"
                f"{target_year}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_wet_days_table_"
                f"{selected_station}_{target_year}"
            )
        )
        
        plt.close(fig)
    # ========================================================
    # TAB 7
    # STANDARD DEVIATION
    # ========================================================
    with tabs[6]:

        st.subheader(f"Daily Rainfall Standard Deviation - {target_year}")

        fig, ax = plt.subplots(figsize=(14, 8))
        bg_color = BG_COLOR

        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        bars = ax.bar(x,std_daily,width=0.60,color="purple",edgecolor="black",linewidth=0.8)

        for bar, value in zip(bars,std_daily):

            if pd.notna(value):
                ax.annotate(
                    f"{value:.1f}",
                    (
                        bar.get_x()
                        + bar.get_width() / 2,
                        value
                    ),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    fontsize=10,
                    fontweight="bold"
                )

        ax.set_title(
            f"{file_name}\n"
            f"Daily Rainfall Standard Deviation - "
            f"{target_year}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel("Month",fontsize=12)
        ax.set_ylabel("Standard Deviation (mm)",fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(months)

        ax.grid(True,axis="y",linestyle="--",alpha=0.4)

        plt.tight_layout()

        st.pyplot(fig,use_container_width=True)

        img_buffer = io.BytesIO()
        
        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        img_buffer.seek(0)
        
        st.download_button(
            "📥 Download Plot PNG",
            data=img_buffer.getvalue(),
            file_name=f"{selected_station}_target_year_{target_year}.png",
            mime="image/png",
            key=f"download_standard_deviation_{selected_station}_{target_year}"
        )
        # ========================================================
        # TABLE DATA
        # ========================================================
        
        std_table = pd.DataFrame({
            "Month": months,
            "Standard Deviation (mm)": list(std_daily)
        })
        
        std_table = std_table.round(2)
        
        st.dataframe(
            std_table,
            use_container_width=True,
            hide_index=True
        )
        
        csv = (
            std_table
            .to_csv(index=False)
            .encode("utf-8")
        )
        
        st.download_button(
            "📥 Download Table CSV",
            data=csv,
            file_name=(
                f"{selected_station}_standard_deviation_"
                f"{target_year}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_std_table_"
                f"{selected_station}_{target_year}"
            )
        )

        plt.close(fig)
    # ========================================================
    # TAB 8
    # RAINFALL CATEGORY DISTRIBUTION
    # ========================================================
    with tabs[7]:
    
        st.subheader(
            f"Daily Rainfall Category Distribution - {target_year}"
        )
    
        # ----------------------------------------------------
        # GET DAILY DATA INCLUDING 0.0 MM
        # ----------------------------------------------------
        category_data = (
            target_data[months]
            .stack()
        )
    
        # Remove N.A. and keep valid rainfall >= 0
        category_data = category_data[
            category_data.notna()
            &
            (category_data >= 0)
        ]
    
        if len(category_data) > 0:
    
            # ------------------------------------------------
            # CATEGORY LABELS
            # ------------------------------------------------
            category_labels = [
                "No Rain\n(0.0 mm)",
                "Slight Rain\n(1.0–10.0 mm)",
                "Moderate Rain\n(>10.0–30.0 mm)",
                "Heavy Rain\n(>30.0–60.0 mm)",
                "Very Heavy Rain\n(>60 mm)"
            ]
    
            # ------------------------------------------------
            # CATEGORY VALUES
            # ------------------------------------------------
            category_values = [
                # NO RAIN
                (category_data == 0).sum(),
                # LIGHT RAIN
                ((category_data >= 1)&(category_data <= 10)).sum(),
                # MODERATE RAIN
                ((category_data > 10)&(category_data <= 30)).sum(),
                # HEAVY RAIN
                ((category_data > 30)&(category_data <= 60)).sum(),
                # VERY HEAVY RAIN
                (category_data > 60).sum()
            ]
    
            # ------------------------------------------------
            # PLOT
            # ------------------------------------------------
            fig, ax = plt.subplots(figsize=(14, 8))
            
            bg_color = BG_COLOR
    
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
    
            x = np.arange(
                len(category_labels)
            )
    
            bars = ax.bar(
                x,
                category_values,
                edgecolor="black",
                linewidth=0.8
            )
    
            # ------------------------------------------------
            # VALUE LABEL
            # ------------------------------------------------
            for bar, value in zip(
                bars,
                category_values
            ):
    
                ax.annotate(
                    f"{value}",
                    (
                        bar.get_x()
                        + bar.get_width() / 2,
                        value
                    ),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold"
                )
    
            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------
            ax.set_title(
                f"{file_name}\n"
                f"Rainfall Data Category Distribution - "
                f"{target_year}",
                fontsize=16,
                fontweight="bold"
            )
    
            ax.set_xlabel("Rainfall Data Category",fontsize=12)
            ax.set_ylabel("Number of Days",fontsize=12)
            ax.set_xticks(x)
            ax.set_xticklabels(category_labels)
    
            ax.grid(
                True,
                axis="y",
                linestyle="--",
                alpha=0.4
            )
    
            plt.tight_layout()
    
            st.pyplot(fig,use_container_width=True)
    
            # ------------------------------------------------
            # DOWNLOAD PNG
            # ------------------------------------------------
            img_buffer = io.BytesIO()
    
            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )
    
            img_buffer.seek(0)
    
            st.download_button(
                "📥 Download Plot PNG",
                data=img_buffer.getvalue(),
                file_name=(
                    f"{selected_station}_rainfall_category_"
                    f"{target_year}.png"
                ),
                mime="image/png",
                key=(
                    f"download_Histogram_"
                    f"{selected_station}_{target_year}"
                )
            )
            # ========================================================
            # TABLE DATA
            # ========================================================
            
            category_bar_table = pd.DataFrame({
                "Rainfall Category": category_labels,
                "Number of Days": category_values
            })
            
            st.dataframe(
                category_bar_table,
                use_container_width=True,
                hide_index=True
            )
            
            csv = (
                category_bar_table
                .to_csv(index=False)
                .encode("utf-8")
            )
            
            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_rainfall_category_"
                    f"{target_year}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_category_bar_table_"
                    f"{selected_station}_{target_year}"
                )
            )
            plt.close(fig)
    
        else:
    
            st.warning("Tiada data hujan sah untuk menghasilkan graf.")
    # ========================================================
    # TAB 9
    # PIE CHART
    # ========================================================
    with tabs[8]:
    
        st.subheader(
            f"Percentage of Wet Days by Rainfall Category - "
            f"{target_year}"
        )
    
        # ====================================================
        # DAILY RAINFALL DATA
        # ====================================================
    
        category_data = (
            target_data[months]
            .stack()
        )
    
        # Buang N.A. dan 0.0 mm
        # Hanya ambil hari hujan >= 1.0 mm
        category_data = category_data[
            category_data.notna()
            &
            (category_data >= 1.0)
        ]
    
        # ====================================================
        # RAINFALL CATEGORY
        # ====================================================
    
        pie_labels = [
            "Slight Rain\n(1.0–10.0 mm)",
            "Moderate Rain\n(>10.0–30.0 mm)",
            "Heavy Rain\n(>30.0–60.0 mm)",
            "Very Heavy Rain\n(>60 mm)"
        ]
    
        pie_values = [
            (
                (category_data >= 1)
                &
                (category_data <= 10)
            ).sum(),
    
            (
                (category_data > 10)
                &
                (category_data <= 30)
            ).sum(),
    
            (
                (category_data > 30)
                &
                (category_data <= 60)
            ).sum(),
    
            (
                category_data > 60
            ).sum()
        ]
    
        # ====================================================
        # CHECK DATA
        # ====================================================
    
        if sum(pie_values) > 0:
    
            # =================================================
            # PIE COLORS
            # =================================================
    
            pie_colors = [
                "green",     # Slight Rain
                "yellow",    # Moderate Rain
                "orange",    # Heavy Rain
                "red"        # Very Heavy Rain
            ]
    
            # =================================================
            # CREATE FIGURE
            # =================================================
    
            fig, ax = plt.subplots(
                figsize=(10, 8)
            )
    
            bg_color = BG_COLOR
    
            fig.patch.set_facecolor(
                bg_color
            )
    
            ax.set_facecolor(
                bg_color
            )
    
            # =================================================
            # PIE CHART
            # =================================================
    
            wedges, texts, autotexts = ax.pie(
                pie_values,
                labels=pie_labels,
                colors=pie_colors,
                autopct="%1.1f%%",
                startangle=90,
                counterclock=False,
                wedgeprops={
                    "edgecolor": "black",
                    "linewidth": 0.8
                }
            )
    
            # =================================================
            # PERCENTAGE LABEL
            # =================================================
    
            for autotext in autotexts:
    
                autotext.set_fontsize(
                    11
                )
    
                autotext.set_fontweight(
                    "bold"
                )
    
            # =================================================
            # TITLE
            # =================================================
    
            ax.set_title(
                f"{file_name}\n"
                f"Percentage of Wet Days by Rainfall "
                f"Category - {target_year}",
                fontsize=16,
                fontweight="bold"
            )
    
            plt.tight_layout()
    
            # =================================================
            # DISPLAY
            # =================================================
    
            st.pyplot(
                fig,
                use_container_width=True
            )
    
            # =================================================
            # DOWNLOAD PNG
            # =================================================
    
            img_buffer = io.BytesIO()
    
            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )
    
            img_buffer.seek(0)
    
            st.download_button(
                "📥 Download Plot PNG",
                data=img_buffer.getvalue(),
                file_name=(
                    f"{selected_station}_rainfall_category_"
                    f"{target_year}.png"
                ),
                mime="image/png",
                key=(
                    f"download_rainfall_category_"
                    f"{selected_station}_{target_year}"
                )
            )
    
            plt.close(fig)
    
            # =================================================
            # TABLE
            # =================================================
    
            total_wet_days = sum(
                pie_values
            )
    
            category_table = pd.DataFrame({
    
                "Rainfall Category":
                    pie_labels,
    
                "Number of Days":
                    pie_values,
    
                "Percentage (%)": [
                    (
                        count /
                        total_wet_days
                    ) * 100
                    for count in pie_values
                ]
            })
    
            category_table[
                "Percentage (%)"
            ] = (
                category_table[
                    "Percentage (%)"
                ].round(2)
            )
    
            # =================================================
            # DISPLAY TABLE
            # =================================================
    
            st.dataframe(
                category_table,
                use_container_width=True,
                hide_index=True
            )
    
            # =================================================
            # DOWNLOAD TABLE CSV
            # =================================================
    
            csv = (
                category_table
                .to_csv(index=False)
                .encode("utf-8")
            )
    
            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_rainfall_category_"
                    f"{target_year}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_rainfall_category_table_"
                    f"{selected_station}_{target_year}"
                )
            )
    
        else:
    
            st.warning(
                "Tiada data hujan ≥ 1.0 mm "
                "untuk menghasilkan pie chart."
            )
    # ========================================================
    # TAB 10
    # BOXPLOT
    # ========================================================
    with tabs[9]:
    
        st.subheader(f"Daily Rainfall Distribution by Month - {target_year}")
        # ----------------------------------------------------
        # Collect daily rainfall ≥ 0.1 mm for each month
        # ----------------------------------------------------
        boxplot_data = []
        boxplot_labels = []
    
        for month in months:
            month_index = (months.index(month) + 1)
    
            days_expected = calendar.monthrange(target_year,month_index)[1]
    
            raw_values = target_data[
                month
            ].iloc[:days_expected].copy()
    
            values = raw_values[
                raw_values.notna() &
                (raw_values >= WET_DAY_MIN)
            ]
    
            boxplot_data.append(values.tolist())
            boxplot_labels.append(month)
        # ----------------------------------------------------
        # Check whether data exists
        # ----------------------------------------------------
        if any(len(values) > 0 for values in boxplot_data):
    
            fig, ax = plt.subplots(figsize=(14, 8))
            bg_color = BG_COLOR
    
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            # ------------------------------------------------
            # Boxplot
            # ------------------------------------------------
            bp = ax.boxplot(
                boxplot_data,
                tick_labels=boxplot_labels,
                patch_artist=True,
                showmeans=True,
                meanline=False,
                showfliers=False
            )
            # ------------------------------------------------
            # INDIVIDUAL DATA POINTS - SIDE OF BOXPLOT
            # ------------------------------------------------
            for i, values in enumerate(boxplot_data, start=1):
            
                if len(values) > 0:
            
                    # Titik diletakkan di sebelah kanan box
                    x_points = np.random.normal(
                        i + 0.5,
                        0.025,
                        size=len(values)
                    )
            
                    ax.scatter(
                        x_points,
                        values,
                        s=25,
                        color="black",
                        alpha=0.55,
                        edgecolors="white",
                        linewidth=0.5,
                        zorder=3
                    )
            # ------------------------------------------------
            # Box colour
            # ------------------------------------------------
            for box in bp["boxes"]:
            
                box.set(
                    facecolor="#87CEEB",
                    edgecolor="black",
                    linewidth=1
                )
            # ------------------------------------------------
            # Box colour
            # ------------------------------------------------
            for box in bp["boxes"]:
    
                box.set(facecolor="#87CEEB",edgecolor="black",linewidth=1)
            # ------------------------------------------------
            # Median
            # ------------------------------------------------
            for median in bp["medians"]:
    
                median.set(color="red",linewidth=2)
            # ------------------------------------------------
            # Mean
            # ------------------------------------------------
            for mean in bp["means"]:
    
                mean.set(marker="o",markerfacecolor="black",markeredgecolor="black",markersize=5)
            # ------------------------------------------------
            # Whisker
            # ------------------------------------------------
            for whisker in bp["whiskers"]:
    
                whisker.set(color="black",linewidth=1)
            # ------------------------------------------------
            # Caps
            # ------------------------------------------------
            for cap in bp["caps"]:
    
                cap.set(color="black",linewidth=1)
            # ------------------------------------------------
            # Outliers
            # ------------------------------------------------
            for flier in bp["fliers"]:
    
                flier.set(
                    marker="o",
                    markerfacecolor="orange",
                    markeredgecolor="black",
                    markersize=5,
                    alpha=0.7
                )
            # ------------------------------------------------
            # Title
            # ------------------------------------------------
            ax.set_title(
                f"{file_name}\n"
                f"Daily Rainfall Distribution by Month - {target_year}",
                fontsize=16,
                fontweight="bold"
            )
    
            ax.set_xlabel("Month",fontsize=12)
            ax.set_ylabel("Daily Rainfall (mm)",fontsize=12)
            ax.grid(True,axis="y",linestyle="--",alpha=0.4)
    
            plt.tight_layout()
    
            st.pyplot(fig,use_container_width=True)

            img_buffer = io.BytesIO()
            
            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )
            
            img_buffer.seek(0)
            
            st.download_button(
                "📥 Download Plot PNG",
                data=img_buffer.getvalue(),
                file_name=f"{selected_station}_target_year_{target_year}.png",
                mime="image/png",
                key=f"download_boxplot_{selected_station}_{target_year}"
            )
            # ========================================================
            # BOXPLOT SUMMARY TABLE
            # ========================================================
            
            boxplot_summary = []
            
            for month, values in zip(
                months,
                boxplot_data
            ):
            
                if len(values) > 0:
            
                    values_array = np.array(values)
            
                    boxplot_summary.append({
                        "Month": month,
                        "Wet Days": len(values_array),
                        "Minimum (mm)": np.min(values_array),
                        "Q1 (mm)": np.percentile(
                            values_array,
                            25
                        ),
                        "Median (mm)": np.median(
                            values_array
                        ),
                        "Mean (mm)": np.mean(
                            values_array
                        ),
                        "Q3 (mm)": np.percentile(
                            values_array,
                            75
                        ),
                        "Maximum (mm)": np.max(
                            values_array
                        ),
                        "Standard Deviation (mm)": np.std(
                            values_array,
                            ddof=1
                        ) if len(values_array) > 1 else 0
                    })
            
                else:
            
                    boxplot_summary.append({
                        "Month": month,
                        "Wet Days": 0,
                        "Minimum (mm)": np.nan,
                        "Q1 (mm)": np.nan,
                        "Median (mm)": np.nan,
                        "Mean (mm)": np.nan,
                        "Q3 (mm)": np.nan,
                        "Maximum (mm)": np.nan,
                        "Standard Deviation (mm)": np.nan
                    })
            
            boxplot_table = pd.DataFrame(
                boxplot_summary
            ).round(2)
            
            st.dataframe(
                boxplot_table,
                use_container_width=True,
                hide_index=True
            )
            
            csv = (
                boxplot_table
                .to_csv(index=False)
                .encode("utf-8")
            )
            
            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=(
                    f"{selected_station}_boxplot_summary_"
                    f"{target_year}.csv"
                ),
                mime="text/csv",
                key=(
                    f"download_boxplot_table_"
                    f"{selected_station}_{target_year}"
                )
            )
            
            plt.close(fig)
    # ========================================================
    # TAB 11
    # QUALITY CONTROL
    # ========================================================
    with tabs[10]:

        st.subheader("⚠️ Quality Control")

        st.markdown(
            f"""
            **QC Rules**
            - `0.0 mm` = data sah
            - `≥ 0.1 mm` = wet day
            - `> {SUSPECT_RAINFALL:.0f} mm` = suspect
            - `> {EXTREME_RAINFALL:.0f} mm` = extreme
            - Negative rainfall/ N.A. = invalid / dibuang
            - Missing days `> {MAX_MISSING_DAYS}` = bulan ditolak
            - Missing berturut-turut `> {MAX_CONSECUTIVE_MISSING}` = bulan ditolak
            """
        )

        qc_tabs = st.tabs([
            "⚠️ Suspect",
            "🚨 Extreme",
            "📅 Missing Count",
            "🔢 Valid Count",
            "🔁 Consecutive Missing",
            "📋 QC Status"
        ])
        # ----------------------------------------------------
        # SUSPECT
        # ----------------------------------------------------
        with qc_tabs[0]:
            st.write(
                f"Jumlah suspect rainfall > {SUSPECT_RAINFALL:.0f} mm: **{len(suspect_df)}**")

            if len(suspect_df) > 0:
                st.dataframe(suspect_df,use_container_width=True,hide_index=True)
                csv = (
                    analysis_table
                    .round(2)
                    .to_csv()
                    .encode("utf-8")
                )
                
                st.download_button(
                    "📥 Download Table CSV",
                    data=csv,
                    file_name=f"{selected_station}_analysis_{target_year}.csv",
                    mime="text/csv",
                    key=f"download_suspect_table_{selected_station}_{target_year}"
                )
            else:
                st.success("Tiada rainfall suspect dikesan.")
        # ----------------------------------------------------
        # EXTREME
        # ----------------------------------------------------
        with qc_tabs[1]:

            st.write(
                f"Jumlah extreme rainfall > {EXTREME_RAINFALL:.0f} mm: **{len(extreme_df)}**")

            if len(extreme_df) > 0:
                st.dataframe(extreme_df,use_container_width=True,hide_index=True)
                csv = (
                    analysis_table
                    .round(2)
                    .to_csv()
                    .encode("utf-8")
                )
                
                st.download_button(
                    "📥 Download Table CSV",
                    data=csv,
                    file_name=f"{selected_station}_analysis_{target_year}.csv",
                    mime="text/csv",
                    key=f"download_extreme_table_{selected_station}_{target_year}"
                )
            else:
                st.success("Tiada rainfall extreme dikesan.")
        # ----------------------------------------------------
        # MISSING
        # ----------------------------------------------------
        with qc_tabs[2]:
            st.dataframe(monthly_missing_count,use_container_width=True)
            csv = (
                analysis_table
                .round(2)
                .to_csv()
                .encode("utf-8")
            )
            
            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=f"{selected_station}_analysis_{target_year}.csv",
                mime="text/csv",
                key=f"download_missing_data_table_{selected_station}_{target_year}"
            )
        # ----------------------------------------------------
        # VALID
        # ----------------------------------------------------
        with qc_tabs[3]:
            st.dataframe(monthly_valid_count,use_container_width=True)
            csv = (
                analysis_table
                .round(2)
                .to_csv()
                .encode("utf-8")
            )
            
            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=f"{selected_station}_analysis_{target_year}.csv",
                mime="text/csv",
                key=f"download_valid_data_table_{selected_station}_{target_year}"
            )
        # ----------------------------------------------------
        # CONSECUTIVE
        # ----------------------------------------------------
        with qc_tabs[4]:
            st.dataframe(monthly_max_consecutive_missing,use_container_width=True)
            csv = (
                analysis_table
                .round(2)
                .to_csv()
                .encode("utf-8")
            )
            
            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=f"{selected_station}_analysis_{target_year}.csv",
                mime="text/csv",
                key=f"download_consecutive_table_{selected_station}_{target_year}"
            )
        # ----------------------------------------------------
        # QC STATUS
        # ----------------------------------------------------
        with qc_tabs[5]:
            st.dataframe(monthly_qc_status,use_container_width=True)
            csv = (
                analysis_table
                .round(2)
                .to_csv()
                .encode("utf-8")
            )
            
            st.download_button(
                "📥 Download Table CSV",
                data=csv,
                file_name=f"{selected_station}_analysis_{target_year}.csv",
                mime="text/csv",
                key=f"download_qc_status_table_{selected_station}_{target_year}"
            )
# ============================================================
# MAIN TAB 2 - ALL YEARS
# ============================================================
with main_tabs[1]:

    st.header(f"📊 All Years Rainfall Analysis {YEAR_RANGE_TEXT}")
    # --------------------------------------------------------
    # SELECT STATION
    # --------------------------------------------------------
    yearly_result = next(
        result
        for result in successful_results
        if result["file_name"] == selected_station
    )
    
    file_name = yearly_result["file_name"]

    yearly_monthly_total = (yearly_result["yearly_monthly_total"].reindex(columns=months))
    # --------------------------------------------------------
    # ALL YEARS TABS
    # --------------------------------------------------------
    all_year_tabs = st.tabs([
        "📊 Yearly Rainfall",
        "🔥 Heatmap",
        "📦 Boxplot",
        "📊 Histogram",
        "🥧 Rainfall Category",
        "📉 Anomaly",
        "📋 Yearly Statistics"
    ])
    # ========================================================
    # TAB 1 - YEARLY RAINFALL
    # ========================================================

    with all_year_tabs[0]:

        st.subheader(
            f"Annual Total Rainfall vs Mean Annual Rainfall "
            f"{YEAR_RANGE_TEXT}"
        )

        yearly_total = (
            yearly_monthly_total.sum(
                axis=1,
                skipna=True
            )
        )

        mean_annual_rainfall = yearly_total.mean()

        x_year = np.arange(
            len(yearly_total)
        )

        fig, ax = plt.subplots(
            figsize=(14, 8)
        )

        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)

        bars = ax.bar(
            x_year,
            yearly_total.values,
            width=0.60,
            color="steelblue",
            edgecolor="black",
            linewidth=0.8,
            label="Annual Total Rainfall"
        )

        for bar, value in zip(
            bars,
            yearly_total.values
        ):

            if pd.notna(value):

                ax.annotate(
                    f"{value:.1f}",
                    (
                        bar.get_x()
                        + bar.get_width() / 2,
                        value
                    ),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    fontsize=9,
                    fontweight="bold"
                )

        ax.axhline(
            mean_annual_rainfall,
            color=LINE_COLOR,
            linewidth=2.5,
            linestyle="--",
            label=(
                f"Mean Annual Rainfall "
                f"({mean_annual_rainfall:.1f} mm)"
            )
        )

        ax.set_title(
            f"{file_name}\n"
            f"Annual Total Rainfall vs Mean Annual Rainfall "
            f"{YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel(
            "Year",
            fontsize=12
        )

        ax.set_ylabel(
            "Total Rainfall (mm)",
            fontsize=12
        )

        ax.set_xticks(x_year)

        ax.set_xticklabels(
            yearly_total.index.astype(str)
        )

        ax.grid(
            True,
            axis="y",
            linestyle="--",
            alpha=0.4
        )

        ax.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left"
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )

        img_buffer = io.BytesIO()
        
        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        img_buffer.seek(0)
        
        st.download_button(
            "📥 Download Yearly Rainfall Plot",
            data=img_buffer.getvalue(),
            file_name=f"{file_name}_yearly_rainfall_{YEAR_RANGE_TEXT}.png",
            mime="image/png",
            key=f"download_yearly_plot_{file_name}"
        )

        plt.close(fig)

    # ========================================================
    # TAB 2 - HEATMAP
    # ========================================================

    with all_year_tabs[1]:

        st.subheader(
            f"Monthly Total Rainfall Heatmap "
            f"{YEAR_RANGE_TEXT}"
        )

        heatmap_data = (
            yearly_monthly_total
            .reindex(columns=months)
        )

        fig, ax = plt.subplots(
            figsize=(14, 8)
        )

        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)

        plot_data = heatmap_data.copy()

        valid_values = plot_data.values[
            ~pd.isna(plot_data.values)
        ]

        if len(valid_values) > 0:

            vmin = valid_values.min()
            vmax = valid_values.max()

            if vmin == vmax:
                vmax = vmin + 1

        else:

            vmin = 0
            vmax = 1

        im = ax.imshow(
            plot_data.values,
            aspect="auto",
            cmap="YlGnBu",
            vmin=vmin,
            vmax=vmax
        )

        ax.set_xticks(
            range(len(months))
        )

        ax.set_xticklabels(months)

        ax.set_yticks(
            range(len(plot_data.index))
        )

        ax.set_yticklabels(
            plot_data.index.astype(str)
        )

        for i in range(
            len(plot_data.index)
        ):

            for j in range(
                len(months)
            ):

                value = plot_data.iloc[i, j]

                if pd.notna(value):

                    ax.text(
                        j,
                        i,
                        f"{value:.0f}",
                        ha="center",
                        va="center",
                        fontsize=7
                    )

                else:

                    ax.text(
                        j,
                        i,
                        "N.A.",
                        ha="center",
                        va="center",
                        fontsize=7
                    )

        cbar = fig.colorbar(
            im,
            ax=ax
        )

        cbar.set_label(
            "Total Rainfall (mm)"
        )

        ax.set_title(
            f"{file_name}\n"
            f"Monthly Total Rainfall Heatmap "
            f"{YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )

        ax.set_xlabel("Month")
        ax.set_ylabel("Year")

        plt.tight_layout()

        st.pyplot(
            fig,
            use_container_width=True
        )
        img_buffer = io.BytesIO()
        
        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
        
        img_buffer.seek(0)
        
        st.download_button(
            "📥 Download Heatmap PNG",
            data=img_buffer.getvalue(),
            file_name=f"{file_name}_heatmap_{YEAR_RANGE_TEXT}.png",
            mime="image/png",
            key=f"download_heatmap_{file_name}"
        )

        plt.close(fig)
                
    # ========================================================
    # TAB 3 - BOXPLOT BY MONTH
    # ========================================================
    
    with all_year_tabs[2]:
    
        st.subheader(
            f"📦 Monthly Rainfall Distribution "
            f"{YEAR_RANGE_TEXT}"
        )
    
        st.caption(
            "Taburan jumlah hujan bagi setiap bulan "
            f"berdasarkan semua tahun {YEAR_RANGE_TEXT}."
        )
    
        # ----------------------------------------------------
        # PREPARE DATA
        # ----------------------------------------------------
    
        boxplot_data = []
    
        boxplot_labels = []
    
        for month in months:
    
            values = (
                yearly_monthly_total[month]
                .dropna()
                .values
            )
    
            boxplot_data.append(
                values
            )
    
            boxplot_labels.append(
                month
            )
    
        # ----------------------------------------------------
        # CHECK DATA
        # ----------------------------------------------------
    
        valid_boxplot_data = [
            values
            for values in boxplot_data
            if len(values) > 0
        ]
    
        if len(valid_boxplot_data) > 0:
    
            fig, ax = plt.subplots(
                figsize=(14, 8)
            )
    
            fig.patch.set_facecolor(
                BG_COLOR
            )
    
            ax.set_facecolor(
                BG_COLOR
            )
    
            # ------------------------------------------------
            # BOXPLOT
            # ------------------------------------------------
    
            ax.boxplot(
                boxplot_data,
                patch_artist=True,
                showmeans=True
            )
            # ------------------------------------------------
            # INDIVIDUAL DATA POINTS - SIDE OF BOXPLOT
            # ------------------------------------------------
            for i, values in enumerate(boxplot_data, start=1):
            
                if len(values) > 0:
            
                    # Titik diletakkan di sebelah kanan box
                    x_points = np.random.normal(
                        i + 0.5,
                        0.025,
                        size=len(values)
                    )
            
                    ax.scatter(
                        x_points,
                        values,
                        s=25,
                        color="black",
                        alpha=0.55,
                        edgecolors="white",
                        linewidth=0.5,
                        zorder=3
                    )
            
            # ------------------------------------------------
            # X AXIS
            # ------------------------------------------------
    
            ax.set_xticks(
                np.arange(
                    1,
                    len(months) + 1
                )
            )
    
            ax.set_xticklabels(
                months
            )
    
            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------
    
            ax.set_title(
                f"{file_name}\n"
                f"Monthly Rainfall Distribution "
                f"{YEAR_RANGE_TEXT}",
                fontsize=16,
                fontweight="bold"
            )
    
            # ------------------------------------------------
            # LABELS
            # ------------------------------------------------
    
            ax.set_xlabel(
                "Month",
                fontsize=12
            )
    
            ax.set_ylabel(
                "Monthly Total Rainfall (mm)",
                fontsize=12
            )
    
            # ------------------------------------------------
            # GRID
            # ------------------------------------------------
    
            ax.grid(
                True,
                axis="y",
                linestyle="--",
                alpha=0.4
            )
    
            plt.tight_layout()
    
            st.pyplot(
                fig,
                use_container_width=True
            )
            img_buffer = io.BytesIO()
            
            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )
            
            img_buffer.seek(0)
            
            st.download_button(
                "📥 Download Heatmap PNG",
                data=img_buffer.getvalue(),
                file_name=f"{file_name}_heatmap_{YEAR_RANGE_TEXT}.png",
                mime="image/png",
                key=f"download_yearly_boxplot_{file_name}"
            )
            
            plt.close(fig)
    
        else:
    
            st.warning(
                "Tiada data yang mencukupi "
                "untuk menghasilkan boxplot."
            )
    # ========================================================
    # TAB 4 - HISTOGRAM BY RAINFALL CATEGORY
    # ========================================================
    
    with all_year_tabs[3]:
    
        st.subheader(
            f"📊 Daily Data Distribution "
            f"{YEAR_RANGE_TEXT}"
        )
    
        st.caption(
            "Taburan bilangan hari mengikut kategori hujan bagi semua tahun {YEAR_RANGE_TEXT}.")
    
        # ----------------------------------------------------
        # GET ALL DAILY VALUES
        # ----------------------------------------------------
    
        histogram_values = (
            yearly_result["all_daily"]
            [months]
            .stack()
        )
    
        histogram_values = histogram_values[
            histogram_values.notna()
            &
            (histogram_values >= VALID_MIN)
        ]
    
        # ----------------------------------------------------
        # CATEGORY LABELS
        # ----------------------------------------------------
    
        category_labels = [
            "No Rain (0.0 mm)",
            "Slight Rain (1.0–10.0 mm)",
            "Moderate Rain (>10.0–30.0 mm)",
            "Heavy Rain (>30.0–60.0 mm)",
            "Very Heavy Rain (>60 mm)"
        ]
    
        # ----------------------------------------------------
        # CATEGORY VALUES
        # ----------------------------------------------------
    
        category_values = [
    
            # NO RAIN
            (
                histogram_values == 0
            ).sum(),
    
            # SLIGHT RAIN
            (
                (histogram_values >= 1)
                &
                (histogram_values <= 10)
            ).sum(),
    
            # MODERATE RAIN
            (
                (histogram_values > 10)
                &
                (histogram_values <= 30)
            ).sum(),
    
            # HEAVY RAIN
            (
                (histogram_values > 30)
                &
                (histogram_values <= 60)
            ).sum(),
    
            # VERY HEAVY RAIN
            (
                histogram_values > 60
            ).sum()
        ]
    
        # ----------------------------------------------------
        # CHECK DATA
        # ----------------------------------------------------
    
        total_days = sum(category_values)
    
        if total_days > 0:
    
            fig, ax = plt.subplots(
                figsize=(14, 8)
            )
    
            fig.patch.set_facecolor(
                BG_COLOR
            )
    
            ax.set_facecolor(
                BG_COLOR
            )
    
            # ------------------------------------------------
            # BAR CHART
            # ------------------------------------------------
    
            x = np.arange(
                len(category_labels)
            )
    
            bars = ax.bar(
                x,
                category_values,
                width=0.65,
                color=[
                    "lightgray",
                    "skyblue",
                    "gold",
                    "orange",
                    "red"
                ],
                edgecolor="black",
                linewidth=0.8
            )
    
            # ------------------------------------------------
            # VALUE LABEL
            # ------------------------------------------------
    
            for bar, value in zip(
                bars,
                category_values
            ):
    
                ax.annotate(
                    f"{value:,}",
                    (
                        bar.get_x()
                        + bar.get_width() / 2,
                        value
                    ),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    fontsize=10,
                    fontweight="bold"
                )
    
            # ------------------------------------------------
            # GRAPH SETTINGS
            # ------------------------------------------------
    
            ax.set_title(
                f"{file_name}\n"
                f"Daily Data Distribution "
                f"{YEAR_RANGE_TEXT}",
                fontsize=16,
                fontweight="bold"
            )
    
            ax.set_xlabel(
                "Daily Data Category",
                fontsize=12
            )
    
            ax.set_ylabel(
                "Number of Days",
                fontsize=12
            )
    
            ax.set_xticks(x)
    
            ax.set_xticklabels(
                category_labels,
                rotation=15,
                ha="right"
            )
    
            ax.grid(
                True,
                axis="y",
                linestyle="--",
                alpha=0.4
            )
    
            plt.tight_layout()
    
            st.pyplot(
                fig,
                use_container_width=True
            )
    
            # ------------------------------------------------
            # DOWNLOAD PLOT
            # ------------------------------------------------
    
            img_buffer = io.BytesIO()
    
            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )
    
            img_buffer.seek(0)
    
            st.download_button(
                "📥 Download Histogram PNG",
                data=img_buffer.getvalue(),
                file_name=(
                    f"{file_name}_"
                    f"rainfall_category_histogram_"
                    f"{YEAR_RANGE_TEXT}.png"
                ),
                mime="image/png",
                key=(
                    f"download_yearly_histogram_"
                    f"{file_name}"
                )
            )
    
            plt.close(fig)
    
            # ------------------------------------------------
            # CATEGORY TABLE
            # ------------------------------------------------
    
            st.subheader(
                "📋 Daily Data Category Statistics"
            )
    
            category_table = pd.DataFrame({
    
                "Data Category":
                    category_labels,
    
                "Number of Days":
                    category_values,
    
                "Percentage (%)": [
                    (
                        value / total_days
                    ) * 100
                    for value in category_values
                ]
            })
    
            category_table[
                "Percentage (%)"
            ] = (
                category_table[
                    "Percentage (%)"
                ].round(2)
            )
    
            st.dataframe(
                category_table,
                use_container_width=True,
                hide_index=True
            )
    
        else:
    
            st.warning(
                "Tiada data hujan sah untuk menghasilkan histogram."
            )
    # ========================================================
    # TAB 5 - RAINFALL CATEGORY
    # ========================================================
    
    with all_year_tabs[4]:
    
        st.subheader(
            f"🥧 Rainfall Category Distribution "
            f"{YEAR_RANGE_TEXT}"
        )
    
        st.caption(
            "Taburan kategori hujan berdasarkan semua "
            f"data harian dalam {file_name} "
            f"bagi tempoh {YEAR_RANGE_TEXT}."
        )
    
        # ----------------------------------------------------
        # GET ALL DAILY VALUES
        # ----------------------------------------------------
    
        all_daily_values = (
            yearly_result["all_daily"]
            [months]
            .stack()
        )
    
        all_daily_values = all_daily_values[
            all_daily_values.notna()
            &
            (all_daily_values >= VALID_MIN)
        ]
    
        # ----------------------------------------------------
        # CATEGORY LABELS
        # ----------------------------------------------------
    
        category_labels = [
            "Slight Rain (1.0–10.0 mm)",
            "Moderate Rain (>10.0–30.0 mm)",
            "Heavy Rain (>30.0–60.0 mm)",
            "Very Heavy Rain (>60 mm)"
        ]
    
        # ----------------------------------------------------
        # CATEGORY VALUES
        # ----------------------------------------------------
    
        category_values = [    
            (
                (all_daily_values >= 1)
                &
                (all_daily_values <= 10)
            ).sum(),
    
            (
                (all_daily_values > 10)
                &
                (all_daily_values <= 30)
            ).sum(),
    
            (
                (all_daily_values > 30)
                &
                (all_daily_values <= 60)
            ).sum(),
    
            (
                all_daily_values > 60
            ).sum()
        ]
    
        total_days = sum(
            category_values
        )
    
        # ----------------------------------------------------
        # PIE CHART
        # ----------------------------------------------------
    
        if total_days > 0:
    
            fig, ax = plt.subplots(
                figsize=(9, 7)
            )
    
            fig.patch.set_facecolor(
                BG_COLOR
            )
    
            ax.set_facecolor(
                BG_COLOR
            )
    
            wedges, texts, autotexts = ax.pie(
                category_values,
                labels=category_labels,
                autopct="%1.1f%%",
                startangle=90,
                counterclock=False,
                wedgeprops={
                    "edgecolor": "black",
                    "linewidth": 0.8
                }
            )
    
            for autotext in autotexts:
    
                autotext.set_fontsize(
                    9
                )
    
                autotext.set_fontweight(
                    "bold"
                )
    
            ax.set_title(
                f"{file_name}\n"
                f"Rainfall Category Distribution "
                f"{YEAR_RANGE_TEXT}",
                fontsize=16,
                fontweight="bold"
            )
    
            plt.tight_layout()
    
            st.pyplot(
                fig,
                use_container_width=True
            )
            img_buffer = io.BytesIO()
            
            fig.savefig(
                img_buffer,
                format="png",
                dpi=300,
                bbox_inches="tight"
            )
            
            img_buffer.seek(0)
            
            st.download_button(
                "📥 Download Heatmap PNG",
                data=img_buffer.getvalue(),
                file_name=f"{file_name}_heatmap_{YEAR_RANGE_TEXT}.png",
                mime="image/png",
                key=f"download_yearly_rainfall_category_{file_name}"
            )

            plt.close(fig)
    
            # ------------------------------------------------
            # CATEGORY TABLE
            # ------------------------------------------------
    
            st.subheader(
                "📋 Rainfall Category Statistics"
            )
    
            category_table = pd.DataFrame({
    
                "Rainfall Category":
                    category_labels,
    
                "Number of Days":
                    category_values,
    
                "Percentage (%)":
                    [
                        (
                            value
                            / total_days
                        ) * 100
                        for value in category_values
                    ]
            })
    
            category_table[
                "Percentage (%)"
            ] = category_table[
                "Percentage (%)"
            ].round(2)
    
            st.dataframe(
                category_table,
                use_container_width=True,
                hide_index=True
            )
    
        else:
    
            st.warning(
                "Tiada data hujan sah untuk menghasilkan pie chart."
            )
    # ========================================================
    # TAB 6 - YEARLY ANOMALY
    # ========================================================
    
    with all_year_tabs[5]:
    
        st.subheader(
            f"📉 Annual Rainfall Anomaly "
            f"{YEAR_RANGE_TEXT}"
        )
    
        st.caption(
            "Anomali jumlah hujan tahunan berbanding "
            f"purata jumlah hujan tahunan bagi {YEAR_RANGE_TEXT}."
        )
    
        # ----------------------------------------------------
        # ANNUAL TOTAL
        # ----------------------------------------------------
    
        yearly_total = (
            yearly_monthly_total
            .sum(
                axis=1,
                skipna=True
            )
        )
    
        # ----------------------------------------------------
        # MEAN ANNUAL RAINFALL
        # ----------------------------------------------------
    
        mean_annual_rainfall = (
            yearly_total.mean(
                skipna=True
            )
        )
    
        # ----------------------------------------------------
        # ANOMALY %
        # ----------------------------------------------------
    
        if (
            pd.notna(mean_annual_rainfall)
            and
            mean_annual_rainfall != 0
        ):
    
            yearly_anomaly = (
                (
                    yearly_total
                    -
                    mean_annual_rainfall
                )
                /
                mean_annual_rainfall
            ) * 100
    
        else:
    
            yearly_anomaly = pd.Series(
                np.nan,
                index=yearly_total.index
            )
    
        # ----------------------------------------------------
        # X AXIS
        # ----------------------------------------------------
    
        x_year = np.arange(
            len(yearly_anomaly)
        )
    
        # ----------------------------------------------------
        # FIGURE
        # ----------------------------------------------------
    
        fig, ax = plt.subplots(
            figsize=(14, 8)
        )
    
        fig.patch.set_facecolor(
            BG_COLOR
        )
    
        ax.set_facecolor(
            BG_COLOR
        )
    
        # ----------------------------------------------------
        # BAR COLOUR
        # Positive = Above Mean
        # Negative = Below Mean
        # ----------------------------------------------------
    
        anomaly_colors = [
            "steelblue" if value >= 0
            else "darkorange"
            if pd.notna(value)
            else "lightgray"
            for value in yearly_anomaly.values
        ]
    
        bars = ax.bar(
            x_year,
            yearly_anomaly.values,
            width=0.60,
            color=anomaly_colors,
            edgecolor="black",
            linewidth=0.8
        )
    
        # ----------------------------------------------------
        # ZERO LINE
        # ----------------------------------------------------
    
        ax.axhline(
            0,
            color="black",
            linewidth=1
        )
    
        # ----------------------------------------------------
        # ANOMALY LABEL
        # ----------------------------------------------------
    
        for bar, value in zip(
            bars,
            yearly_anomaly.values
        ):
    
            if pd.notna(value):
    
                if value >= 0:
    
                    offset = 5
                    vertical = "bottom"
    
                else:
    
                    offset = -8
                    vertical = "top"
    
                ax.annotate(
                    f"{value:.1f}%",
                    (
                        bar.get_x()
                        + bar.get_width() / 2,
                        value
                    ),
                    xytext=(
                        0,
                        offset
                    ),
                    textcoords="offset points",
                    ha="center",
                    va=vertical,
                    fontsize=9,
                    fontweight="bold"
                )
    
        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------
    
        ax.set_title(
            f"{file_name}\n"
            f"Annual Rainfall Anomaly "
            f"{YEAR_RANGE_TEXT}",
            fontsize=16,
            fontweight="bold"
        )
    
        # ----------------------------------------------------
        # AXIS LABEL
        # ----------------------------------------------------
    
        ax.set_xlabel(
            "Year",
            fontsize=12
        )
    
        ax.set_ylabel(
            "Rainfall Anomaly (%)",
            fontsize=12
        )
    
        # ----------------------------------------------------
        # X TICKS
        # ----------------------------------------------------
    
        ax.set_xticks(
            x_year
        )
    
        ax.set_xticklabels(
            yearly_anomaly.index.astype(str)
        )
    
        # ----------------------------------------------------
        # GRID
        # ----------------------------------------------------
    
        ax.grid(
            True,
            axis="y",
            linestyle="--",
            alpha=0.4
        )
    
        plt.tight_layout()
    
        st.pyplot(
            fig,
            use_container_width=True
        )
    
        # ----------------------------------------------------
        # DOWNLOAD PLOT
        # ----------------------------------------------------
    
        img_buffer = io.BytesIO()
    
        fig.savefig(
            img_buffer,
            format="png",
            dpi=300,
            bbox_inches="tight"
        )
    
        img_buffer.seek(0)
    
        st.download_button(
            "📥 Download Anomaly Plot",
            data=img_buffer.getvalue(),
            file_name=(
                f"{file_name}_"
                f"annual_anomaly_{YEAR_RANGE_TEXT}.png"
            ),
            mime="image/png",
            key=(
                f"download_annual_anomaly_"
                f"{file_name}"
            )
        )
    
        plt.close(fig)
    
        # ----------------------------------------------------
        # ANOMALY TABLE
        # ----------------------------------------------------
    
        anomaly_table = pd.DataFrame({
    
            "Year":
                yearly_total.index,
    
            "Annual Total (mm)":
                yearly_total.values,
    
            "Mean Annual Rainfall (mm)":
                mean_annual_rainfall,
    
            "Anomaly (%)":
                yearly_anomaly.values
        })
    
        anomaly_table[
            "Annual Total (mm)"
        ] = anomaly_table[
            "Annual Total (mm)"
        ].round(2)
    
        anomaly_table[
            "Mean Annual Rainfall (mm)"
        ] = anomaly_table[
            "Mean Annual Rainfall (mm)"
        ].round(2)
    
        anomaly_table[
            "Anomaly (%)"
        ] = anomaly_table[
            "Anomaly (%)"
        ].round(2)
    
        st.subheader(
            "📋 Annual Rainfall Anomaly Statistics"
        )
    
        st.dataframe(
            anomaly_table,
            use_container_width=True,
            hide_index=True
        )
    
        # ----------------------------------------------------
        # DOWNLOAD TABLE
        # ----------------------------------------------------
    
        csv = (
            anomaly_table
            .to_csv(index=False)
            .encode("utf-8")
        )
    
        st.download_button(
            "📥 Download Anomaly Table CSV",
            data=csv,
            file_name=(
                f"{file_name}_"
                f"annual_anomaly_{YEAR_RANGE_TEXT}.csv"
            ),
            mime="text/csv",
            key=(
                f"download_annual_anomaly_table_"
                f"{file_name}"
            )
        )
    # ========================================================
    # TAB 7 - YEARLY STATISTICS
    # ========================================================

    with all_year_tabs[6]:

        st.subheader(
            f"Yearly Rainfall Statistics "
            f"{YEAR_RANGE_TEXT}"
        )

        yearly_statistics = (
            yearly_monthly_total
            .reindex(columns=months)
            .copy()
        )

        yearly_statistics[
            "Annual Total (mm)"
        ] = yearly_statistics.sum(
            axis=1,
            skipna=True
        )

        yearly_statistics = (
            yearly_statistics
            .reset_index()
            .rename(
                columns={
                    "index": "Year"
                }
            )
        )

        st.dataframe(
            yearly_statistics.round(2),
            use_container_width=True,
            hide_index=True
        )
        csv = (
            yearly_statistics
            .round(2)
            .to_csv(
                index=False
            )
            .encode("utf-8")
        )
        
        st.download_button(
            "📥 Download Yearly Statistics CSV",
            data=csv,
            file_name=f"{file_name}_yearly_statistics_{YEAR_RANGE_TEXT}.csv",
            mime="text/csv",
            key=f"download_yearly_statistics_{file_name}"
        )
# ============================================================
# MAIN TAB 3
# STATION COMPARISON
# ============================================================
with main_tabs[2]:

    st.header(
        f"🔄 Station Comparison {YEAR_RANGE_TEXT}"
    )

    st.markdown(
        f"""
        Perbandingan jumlah, purata, anomaly dan kategori
        hujan bagi **2 atau lebih stesen** untuk tempoh
        **{YEAR_RANGE_TEXT}**.
        """
    )

    # ========================================================
    # SELECT STATIONS
    # ========================================================
    comparison_stations = st.multiselect(
        "📍 Select Stations to Compare",
        station_options,
        default=(
            station_options[:2]
            if len(station_options) >= 2
            else station_options
        ),
        key="comparison_stations"
    )

    if len(comparison_stations) < 2:

        st.warning(
            "⚠️ Sila pilih sekurang-kurangnya 2 stesen "
            "untuk membuat perbandingan."
        )

    else:

        # ====================================================
        # PREPARE COMPARISON DATA
        # ====================================================
        comparison_data = {}

        for station in comparison_stations:

            station_result = next(
                (
                    result
                    for result in successful_results
                    if result["file_name"] == station
                ),
                None
            )

            if station_result is None:
                continue

            yearly_data = (
                station_result["yearly_monthly_total"]
                .reindex(columns=months)
            )

            # ------------------------------------------------
            # TOTAL RAINFALL BY MONTH
            # ALL YEARS IN FILE
            # ------------------------------------------------
            monthly_total = (
                yearly_data
                .sum(
                    axis=0,
                    skipna=True
                )
                .reindex(months)
            )

            # ------------------------------------------------
            # MEAN RAINFALL BY MONTH
            # ALL YEARS IN FILE
            # ------------------------------------------------
            monthly_mean = (
                yearly_data
                .mean(
                    axis=0,
                    skipna=True
                )
                .reindex(months)
            )

            # ------------------------------------------------
            # ANOMALY
            # BASED ON MONTHLY MEAN VS
            # OVERALL 12-MONTH MEAN
            # ------------------------------------------------
            overall_mean = (
                monthly_mean
                .mean(skipna=True)
            )

            if (
                pd.notna(overall_mean)
                and overall_mean != 0
            ):

                anomaly = (
                    (
                        monthly_mean
                        - overall_mean
                    )
                    / overall_mean
                ) * 100

            else:

                anomaly = pd.Series(
                    np.nan,
                    index=months
                )

            # ------------------------------------------------
            # RAINFALL CATEGORY
            # ALL DAILY DATA
            # ------------------------------------------------
            all_daily = (
                station_result["all_daily"]
            )

            all_values = (
                all_daily[months]
                .stack()
            )

            all_values = all_values[
                all_values.notna()
                &
                (all_values >= VALID_MIN)
            ]

            category_values = [
                # SLIGHT RAIN
                (
                    (all_values >= 1)
                    &
                    (all_values <= 10)
                ).sum(),

                # MODERATE RAIN
                (
                    (all_values > 10)
                    &
                    (all_values <= 30)
                ).sum(),

                # HEAVY RAIN
                (
                    (all_values > 30)
                    &
                    (all_values <= 60)
                ).sum(),

                # Very Heavy RAIN
                (
                    all_values > 60
                ).sum()
            ]

            comparison_data[station] = {

                "total":
                    monthly_total,

                "mean":
                    monthly_mean,

                "anomaly":
                    anomaly,

                "category":
                    category_values
            }

        # ====================================================
        # CHECK DATA
        # ====================================================
        if len(comparison_data) < 2:

            st.warning(
                "⚠️ Data tidak mencukupi untuk "
                "membandingkan sekurang-kurangnya 2 stesen."
            )

        else:

            # =================================================
            # CATEGORY LABELS
            # =================================================
            category_labels = [
                "Slight Rain (1.0–10.0 mm)",
                "Moderate Rain (>10.0–30.0 mm)",
                "Heavy Rain (>30.0–60.0 mm)",
                "Very Heavy Rain (>60 mm)"
            ]

            # =================================================
            # COMPARISON TABS
            # =================================================
            comparison_tabs = st.tabs([
                "📊 Total & Mean Rainfall",
                "📉 Anomaly",
                "🥧 Rainfall Category"
            ])

            # =================================================
            # TAB 1
            # TOTAL + MEAN RAINFALL
            # BAR + LINE
            # =================================================
            with comparison_tabs[0]:
            
                st.subheader(
                    f"📊 Monthly Total & Mean Rainfall Comparison "
                    f"{YEAR_RANGE_TEXT}"
                )
            
                st.caption(
                    "Bar menunjukkan jumlah hujan bulanan, manakala "
                    "garisan menunjukkan purata hujan bulanan bagi "
                    f"setiap stesen berdasarkan {YEAR_RANGE_TEXT}."
                )
            
                fig, ax = plt.subplots(
                    figsize=(14, 8)
                )
            
                fig.patch.set_facecolor(BG_COLOR)
                ax.set_facecolor(BG_COLOR)
            
                # --------------------------------------------
                # X POSITION
                # --------------------------------------------
            
                x = np.arange(
                    len(months)
                )
            
                n_stations = len(
                    comparison_data
                )
            
                bar_width = (
                    0.8 / n_stations
                )
            
                # --------------------------------------------
                # COLOUR
                # --------------------------------------------
            
                station_colors = plt.cm.tab10(
                    np.linspace(
                        0,
                        1,
                        n_stations
                    )
                )
            
                legend_handles = []
            
                # --------------------------------------------
                # EACH STATION
                # --------------------------------------------
            
                for i, (station, color) in enumerate(
                    zip(
                        comparison_data,
                        station_colors
                    )
                ):
            
                    total_values = (
                        comparison_data[station]["total"]
                        .reindex(months)
                    )
            
                    mean_values = (
                        comparison_data[station]["mean"]
                        .reindex(months)
                    )
            
                    # ----------------------------------------
                    # BAR POSITION
                    # ----------------------------------------
            
                    offset = (
                        i
                        - (n_stations - 1) / 2
                    ) * bar_width
            
                    # ----------------------------------------
                    # TOTAL RAINFALL - BAR
                    # ----------------------------------------
            
                    bars = ax.bar(
                        x + offset,
                        total_values.values,
                        width=bar_width,
                        color=color,
                        alpha=0.65,
                        edgecolor="black",
                        linewidth=0.8
                    )
            
                    # ----------------------------------------
                    # MEAN RAINFALL - LINE
                    # ----------------------------------------
            
                    line, = ax.plot(
                        x,
                        mean_values.values,
                        color=color,
                        marker="o",
                        markersize=6,
                        linewidth=2.5,
                        linestyle="-"
                    )
            
                    # ----------------------------------------
                    # VALUE LABEL - TOTAL
                    # ----------------------------------------
            
                    for bar, value in zip(
                        bars,
                        total_values.values
                    ):
            
                        if pd.notna(value):
            
                            ax.annotate(
                                f"{value:.0f}",
                                (
                                    bar.get_x()
                                    + bar.get_width() / 2,
                                    value
                                ),
                                xytext=(0, 5),
                                textcoords="offset points",
                                ha="center",
                                va="bottom",
                                fontsize=7
                            )
            
                    # ----------------------------------------
                    # VALUE LABEL - MEAN
                    # ----------------------------------------
            
                    for xi, value in zip(
                        x,
                        mean_values.values
                    ):
            
                        if pd.notna(value):
            
                            ax.annotate(
                                f"{value:.1f}",
                                (
                                    xi,
                                    value
                                ),
                                xytext=(0, 8),
                                textcoords="offset points",
                                ha="center",
                                va="bottom",
                                fontsize=7,
                                fontweight="bold"
                            )
            
                    # ----------------------------------------
                    # LEGEND
                    # ----------------------------------------
            
                    legend_handles.append(
                        Patch(
                            facecolor=color,
                            edgecolor="black",
                            alpha=0.65,
                            label=f"{station} - Total"
                        )
                    )
            
                    legend_handles.append(
                        Line2D(
                            [0],
                            [0],
                            color=color,
                            marker="o",
                            linewidth=2.5,
                            label=f"{station} - Mean"
                        )
                    )
            
                # --------------------------------------------
                # GRAPH SETTINGS
                # --------------------------------------------
            
                ax.set_title(
                    f"Monthly Total & Mean Rainfall Comparison\n"
                    f"{YEAR_RANGE_TEXT}",
                    fontsize=16,
                    fontweight="bold"
                )
            
                ax.set_xlabel(
                    "Month",
                    fontsize=12
                )
            
                ax.set_ylabel(
                    "Rainfall (mm)",
                    fontsize=12
                )
            
                ax.set_xticks(
                    x
                )
            
                ax.set_xticklabels(
                    months
                )
            
                ax.grid(
                    True,
                    axis="y",
                    linestyle="--",
                    alpha=0.4
                )
            
                # --------------------------------------------
                # LEGEND
                # --------------------------------------------
            
                ax.legend(
                    handles=legend_handles,
                    title="Station",
                    bbox_to_anchor=(1.02, 1),
                    loc="upper left",
                    fontsize=9,
                    title_fontsize=10
                )
            
                plt.tight_layout()
            
                st.pyplot(
                    fig,
                    use_container_width=True
                )
            
                # --------------------------------------------
                # DOWNLOAD PLOT
                # --------------------------------------------
            
                img_buffer = io.BytesIO()
            
                fig.savefig(
                    img_buffer,
                    format="png",
                    dpi=300,
                    bbox_inches="tight"
                )
            
                img_buffer.seek(0)
            
                st.download_button(
                    "📥 Download Total & Mean Rainfall Plot",
                    data=img_buffer.getvalue(),
                    file_name=(
                        f"station_comparison_total_mean_"
                        f"{YEAR_RANGE_TEXT}.png"
                    ),
                    mime="image/png",
                    key="download_comparison_total_mean_plot"
                )
            
                plt.close(fig)
            
                # --------------------------------------------
                # TOTAL TABLE
                # --------------------------------------------
            
                st.subheader(
                    "📋 Monthly Total Rainfall"
                )
            
                total_table = pd.DataFrame(
                    {
                        station:
                        comparison_data[station]["total"]
                        .reindex(months)
            
                        for station in comparison_data
                    },
                    index=months
                )
            
                total_table.index.name = "Month"
            
                st.dataframe(
                    total_table.round(2),
                    use_container_width=True
                )
            
                csv_total = (
                    total_table
                    .round(2)
                    .to_csv()
                    .encode("utf-8")
                )
            
                st.download_button(
                    "📥 Download Total Rainfall Table CSV",
                    data=csv_total,
                    file_name=(
                        f"station_comparison_total_"
                        f"{YEAR_RANGE_TEXT}.csv"
                    ),
                    mime="text/csv",
                    key="download_comparison_total_table"
                )
            
                # --------------------------------------------
                # MEAN TABLE
                # --------------------------------------------
            
                st.subheader(
                    "📋 Mean Monthly Rainfall"
                )
            
                mean_table = pd.DataFrame(
                    {
                        station:
                        comparison_data[station]["mean"]
                        .reindex(months)
            
                        for station in comparison_data
                    },
                    index=months
                )
            
                mean_table.index.name = "Month"
            
                st.dataframe(
                    mean_table.round(2),
                    use_container_width=True
                )
            
                csv_mean = (
                    mean_table
                    .round(2)
                    .to_csv()
                    .encode("utf-8")
                )
            
                st.download_button(
                    "📥 Download Mean Rainfall Table CSV",
                    data=csv_mean,
                    file_name=(
                        f"station_comparison_mean_"
                        f"{YEAR_RANGE_TEXT}.csv"
                    ),
                    mime="text/csv",
                    key="download_comparison_mean_table"
                )
            # =================================================
            # TAB 2
            # ANOMALY - BAR
            # =================================================
            with comparison_tabs[1]:

                st.subheader(
                    f"📉 Monthly Rainfall Anomaly "
                    f"{YEAR_RANGE_TEXT}"
                )

                st.caption(
                    "Anomaly dikira berdasarkan perbezaan "
                    "purata hujan bulanan daripada purata "
                    "keseluruhan 12 bulan bagi setiap stesen."
                )

                fig, ax = plt.subplots(
                    figsize=(14, 8)
                )

                fig.patch.set_facecolor(BG_COLOR)
                ax.set_facecolor(BG_COLOR)

                # --------------------------------------------
                # BAR POSITION
                # --------------------------------------------
                x_anomaly = np.arange(
                    len(months)
                )

                n_stations = len(
                    comparison_data
                )

                bar_width = (
                    0.8 / n_stations
                )

                # --------------------------------------------
                # BARS
                # --------------------------------------------
                legend_handles = []

                for i, station in enumerate(
                    comparison_data
                ):

                    values = (
                        comparison_data[station]["anomaly"]
                        .reindex(months)
                    )

                    offset = (
                        i
                        - (n_stations - 1) / 2
                    ) * bar_width

                    bars = ax.bar(
                        x_anomaly + offset,
                        values.values,
                        width=bar_width,
                        edgecolor="black",
                        linewidth=0.8
                    )

                    # MANUAL LEGEND
                    if len(bars) > 0:

                        legend_handles.append(
                            Patch(
                                facecolor=(
                                    bars[0]
                                    .get_facecolor()
                                ),
                                edgecolor="black",
                                label=str(station)
                            )
                        )

                    # VALUE LABEL
                    for bar, value in zip(
                        bars,
                        values.values
                    ):

                        if pd.notna(value):

                            if value >= 0:

                                offset_text = 5
                                vertical = "bottom"

                            else:

                                offset_text = -12
                                vertical = "top"

                            ax.annotate(
                                f"{value:.1f}%",
                                (
                                    bar.get_x()
                                    + bar.get_width() / 2,
                                    value
                                ),
                                xytext=(
                                    0,
                                    offset_text
                                ),
                                textcoords="offset points",
                                ha="center",
                                va=vertical,
                                fontsize=8
                            )

                # --------------------------------------------
                # GRAPH SETTINGS
                # --------------------------------------------
                ax.axhline(
                    0,
                    color="black",
                    linewidth=1
                )

                ax.set_title(
                    f"Monthly Rainfall Anomaly Comparison\n"
                    f"{YEAR_RANGE_TEXT}",
                    fontsize=16,
                    fontweight="bold"
                )

                ax.set_xlabel(
                    "Month",
                    fontsize=12
                )

                ax.set_ylabel(
                    "Anomaly (%)",
                    fontsize=12
                )

                ax.set_xticks(x_anomaly)
                ax.set_xticklabels(months)

                ax.grid(
                    True,
                    axis="y",
                    linestyle="--",
                    alpha=0.4
                )

                # LEGEND
                ax.legend(
                    handles=legend_handles,
                    title="Station",
                    bbox_to_anchor=(1.02, 1),
                    loc="upper left"
                )

                plt.tight_layout()

                st.pyplot(
                    fig,
                    use_container_width=True
                )
                img_buffer = io.BytesIO()
                
                fig.savefig(
                    img_buffer,
                    format="png",
                    dpi=300,
                    bbox_inches="tight"
                )
                
                img_buffer.seek(0)
                
                st.download_button(
                    "📥 Download Anomaly Plot",
                    data=img_buffer.getvalue(),
                    file_name=f"station_comparison_anomaly_{YEAR_RANGE_TEXT}.png",
                    mime="image/png",
                    key="download_comparison_anomaly_plot"
                )
                plt.close(fig)

                # --------------------------------------------
                # TABLE
                # --------------------------------------------
                st.subheader(
                    "📋 Monthly Rainfall Anomaly"
                )

                anomaly_table = pd.DataFrame(
                    {
                        station:
                        comparison_data[station]["anomaly"]
                        .reindex(months)

                        for station
                        in comparison_data
                    },
                    index=months
                )

                anomaly_table.index.name = "Month"

                st.dataframe(
                    anomaly_table.round(2),
                    use_container_width=True
                )
                csv = (
                    anomaly_table
                    .round(2)
                    .to_csv()
                    .encode("utf-8")
                )
                
                st.download_button(
                    "📥 Download Anomaly Table CSV",
                    data=csv,
                    file_name=f"station_comparison_anomaly_{YEAR_RANGE_TEXT}.csv",
                    mime="text/csv",
                    key="download_comparison_anomaly_table"
                )
            # =================================================
            # TAB 3
            # RAINFALL CATEGORY - PIE
            # =================================================
            with comparison_tabs[2]:

                st.subheader(
                    f"🥧 Rainfall Category Comparison "
                    f"{YEAR_RANGE_TEXT}"
                )

                st.caption(
                    "Taburan kategori hujan berdasarkan "
                    "semua data harian dalam tempoh "
                    f"{YEAR_RANGE_TEXT}."
                )

                # --------------------------------------------
                # PIE CHART FOR EACH STATION
                # --------------------------------------------
                category_columns = st.columns(
                    len(comparison_data)
                )

                for col, station in zip(
                    category_columns,
                    comparison_data
                ):

                    with col:

                        st.markdown(
                            f"### 📍 {station}"
                        )

                        values = (
                            comparison_data[station]["category"]
                        )

                        total_days = sum(values)

                        if total_days > 0:

                            fig, ax = plt.subplots(
                                figsize=(7, 6)
                            )

                            fig.patch.set_facecolor(
                                BG_COLOR
                            )

                            ax.set_facecolor(
                                BG_COLOR
                            )

                            wedges, texts, autotexts = ax.pie(
                                values,
                                labels=category_labels,
                                autopct="%1.1f%%",
                                startangle=90,
                                counterclock=False,
                                wedgeprops={
                                    "edgecolor": "black",
                                    "linewidth": 0.8
                                }
                            )

                            for autotext in autotexts:

                                autotext.set_fontsize(9)

                                autotext.set_fontweight(
                                    "bold"
                                )

                            ax.set_title(
                                station,
                                fontsize=13,
                                fontweight="bold"
                            )

                            plt.tight_layout()

                            st.pyplot(
                                fig,
                                use_container_width=True
                            )
                            img_buffer = io.BytesIO()
                            
                            fig.savefig(
                                img_buffer,
                                format="png",
                                dpi=300,
                                bbox_inches="tight"
                            )
                            
                            img_buffer.seek(0)
                            
                            st.download_button(
                                f"📥 Download {station} Pie Chart",
                                data=img_buffer.getvalue(),
                                file_name=f"{station}_rainfall_category_{YEAR_RANGE_TEXT}.png",
                                mime="image/png",
                                key=f"download_category_plot_{station}"
                            )
                            plt.close(fig)

                        else:

                            st.warning(
                                "Tiada data hujan sah."
                            )
                            
                # --------------------------------------------
                # CATEGORY TABLE
                # --------------------------------------------
                category_comparison_table = pd.DataFrame(
                    {
                        station:
                        comparison_data[station]["category"]

                        for station
                        in comparison_data
                    },
                    index=category_labels
                )

                category_comparison_table.index.name = (
                    "Rainfall Category"
                )

                st.subheader(
                    "📋 Rainfall Category Comparison Table"
                )

                st.dataframe(
                    category_comparison_table,
                    use_container_width=True
                )
                csv = (
                    category_comparison_table
                    .to_csv()
                    .encode("utf-8")
                )
                
                st.download_button(
                    "📥 Download Category Comparison Table CSV",
                    data=csv,
                    file_name=f"station_comparison_category_{YEAR_RANGE_TEXT}.csv",
                    mime="text/csv",
                    key="download_category_comparison_table"
                )
                st.divider()            
# ============================================================
# FOOTER
# ============================================================
st.divider()

st.caption("🌧️ Rainfall Data Analysis | Quality Control, Climatological Mean, Anomaly and Statistical Analysis| Iya iya ja kau ba" )
