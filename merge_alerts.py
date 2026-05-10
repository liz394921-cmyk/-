import os
import pandas as pd

base_dir = r"/mnt/f/vs-code-openclaw/data/ExcelData/Hospital_Data_Visualization"
alert_xlsx = os.path.join(base_dir, '当前告警.xlsx')
alert_csv = os.path.join(base_dir, '告警导出列表.csv')
asset_xlsx = os.path.join(base_dir, '资产信息.xlsx')
asset_csv = os.path.join(base_dir, 'exportInstanceList.csv')
output_csv = os.path.join(base_dir, 'Merged_Cleaned_Alerts.csv')

print('Base dir:', base_dir)
print('Alert XLSX exists:', os.path.exists(alert_xlsx))
print('Alert CSV exists:', os.path.exists(alert_csv))
print('Asset XLSX exists:', os.path.exists(asset_xlsx))
print('Asset CSV exists:', os.path.exists(asset_csv))

# Read function that tries multiple encodings

def read_csv_try(path, **kwargs):
    encodings = ['utf-8', 'gbk', 'utf-16', 'latin1']
    last_err = None
    for enc in encodings:
        try:
            print(f"Trying to read {os.path.basename(path)} with encoding={enc}")
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError as e:
            last_err = e
            print(f"UnicodeDecodeError with encoding={enc}")
        except Exception as e:
            last_err = e
            print(f"Failed to read {os.path.basename(path)} with encoding={enc}: {e}")
    raise last_err

# Load alert table from CSV if available, otherwise from Excel
if os.path.exists(alert_csv):
    alert_df = read_csv_try(alert_csv)
elif os.path.exists(alert_xlsx):
    alert_df = pd.read_excel(alert_xlsx)
else:
    raise FileNotFoundError('Neither alert CSV nor alert XLSX was found.')

# Load asset table from CSV if available, otherwise from Excel
if os.path.exists(asset_csv):
    asset_df = read_csv_try(asset_csv)
elif os.path.exists(asset_xlsx):
    asset_df = pd.read_excel(asset_xlsx)
else:
    raise FileNotFoundError('Neither asset CSV nor asset XLSX was found.')

# Normalize IP columns
alert_df['IP地址'] = alert_df['IP地址'].astype(str).str.strip()
asset_df['IP地址'] = asset_df['IP地址'].astype(str).str.strip()

# Drop duplicates on asset table by IP address
asset_df = asset_df.drop_duplicates(subset=['IP地址'], keep='last')

# Merge inner
merged_df = alert_df.merge(asset_df, on='IP地址', how='inner')

# Save result
merged_df.to_csv(output_csv, index=False, encoding='utf-8-sig')

print('原始告警行数:', len(alert_df))
print('匹配成功的告警行数:', len(merged_df))
print('Saved merged file to:', output_csv)
