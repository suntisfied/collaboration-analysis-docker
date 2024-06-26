from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import seaborn as sns
import matplotlib.colors as mcolors

def initialize_overall_app(dash_app, dataset):
    @dash_app.callback(
        Output('meeting-dropdown', 'options'),
        Input('view-type-radio', 'value')
    )
    def set_meeting_options(view_type):
        meetings = dataset['meeting_number'].unique()
        return [{'label': f'Meeting {i}', 'value': i} for i in meetings]

    @dash_app.callback(
        Output('speaker-dropdown', 'options'),
        Input('view-type-radio', 'value')
    )
    def set_speaker_options(view_type):
        speakers = dataset['speaker_number'].unique()
        return [{'label': f'Speaker {i}', 'value': i} for i in speakers]

    @dash_app.callback(
        [Output('meeting-dropdown', 'value'),
         Output('speaker-dropdown', 'value')],
        Input('reset-button', 'n_clicks')
    )
    def reset_filters(n_clicks):
        return None, None

    @dash_app.callback(
        Output('collaboration-score-graph', 'figure'),
        [Input('meeting-dropdown', 'value'),
         Input('speaker-dropdown', 'value'),
         Input('view-type-radio', 'value')]
    )
    def update_collaboration_score_graph(selected_meeting, selected_speakers, view_type):
        filtered_df = dataset

        if selected_meeting:
            filtered_df = filtered_df[filtered_df['meeting_number'].isin(selected_meeting)]
        if selected_speakers:
            filtered_df = filtered_df[filtered_df['speaker_number'].isin(selected_speakers)]

        fig = go.Figure()

        if view_type == 'total':
            overall_score_by_meeting = filtered_df.groupby('meeting_number')['overall_collaboration_score'].agg(['mean', 'std']).reset_index()
            fig.add_trace(go.Scatter(
                x=overall_score_by_meeting['meeting_number'],
                y=overall_score_by_meeting['mean'],
                mode='lines+markers',
                name='Mean Collaboration Score',
                line=dict(color='blue'),
                marker=dict(color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=overall_score_by_meeting['meeting_number'],
                y=overall_score_by_meeting['mean'],
                mode='markers',
                marker=dict(size=8, color='blue'),
                error_y=dict(
                    type='data',
                    array=overall_score_by_meeting['std'],
                    visible=True
                ),
                showlegend=False
            ))

        else:  # view_type == 'by_speakers'
            overall_score_by_meeting_speaker = filtered_df.groupby(['meeting_number', 'speaker_number'])['overall_collaboration_score'].agg(['mean']).reset_index()
            palette = sns.color_palette('tab10', n_colors=overall_score_by_meeting_speaker['speaker_number'].nunique())
            color_map = {speaker: mcolors.rgb2hex(palette[i % len(palette)]) for i, speaker in enumerate(overall_score_by_meeting_speaker['speaker_number'].unique())}

            for speaker in overall_score_by_meeting_speaker['speaker_number'].unique():
                speaker_data = overall_score_by_meeting_speaker[overall_score_by_meeting_speaker['speaker_number'] == speaker]
                color = color_map[speaker]
                fig.add_trace(go.Scatter(
                    x=speaker_data['meeting_number'],
                    y=speaker_data['mean'],
                    mode='lines+markers',
                    name=f'Speaker {speaker}',
                    line=dict(color=color),
                    marker=dict(color=color)
                ))

        fig.update_layout(
            title='Mean of Overall Collaboration Score by Meeting',
            xaxis_title='Meeting Number',
            yaxis_title='Mean Overall Collaboration Score',
            xaxis=dict(tickmode='array', tickvals=filtered_df['meeting_number'].unique()),
            showlegend=True
        )

        # Bar plot for selected meetings
        if selected_meeting:
            bar_data = filtered_df[filtered_df['meeting_number'].isin(selected_meeting)]
            if not bar_data.empty:
                bar_data_agg = bar_data.groupby('speaker_number')['overall_collaboration_score'].mean().reset_index()
                fig = go.Figure(data=[go.Bar(
                    x=bar_data_agg['speaker_number'],
                    y=bar_data_agg['overall_collaboration_score'],
                    marker_color=[color_map[speaker] for speaker in bar_data_agg['speaker_number']]
                )])
                fig.update_layout(
                    title='Mean Overall Collaboration Score by Speaker for Selected Meetings',
                    xaxis_title='Speaker Number',
                    yaxis_title='Overall Collaboration Score',
                    showlegend=False
                )

        return fig