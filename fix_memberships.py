"""
Script to fix membership statuses in database
Run this once to fix existing data
"""
from app import create_app
from app.extensions import db
from app.models import Membership
from datetime import datetime, timezone

app = create_app()

with app.app_context():
    # Get all memberships for the user, ordered by start date
    memberships = Membership.query.order_by(Membership.start_date.asc()).all()

    now = datetime.now(timezone.utc)

    print(f"Found {len(memberships)} memberships")

    for membership in memberships:
        # Make end_date timezone aware if needed
        end_date = membership.end_date
        if end_date and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        print(f"\nMembership ID: {membership.id}")
        print(f"  Package: {membership.package.name}")
        print(f"  Start: {membership.start_date}")
        print(f"  End: {membership.end_date}")
        print(f"  Current Active: {membership.active}")

        # Logic: Only the membership with latest end date that hasn't expired should be active
        # All others should be inactive

    # Find the membership that should be active
    # It's the one with the earliest end date that hasn't expired yet
    active_membership = None
    for membership in memberships:
        end_date = membership.end_date
        if end_date and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        start_date = membership.start_date
        if start_date and start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)

        # Check if this membership should be active
        # Active if: start_date <= now < end_date
        if start_date <= now < end_date:
            active_membership = membership
            break

    # Update all memberships
    for membership in memberships:
        old_active = membership.active

        if membership == active_membership:
            membership.active = True
        else:
            membership.active = False

        if old_active != membership.active:
            print(f"\n✓ Updated Membership ID {membership.id} ({membership.package.name}): active={membership.active}")

    db.session.commit()
    print("\n✓ All memberships updated successfully!")
