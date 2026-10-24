
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Bike Sharing Analytics",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
""", unsafe_allow_html=True)

BLUE = "#2563EB"
CYAN = "#06B6D4"
ORANGE = "#F59E0B"
GREEN = "#10B981"
PURPLE = "#8B5CF6"

MONTH_NAMES = {
    1: "Januari", 2: "Februari", 3: "Maret",
    4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September",
    10: "Oktober", 11: "November", 12: "Desember"
}

WEEKDAY_NAMES = {
    0: "Minggu", 1: "Senin", 2: "Selasa",
    3: "Rabu", 4: "Kamis", 5: "Jumat",
    6: "Sabtu"
}

WEATHER_NAMES = {
    1: "Cerah / sedikit berawan",
    2: "Berkabut / berawan",
    3: "Hujan ringan / salju ringan",
    4: "Cuaca buruk"
}

YEAR_LABELS = {
    0: "2011",
    1: "2012"
}

def load_data():
    day = pd.read_csv("day_clean.csv")
    hour = pd.read_csv("hour_clean.csv")

    day["dteday"] = pd.to_datetime(day["dteday"])
    hour["dteday"] = pd.to_datetime(hour["dteday"])

    for df in [day, hour]:
        for col in ["yr", "mnth", "workingday", "weathersit"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    day = day.dropna(subset=["dteday", "cnt"])
    hour = hour.dropna(subset=["dteday", "cnt", "hr"])

    return day, hour


try:
    day_df, hour_df = load_data()
except FileNotFoundError:
    st.error(
        "File day_clean.csv atau hour_clean.csv tidak ditemukan. "
        "Pastikan kedua file berada di folder yang sama dengan dashboard.py."
    )
    st.stop()
except (ValueError, KeyError) as error:
    st.error(f"Terjadi kesalahan saat membaca dataset: {error}")
    st.stop()

if day_df.empty or hour_df.empty:
    st.error("Dataset kosong. Periksa kembali file CSV yang digunakan.")
    st.stop()

st.sidebar.title("🚲 Bike Sharing")
st.sidebar.caption("Analytics Dashboard")
st.sidebar.divider()
st.sidebar.subheader("Filter Data")

min_date = day_df["dteday"].min().date()
max_date = day_df["dteday"].max().date()

date_range = st.sidebar.date_input(
    "Rentang tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, (tuple, list)):
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = end_date = date_range[0]
    else:
        start_date = end_date = min_date
else:
    start_date = end_date = date_range

if start_date > end_date:
    st.sidebar.error("Tanggal awal tidak boleh melebihi tanggal akhir.")
    st.stop()

day_filtered = day_df[
    (day_df["dteday"].dt.date >= start_date) &
    (day_df["dteday"].dt.date <= end_date)
].copy()

hour_filtered = hour_df[
    (hour_df["dteday"].dt.date >= start_date) &
    (hour_df["dteday"].dt.date <= end_date)
].copy()

if day_filtered.empty:
    st.warning("Tidak ada data pada rentang tanggal yang dipilih.")
    st.stop()

available_years = sorted(day_filtered["yr"].dropna().unique())

selected_years = st.sidebar.multiselect(
    "Tahun",
    options=available_years,
    default=available_years,
    format_func=lambda x: YEAR_LABELS.get(int(x), str(int(x)))
)

available_months = sorted(day_filtered["mnth"].dropna().unique())

selected_months = st.sidebar.multiselect(
    "Bulan",
    options=available_months,
    default=available_months,
    format_func=lambda x: MONTH_NAMES.get(int(x), str(int(x)))
)

day_type_options = {
    "Hari kerja": 1,
    "Hari nonkerja": 0
}

selected_day_types = st.sidebar.multiselect(
    "Jenis hari",
    options=list(day_type_options.keys()),
    default=list(day_type_options.keys())
)

available_weather = sorted(
    day_filtered["weathersit"].dropna().unique()
)

selected_weather = st.sidebar.multiselect(
    "Kondisi cuaca",
    options=available_weather,
    default=available_weather,
    format_func=lambda x: WEATHER_NAMES.get(int(x), f"Cuaca {int(x)}")
)

selected_workingday_values = [
    day_type_options[label] for label in selected_day_types
]

day_mask = (
    day_filtered["yr"].isin(selected_years) &
    day_filtered["mnth"].isin(selected_months) &
    day_filtered["workingday"].isin(selected_workingday_values) &
    day_filtered["weathersit"].isin(selected_weather)
)

filtered_day = day_filtered[day_mask].copy()

hour_mask = (
    hour_filtered["yr"].isin(selected_years) &
    hour_filtered["mnth"].isin(selected_months) &
    hour_filtered["workingday"].isin(selected_workingday_values) &
    hour_filtered["weathersit"].isin(selected_weather)
)

filtered_hour = hour_filtered[hour_mask].copy()

st.title("🚲 Bike Sharing Analytics Dashboard")
st.markdown(
    "Eksplorasi pola peminjaman sepeda berdasarkan waktu, "
    "jenis hari, jenis pengguna, dan kondisi cuaca."
)

st.caption(
    f"Rentang tanggal: {start_date.strftime('%d %b %Y')} – "
    f"{end_date.strftime('%d %b %Y')}"
)

st.divider()

if filtered_day.empty:
    st.warning(
        "Tidak ada data yang sesuai dengan kombinasi filter. "
        "Silakan ubah filter pada sidebar."
    )
    st.stop()

total_rentals = int(filtered_day["cnt"].sum())
avg_rentals = filtered_day["cnt"].mean()
max_rentals = int(filtered_day["cnt"].max())
total_days = filtered_day["dteday"].nunique()
casual_total = int(filtered_day["casual"].sum())
registered_total = int(filtered_day["registered"].sum())

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Peminjaman", f"{total_rentals:,.0f}")
k2.metric("Rata-rata per Hari", f"{avg_rentals:,.0f}")
k3.metric("Peminjaman Harian Tertinggi", f"{max_rentals:,.0f}")
k4.metric("Jumlah Hari Dianalisis", f"{total_days:,}")

st.divider()

tab_overview, tab_time, tab_users, tab_extra, tab_data = st.tabs([
    "📊 Ringkasan",
    "🕒 Analisis Waktu",
    "👥 Analisis Pengguna",
    "🌦️ Analisis Tambahan",
    "📁 Data & Unduhan"
])

with tab_overview:
    st.subheader("Tren Peminjaman Sepeda")

    monthly_trend = (
        filtered_day.assign(
            periode=filtered_day["dteday"].dt.to_period("M").dt.to_timestamp()
        )
        .groupby("periode", as_index=False)
        .agg(total_rentals=("cnt", "sum"))
        .sort_values("periode")
    )

    fig_trend = px.line(
        monthly_trend,
        x="periode",
        y="total_rentals",
        markers=True,
        title="Total Peminjaman Sepeda per Bulan",
        labels={
            "periode": "Bulan",
            "total_rentals": "Total Peminjaman"
        },
        color_discrete_sequence=[BLUE]
    )

    fig_trend.update_layout(
        height=350,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    fig_trend.update_xaxes(dtick="M2", tickformat="%b %Y")
    fig_trend.update_traces(line=dict(width=3), marker=dict(size=6))
    st.plotly_chart(fig_trend, use_container_width=True)

    left, right = st.columns(2)

    with left:
        monthly_data = (
            filtered_day.groupby("mnth", as_index=False)
            .agg(
                average_rentals=("cnt", "mean"),
                total_rentals=("cnt", "sum")
            )
            .sort_values("mnth")
        )
        monthly_data["nama_bulan"] = monthly_data["mnth"].map(MONTH_NAMES)

        fig_month = px.bar(
            monthly_data,
            x="nama_bulan",
            y="average_rentals",
            title="Rata-rata Peminjaman per Bulan",
            labels={
                "nama_bulan": "Bulan",
                "average_rentals": "Rata-rata Peminjaman Harian"
            },
            color="average_rentals",
            color_continuous_scale="Blues"
        )
        fig_month.update_layout(height=380)
        st.plotly_chart(fig_month, use_container_width=True)

    with right:
        yearly_data = (
            filtered_day.groupby("yr", as_index=False)
            .agg(total_rentals=("cnt", "sum"))
        )
        yearly_data["tahun"] = yearly_data["yr"].map(YEAR_LABELS)

        fig_year = px.bar(
            yearly_data,
            x="tahun",
            y="total_rentals",
            title="Total Peminjaman per Tahun",
            labels={
                "tahun": "Tahun",
                "total_rentals": "Total Peminjaman"
            },
            text_auto=",.0f",
            color_discrete_sequence=[CYAN]
        )
        fig_year.update_layout(height=380)
        st.plotly_chart(fig_year, use_container_width=True)

    st.subheader("💡 Insight Otomatis")

    if not monthly_data.empty:
        peak_month = monthly_data.loc[
            monthly_data["average_rentals"].idxmax()
        ]
        low_month = monthly_data.loc[
            monthly_data["average_rentals"].idxmin()
        ]

        c1, c2 = st.columns(2)
        c1.info(
            f"Bulan dengan rata-rata peminjaman tertinggi adalah "
            f"**{peak_month['nama_bulan']}**, sekitar "
            f"**{peak_month['average_rentals']:,.0f} peminjaman per hari**."
        )
        c2.info(
            f"Bulan dengan rata-rata peminjaman terendah adalah "
            f"**{low_month['nama_bulan']}**, sekitar "
            f"**{low_month['average_rentals']:,.0f} peminjaman per hari**."
        )

with tab_time:
    st.subheader("Pola Peminjaman Berdasarkan Jam")

    if filtered_hour.empty:
        st.warning("Tidak ada data per jam yang sesuai dengan filter.")
    else:
        hourly_data = (
            filtered_hour.groupby("hr", as_index=False)
            .agg(average_rentals=("cnt", "mean"))
            .sort_values("hr")
        )

        fig_hour = px.line(
            hourly_data,
            x="hr",
            y="average_rentals",
            markers=True,
            title="Rata-rata Peminjaman pada Setiap Jam",
            labels={
                "hr": "Jam",
                "average_rentals": "Rata-rata Peminjaman"
            },
            color_discrete_sequence=[PURPLE]
        )
        fig_hour.update_xaxes(tickmode="linear", tick0=0, dtick=1)
        fig_hour.update_layout(height=420)
        st.plotly_chart(fig_hour, use_container_width=True)

        peak_row = hourly_data.loc[
            hourly_data["average_rentals"].idxmax()
        ]

        st.success(
            f"Jam dengan rata-rata peminjaman tertinggi pada filter "
            f"yang dipilih adalah pukul {int(peak_row['hr']):02d}.00, "
            f"dengan rata-rata {peak_row['average_rentals']:,.1f} peminjaman."
        )

        hourly_by_type = (
            filtered_hour.groupby(["hr", "workingday"], as_index=False)
            .agg(average_rentals=("cnt", "mean"))
        )
        hourly_by_type["jenis_hari"] = hourly_by_type["workingday"].map({
            1: "Hari kerja",
            0: "Hari nonkerja"
        })

        fig_type = px.line(
            hourly_by_type,
            x="hr",
            y="average_rentals",
            color="jenis_hari",
            markers=True,
            title="Perbandingan Pola Jam: Hari Kerja vs Nonkerja",
            labels={
                "hr": "Jam",
                "average_rentals": "Rata-rata Peminjaman",
                "jenis_hari": "Jenis Hari"
            },
            color_discrete_map={
                "Hari kerja": BLUE,
                "Hari nonkerja": ORANGE
            }
        )
        fig_type.update_xaxes(tickmode="linear", tick0=0, dtick=1)
        fig_type.update_layout(height=420)
        st.plotly_chart(fig_type, use_container_width=True)

        heat_data = (
            filtered_hour.groupby(["weekday", "hr"], as_index=False)
            .agg(average_rentals=("cnt", "mean"))
        )
        heat_pivot = heat_data.pivot(
            index="weekday",
            columns="hr",
            values="average_rentals"
        ).reindex(range(7))

        heat_pivot.index = [
            WEEKDAY_NAMES.get(int(i), str(i))
            for i in heat_pivot.index
        ]

        fig_heat = go.Figure(
            data=go.Heatmap(
                z=heat_pivot.values,
                x=heat_pivot.columns,
                y=heat_pivot.index,
                colorscale="Blues",
                colorbar_title="Rata-rata"
            )
        )
        fig_heat.update_layout(
            title="Heatmap Rata-rata Peminjaman Berdasarkan Hari dan Jam",
            xaxis_title="Jam",
            yaxis_title="Hari",
            height=420
        )
        st.plotly_chart(fig_heat, use_container_width=True)

with tab_users:
    st.subheader("Komposisi Pengguna Sepeda")

    user_data = pd.DataFrame({
        "jenis_pengguna": ["Kasual", "Terdaftar"],
        "total_peminjaman": [casual_total, registered_total]
    })

    fig_users = px.pie(
        user_data,
        names="jenis_pengguna",
        values="total_peminjaman",
        hole=0.55,
        title="Proporsi Peminjaman Berdasarkan Jenis Pengguna",
        color="jenis_pengguna",
        color_discrete_map={
            "Kasual": ORANGE,
            "Terdaftar": BLUE
        }
    )
    fig_users.update_traces(textposition="inside", textinfo="percent+label")
    fig_users.update_layout(height=420)
    st.plotly_chart(fig_users, use_container_width=True)

    u1, u2 = st.columns(2)
    u1.metric("Peminjaman Pengguna Kasual", f"{casual_total:,.0f}")
    u2.metric("Peminjaman Pengguna Terdaftar", f"{registered_total:,.0f}")

    user_trend = (
        filtered_day.groupby("dteday", as_index=False)
        .agg(casual=("casual", "sum"), registered=("registered", "sum"))
        .sort_values("dteday")
    )

    user_trend_long = user_trend.melt(
        id_vars="dteday",
        value_vars=["casual", "registered"],
        var_name="jenis_pengguna",
        value_name="total_peminjaman"
    )
    user_trend_long["jenis_pengguna"] = user_trend_long[
        "jenis_pengguna"
    ].map({
        "casual": "Kasual",
        "registered": "Terdaftar"
    })

    fig_user_trend = px.area(
        user_trend_long,
        x="dteday",
        y="total_peminjaman",
        color="jenis_pengguna",
        title="Tren Peminjaman Berdasarkan Jenis Pengguna",
        labels={
            "dteday": "Tanggal",
            "total_peminjaman": "Jumlah Peminjaman",
            "jenis_pengguna": "Jenis Pengguna"
        },
        color_discrete_map={
            "Kasual": ORANGE,
            "Terdaftar": BLUE
        }
    )
    fig_user_trend.update_layout(height=420)
    st.plotly_chart(fig_user_trend, use_container_width=True)

    if casual_total + registered_total > 0:
        registered_share = (
            registered_total / (casual_total + registered_total) * 100
        )
        st.info(
            f"Pengguna terdaftar menyumbang sekitar "
            f"**{registered_share:.1f}%** dari seluruh peminjaman "
            f"pada filter yang dipilih."
        )

with tab_extra:
    st.subheader("Eksplorasi Faktor Peminjaman Sepeda")
    st.caption(
        "Analisis berdasarkan jenis hari, cuaca, suhu, kelembapan, "
        "kecepatan angin, dan distribusi peminjaman."
    )

    # 1. Hari kerja vs nonkerja
    st.subheader("1. Peminjaman Berdasarkan Jenis Hari")

    workingday_data = (
        filtered_day.groupby("workingday", as_index=False)
        .agg(
            average_rentals=("cnt", "mean"),
            total_rentals=("cnt", "sum")
        )
    )
    workingday_data["jenis_hari"] = workingday_data["workingday"].map({
        0: "Hari Nonkerja",
        1: "Hari Kerja"
    })

    fig_workingday = px.bar(
        workingday_data,
        x="jenis_hari",
        y="average_rentals",
        color="jenis_hari",
        text_auto=".0f",
        title="Rata-rata Peminjaman: Hari Kerja vs Nonkerja",
        labels={
            "jenis_hari": "Jenis Hari",
            "average_rentals": "Rata-rata Peminjaman per Hari"
        },
        color_discrete_map={
            "Hari Kerja": BLUE,
            "Hari Nonkerja": ORANGE
        }
    )
    fig_workingday.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_workingday, use_container_width=True)

    # 2. Cuaca
    st.subheader("2. Peminjaman Berdasarkan Kondisi Cuaca")

    weather_data = (
        filtered_day.groupby("weathersit", as_index=False)
        .agg(
            average_rentals=("cnt", "mean"),
            total_rentals=("cnt", "sum")
        )
    )
    weather_data["kondisi_cuaca"] = weather_data["weathersit"].map(
        WEATHER_NAMES
    )

    fig_weather = px.bar(
        weather_data,
        x="kondisi_cuaca",
        y="average_rentals",
        color="average_rentals",
        text_auto=".0f",
        title="Rata-rata Peminjaman Berdasarkan Cuaca",
        labels={
            "kondisi_cuaca": "Kondisi Cuaca",
            "average_rentals": "Rata-rata Peminjaman per Hari"
        },
        color_continuous_scale="Blues"
    )
    fig_weather.update_layout(height=380)
    st.plotly_chart(fig_weather, use_container_width=True)

    # 3. Suhu
    st.subheader("3. Hubungan Suhu dengan Jumlah Peminjaman")

    fig_temp = px.scatter(
        filtered_day,
        x="temp",
        y="cnt",
        color="weathersit",
        hover_data=["dteday", "casual", "registered"],
        title="Suhu vs Jumlah Peminjaman Harian",
        labels={
            "temp": "Suhu (Skala Ternormalisasi)",
            "cnt": "Jumlah Peminjaman",
            "weathersit": "Kode Cuaca"
        },
        opacity=0.7,
        color_continuous_scale="Viridis"
    )
    fig_temp.update_layout(height=420)
    st.plotly_chart(fig_temp, use_container_width=True)

    # 4. Pengguna per bulan
    st.subheader("4. Perbandingan Pengguna per Bulan")

    user_monthly = (
        filtered_day.groupby("mnth", as_index=False)
        .agg(casual=("casual", "sum"), registered=("registered", "sum"))
        .sort_values("mnth")
    )
    user_monthly["nama_bulan"] = user_monthly["mnth"].map(MONTH_NAMES)

    user_monthly_long = user_monthly.melt(
        id_vars="nama_bulan",
        value_vars=["casual", "registered"],
        var_name="jenis_pengguna",
        value_name="total_peminjaman"
    )
    user_monthly_long["jenis_pengguna"] = user_monthly_long[
        "jenis_pengguna"
    ].map({
        "casual": "Kasual",
        "registered": "Terdaftar"
    })

    fig_user_monthly = px.bar(
        user_monthly_long,
        x="nama_bulan",
        y="total_peminjaman",
        color="jenis_pengguna",
        barmode="group",
        title="Total Peminjaman Bulanan Menurut Jenis Pengguna",
        labels={
            "nama_bulan": "Bulan",
            "total_peminjaman": "Total Peminjaman",
            "jenis_pengguna": "Jenis Pengguna"
        },
        color_discrete_map={
            "Kasual": ORANGE,
            "Terdaftar": BLUE
        }
    )
    fig_user_monthly.update_layout(height=420)
    st.plotly_chart(fig_user_monthly, use_container_width=True)

    # 5. Kelembapan
    st.subheader("5. Kelembapan vs Jumlah Peminjaman")

    fig_humidity = px.scatter(
        filtered_day,
        x="hum",
        y="cnt",
        color="weathersit",
        hover_data=["dteday", "temp", "windspeed"],
        title="Kelembapan vs Jumlah Peminjaman Harian",
        labels={
            "hum": "Kelembapan (Skala Ternormalisasi)",
            "cnt": "Jumlah Peminjaman",
            "weathersit": "Kode Cuaca"
        },
        opacity=0.7
    )
    fig_humidity.update_layout(height=400)
    st.plotly_chart(fig_humidity, use_container_width=True)

    # 6. Kecepatan angin
    st.subheader("6. Kecepatan Angin vs Jumlah Peminjaman")

    fig_wind = px.scatter(
        filtered_day,
        x="windspeed",
        y="cnt",
        color="weathersit",
        hover_data=["dteday", "temp", "hum"],
        title="Kecepatan Angin vs Jumlah Peminjaman Harian",
        labels={
            "windspeed": "Kecepatan Angin (Skala Ternormalisasi)",
            "cnt": "Jumlah Peminjaman",
            "weathersit": "Kode Cuaca"
        },
        opacity=0.7
    )
    fig_wind.update_layout(height=400)
    st.plotly_chart(fig_wind, use_container_width=True)

    # 7. Distribusi peminjaman harian
    st.subheader("7. Distribusi Jumlah Peminjaman Harian")

    fig_box = px.box(
        filtered_day,
        y="cnt",
        points="outliers",
        title="Sebaran Jumlah Peminjaman per Hari",
        labels={"cnt": "Jumlah Peminjaman Harian"},
        color_discrete_sequence=[PURPLE]
    )
    fig_box.update_layout(height=400)
    st.plotly_chart(fig_box, use_container_width=True)

    # 8. Distribusi pengguna
    st.subheader("8. Distribusi Peminjaman Menurut Jenis Pengguna")

    user_distribution = filtered_day[
        ["casual", "registered"]
    ].melt(
        var_name="jenis_pengguna",
        value_name="jumlah_peminjaman"
    )

    user_distribution["jenis_pengguna"] = user_distribution[
        "jenis_pengguna"
    ].map({
        "casual": "Kasual",
        "registered": "Terdaftar"
    })

    fig_user_box = px.box(
        user_distribution,
        x="jenis_pengguna",
        y="jumlah_peminjaman",
        color="jenis_pengguna",
        points="outliers",
        title="Distribusi Peminjaman Harian per Jenis Pengguna",
        labels={
            "jenis_pengguna": "Jenis Pengguna",
            "jumlah_peminjaman": "Jumlah Peminjaman Harian"
        },
        color_discrete_map={
            "Kasual": ORANGE,
            "Terdaftar": BLUE
        }
    )
    fig_user_box.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_user_box, use_container_width=True)

    st.info(
        "Catatan: suhu, kelembapan, dan kecepatan angin menggunakan "
        "skala ternormalisasi. Grafik menunjukkan pola hubungan, "
        "bukan bukti sebab-akibat."
    )

with tab_data:
    st.subheader("Data Peminjaman Harian")

    st.dataframe(
        filtered_day.sort_values("dteday", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    day_csv = filtered_day.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Unduh Data Harian (CSV)",
        data=day_csv,
        file_name="bike_sharing_harian.csv",
        mime="text/csv"
    )

    st.divider()
    st.subheader("Data Peminjaman per Jam")

    if not filtered_hour.empty:
        st.dataframe(
            filtered_hour.sort_values(
                ["dteday", "hr"],
                ascending=[False, True]
            ),
            use_container_width=True,
            hide_index=True
        )

        hour_csv = filtered_hour.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="⬇️ Unduh Data Per Jam (CSV)",
            data=hour_csv,
            file_name="bike_sharing_per_jam.csv",
            mime="text/csv"
        )
    else:
        st.info("Tidak ada data per jam untuk filter yang dipilih.")

st.divider()
st.caption(
    "Sumber: Bike Sharing Dataset (2011–2012). "
    "Gunakan filter pada sidebar untuk mengeksplorasi data."
)