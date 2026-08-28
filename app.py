import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Complaint

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "complaints.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

CATEGORIES = ["Hostel", "Mess/Canteen", "Academics", "Infrastructure", "Wi-Fi/IT", "Other"]
STATUSES = ["Open", "In Progress", "Resolved"]
PRIORITIES = ["Low", "Medium", "High"]

# Order used to move a complaint to the "next" status with one click
STATUS_FLOW = {"Open": "In Progress", "In Progress": "Resolved", "Resolved": "Resolved"}


@app.route("/")
def index():
    """Dashboard: list complaints with optional search/filter, plus summary stats."""
    query = Complaint.query

    status_filter = request.args.get("status", "")
    category_filter = request.args.get("category", "")
    search_term = request.args.get("q", "").strip()

    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)
    if search_term:
        like_term = f"%{search_term}%"
        query = query.filter(
            db.or_(
                Complaint.title.ilike(like_term),
                Complaint.description.ilike(like_term),
            )
        )

    complaints = query.order_by(Complaint.created_at.desc()).all()

    total_count = Complaint.query.count()
    open_count = Complaint.query.filter_by(status="Open").count()
    in_progress_count = Complaint.query.filter_by(status="In Progress").count()
    resolved_count = Complaint.query.filter_by(status="Resolved").count()

    return render_template(
        "index.html",
        complaints=complaints,
        categories=CATEGORIES,
        statuses=STATUSES,
        status_filter=status_filter,
        category_filter=category_filter,
        search_term=search_term,
        total_count=total_count,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
    )


@app.route("/submit", methods=["GET", "POST"])
def submit_complaint():
    """Form to submit a new complaint."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "Other")
        location = request.form.get("location", "").strip()
        submitted_by = request.form.get("submitted_by", "").strip()
        priority = request.form.get("priority", "Medium")

        if not title or not description:
            flash("Title and description are required.", "danger")
            return render_template(
                "submit_complaint.html",
                categories=CATEGORIES,
                priorities=PRIORITIES,
                form_data=request.form,
            )

        new_complaint = Complaint(
            title=title,
            description=description,
            category=category,
            location=location or None,
            submitted_by=submitted_by or "Anonymous",
            priority=priority,
            status="Open",
            created_at=datetime.utcnow(),
        )
        db.session.add(new_complaint)
        db.session.commit()

        flash("Complaint submitted successfully!", "success")
        return redirect(url_for("index"))

    return render_template("submit_complaint.html", categories=CATEGORIES, priorities=PRIORITIES, form_data={})


@app.route("/complaint/<int:complaint_id>")
def complaint_detail(complaint_id):
    """Detail view for a single complaint."""
    complaint = Complaint.query.get_or_404(complaint_id)
    return render_template("complaint_detail.html", complaint=complaint, statuses=STATUSES)


@app.route("/complaint/<int:complaint_id>/update_status", methods=["POST"])
def update_status(complaint_id):
    """Update the status of a complaint from the detail page."""
    complaint = Complaint.query.get_or_404(complaint_id)
    new_status = request.form.get("status")

    if new_status in STATUSES:
        complaint.status = new_status
        db.session.commit()
        flash(f"Status updated to '{new_status}'.", "success")
    else:
        flash("Invalid status.", "danger")

    return redirect(url_for("complaint_detail", complaint_id=complaint.id))


@app.route("/complaint/<int:complaint_id>/delete", methods=["GET", "POST"])
def delete_complaint(complaint_id):
    """Delete a complaint, with a confirmation step."""
    complaint = Complaint.query.get_or_404(complaint_id)

    if request.method == "POST":
        db.session.delete(complaint)
        db.session.commit()
        flash("Complaint deleted.", "success")
        return redirect(url_for("index"))

    # GET request shows a confirmation page
    return render_template("confirm_delete.html", complaint=complaint)


def seed_sample_data():
    """Add a few sample complaints so the dashboard isn't empty on first run."""
    if Complaint.query.count() > 0:
        return

    samples = [
        Complaint(
            title="Wi-Fi not working in Block C hostel",
            description="The Wi-Fi router on the 2nd floor of Block C has been down for 3 days. "
            "Multiple students are unable to attend online classes.",
            category="Wi-Fi/IT",
            location="Hostel Block C, 2nd Floor",
            submitted_by="Anonymous",
            status="Open",
            priority="High",
        ),
        Complaint(
            title="Broken chairs in Lecture Hall 5",
            description="At least 6 chairs in LH-5 are broken and unsafe to sit on. "
            "Needs urgent replacement before next semester's classes.",
            category="Infrastructure",
            location="Lecture Hall 5, Academic Block",
            submitted_by="Rahul S.",
            status="In Progress",
            priority="Medium",
        ),
        Complaint(
            title="Food quality issue in mess",
            description="The dinner served yesterday was undercooked and several students complained "
            "of stomach issues afterward.",
            category="Mess/Canteen",
            location="Main Mess Hall",
            submitted_by="Anonymous",
            status="Open",
            priority="High",
        ),
        Complaint(
            title="Delay in semester grade uploads",
            description="Grades for the last semester have not been uploaded to the portal even "
            "though it has been 3 weeks since exams ended.",
            category="Academics",
            location="",
            submitted_by="Priya M.",
            status="Resolved",
            priority="Low",
        ),
    ]

    db.session.bulk_save_objects(samples)
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_sample_data()
    app.run(debug=True)
