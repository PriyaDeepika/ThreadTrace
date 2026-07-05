"""
seed/demo_seed.py — Populate ThreadTrace with realistic demo data.

Run once before your first demo:
    python seed/demo_seed.py

Creates 5 student cases with realistic documents, follow-ups, and blockers
that make every Cognee recall query return meaningful, compelling answers.

If Cognee is configured, it also ingests everything into memory so the
AI features work immediately on first demo.
"""

import sys
import os

# Make sure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta, datetime
from services import storage_service as storage
from services import cognee_service as cognee_svc

USE_COGNEE = cognee_svc.cognee_available()


def seed():
    print("=" * 60)
    print("ThreadTrace Demo Seed")
    print("=" * 60)
    if USE_COGNEE:
        print("✅ Cognee configured — will ingest into memory")
    else:
        print("⚠️  Cognee not configured — seeding local storage only")
        print("    Set COGNEE_BASE_URL + COGNEE_API_KEY to enable AI features")
    print()

    # ── CASE 1: Anjali Reddy ──────────────────────────────────────────────────
    print("Creating case 1: Anjali Reddy...")
    c1 = storage.create_case(
        student_name="Anjali Reddy",
        location="Kadapa",
        goal="Scholarship",
        target_program_or_scholarship="AP State Merit Scholarship",
        deadline=(date.today() + timedelta(days=4)).isoformat(),
        assigned_volunteer="Deepika",
        summary="First-generation learner from a farming family. Father is daily wage worker. Strong academic record — 92% in Class 12.",
        contact_number="9876543210",
        age="18",
        education_level="Class 12",
    )
    storage.add_document(c1["case_id"], "Income certificate", "missing",
                         "Family hasn't visited village office yet")
    storage.add_document(c1["case_id"], "Caste certificate", "submitted")
    storage.add_document(c1["case_id"], "Marks memo", "submitted")
    storage.add_document(c1["case_id"], "Aadhaar card", "submitted")
    storage.add_document(c1["case_id"], "SOP", "pending_verification",
                         "Revised draft submitted, waiting on mentor review")
    storage.add_followup(
        c1["case_id"], "Deepika",
        "Initial counseling call completed. Anjali is very motivated and has been tracking the scholarship deadline herself. She understands the requirements clearly.",
        blockers="", next_step="Send her the document checklist",
        followup_type="call",
    )
    storage.add_followup(
        c1["case_id"], "Deepika",
        "Called Anjali today. She confirmed caste certificate and marks memo are ready. Income certificate is still pending — her father needs to visit the village office but has been busy with harvest work. She sounded worried about the deadline.",
        blockers="Father hasn't visited village office for income certificate. Harvest season making it difficult.",
        next_step="Volunteer to follow up in 2 days. Ask her to request a relative to go instead if father can't.",
        followup_type="call",
    )
    storage.add_followup(
        c1["case_id"], "Meena",
        "Covering for Deepika today. Spoke with Anjali. She managed to get a neighbour to accompany her father. Income certificate may be ready by tomorrow. Also reviewed her SOP — it needs one more revision to highlight financial need more clearly.",
        blockers="SOP still needs revision. Income certificate not yet in hand.",
        next_step="Deepika to collect income certificate and final SOP by July 5",
        followup_type="call",
    )
    _ingest_case(c1, "Anjali Reddy", [
        "First-generation learner. Very motivated, tracks deadline herself.",
        "Caste certificate and marks memo submitted. Income certificate still missing — father delayed due to harvest season.",
        "SOP submitted but needs revision to better highlight financial hardship.",
        "Covering volunteer (Meena) spoke with student. Neighbour accompanying father to village office. Income cert expected tomorrow.",
        "SOP needs one more round of revision before submission.",
    ])

    # ── CASE 2: Ravi Kumar ────────────────────────────────────────────────────
    print("Creating case 2: Ravi Kumar...")
    c2 = storage.create_case(
        student_name="Ravi Kumar",
        location="Tirupati",
        goal="Fee reimbursement",
        target_program_or_scholarship="BC Welfare Fee Reimbursement + Hostel Support",
        deadline=(date.today() + timedelta(days=10)).isoformat(),
        assigned_volunteer="Arjun",
        summary="Enrolled in B.Tech at SVCE. First year. Needs fee reimbursement and hostel support. Unsure about the college letter format required for the reimbursement form.",
        contact_number="9123456780",
        age="19",
        education_level="Undergraduate",
    )
    storage.add_document(c2["case_id"], "Marks memo", "submitted")
    storage.add_document(c2["case_id"], "Aadhaar card", "submitted")
    storage.add_document(c2["case_id"], "Recommendation letter", "missing",
                         "College format unclear — student unsure which format is acceptable")
    storage.add_document(c2["case_id"], "Income certificate", "submitted")
    storage.add_document(c2["case_id"], "Bank passbook copy", "pending_verification")
    storage.add_followup(
        c2["case_id"], "Arjun",
        "Spoke with Ravi. He has uploaded marks memo and Aadhaar successfully. Very relieved about the hostel support possibility. Main concern is the recommendation letter — he isn't sure whether the department head or the principal should sign it.",
        blockers="Recommendation letter: unsure whether department head or principal should sign. College admin hasn't responded to his query.",
        next_step="Arjun to call the college welfare officer directly to clarify the format.",
        followup_type="call",
    )
    storage.add_followup(
        c2["case_id"], "Arjun",
        "Called the college welfare officer. Confirmed that BOTH department head and principal signatures are required. Shared the correct format template with Ravi over WhatsApp. He missed our scheduled call today — will try again tomorrow.",
        blockers="Ravi missed the follow-up call. Recommendation letter still not submitted.",
        next_step="Try to reach Ravi again tomorrow. Confirm he received the format template.",
        followup_type="call",
    )
    _ingest_case(c2, "Ravi Kumar", [
        "B.Tech student at SVCE needing fee reimbursement and hostel support.",
        "Marks memo, Aadhaar, income certificate all submitted. Recommendation letter still missing.",
        "Confusion about recommendation letter format — needs both department head AND principal signatures.",
        "Volunteer Arjun called college welfare officer and confirmed the format. Template sent to Ravi via WhatsApp.",
        "Ravi missed the second follow-up call. Not yet confirmed he received the template.",
    ])

    # ── CASE 3: Priya Shaik ───────────────────────────────────────────────────
    print("Creating case 3: Priya Shaik...")
    c3 = storage.create_case(
        student_name="Priya Shaik",
        location="Kurnool",
        goal="Admission support",
        target_program_or_scholarship="Government Nursing College Counseling",
        deadline=(date.today() + timedelta(days=2)).isoformat(),  # Very urgent
        assigned_volunteer="Deepika",
        summary="Wants a nursing seat in a government college. Family unable to pay the counseling fee upfront. Needs help understanding the counseling process and financial assistance options.",
        contact_number="9988776655",
        age="17",
        education_level="Class 12",
    )
    storage.add_document(c3["case_id"], "Caste certificate", "missing")
    storage.add_document(c3["case_id"], "Marks memo", "submitted")
    storage.add_document(c3["case_id"], "Income certificate", "submitted")
    storage.add_document(c3["case_id"], "Aadhaar card", "submitted")
    storage.add_document(c3["case_id"], "Counseling fee receipt", "missing",
                         "Family cannot pay upfront. Exploring fee waiver options.")
    storage.add_followup(
        c3["case_id"], "Deepika",
        "First contact with Priya. She is very keen on nursing. Academic performance is good. Main issue is the counseling fee — family doesn't have the money right now. Also, her caste certificate is not in hand yet.",
        blockers="Family cannot pay the ₹500 counseling fee. Caste certificate missing.",
        next_step="Explore whether the NGO has an emergency fund that can cover the counseling fee. Check if caste certificate can be obtained urgently.",
        followup_type="visit",
    )
    storage.add_followup(
        c3["case_id"], "Deepika",
        "Escalated to NGO coordinator about the fee. Coordinator has approved ₹500 from the emergency fund — Deepika will transfer today. Caste certificate: Priya's mother is at the tahsildar office right now trying to get it. Deadline is in 2 days.",
        blockers="Caste certificate still not in hand. Time is very short.",
        next_step="Confirm caste certificate by end of day. Transfer the counseling fee. Prepare Priya for the counseling process.",
        followup_type="message",
    )
    _ingest_case(c3, "Priya Shaik", [
        "Wants government nursing seat. Very motivated. Deadline in 2 days.",
        "Family cannot pay ₹500 counseling fee. NGO emergency fund approved — fee being transferred.",
        "Caste certificate missing. Mother at tahsildar office to get it urgently.",
        "Marks memo, income cert, Aadhaar all submitted.",
        "Extremely urgent — deadline in 2 days. Both caste certificate and counseling fee receipt still outstanding.",
    ])

    # ── CASE 4: Naveen Babu ───────────────────────────────────────────────────
    print("Creating case 4: Naveen Babu...")
    c4 = storage.create_case(
        student_name="Naveen Babu",
        location="Anantapur",
        goal="Scholarship",
        target_program_or_scholarship="Polytechnic Merit Scholarship",
        deadline=(date.today() + timedelta(days=12)).isoformat(),
        assigned_volunteer="Meena",
        summary="Polytechnic student. First time applying for any scholarship. Doesn't know how to fill the online application. Needs guidance through the process.",
        contact_number="9001234567",
        age="17",
        education_level="Diploma",
    )
    storage.add_document(c4["case_id"], "Marks memo", "submitted")
    storage.add_document(c4["case_id"], "Aadhaar card", "submitted")
    storage.add_document(c4["case_id"], "Bank passbook copy", "missing",
                         "Student doesn't have a personal bank account")
    storage.add_document(c4["case_id"], "Income certificate", "pending_verification")
    storage.add_followup(
        c4["case_id"], "Meena",
        "Met Naveen in person at the polytechnic. He is shy but eager. Has never applied online for anything before. Walked him through the scholarship portal. He got confused at the bank account section — he doesn't have a personal account, only a family joint account. Need to clarify whether a joint account is acceptable.",
        blockers="No personal bank account. Uses family joint account — unclear if acceptable for scholarship disbursement.",
        next_step="Call the scholarship helpline to confirm if joint account is acceptable. Also check if he can open a zero-balance account urgently.",
        followup_type="visit",
    )
    _ingest_case(c4, "Naveen Babu", [
        "First-time scholarship applicant. Needs hand-holding through the process.",
        "No personal bank account — only family joint account. Unclear if acceptable.",
        "Marks memo and Aadhaar submitted. Income certificate pending verification.",
        "Volunteer Meena met him in person. He is shy and not confident with online forms.",
        "Next step: clarify joint account policy and potentially open a zero-balance account.",
    ])

    # ── CASE 5: Sushmita Rao ─────────────────────────────────────────────────
    print("Creating case 5: Sushmita Rao...")
    c5 = storage.create_case(
        student_name="Sushmita Rao",
        location="Nellore",
        goal="Fee concession",
        target_program_or_scholarship="Private College Fee Concession (Management Quota)",
        deadline=(date.today() + timedelta(days=7)).isoformat(),
        assigned_volunteer="Arjun",
        summary="Bright student who got a management quota seat in a private college but cannot afford the fees. The college has a fee concession committee. She has already missed one follow-up due to travel.",
        contact_number="9765432198",
        age="18",
        education_level="Class 12",
    )
    storage.add_document(c5["case_id"], "Previous fee receipt", "missing")
    storage.add_document(c5["case_id"], "ID proof", "submitted")
    storage.add_document(c5["case_id"], "Income certificate", "submitted")
    storage.add_document(c5["case_id"], "Marks memo", "submitted")
    storage.add_document(c5["case_id"], "Aadhaar card", "submitted")
    storage.add_followup(
        c5["case_id"], "Arjun",
        "Sushmita is a strong student — 88% in boards. The college fee concession committee requires proof of previous fees paid. She was traveling to her native village when we last tried to connect. Finally reached her today.",
        blockers="Previous fee receipt missing — not sure which institution it should be from. Was traveling and missed earlier calls.",
        next_step="Clarify with the college exactly which fee receipt they need. Then Sushmita needs to collect it from her Class 12 school.",
        followup_type="call",
    )
    storage.add_followup(
        c5["case_id"], "Arjun",
        "Confirmed with the college admissions office: they need the Class 12 fee receipt from the last attended school. Sushmita says she has it but it's at her village home. She's returning on July 5. Deadline is July 9 — tight but doable.",
        blockers="Fee receipt is at the village home. She returns July 5 — only 4 days before deadline.",
        next_step="Confirm she has collected the receipt by July 6. Then review the concession application together.",
        followup_type="call",
    )
    _ingest_case(c5, "Sushmita Rao", [
        "Management quota seat secured. Needs fee concession from college committee.",
        "ID proof, income cert, marks memo, Aadhaar all submitted.",
        "Previous fee receipt (Class 12 school) still missing — it's at her village home.",
        "She returns from village on July 5. Deadline is July 9 — tight window.",
        "All other documents ready. Just the one missing receipt preventing submission.",
    ])

    print()
    print("=" * 60)
    print(f"✅ Demo data created: 5 cases, documents, follow-ups")
    if USE_COGNEE:
        print("✅ All cases ingested into Cognee memory")
    print()
    print("Run the app with:")
    print("  streamlit run app.py")
    print("=" * 60)


def _ingest_case(case: dict, student_name: str, notes: list):
    """Ingests the case context and all its notes into Cognee memory."""
    if not USE_COGNEE:
        return

    print(f"  → Ingesting {student_name} into Cognee...", end=" ", flush=True)
    try:
        cognee_svc.remember_case_context(
            case_id=case["case_id"],
            student_name=student_name,
            location=case["location"],
            goal=case["goal"],
            program=case["target_program_or_scholarship"],
            deadline=case["deadline"],
            volunteer=case["assigned_volunteer"],
            summary=case.get("summary", ""),
        )
        for note in notes:
            cognee_svc.remember_followup(
                case_id=case["case_id"],
                student_name=student_name,
                worker_name=case["assigned_volunteer"],
                note_text=note,
            )
        print("done")
    except Exception as e:
        print(f"failed ({e})")
        print(f"    (Local data was saved — only Cognee ingestion failed)")


if __name__ == "__main__":
    seed()
