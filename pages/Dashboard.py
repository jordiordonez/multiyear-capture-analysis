import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import unicodedata

COLOR_FORECAST = '#d9d9d9'
COLOR_APPS_BELOW = '#ff7f0e'
COLOR_APPS_ABOVE = '#d62728'
TIPUS_COLORS = {
    'General': '#1f77b4',
    'Reserva': '#2ca02c',
    'Altres': '#9467bd',
}
ESTRANGER_COLORS = {'Si': '#d62728', 'No': '#1f77b4'}
PARROQUIA_COLORS = {
    'Andorra la Vella': '#2ca02c',
    'Escaldes-Engordany': '#ff7f0e',
    'Encamp': '#17becf',
    'La Massana': '#bcbd22',
    'Ordino': '#8c564b',
    'Canillo': '#e377c2',
    'Sant Julià de Lòria': '#7f7f7f',
}


def strip_accents(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {}
    for col in df.columns:
        key = strip_accents(col).lower().replace(' ', '_')
        mapping[col] = key
    rename = {}
    for col, key in mapping.items():
        if key in {'sorteig'}:
            rename[col] = 'Sorteig'
        elif key in {'tipus'}:
            rename[col] = 'Tipus'
        elif key in {'assignacions_previstes', 'previstes', 'forecast'}:
            rename[col] = 'Assignacions_previstes'
        elif key in {'assignacions_finals', 'finals', 'final', 'assignacions_definitives'}:
            rename[col] = 'Assignacions_finals'
        elif key in {'sol_licituds', 'sollicituds', 'applications', 'demand'}:
            rename[col] = 'Sol_licituds'
    df = df.rename(columns=rename)
    required = {'Sorteig', 'Tipus', 'Assignacions_previstes',
                'Assignacions_finals', 'Sol_licituds'}
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.warning('Falten columnes: ' + ', '.join(missing))
    return df


@st.cache_data
def build_summaries(resultat_df: pd.DataFrame,
                    resums_list: list[pd.DataFrame]):
    if resums_list:
        summary = pd.concat(resums_list, ignore_index=True)
        summary = standardize_columns(summary)
    else:
        summary = standardize_columns(resultat_df)
    for col in ['Assignacions_previstes', 'Assignacions_finals', 'Sol_licituds']:
        if col not in summary.columns:
            summary[col] = 0
        summary[col] = pd.to_numeric(summary[col], errors='coerce').fillna(0).astype(int)
    # group only when the required columns are present
    if {'Sorteig', 'Tipus'}.issubset(summary.columns):
        summary_tipus = summary.groupby(['Sorteig', 'Tipus'], as_index=False)[
            'Assignacions_finals'].sum()
    else:
        summary_tipus = pd.DataFrame(columns=['Sorteig', 'Tipus',
                                             'Assignacions_finals'])

    if 'Sorteig' in summary.columns:
        summary_totals = summary.groupby('Sorteig', as_index=False)[
            ['Assignacions_previstes',
             'Assignacions_finals', 'Sol_licituds']].sum()
    else:
        summary_totals = pd.DataFrame(columns=['Sorteig',
            'Assignacions_previstes', 'Assignacions_finals', 'Sol_licituds'])

    return summary_totals, summary_tipus


def load_demo():
    df = pd.DataFrame({
        'Sorteig': ['S1'] * 20 + ['S2'] * 15,
        'Tipus': ['General'] * 15 + ['Reserva'] * 5 + ['General'] * 10 + ['Altres'] * 5,
        'Estranger': ['No'] * 25 + ['Si'] * 10,
        'Modalitat': ['A'] * 20 + ['B'] * 15,
        'Parroquia': ['Andorra la Vella'] * 10 + ['La Massana'] * 10 + ['Encamp'] * 15,
        'Prioritat': np.random.randint(1, 5, size=35),
        'Assignacions_previstes': [12] * 20 + [10] * 15,
        'Assignacions_finals': [1] * 12 + [0] * 8 + [1] * 10 + [0] * 5,
        'Sol_licituds': [20] * 20 + [15] * 15,
    })
    st.session_state['resultat'] = df
    st.session_state['resums'] = []


def plot_main_chart(totals: pd.DataFrame, details: pd.DataFrame):
    sorteigs = totals['Sorteig']
    pivot = details.pivot_table(index='Sorteig', columns='Tipus',
                               values='Assignacions_finals', fill_value=0)
    pivot = pivot.reindex(sorteigs)
    fig = go.Figure()
    if 'Assignacions_previstes' in totals.columns:
        fig.add_trace(go.Bar(
            x=totals['Assignacions_previstes'],
            y=totals['Sorteig'],
            orientation='h',
            marker_color=COLOR_FORECAST,
            name='Previstes',
        ))
    cumulative = np.zeros(len(pivot))
    for tip in pivot.columns:
        vals = pivot[tip].values
        fig.add_trace(go.Bar(
            x=vals,
            y=sorteigs,
            orientation='h',
            base=cumulative,
            marker_color=TIPUS_COLORS.get(tip, None),
            name=tip,
        ))
        cumulative += vals
    for idx, row in totals.iterrows():
        if 'Sol_licituds' in row:
            color = COLOR_APPS_BELOW if row['Sol_licituds'] <= row['Assignacions_previstes'] else COLOR_APPS_ABOVE
            fig.add_trace(go.Scatter(
                x=[row['Sol_licituds']],
                y=[row['Sorteig']],
                mode='markers',
                marker_symbol='line-ns-open',
                marker_line_color=color,
                marker_color=color,
                marker_size=12,
                name='Sol·licituds' if idx == 0 else None,
            ))
    max_val = 0
    if not totals.empty:
        max_val = totals[['Assignacions_previstes', 'Assignacions_finals', 'Sol_licituds']].max().max()
    fig.update_layout(
        barmode='overlay',
        xaxis_range=[0, max_val * 1.05 if max_val else 1],
        xaxis_title='Captures',
        yaxis_title='',
        height=400,
    )
    return fig


def plot_drill(data: pd.DataFrame, dim: str):
    if dim == 'Tipus':
        grp = data.groupby('Tipus')['Assignacions_finals'].sum().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=grp['Assignacions_finals'],
            y=grp['Tipus'],
            orientation='h',
            marker_color=[TIPUS_COLORS.get(t, '#888') for t in grp['Tipus']],
        ))
        fig.update_layout(height=350, xaxis_title='Assignacions')
    elif dim == 'Estranger' and 'Estranger' in data.columns:
        grp = data.groupby('Estranger')['Assignacions_finals'].sum().reset_index()
        colors = [ESTRANGER_COLORS.get(x, '#888') for x in grp['Estranger']]
        fig = go.Figure(go.Bar(x=grp['Assignacions_finals'], y=grp['Estranger'],
                               orientation='h', marker_color=colors))
        fig.update_layout(height=350, xaxis_title='Assignacions')
    elif dim == 'Parròquia' and 'Parroquia' in data.columns:
        grp = data.groupby('Parroquia')['Assignacions_finals'].sum().reset_index()
        colors = [PARROQUIA_COLORS.get(x, '#888') for x in grp['Parroquia']]
        fig = go.Figure(go.Bar(x=grp['Assignacions_finals'], y=grp['Parroquia'],
                               orientation='h', marker_color=colors))
        fig.update_layout(height=350, xaxis_title='Assignacions')
    else:  # Prioritat
        if 'Prioritat' not in data.columns:
            return go.Figure()
        grp = data.groupby('Prioritat')['Assignacions_finals'].sum().reset_index()
        fig = go.Figure(go.Bar(x=grp['Assignacions_finals'], y=grp['Prioritat'],
                               orientation='h'))
        fig.update_layout(height=350, xaxis_title='Assignacions')
    return fig


def main():
    st.set_page_config(
        page_title='📊 Resultats sorteig',
        layout='wide',
        menu_items={'Get Help': None, 'Report a bug': None, 'About': None},
    )
    st.markdown(
        """
        <style>
        header[data-testid="stHeader"] {display: none;}
        section[data-testid="stSidebarNav"],
        nav[data-testid="stSidebarNav"],
        ul[data-testid="stSidebarNavItems"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    default_idx = 1 if st.session_state.get('section') == 'Dashboard' else 0
    with st.sidebar:
        section = option_menu(
            'Menú', ['Sorteig', 'Dashboard'],
            icons=['dice-5', 'bar-chart'], default_index=default_idx,
        )
        st.session_state['section'] = section
    if section == 'Sorteig':
        st.switch_page('app_sorteig.py')

    if 'resultat' not in st.session_state:
        st.error('⚠️ Primer executa un sorteig des de la pestanya «🎲 Sorteig».')
        if st.button('Carregar demo'):
            load_demo()
        else:
            return
    df = standardize_columns(st.session_state['resultat'])
    resums = [standardize_columns(r) for r in st.session_state.get('resums', [])]
    totals, details = build_summaries(df, resums)

    with st.sidebar:
        st.header('Filtres')
        mod_sel = []
        if 'Modalitat' in df.columns:
            mod_sel = st.multiselect('Modalitat', sorted(df['Modalitat'].dropna().unique()))
        parro_sel = []
        if 'Parroquia' in df.columns and df['Parroquia'].dropna().nunique() > 1:
            parro_sel = st.multiselect('Parròquia', sorted(df['Parroquia'].dropna().unique()))
        pri_max = int(df.get('Prioritat', pd.Series([0])).max())
        pri_sel = st.slider('Prioritat', 0, pri_max, (0, pri_max))
        sorteig_opts = sorted(df['Sorteig'].dropna().unique())
        sorteig_sel = st.multiselect('Sorteig', sorteig_opts, default=sorteig_opts)
        show_only = st.checkbox('Mostrar només seleccionats')

    mask = pd.Series(True, index=df.index)
    if mod_sel:
        mask &= df['Modalitat'].isin(mod_sel)
    if parro_sel:
        mask &= df['Parroquia'].isin(parro_sel)
    mask &= df['Prioritat'].between(pri_sel[0], pri_sel[1])
    if show_only and sorteig_sel:
        mask &= df['Sorteig'].isin(sorteig_sel)

    data = df[mask]
    totals_filt = totals[totals['Sorteig'].isin(sorteig_sel)] if sorteig_sel else totals
    details_filt = details[details['Sorteig'].isin(sorteig_sel)] if sorteig_sel else details

    st.title('📊 Resultats del sorteig')

    if data.empty:
        st.info('No hi ha dades després dels filtres.')
        return

    total_apps = len(data)
    prev = totals_filt['Assignacions_previstes'].sum()
    finals = totals_filt['Assignacions_finals'].sum()
    k1, k2, k3 = st.columns(3)
    k1.metric('Sol·licituds totals', f'{total_apps:,}')
    k2.metric('Assignacions previstes', f'{prev:,}')
    cap2 = f"{prev/total_apps:.1%} del total" if total_apps else ""
    k2.caption(cap2)
    k3.metric('Assignacions finals', f'{finals:,}')
    cap3 = ''
    if total_apps:
        cap3 += f"{finals/total_apps:.1%} del total"
    if prev:
        cap3 += f" · {finals/prev:.1%} de previstes"
    k3.caption(cap3)

    st.plotly_chart(plot_main_chart(totals_filt, details_filt), use_container_width=True)

    dim_options = ['Tipus']
    if 'Estranger' in data.columns:
        dim_options.append('Estranger')
    if 'Parroquia' in data.columns:
        dim_options.append('Parròquia')
    if 'Prioritat' in data.columns:
        dim_options.append('Prioritat')
    dim = st.radio('Desglossament', dim_options, horizontal=True)
    drill_fig = plot_drill(data[data['Sorteig'].isin(sorteig_sel)], dim)
    st.plotly_chart(drill_fig, use_container_width=True)

    with st.expander('Dades filtrades'):
        st.dataframe(data, use_container_width=True)


if __name__ == '__main__':
    main()
