
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)

FILE_NAME = "student_data_v2.csv"


# HOME / DATA ENTRY
@app.route("/")
def home():
    return render_template("form.html")


# SAVE LEARNING DATA
@app.route("/analyze", methods=["POST"])
def analyze():

    student_id = request.form["student_id"].strip()
    concept = request.form["concept"].strip()
    learning_method = request.form["learning_method"]
    study_time = float(request.form["study_time"])
    confidence = int(request.form["confidence"])
    immediate_score = float(request.form["immediate_score"])
    delayed_score = float(request.form["delayed_score"])

    retention = (
        (delayed_score / immediate_score) * 100
        if immediate_score > 0 else 0
    )

    score_difference = delayed_score - immediate_score

    new_data = pd.DataFrame([{
        "Student ID": student_id,
        "Concept": concept,
        "Learning Method": learning_method,
        "Study Time": study_time,
        "Confidence": confidence,
        "Immediate Score": immediate_score,
        "Delayed Score": delayed_score,
        "Retention": round(retention, 2),
        "Score Difference": round(score_difference, 2)
    }])

    if os.path.exists(FILE_NAME):
        old_data = pd.read_csv(FILE_NAME)
        updated_data = pd.concat(
            [old_data, new_data],
            ignore_index=True
        )
    else:
        updated_data = new_data

    updated_data.to_csv(FILE_NAME, index=False)

    return render_template(
        "result.html",
        student_id=student_id,
        concept=concept,
        learning_method=learning_method,
        study_time=study_time,
        confidence=confidence,
        immediate_score=immediate_score,
        delayed_score=delayed_score,
        retention=round(retention, 2),
        score_difference=round(score_difference, 2)
    )


# COMPARISON PAGE
@app.route("/comparison")
def comparison():

    if os.path.exists(FILE_NAME):
        data = pd.read_csv(FILE_NAME)
        data = data.reset_index(drop=True)
        records = data.to_dict(orient="records")
    else:
        records = []

    return render_template(
        "comparison.html",
        records=records
    )


# EDIT STUDENT RECORD
@app.route("/edit_record/<int:record_index>", methods=["GET", "POST"])
def edit_record(record_index):

    if not os.path.exists(FILE_NAME):
        return redirect(url_for("comparison"))

    data = pd.read_csv(FILE_NAME)
    data = data.reset_index(drop=True)

    if record_index < 0 or record_index >= len(data):
        return redirect(url_for("comparison"))

    if request.method == "POST":

        try:
            student_id = request.form["student_id"].strip()
            concept = request.form["concept"].strip()
            learning_method = request.form["learning_method"]
            study_time = float(request.form["study_time"])
            confidence = int(request.form["confidence"])
            immediate_score = float(request.form["immediate_score"])
            delayed_score = float(request.form["delayed_score"])

            if not student_id or not concept:
                raise ValueError("Student ID and concept are required.")

            if not 0 <= confidence <= 100:
                raise ValueError("Confidence must be between 0 and 100.")

            if not 0 <= immediate_score <= 100:
                raise ValueError("Immediate score must be between 0 and 100.")

            if not 0 <= delayed_score <= 100:
                raise ValueError("Delayed score must be between 0 and 100.")

            if study_time < 0:
                raise ValueError("Study time cannot be negative.")

            retention = (
                (delayed_score / immediate_score) * 100
                if immediate_score > 0 else 0
            )

            score_difference = delayed_score - immediate_score

            data.loc[record_index] = {
                "Student ID": student_id,
                "Concept": concept,
                "Learning Method": learning_method,
                "Study Time": study_time,
                "Confidence": confidence,
                "Immediate Score": immediate_score,
                "Delayed Score": delayed_score,
                "Retention": round(retention, 2),
                "Score Difference": round(score_difference, 2)
            }

            data.to_csv(FILE_NAME, index=False)

            return redirect(url_for("comparison"))

        except ValueError as error:
            record = data.iloc[record_index].to_dict()

            return render_template(
                "edit_record.html",
                record=record,
                record_index=record_index,
                error=str(error)
            )

    record = data.iloc[record_index].to_dict()

    return render_template(
        "edit_record.html",
        record=record,
        record_index=record_index
    )


# DELETE STUDENT RECORD
@app.route("/delete_record", methods=["POST"])
def delete_record():

    if not os.path.exists(FILE_NAME):
        return redirect(url_for("comparison"))

    try:
        record_index = int(request.form.get("record_index", -1))

        data = pd.read_csv(FILE_NAME)
        data = data.reset_index(drop=True)

        if record_index < 0 or record_index >= len(data):
            return redirect(url_for("comparison"))

        data = data.drop(index=record_index)
        data.to_csv(FILE_NAME, index=False)

    except (ValueError, pd.errors.EmptyDataError):
        pass

    return redirect(url_for("comparison"))


# ANALYSIS PAGE
@app.route("/analysis")
def analysis():

    if os.path.exists(FILE_NAME):
        data = pd.read_csv(FILE_NAME)

        concepts = sorted(
            data["Concept"].dropna().unique().tolist()
        )

        selected_concept = request.args.get("concept", "")

        if selected_concept in concepts:
            concept_data = data[
                data["Concept"] == selected_concept
            ]
        else:
            selected_concept = ""
            concept_data = data

        if not concept_data.empty:
            method_analysis = (
                concept_data.groupby("Learning Method")
                .agg(
                    Average_Immediate_Score=("Immediate Score", "mean"),
                    Average_Delayed_Score=("Delayed Score", "mean"),
                    Average_Retention=("Retention", "mean")
                )
                .round(2)
                .reset_index()
            )

            results = method_analysis.to_dict(orient="records")
        else:
            results = []

    else:
        concepts = []
        selected_concept = ""
        results = []

    return render_template(
        "analysis.html",
        concepts=concepts,
        selected_concept=selected_concept,
        results=results
    )


# DASHBOARD
@app.route("/dashboard")
def dashboard():

    selected_student_id = request.args.get(
        "student_id", ""
    ).strip()

    selected_concept = request.args.get(
        "concept", ""
    ).strip()

    not_found = False

    if os.path.exists(FILE_NAME):
        all_data = pd.read_csv(FILE_NAME)
        data = all_data.copy()

        if selected_student_id:
            data = data[
                data["Student ID"].astype(str).str.strip().str.lower()
                == selected_student_id.lower()
            ]

        if selected_concept:
            data = data[
                data["Concept"].astype(str).str.strip().str.lower()
                == selected_concept.lower()
            ]

        if data.empty and (selected_student_id or selected_concept):
            not_found = True

    else:
        all_data = pd.DataFrame()
        data = pd.DataFrame()

    # STUDENT DETAILS
    if not all_data.empty:
        student_details = (
            all_data.groupby("Student ID")
            .agg(
                Concepts=("Concept", lambda x: ", ".join(
                    sorted(set(x.dropna().astype(str)))
                )),
                Records=("Concept", "count"),
                Average_Score=("Immediate Score", "mean")
            )
            .round(2)
            .reset_index()
            .to_dict(orient="records")
        )
    else:
        student_details = []

    # DEFAULT DASHBOARD VALUES
    method_labels = []
    immediate_averages = []
    delayed_averages = []
    retention_averages = []
    student_labels = []
    student_immediate = []
    student_delayed = []
    study_time = []
    study_scores = []
    confidence_labels = []
    confidence_scores = []

    total_students = 0
    average_score = 0
    average_retention = 0

    recommendation_method = "Not available"
    recommendation_text = (
        "Add student learning data to receive recommendations."
    )
    performance_level = "Not available"

    # CALCULATE GRAPHS AND RECOMMENDATION
    if not data.empty:

        method_data = data.groupby("Learning Method").agg(
            immediate=("Immediate Score", "mean"),
            delayed=("Delayed Score", "mean"),
            retention=("Retention", "mean")
        ).round(2).reset_index()

        confidence_data = data.groupby("Confidence")[
            "Immediate Score"
        ].mean().round(2).reset_index()

        method_labels = method_data["Learning Method"].tolist()
        immediate_averages = method_data["immediate"].tolist()
        delayed_averages = method_data["delayed"].tolist()
        retention_averages = method_data["retention"].tolist()

        student_labels = data["Concept"].astype(str).tolist()
        student_immediate = data["Immediate Score"].tolist()
        student_delayed = data["Delayed Score"].tolist()

        study_time = data["Study Time"].tolist()
        study_scores = data["Immediate Score"].tolist()

        confidence_labels = confidence_data["Confidence"].astype(str).tolist()
        confidence_scores = confidence_data["Immediate Score"].tolist()

        total_students = len(data)
        average_score = round(data["Immediate Score"].mean(), 2)
        average_retention = round(data["Retention"].mean(), 2)

        if average_score >= 85:
            performance_level = "Excellent"
        elif average_score >= 70:
            performance_level = "Good"
        elif average_score >= 50:
            performance_level = "Average"
        else:
            performance_level = "Needs Improvement"

        best_method = method_data.sort_values(
            by="retention", ascending=False
        ).iloc[0]

        recommendation_method = best_method["Learning Method"]

        recommendation_text = (
            f"{recommendation_method} has the highest average knowledge "
            f"retention in the selected records. Continue using this method "
            f"and practise regularly to improve learning performance."
        )

    return render_template(
        "dashboard.html",
        method_labels=method_labels,
        immediate_averages=immediate_averages,
        delayed_averages=delayed_averages,
        retention_averages=retention_averages,
        student_labels=student_labels,
        student_immediate=student_immediate,
        student_delayed=student_delayed,
        study_time=study_time,
        study_scores=study_scores,
        confidence_labels=confidence_labels,
        confidence_scores=confidence_scores,
        total_students=total_students,
        average_score=average_score,
        average_retention=average_retention,
        selected_student_id=selected_student_id,
        selected_concept=selected_concept,
        not_found=not_found,
        student_details=student_details,
        recommendation_method=recommendation_method,
        recommendation_text=recommendation_text,
        performance_level=performance_level
    )


if __name__ == "__main__":
    app.run(debug=True)
