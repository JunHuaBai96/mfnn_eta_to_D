import json, numpy as np, pandas as pd, pathlib

OUT = pathlib.Path(r'C:\Users\17868\OneDrive\Desktop\mfnn_eta_to_D\outputs\origin_data')
B = 0.30103  # log10(2)
LO, HI = -9.2, -7.6

base = np.linspace(LO, HI, 65)
kinks = np.array([LO + B, HI - B])          # -8.89897, -7.90103
x = np.unique(np.round(np.concatenate([base, kinks]), 6))
up = np.minimum(x + B, HI)
dn = np.maximum(x - B, LO)

df = pd.DataFrame({
    'x': x,
    'identity': x,
    'band_upper': np.round(up, 6),
    'band_lower': np.round(dn, 6),
})
df.to_csv(OUT / 'fig3_parity_reference_lines.csv', index=False, float_format='%.6f', lineterminator='\n')

spec = {
  'schema': 'fig3-protocol-W-origin-v2',
  'figure': 'Fig3_protocol_W_parity_metrics',
  'canvas_mm': [176.507, 58.893],
  'panel_layout_mm': {
    'a': {'left': 14.040, 'top': 6.020, 'width': 50.397, 'height': 44.045},
    'b': {'left': 86.006, 'top': 6.020, 'width': 39.576, 'height': 44.045},
    'c': {'left': 136.440, 'top': 6.020, 'width': 39.576, 'height': 44.045}
  },
  'parity_axis_limits': [LO, HI],
  'parity_x_ticks': [-9.0, -8.5, -8.0],
  'parity_y_ticks': [-9.0, -8.75, -8.5, -8.25, -8.0, -7.75],
  'parity_x_decimals': 1,
  'parity_y_decimals': 2,
  'log10_2_band': B,
  'mape_axis': {'limits': [0, 145], 'ticks': [0, 25, 50, 75, 100, 125], 'decimals': 0},
  'factor2_axis': {'limits': [0, 1.25], 'ticks': [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2], 'decimals': 1,
                    'reference_line': 1.0},
  'bar_categories': ['LF-only', 'HF-only', 'MFNN'],
  'bar_value_label_decimals': {'mape': 2, 'factor2': 'g3'},
  'n_points_total': 63, 'n_filled': 39, 'n_open': 24,
  'r2_mfnn_annotation': 'R2_MFNN = 0.392 +/- 0.094 (frozen; n_test = 15/seed)',
  'okabe_ito': {
    'LF-only': {'fill': '#E69F00', 'stroke': '#A87300'},
    'HF-only': {'fill': '#0072B2', 'stroke': '#004D7A'},
    'MFNN': {'fill': '#009E73', 'stroke': '#006B4E'},
    'reference_dark': '#333333',
    'reference_mid': '#7F7F7F',
    'band_fill': '#F3F3F3',
    'partial_seed_open': '#333333'
  },
  'fonts': {'family': 'Arial', 'tick_pt': 8, 'axis_title_a_pt': 9,
            'axis_title_bc_pt': 8, 'bar_x_label_pt': 7, 'bar_value_pt': 7.5,
            'legend_pt': 6, 'callout_pt': 6.5, 'panel_tag_pt': 10},
  'frame': {'four_side': True, 'ticks_direction': 'in', 'tick_length_pt': 3.5,
            'tick_width_pt': 0.75, 'axis_linewidth_pt': 0.75},
  'provenance': {
    'parity_points': 'outputs\\results\\protocol_W_parity_ensemble_points.csv',
    'reference_lines': 'geometry only (lims, log10(2) band); no metrics recomputed',
    'bars': 'frozen Protocol W table in outputs/PAPER_JCP_draft_EN.md (transcribed, not recomputed)',
    'frozen_metrics': {'mape': [[109.6, 13.13], [30.98, 4.43], [26.18, 1.33]],
                        'factor2': [[0.56, 0.10], [0.973, 0.033], [0.96, 0.033]],
                        'r2': [[-2.588, 0.399], [0.263, 0.076], [0.392, 0.094]]}
  }
}
(OUT / 'fig3_axis_ranges.json').write_text(json.dumps(spec, indent=2) + '\n', encoding='utf-8')

lines = []
lines.append('reflines rows=%d cols=%s' % (len(df), list(df.columns)))
lines.append('x min/max %.6f %.6f n=%d' % (x.min(), x.max(), len(x)))
lines.append('kinks in x: %s' % ([bool(np.isclose(x, k).any()) for k in kinks]))
lines.append('band_upper clipped rows=%d  band_lower clipped rows=%d' % (int((up == HI).sum()), int((dn == LO).sum())))
lines.append('first row: ' + df.iloc[0].to_dict().__str__())
lines.append('kink row: ' + df.loc[np.isclose(df.x, -8.898970).argmax()].to_dict().__str__())
lines.append('json bytes=%d' % len((OUT/'fig3_axis_ranges.json').read_bytes()))
(OUT / '_qa_reflines.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('OK')
