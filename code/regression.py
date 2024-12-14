import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.api import VAR
import matplotlib.pyplot as plt
import os
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from linearmodels.panel import PanelOLS
from linearmodels.iv import IVGMM
from linearmodels.panel.data import PanelData


def prepare_data_for_arima_var(file_path):
    """Prepares the data for ARIMA and VAR analysis by cleaning, differencing, and adding lagged features."""
    df = pd.read_excel(file_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date")
    df.set_index("date", inplace=True)
    df = df[
        df["daily_weighted_sentiment"].notna() & (df["daily_weighted_sentiment"] != 0)
    ]
    df["log_volume"] = np.log(df["volume"])
    df["log_return"] = np.log(df["return"])
    df["logreturn_diff"] = df["log_return"].diff()
    df["return_diff"] = df["return"].diff()
    df["volume_diff"] = df["log_volume"].diff()
    df["sentiment_diff"] = df["daily_weighted_sentiment"].diff()
    for lag in range(1, 4):
        df[f"daily_weighted_sentiment_lag{lag}"] = df["daily_weighted_sentiment"].shift(
            lag
        )
    df["daily_weighted_sentiment_lag3_diff"] = df[
        "daily_weighted_sentiment_lag3"
    ].diff()
    df = df.dropna(
        subset=[
            "return_diff",
            "volume_diff",
            "sentiment_diff",
            "log_return",
            "daily_weighted_sentiment_lag1",
            "daily_weighted_sentiment_lag2",
            "daily_weighted_sentiment_lag3",
            "daily_weighted_sentiment_lag3_diff",
        ]
    )
    return df


def prepare_data_for_panel_var(file_path):
    """Prepares the data for Panel VAR analysis by setting indices and sorting."""
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    df["date"] = pd.to_datetime(df["date"])
    df["log_volume"] = np.log(df["volume"] + 1)
    df["log_return"] = np.log(df["return"] + 1)
    df["log_size"] = np.log(df["size"] + 1)
    df = df.dropna(subset=["log_volume", "log_return", "log_size"])
    df = df.sort_values(by=["stock", "date"])
    df = df.set_index(["stock", "date"])
    return df


def run_arima(y_series, x_series, order=(2, 1, 2)):
    """Fits an ARIMA model with exogenous variables."""
    model = ARIMA(y_series, exog=x_series, order=order)
    return model.fit()


def save_arima_results(model, output_file):
    """Saves the results of an ARIMA model to a text file."""
    with open(output_file, "w") as f:
        f.write(model.summary().as_text())


def plot_arima_fit(actual, fitted, title, filename, output_dir):
    """Plots and saves the ARIMA model fit against actual data."""
    plt.figure(figsize=(10, 6))
    plt.plot(actual, label="Actual")
    plt.plot(fitted, label="Fitted", color="red")
    plt.title(title)
    plt.legend()
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()


def run_var(data, lags=2):
    """Fits a VAR model to the data with the specified number of lags."""
    model = VAR(data)
    return model.fit(lags)


def forecast_var(var_model, data, title, filename, steps, output_dir):
    """Forecasts future values using a fitted VAR model."""
    forecast = var_model.forecast(data.values[-var_model.k_ar :], steps=steps)
    forecast_df = pd.DataFrame(forecast, columns=data.columns)
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.plot(
        range(steps),
        forecast_df.iloc[:, 0],
        label=f"{data.columns[0]} Forecast",
        color="blue",
    )
    ax1.set_ylabel(data.columns[0], color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax2 = ax1.twinx()
    ax2.plot(
        range(steps),
        forecast_df.iloc[:, 1],
        label=f"{data.columns[1]} Forecast",
        color="orange",
    )
    ax2.set_ylabel(data.columns[1], color="orange")
    ax2.tick_params(axis="y", labelcolor="orange")
    plt.title(title)
    fig.tight_layout()
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()


def generate_lagged_variables(data, variables, lags):
    """Generates lagged variables for specified columns."""
    for lag in range(1, lags + 1):
        for var in variables:
            data[f"{var}_lag{lag}"] = data.groupby("stock")[var].shift(lag)
    return data


def plot_impulse_response(
    var_model, steps, output_dir, title_prefix="Impulse Response"
):
    """Plots and saves impulse response functions of the VAR model."""
    irf = var_model.irf(steps)
    fig = irf.plot(orth=True)
    fig.suptitle(f"{title_prefix} (Steps={steps})", fontsize=16)
    plt.savefig(
        os.path.join(output_dir, f"{title_prefix.lower().replace(' ', '_')}_irf.png")
    )
    plt.close()


def save_variance_decomposition(var_model, steps, output_file):
    """Saves variance decomposition results to a text file."""
    fevd = var_model.fevd(steps)
    decomposition = fevd.decomp
    with open(output_file, "w") as f:
        f.write(f"Variance Decomposition (Steps={steps}):\n")
        for i in range(decomposition.shape[0]):
            f.write(f"\nStep {i + 1}:\n")
            for j, col in enumerate(var_model.names):
                contribution = decomposition[i, j]
                if isinstance(contribution, (np.ndarray, list)):
                    contribution_str = ", ".join([f"{val:.4f}" for val in contribution])
                    f.write(f"{col}: [{contribution_str}]\n")
                else:
                    f.write(f"{col}: {contribution:.4f}\n")


def save_results_to_csv(model, output_file):
    """Saves regression results as a CSV file with values formatted to 4 decimal places."""
    results = {
        "Variable": model.params.index,
        "Coefficient": model.params.round(4).values,
        "Std Error": model.bse.round(4).values,
        "t-value": model.tvalues.round(4).values,
        "p-value": model.pvalues.round(4).values,
    }
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_file, index=False)


def save_arima_results(model, text_output_file, csv_output_file):
    """Saves ARIMA model results to a text file and a CSV file with 4 decimal places."""
    with open(text_output_file, "w") as f:
        f.write(model.summary().as_text())
    save_results_to_csv(model, csv_output_file)


def estimate_gmm(data, dependent_vars, lags, control_vars=None, output_dir=None):
    """Estimates a dynamic panel model using GMM for single equations and saves results."""
    results = {}
    panel_data = PanelData(data)

    for dep_var in dependent_vars:
        lagged_y = f"{dep_var}_lag1"
        data[lagged_y] = data.groupby(level=0)[dep_var].shift(1)

        x_vars = [f"sentiment_score_lag{lag}" for lag in range(1, lags + 1)]
        if control_vars:
            x_vars += control_vars

        formula = f"{dep_var} ~ {lagged_y} + {' + '.join(x_vars)}"
        print(f"Estimating GMM for {dep_var} with formula: {formula}")

        model = IVGMM.from_formula(formula, data=data)
        result = model.fit(iter_limit=5000)
        results[dep_var] = result

        if output_dir:
            csv_file = f"{output_dir}/gmm_{dep_var}_results.csv"
            save_gmm_results_to_csv(result, dep_var, csv_file)

    return results


def save_gmm_results_to_csv(result, dep_var, output_file):
    """Saves GMM regression results to a CSV file with coefficients, standard errors, t-values, and p-values."""
    results_data = {
        "Dependent Variable": [dep_var] * len(result.params),
        "Variable": result.params.index,
        "Coefficient": result.params.values.round(4),
        "Std Error": result.std_errors.values.round(4),
        "t-value": result.tstats.values.round(4),
        "p-value": result.pvalues.values.round(4),
    }

    df_results = pd.DataFrame(results_data)
    df_results.to_csv(output_file, index=False)


def run_analysis(input_file_arima_var, input_file_panel_var, output_dir, steps=10):
    """Runs ARIMA, VAR, and Panel VAR analyses and saves results."""
    os.makedirs(output_dir, exist_ok=True)

    df_arima_var = prepare_data_for_arima_var(input_file_arima_var)
    arma_return = run_arima(
        df_arima_var["log_return"],
        df_arima_var[["daily_weighted_sentiment_lag1"]],
        order=(0, 0, 0),
    )
    arma_volume = run_arima(
        df_arima_var["log_volume"],
        df_arima_var[["daily_weighted_sentiment_lag3"]],
        order=(0, 0, 2),
    )

    save_arima_results(
        arma_return,
        os.path.join(output_dir, "arima_return_results.txt"),
        os.path.join(output_dir, "arima_return_results.csv"),
    )
    save_arima_results(
        arma_volume,
        os.path.join(output_dir, "arima_volume_results.txt"),
        os.path.join(output_dir, "arima_volume_results.csv"),
    )
    plot_arima_fit(
        df_arima_var["log_return"],
        arma_return.fittedvalues,
        "ARIMA Model Fit for Return",
        "arima_return_fit.png",
        output_dir,
    )
    plot_arima_fit(
        df_arima_var["log_volume"],
        arma_volume.fittedvalues,
        "ARIMA Model Fit for Volume",
        "arima_volume_fit.png",
        output_dir,
    )

    var_data_return = df_arima_var[["log_return", "daily_weighted_sentiment"]]
    var_return_model = run_var(var_data_return, lags=3)
    var_data_volume = df_arima_var[["log_volume", "daily_weighted_sentiment"]]
    var_volume_model = run_var(var_data_volume, lags=3)

    save_variance_decomposition(
        var_return_model, steps, os.path.join(output_dir, "var_return_fevd.txt")
    )
    save_variance_decomposition(
        var_volume_model, steps, os.path.join(output_dir, "var_volume_fevd.txt")
    )
    plot_impulse_response(
        var_return_model, steps, output_dir, title_prefix="VAR Return Impulse Response"
    )
    plot_impulse_response(
        var_volume_model, steps, output_dir, title_prefix="VAR Volume Impulse Response"
    )

    df_panel_var = prepare_data_for_panel_var(input_file_panel_var)
    df_panel_var = generate_lagged_variables(df_panel_var, ["sentiment_score"], lags=3)
    df_panel_var = df_panel_var.dropna(
        subset=[f"sentiment_score_lag{lag}" for lag in range(1, 4)]
    )
    dependent_vars = ["log_return", "log_volume"]
    control_vars = ["variation", "log_size"]

    gmm_results = estimate_gmm(
        data=df_panel_var,
        dependent_vars=dependent_vars,
        lags=3,
        control_vars=control_vars,
        output_dir=output_dir,
    )

    gmm_results1 = estimate_gmm(
        data=df_panel_var,
        dependent_vars=dependent_vars,
        lags=3,
        control_vars=control_vars,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    input_file_arima_var = "data/processed_dowjones.xlsx"
    input_file_panel_var = "data/processed_stock_sentiment_data_with_variation.xlsx"
    output_dir = "artifacts"
    run_analysis(input_file_arima_var, input_file_panel_var, output_dir, steps=10)
