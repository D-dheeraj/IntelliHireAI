import plotly.express as px


def match_chart(score):

    fig = px.pie(
        values=[score,100-score],
        names=["Match","Remaining"],
        hole=0.5
    )

    return fig
    
def candidate_chart(candidates):

    names = []

    scores = []


    for candidate in candidates:

        names.append(
            candidate.name
        )

        scores.append(
            candidate.match_score
        )


    fig = px.bar(

        x=names,

        y=scores,

        title="Candidate Match Ranking",

        labels={
            "x":"Candidates",
            "y":"Match Score"
        }

    )


    return fig   