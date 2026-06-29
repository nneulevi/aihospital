import argparse
import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, roc_curve, auc
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures
from sklearn.cluster import KMeans
from sklearn.exceptions import NotFittedError


def load_glucose_csv(path):
    df = pd.read_csv(path)
    df = df.dropna(subset=['date', 'time', 'glucose'])
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], errors='coerce')
    df = df.dropna(subset=['datetime'])
    df = df.sort_values('datetime')
    df = df.reset_index(drop=True)
    df['minutes'] = (df['datetime'] - df['datetime'].iloc[0]).dt.total_seconds() / 60.0
    return df


def fit_models(X, y):
    models = {
        'Linear': LinearRegression(),
        'Poly2': make_pipeline(PolynomialFeatures(degree=2, include_bias=False), LinearRegression()),
        'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42)
    }
    fitted = {}
    for name, model in models.items():
        model.fit(X, y)
        fitted[name] = model
    return fitted


def plot_prediction(df, fitted_models, out_path):
    x_min, x_max = df['minutes'].min(), df['minutes'].max()
    x_pred = np.linspace(x_min, x_max + 30, 200).reshape(-1, 1)

    plt.figure(figsize=(10, 6))
    plt.scatter(df['minutes'], df['glucose'], label='Actual', color='black', s=25, alpha=0.8)
    for name, model in fitted_models.items():
        y_pred = model.predict(x_pred)
        plt.plot(x_pred.ravel(), y_pred, label=f'{name} prediction', linewidth=2)

    plt.title(f"{os.path.basename(out_path)} - Glucose Regression Prediction")
    plt.xlabel('Time (minutes from first reading)')
    plt.ylabel('Glucose')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def plot_combined(results, out_path):
    n = len(results)
    ncols = 3
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 14), sharey=True)
    axes = axes.flatten()

    for ax, (path, df, fitted_models) in zip(axes, results):
        x_min, x_max = df['minutes'].min(), df['minutes'].max()
        x_pred = np.linspace(x_min, x_max + 30, 200).reshape(-1, 1)

        ax.scatter(df['minutes'], df['glucose'], label='Actual', color='black', s=20, alpha=0.8)
        for name, model in fitted_models.items():
            y_pred = model.predict(x_pred)
            ax.plot(x_pred.ravel(), y_pred, label=name, linewidth=1.8)

        ax.set_title(os.path.basename(path))
        ax.set_xlabel('Minutes')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(fontsize='small')

    for ax in axes[len(results):]:
        ax.axis('off')

    fig.supylabel('Glucose')
    fig.suptitle('Glucose Prediction for All CSV Files', fontsize=18)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_roc_comparison(df, y_col='y_true', model_cols=None, out_path='roc_compare.png', title='ROC Comparison'):
    y = df[y_col].values
    if model_cols is None:
        model_cols = [c for c in df.columns if c != y_col]

    plt.figure(figsize=(8, 6))
    for col in model_cols:
        scores = df[col].values
        try:
            fpr, tpr, _ = roc_curve(y, scores)
            roc_auc = auc(fpr, tpr)
        except ValueError:
            # Skip columns that cannot produce an ROC (e.g., constant values)
            continue
        plt.plot(fpr, tpr, lw=2, label=f'{col} (AUC={roc_auc:.3f})')

    plt.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend(loc='lower right')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def run_roc_from_csv(csv_path, y_col='y_true', model_cols=None, out_path='roc_compare.png', title='ROC Comparison'):
    df = pd.read_csv(csv_path)
    if y_col not in df.columns:
        raise ValueError(f"指定的标签列 '{y_col}' 在 CSV 中不存在。请使用包含真实二分类标签的列名（0/1）。")
    if model_cols:
        model_cols = [c.strip() for c in model_cols.split(',')]
    else:
        model_cols = None
    plot_roc_comparison(df, y_col=y_col, model_cols=model_cols, out_path=out_path, title=title)


def plot_label_pred_cluster(csv_path, y_col='y_true', score_col=None, pred_col=None, threshold=0.5, n_clusters=3, out_path='compare_labels.png', title='True vs Predicted vs Clusters'):
    df = pd.read_csv(csv_path)

    if y_col not in df.columns:
        raise ValueError(f"标签列 '{y_col}' 在 CSV 中不存在。")

    # determine x axis value
    if 'datetime' in df.columns:
        x = pd.to_datetime(df['datetime'], errors='coerce')
    else:
        x = np.arange(len(df))

    # classification prediction
    if pred_col and pred_col in df.columns:
        pred = df[pred_col].values
    elif score_col and score_col in df.columns:
        pred = (df[score_col].astype(float) >= float(threshold)).astype(int).values
    else:
        # try common score columns
        possible = [c for c in df.columns if 'prob' in c or 'score' in c or 'pred' in c]
        pred = None
        for c in possible:
            if c != y_col:
                pred = (df[c].astype(float) >= float(threshold)).astype(int).values
                score_col = c
                break

    if pred is None:
        raise ValueError('未找到可用于生成分类结果的分数或预测列，请提供 --score-col 或 --pred-col。')

    # clustering
    # choose numeric feature columns for clustering
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != y_col]
    if not numeric_cols:
        raise ValueError('在 CSV 中未找到用于聚类的数值列。')
    X = df[numeric_cols].fillna(0).values
    kmeans = KMeans(n_clusters=int(n_clusters), random_state=42)
    clusters = kmeans.fit_predict(X)

    # plotting
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), sharey=True)

    # True labels
    axes[0].scatter(x, df[numeric_cols[0]], c=df[y_col], cmap='bwr', s=25)
    axes[0].set_title('True Labels')
    axes[0].set_xlabel('Index' if not isinstance(x, pd.DatetimeIndex) else 'Datetime')

    # Predicted classes
    axes[1].scatter(x, df[numeric_cols[0]], c=pred, cmap='bwr', s=25)
    axes[1].set_title(f'Predicted (threshold={threshold})')
    axes[1].set_xlabel('Index' if not isinstance(x, pd.DatetimeIndex) else 'Datetime')

    # Clusters
    axes[2].scatter(x, df[numeric_cols[0]], c=clusters, cmap='tab10', s=25)
    axes[2].set_title(f'KMeans clusters (k={n_clusters})')
    axes[2].set_xlabel('Index' if not isinstance(x, pd.DatetimeIndex) else 'Datetime')

    for ax in axes:
        ax.grid(True, linestyle='--', alpha=0.3)

    fig.suptitle(title)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_kmeans_convergence(csv_path, numeric_cols=None, n_clusters=3, max_iter=30, out_path='kmeans_convergence.png', title='KMeans Convergence'):
    df = pd.read_csv(csv_path)
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != 'y_true']
    if not numeric_cols:
        raise ValueError('未找到用于聚类的数值列来绘制收敛曲线。')

    X = df[numeric_cols].fillna(0).values
    inertias = []
    iterations = list(range(1, int(max_iter) + 1))
    for it in iterations:
        kmeans = KMeans(n_clusters=int(n_clusters), max_iter=it, n_init=10, random_state=42)
        kmeans.fit(X)
        inertias.append(kmeans.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(iterations, inertias, marker='o')
    plt.xlabel('Max iterations allowed')
    plt.ylabel('Inertia')
    plt.title(title)
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()





def main():
    parser = argparse.ArgumentParser(description='Glucose tools and ROC comparison')
    # ROC options
    parser.add_argument('--roc-csv', help='CSV file path containing true labels and model score columns for ROC comparison')
    parser.add_argument('--ycol', default='y_true', help='Column name for true binary labels (default: y_true)')
    parser.add_argument('--models', default=None, help='Comma-separated model score column names to compare (default: all columns except ycol)')
    parser.add_argument('--out', default='roc_compare.png', help='Output image path for ROC plot')
    parser.add_argument('--title', default='ROC Comparison', help='Title for the ROC plot')

    # compare labels/pred/clusters options
    parser.add_argument('--compare-csv', help='CSV file path to produce True vs Predicted vs Clusters comparison')
    parser.add_argument('--score-col', default=None, help='Score column to threshold into predicted class')
    parser.add_argument('--pred-col', default=None, help='Direct predicted class column name (0/1)')
    parser.add_argument('--threshold', default=0.5, help='Threshold for score to produce predicted class')
    parser.add_argument('--nclusters', default=3, help='Number of clusters for KMeans')
    parser.add_argument('--compare-out', default='compare_labels.png', help='Output path for comparison image')

    # kmeans convergence options
    parser.add_argument('--kmeans-conv-csv', help='CSV file path to plot KMeans convergence (inertia vs iterations)')
    parser.add_argument('--kmeans-ncols', default=None, help='Comma-separated numeric columns to use for clustering (default: all numeric except y_true)')
    parser.add_argument('--kmeans-max-iter', default=30, help='Maximum iterations to test for convergence plot')
    parser.add_argument('--kmeans-out', default='kmeans_convergence.png', help='Output path for KMeans convergence image')

    args = parser.parse_args()

    if args.roc_csv:
        run_roc_from_csv(args.roc_csv, y_col=args.ycol, model_cols=args.models, out_path=args.out, title=args.title)
        print(f'已生成 ROC 对比图: {args.out}')
        return

    if args.compare_csv:
        plot_label_pred_cluster(args.compare_csv, y_col=args.ycol, score_col=args.score_col, pred_col=args.pred_col, threshold=args.threshold, n_clusters=args.nclusters, out_path=args.compare_out, title=args.title)
        print(f'已生成对比图: {args.compare_out}')
        return

    if args.kmeans_conv_csv:
        cols = None
        if args.kmeans_ncols:
            cols = [c.strip() for c in args.kmeans_ncols.split(',')]
        plot_kmeans_convergence(args.kmeans_conv_csv, numeric_cols=cols, n_clusters=args.nclusters, max_iter=args.kmeans_max_iter, out_path=args.kmeans_out, title=f'KMeans Convergence (k={args.nclusters})')
        print(f'已生成 KMeans 收敛图: {args.kmeans_out}')
        return

    files = sorted(glob.glob('glucose_*.csv'))
    if not files:
        print('未找到 glucose_*.csv 文件。')
        return

    results = []
    for path in files:
        df = load_glucose_csv(path)
        if df.empty:
            print(f'{path} 数据为空或无法解析，跳过。')
            continue

        X = df[['minutes']].values
        y = df['glucose'].values
        models = fit_models(X, y)
        results.append((path, df, models))

        print(f'=== {path} ===')
        for name, model in models.items():
            y_pred = model.predict(X)
            rmse = mean_squared_error(y, y_pred) ** 0.5
            print(f'{name} RMSE: {rmse:.4f}')
        print()

    if results:
        plot_combined(results, 'glucose_combined_prediction.png')
        print('已生成组合图像: glucose_combined_prediction.png')

        out_name = os.path.splitext(os.path.basename(path))[0] + '_prediction.png'
        plot_prediction(df, models, out_name)
        print(f'已生成图像: {out_name}\n')


if __name__ == '__main__':
    main()
