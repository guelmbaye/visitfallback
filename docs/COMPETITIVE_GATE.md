# Gate −1 — Competitive First (24 Nov 2026)

## Locked human problem

A care recipient needs an outbound trip, an in-person escort and a return trip for a medical appointment. A family helper cancels. The *whole chain* must remain covered; isolated offers or a partially filled calendar are not sufficient evidence.

## Existing alternatives: verified documented functions

| Alternative | Verified capability | What we have NOT established |
|---|---|---|
| ianacare | Tasks/asks, rides and appointments; supporters explicitly confirm with "I GOT THIS"; confirmed requests appear in task view; cancel-and-recreate flow for changed plans | Whether its current app automatically validates the entire trip/escort/return chain, continuity, and conflicts across commitments |
| Lotsa Helping Hands | Calendar tasks, ride coordination, volunteer signup, confirmations/reminders; activities may contain multiple tasks | Whether its current workflow performs automatic global consistency checks over dependent tasks and shared commitments |
| Caring Village | Shared care calendar, assigned tasks, care plans and messaging | Whether its current workflow prevents any incomplete multi-step chain from appearing covered |
| Ordinary shared calendar + chat | Reminders and coordinating offers | Whether a family can attain the same outcome via explicit checklist and manual review (yes, in principle) |

Sources (current official documentation):
- https://support.ianacare.com/hc/en-us/articles/35255491371661-What-is-the-Caregiver-Organizer-Tool
- https://support.ianacare.com/hc/en-us/articles/47294099253517-How-do-I-offer-help-to-my-caregiver
- https://support.ianacare.com/hc/en-us/articles/360042392232-How-do-I-edit-or-cancel-a-request
- https://lotsahelpinghands.com/how-it-works
- https://mycancercirclenet.lotsahelpinghands.com/help/pe_activities.html
- https://caringvillage.com/app/

**Competition status: UNRESOLVED.** We have no access to tested competitor instances or authorized user trials. Neither public marketing descriptions nor a negative search result establishes a capability gap. The two naive rules in our test harness are *baselines*, not stand-ins for the best competitors.

## Testable product proposition

Automatic, auditable, **all-obligations-must-be-confirmed** care handoff proof with people/capability/availability/commitment/temporal/location consistency. A 'help offered' event must never silently become 'help confirmed'. A confirmed task must never by itself declare a whole appointment covered.

**Relate necessity test**: Cypher graph holds the connected commitments, each evaluation reads live graph edges, and removing one capability edge changes the outcome. Graph should not simply decorate JSON state. SQL could still implement similar functionality; do not claim otherwise.

## Proceed / kill rules

- Technical GO to demo if real Relate + edge mutation + independent oracle pass, with zero false `COVERED` cases on the 11 adversarial fixtures.
- Competitive differentiation is **NOT yet proven**. Before making any 'better than competitor' claim, test the exact same appointment cancellation and conflicting handoff scenario within the strongest existing product, or remove the comparative claim.
- Safety NO-GO for real care coordination until consent, audit, secure identity, safety escalation, accessibility and privacy protections are specified and validated.
